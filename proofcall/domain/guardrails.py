"""Deterministic guardrail auditor and slot renderer. Pure functions, standard library only.

Rules (codes):
  PRICE_UNSOURCED        currency amount or percentage not present in any tool-sourced variable
  NUMBER_UNSOURCED       any other number not from a tool variable, the customer's own words, or the config
  <claim rule code>      e.g. AVAILABILITY_UNVERIFIED / BOOKING_UNBACKED: assertive claim before the backing tool result
  FORBIDDEN_CLAIM        phrase listed in config.forbidden_claims
  DISCLOSURE_MISSING     first agent turn lacks the configured disclosure
  ACTION_NOT_ALLOWED     action not allowed in the current state
  ACTION_WITHOUT_CONSENT consent-gated action without a live consent for its purpose
  SLOT_UNFILLED          slot whose variable is not set (raised by the agent engine after render_slots)
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .consent import ConsentLedger
from .model import AgentConfig, Violation
from .store import VariableStore

SLOT = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")
DIGITS = re.compile(r"\d[\d,]*(?:\.\d+)?")
CURRENCY_BEFORE = re.compile(r"(?:₹|\brs\.?|\binr|\brupees?|रु\.?)\s*$", re.I)
CURRENCY_AFTER = re.compile(r"^\s*(?:/-|%|percent\b|per ?cent\b|rupees?\b|rs\b|inr\b|lakh|lac\b|crore|k\b|"
                            r"thousand|hundred|per month|a month|/month|per year|a year|rupaye|rupaiye|रुपये|रुपए|प्रतिशत)", re.I)

UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
         "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
         "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
         # Hinglish (romanised Hindi)
         "ek": 1, "do": 2, "teen": 3, "tin": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6,
         "chhah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "barah": 12, "pandrah": 15,
         "bees": 20, "pachees": 25, "pachchis": 25, "tees": 30, "chalis": 40, "chalees": 40, "pachaas": 50,
         "pachas": 50, "sattar": 70, "assi": 80, "nabbe": 90, "dedh": 1.5, "dhai": 2.5, "adhai": 2.5,
         # Devanagari
         "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9,
         "दस": 10, "बीस": 20, "पच्चीस": 25, "तीस": 30, "चालीस": 40, "पचास": 50, "डेढ़": 1.5, "ढाई": 2.5}
SCALES = {"hundred": 100, "thousand": 1000, "lakh": 100000, "lac": 100000, "lakhs": 100000, "crore": 10000000,
          "sau": 100, "hazaar": 1000, "hazar": 1000, "hajar": 1000, "hazaar": 1000,
          "सौ": 100, "हज़ार": 1000, "हजार": 1000, "लाख": 100000, "करोड़": 10000000}
MONEY_WORDS = {"rupees", "rupee", "rs", "inr", "rupaye", "rupaiye", "rupay", "rupiya", "rupiye", "percent",
               "रुपये", "रुपए", "रुपया", "प्रतिशत", "mahina", "month", "monthly"}
AMBIGUOUS = {"do", "tin", "char", "bees", "das", "nau"}
TOKEN = re.compile(r"[A-Za-z\u0900-\u097F]+")
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _norm_number(tok: str) -> str:
    t = tok.replace(",", "")
    try:
        f = float(t)
    except ValueError:
        return t
    return str(int(f)) if f == int(f) else str(f)


def extract_numbers(text: str) -> List[str]:
    """Digit tokens, normalised ('₹1,499' -> '1499', '10:00' -> '10', '0')."""
    return [_norm_number(m.group(0)) for m in DIGITS.finditer((text or "").translate(DEVANAGARI_DIGITS))]


def _words_to_int(words: List[str]) -> Optional[float]:
    total, current, seen = 0, 0, False
    for w in words:
        if not w or w == "and":
            continue
        if w in UNITS:
            current += UNITS[w]
            seen = True
        elif w in SCALES:
            current = max(current, 1) * SCALES[w]
            if SCALES[w] >= 1000:
                total, current = total + current, 0
            seen = True
    val = total + current
    if not seen:
        return None
    return int(val) if float(val) == int(val) else val


def _amounts(text: str) -> List[Tuple[str, bool]]:
    """(normalised number, is_money) for digits and for spelled-out amounts with a scale or currency word."""
    out: List[Tuple[str, bool]] = []
    text = (text or "").translate(DEVANAGARI_DIGITS)
    for m in DIGITS.finditer(text):
        before, after = text[max(0, m.start() - 8):m.start()], text[m.end():m.end() + 12]
        if LABEL_AFTER.match(after):
            continue            # "2BHK", "3 BHK" are configuration names, not quantities
        money = bool(CURRENCY_BEFORE.search(before) or CURRENCY_AFTER.search(after))
        sc = SCALE_AFTER.match(after)
        if sc:                  # "₹2 lakh" is 200000, never just "2"
            val = float(m.group(0).replace(",", "")) * SCALE_OF[sc.group(1).lower()]
            out.append((_norm_number(str(round(val, 2))), True))
            continue
        out.append((_norm_number(m.group(0)), money))
    toks = [(m.group(0).lower(), m.start(), m.end()) for m in TOKEN.finditer(text)]
    def is_num(k: int) -> bool:
        w = toks[k][0]
        if w in AMBIGUOUS:      # English words that are also Hindi numbers: only with a scale/money word next
            nxt_w = toks[k + 1][0] if k + 1 < len(toks) else ""
            return nxt_w in SCALES or nxt_w in MONEY_WORDS
        return w in UNITS or w in SCALES

    i = 0
    while i < len(toks):
        if is_num(i):
            j = i
            while j < len(toks) and (is_num(j) or toks[j][0] == "and"):
                j += 1
            run = [w for (w, _, _) in toks[i:j] if w != "and"]
            nxt = toks[j][0] if j < len(toks) else ""
            prev = text[max(0, toks[i][1] - 8):toks[i][1]]
            has_scale = any(w in SCALES for w in run)
            money = has_scale or nxt in MONEY_WORDS or bool(CURRENCY_BEFORE.search(prev)) or \
                bool(CURRENCY_AFTER.search(text[toks[j - 1][2]:toks[j - 1][2] + 12]))
            if money and not (len(run) == 1 and run[0] in SCALES):
                val = _words_to_int(run)
                if val is not None:
                    out.append((_norm_number(str(val)), True))
            i = j
        else:
            i += 1
    return out


SCALED = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lac|crore|crores|k|thousand|हज़ार|लाख|करोड़)\b", re.I)
LABEL_AFTER = re.compile(r"^\s?(?:bhk|rk)\b", re.I)
SCALE_AFTER = re.compile(r"^\s*(lakh|lakhs|lac|crore|crores|thousand|हज़ार|लाख|करोड़)\b", re.I)
SCALE_OF = {"lakh": 100000, "lakhs": 100000, "lac": 100000, "crore": 10000000, "crores": 10000000, "k": 1000,
            "thousand": 1000, "हज़ार": 1000, "लाख": 100000, "करोड़": 10000000}


def _numbers_in(values: Iterable[Any]) -> Set[str]:
    """All numbers in tool values, plus absolute forms of '1.12 crore' / '5 lakh'."""
    found: Set[str] = set()
    for v in values:
        if isinstance(v, (dict, list)):
            found |= _numbers_in(v.values() if isinstance(v, dict) else v)
        else:
            s = str(v).translate(DEVANAGARI_DIGITS)
            found |= set(extract_numbers(s))
            for m in SCALED.finditer(s):
                found.add(_norm_number(str(round(float(m.group(1).replace(",", "")) * SCALE_OF[m.group(2).lower()], 2))))
    return found


def render_slots(text: str, store: VariableStore) -> Tuple[str, List[str]]:
    missing: List[str] = []

    def sub(m: "re.Match[str]") -> str:
        name = m.group(1)
        if not store.has(name) or store.get(name) in ("", None):
            missing.append(name)
            return m.group(0)
        return str(store.get(name))

    return SLOT.sub(sub, text or ""), missing


HINDI_CUSTOMER_EXTRA = {"ji", "bhej", "kariye", "karo", "batao", "bhai", "mujhe", "hoon", "kijiye", "haanji", "acha",
                        "accha", "nahi", "matlab", "rate", "kitne"}
HINDI_MARKERS = {"hai", "hain", "aap", "aapka", "aapko", "aapki", "kya", "nahi", "nahin", "kar", "karna", "karein",
                 "chahenge", "chahengi", "chahiye", "toh", "mein", "sirf", "bhi", "haan", "theek", "bataiye", "dijiye",
                 "hoga", "raha", "rahi", "gaya", "diya", "kijiye", "abhi", "kitna", "kab"}


def is_hindi(text: str, lenient: bool = False) -> bool:
    """Agent text: >=2 Hindi function words. Customer text (lenient): any Hindi word counts."""
    if re.search(r"[\u0900-\u097F]", text or ""):
        return True
    words = re.findall(r"[a-z]+", (text or "").lower())
    if lenient:
        return any(w in HINDI_MARKERS or w in HINDI_CUSTOMER_EXTRA for w in words)
    return sum(1 for w in words if w in HINDI_MARKERS) >= 2


def audit_turn(config: AgentConfig, state_name: str, spoken: str, action: Optional[Dict[str, Any]],
               store: VariableStore, ledger: ConsentLedger, turn_index: int,
               customer_texts: Sequence[str] = (), agent_texts: Sequence[str] = ()) -> List[Violation]:
    """Audit one agent turn (the text that will be spoken + the action it takes)."""
    vs: List[Violation] = []
    text = spoken or ""
    tool_nums = _numbers_in(store.values_from("tool"))
    const_nums = _numbers_in(store.values_from("constant")) | _numbers_in(config.raw.get("allowed_numbers", []))
    customer_nums = _numbers_in(customer_texts)

    for num, money in _amounts(text):
        if num in tool_nums:
            continue
        if money:
            vs.append(Violation("PRICE_UNSOURCED", f"amount {num} not returned by any tool in this call"))
        elif num not in customer_nums and num not in const_nums:
            vs.append(Violation("NUMBER_UNSOURCED", f"number {num} not from a tool, the customer or config"))

    for rule in config.claim_rules:
        m = re.search(rule.pattern, text, re.I)
        if m and not any(store.has_prefix(px) for px in rule.requires_var_prefix.split("|")):
            vs.append(Violation(rule.code, f"claim '{m.group(0)}' before any {rule.requires_var_prefix}* tool result"))

    for pat in config.forbidden_claims:
        m = re.search(pat, text, re.I)
        if m:
            vs.append(Violation("FORBIDDEN_CLAIM", f"forbidden phrase '{m.group(0)}'"))

    if turn_index == 0 and config.disclosure_required_any:
        if not any(p.lower() in text.lower() for p in config.disclosure_required_any):
            vs.append(Violation("DISCLOSURE_MISSING", "opening turn lacks disclosure: " + " / ".join(config.disclosure_required_any)))

    max_q = config.raw.get("max_questions_per_turn")
    if max_q and text.count("?") > max_q:
        vs.append(Violation("MULTI_QUESTION", f"{text.count('?')} questions in one turn (max {max_q})"))

    if config.raw.get("mirror_language") and customer_texts and text:
        if not any(is_hindi(c, lenient=True) for c in customer_texts) and is_hindi(text):
            vs.append(Violation("LANGUAGE_MISMATCH", "customer has spoken only English; agent replied in Hindi/Hinglish"))
        elif is_hindi(customer_texts[-1]) and not is_hindi(text, lenient=True) and len(text.split()) >= 4:
            vs.append(Violation("LANGUAGE_MISMATCH", "customer spoke Hindi; agent replied in English"))

    if action and action.get("name"):
        name = action["name"]
        must = config.raw.get("consent_must_name", {}).get(name)
        if must:
            value = str((action.get("args") or {}).get(must, ""))
            asked = agent_texts[-1] if agent_texts else ""
            if not value or value.lower() not in asked.lower():
                vs.append(Violation("SLOT_NOT_NAMED", f"{name}({must}={value!r}) was not named in the yes/no question"))
        try:
            allowed = config.state(state_name).allowed_actions
        except KeyError:
            allowed = []
        if name not in allowed:
            vs.append(Violation("ACTION_NOT_ALLOWED", f"action {name} not allowed in state {state_name}"))
        purpose = config.consent_gated_actions.get(name)
        if purpose and not ledger.has(purpose):
            vs.append(Violation("ACTION_WITHOUT_CONSENT", f"action {name} needs live consent for '{purpose}'"))
    return vs
