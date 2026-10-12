"""UC-4 export: the same config the runner used -> platform-neutral JSON, numbered prompt, variable table,
pathway diagram, and CallKaro-style in-call Python functions (@tool, async def, imports inside, return dict).
The consent rules in the generated functions are copied from proofcall.domain.consent (single source)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from ..domain import consent as consent_rules


def _numbered_prompt(cfg: Dict[str, Any]) -> str:
    c = cfg.get("company", {})
    out = [f"# {cfg['name']} — prompt (v{cfg.get('version', '0')})", "",
           "## 1. Role", f"1.1 You are {cfg.get('persona')}, an AI calling assistant for {c.get('name')}.", "",
           "## 2. Goal", f"2.1 {c.get('context', '')}", "",
           "## 3. Guardrails (numbered, non-contradicting)"]
    out += [f"3.{i + 1} {r}" for i, r in enumerate(cfg.get("global_rules", []))]
    out += ["", "## 4. Call flow (one node per state; transitions are conditions, not prompt text)"]
    for i, s in enumerate(cfg.get("states", [])):
        out += [f"### 4.{i + 1} Node `{s['name']}` — {s['goal']}", f"- Instructions: {s['instructions']}",
                f"- Allowed functions: {', '.join(s.get('allowed_actions', [])) or 'none'}",
                f"- Conditions: " + ("; ".join(f"{k} -> {v}" for k, v in s.get('transitions', {}).items()) or "end"),
                f"- If unsure / blocked, say: \"{s.get('fallback', '')}\"", ""]
    out += ["## 5. Intents", "", "| intent | resolved by |", "|---|---|"]
    out += [f"| {i['name']} | {i.get('resolves_with', '')} |" for i in cfg.get("intents", [])]
    out += ["", "## 6. Compliance"] + [f"- {k}: {v}" for k, v in cfg.get("compliance", {}).items()]
    return "\n".join(out) + "\n"


def _variables_md(cfg: Dict[str, Any]) -> str:
    rows = ["| variable | type | source | required | validation / meaning |", "|---|---|---|---|---|"]
    for v in cfg.get("variables", []):
        rows.append(f"| `{v['name']}` | {v.get('type', '')} | {v.get('source', '')} | {'yes' if v.get('required') else ''} | "
                    f"{v.get('validation') or v.get('description', '')} |")
    return "# Variables\n\nSource `tool` = may only be filled by a function result. Source `customer` = captured from " \
           "the customer's words. `post_call` = extracted after the call.\n\n" + "\n".join(rows) + "\n"


def _pathway_mermaid(cfg: Dict[str, Any]) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for s in cfg.get("states", []):
        for cond, target in s.get("transitions", {}).items():
            lines.append(f"  {s['name']} -- {cond} --> {target}")
    lines.append("```")
    return "# Pathway\n\n" + "\n".join(lines) + "\n"


FN_HEADER = """@tool
async def {name}({params}) -> dict:
    \"\"\"
{doc}
    \"\"\"
"""


def _fn(name: str, params: str, doc: str, body: str) -> str:
    doc = "\n".join("    " + line for line in doc.strip().splitlines())
    return FN_HEADER.format(name=name, params=params, doc=doc) + body


def callkaro_functions(cfg: Dict[str, Any], catalog: Dict[str, Any]) -> Dict[str, str]:
    """In-call function sources, one per config tool. Values are rendered here (`say`, English or Hinglish), so the
    model never has to produce a number. Consent is enforced inside the action functions: book_site_visit and
    send_brochure refuse without a consent_id that matches the customer's affirmative quote.
    The test harness executes exactly these sources (adapters/function_tools.py)."""
    cat = json.dumps(catalog, ensure_ascii=False)
    aff, neg = consent_rules.AFFIRMATIVE.pattern, consent_rules.NEGATIVE.pattern
    ctx = '    ctx = globals().get("x_context") or {}  # runtime-injected call context (phone, time)\n'
    check = f"""    import hashlib, re
    affirmative = re.compile(r\"\"\"{aff}\"\"\", re.I)
    negative = re.compile(r\"\"\"{neg}\"\"\", re.I)

    def consent_ok(purpose, consent_id, quote):
        q = quote or ""
        expected = "CN-" + hashlib.sha1((purpose + "|" + q).encode()).hexdigest()[:6].upper()
        return consent_id == expected and bool(affirmative.search(q)) and not negative.search(q)
"""
    hi = '(lang or "en").lower().startswith("hi")'
    src = {
        "get_price": _fn("get_price", 'bhk: str, lang: str = "en"', """
Exact price-sheet line for a configuration (2bhk, 3bhk or 4bhk). lang = "en" or "hi" (Hinglish).
Use whenever the customer asks about price, cost, rate or booking amount. Speak the returned `say` text.""", f"""    catalog = {cat}
    key = (bhk or "").lower().replace(" ", "")
    p = catalog["prices"].get(key)
    if not p:
        return {{"ok": False, "say": "Kaunsa configuration check karoon?" if {hi} else "Which configuration should I check?"}}
    if {hi}:
        say = f"{{key.upper()}} {{p['from']}} se shuru hota hai, GST aur stamp duty alag, booking amount {{p['booking_amount']}}."
    else:
        say = f"The {{key.upper()}} starts at {{p['from']}}, {{catalog['price_note']}}, with a booking amount of {{p['booking_amount']}}."
    return {{"ok": True, "bhk": key, "price_from": p["from"], "price_from_inr": p["from_inr"],
            "booking_amount": p["booking_amount"], "booking_amount_inr": p["booking_amount_inr"], "say": say}}
"""),
        "check_units": _fn("check_units", 'bhk: str, lang: str = "en"', """
Units left for a configuration. Use before saying anything is available or sold out. Speak the returned `say` text.""", f"""    catalog = {cat}
    key = (bhk or "").lower().replace(" ", "")
    if key not in catalog["units"]:
        return {{"ok": False, "say": "Kaunsa configuration check karoon?" if {hi} else "Which configuration should I check?"}}
    n = catalog["units"][key]
    if {hi}:
        say = (f"Haan, {{key.upper()}} abhi available hai." if n > 0 else
               f"{{key.upper()}} abhi poora sold out hai. Koi unit khulte hi main aapko call karwa sakti hoon.")
    else:
        say = (f"Yes, {{key.upper()}} homes are available right now." if n > 0 else
               f"The {{key.upper()}} homes are fully sold out right now. I can arrange a call if one opens up.")
    return {{"ok": True, "bhk": key, "units_left": n, "available": n > 0, "say": say}}
"""),
        "check_slots": _fn("check_slots", 'day: str, lang: str = "en"', """
Open site-visit slots for a day (today, tomorrow, saturday, sunday, weekday).
Use before offering or confirming any visit time. Offer first_slot by its exact label.""", f"""    catalog = {cat}
    d = (day or "").lower()
    slots = catalog["slots"].get(d)
    if slots is None:
        return {{"ok": False, "slots": "", "first_slot": "",
                "say": "Kaunsa din theek rahega, kal ya weekend?" if {hi} else "Which day suits you, tomorrow or the weekend?"}}
    if not slots:
        return {{"ok": True, "slots": "", "first_slot": "",
                "say": f"{{d}} koi slot khali nahi hai. Kal check karoon?" if {hi} else f"There are no open slots {{d}}. Shall I check tomorrow?"}}
    first = slots[0]
    return {{"ok": True, "slots": ", ".join(s["label"] for s in slots), "first_slot": first["label"], "first_slot_iso": first["iso"],
            "say": f"Sabse pehla khali slot {{first['label']}} hai." if {hi} else f"The earliest open slot is {{first['label']}}."}}
"""),
        "get_offer": _fn("get_offer", 'lang: str = "en"', """
Live offer, if any. Use whenever the customer asks for a discount, offer, waiver or cashback.
Never promise anything that is not returned here.""", f"""    catalog = {cat}
    offer = catalog.get("offer") or "none"
    if offer == "none":
        return {{"ok": True, "offer": "none",
                "say": "Abhi koi offer nahi chal raha, price sheet wala rate hi lagega." if {hi} else "There is no offer running right now; the price-sheet price applies."}}
    return {{"ok": True, "offer": offer, "say": f"Current offer: {{offer}}."}}
"""),
        "record_consent": _fn("record_consent", "purpose: str, customer_words: str, question_asked: str", """
Record explicit consent right after the customer answers a yes/no question that named the action
(purpose = site_visit or whatsapp). Pass the question you asked and the customer's exact words.
Returns consent_id only for a clear yes; pass consent_id and customer_words to the action function.""", ctx + check + """    if not affirmative.search(customer_words or "") or negative.search(customer_words or ""):
        return {"ok": True, "accepted": False, "reason": "not a clear yes", "say": "No problem, I won't do that."}
    cid = "CN-" + hashlib.sha1((purpose + "|" + customer_words).encode()).hexdigest()[:6].upper()
    return {"ok": True, "accepted": True, "consent_id": cid, "purpose": purpose, "quote": customer_words,
            "question": question_asked, "recorded_at": ctx.get("current_time", "")}
"""),
        "book_site_visit": _fn("book_site_visit", 'slot: str, consent_id: str, consent_quote: str, lang: str = "en"', """
Book a site visit for an exact open slot label. Refuses unless consent_id matches the customer's yes
(from record_consent, purpose site_visit).""", ctx + check + f"""    catalog = {cat}
    if not consent_ok("site_visit", consent_id, consent_quote):
        return {{"ok": False, "reason": "no valid consent", "say": "Pehle confirm kar loon, visit book karoon?" if {hi} else "Before I book, may I confirm you want the visit?"}}
    match = [s for v in catalog["slots"].values() for s in v if s["label"] == slot]
    if not match:
        return {{"ok": False, "reason": "slot not open", "say": "Yeh time khali nahi hai, main dobara check karti hoon." if {hi} else "That time is not open. Let me check the open slots again."}}
    seed = slot + ctx.get("user_phone_number", "") + ctx.get("current_time", "")
    ref = "GL-" + str(int(hashlib.sha1(seed.encode()).hexdigest(), 16) % 9000 + 1000)
    say = (f"Ho gaya, aapka site visit {{slot}} ke liye book hai. Reference {{ref}} WhatsApp par bhi aa jayega." if {hi}
           else f"Done. Your site visit is booked for {{slot}}. Your reference {{ref}} will also come on WhatsApp.")
    return {{"ok": True, "booking_id": ref, "slot": slot, "slot_iso": match[0]["iso"], "say": say}}
"""),
        "cancel_booking": _fn("cancel_booking", 'booking_id: str, reason: str, lang: str = "en"', """
Cancel a site visit booked earlier in this call when the customer withdraws.""", f"""    if not (booking_id or "").startswith("GL-"):
        return {{"ok": False, "say": "There is no booking to cancel."}}
    return {{"ok": True, "cancelled": booking_id, "reason": reason,
            "say": "Theek hai, visit cancel kar diya." if {hi} else "Okay, I have cancelled that visit."}}
"""),
        "send_brochure": _fn("send_brochure", 'consent_id: str, consent_quote: str, lang: str = "en"', """
Send the project brochure on WhatsApp to the number on this call. Refuses unless consent_id matches the
customer's yes (record_consent, purpose whatsapp).""", ctx + check + f"""    if not consent_ok("whatsapp", consent_id, consent_quote):
        return {{"ok": False, "reason": "no valid consent", "say": "Kya main brochure WhatsApp par bhej doon?" if {hi} else "Shall I send the brochure to this WhatsApp number?"}}
    return {{"ok": True, "sent": True, "to": ctx.get("user_phone_number", ""),
            "say": "Ho gaya, brochure aapke WhatsApp par aa raha hai." if {hi} else "Done, the brochure is on its way to this WhatsApp number."}}
"""),
        "schedule_callback": _fn("schedule_callback", 'when: str, reason: str, lang: str = "en"', """
Note a callback when the customer asks to be called later or wants a call when a sold-out unit opens up.""",
            f"""    return {{"ok": True, "when": when, "reason": reason,
            "say": ("Theek hai, hum aapko " + (when or "jaldi") + " call karenge.") if {hi} else ("Noted, we will call you back " + (when or "soon") + ".")}}
"""),
        "mark_dnd": _fn("mark_dnd", 'reason: str, lang: str = "en"', """
The customer asked not to be called again. Add this number to the do-not-call list, then end the call.""",
            ctx + f"""    return {{"ok": True, "dnd": True, "number": ctx.get("user_phone_number", ""), "reason": reason,
            "say": "Samajh gayi, hum aapko dobara call nahi karenge. Maaf kijiye." if {hi} else "Understood. We will not call you again. Sorry for the trouble."}}
"""),
        "transfer_to_sales": _fn("transfer_to_sales", 'summary: str, lang: str = "en"', """
Warm transfer to a human sales executive (maps to the platform transfer_call, warm mode) with a one-line summary.""",
            f"""    return {{"ok": True, "summary": summary,
            "say": "Main aapko abhi sales manager se connect karti hoon, ek moment." if {hi} else "I'm connecting you to our sales manager now, one moment."}}
"""),
        "end_call": _fn("end_call", "reason: str", """
End the call (maps to the platform end_call) once the outcome is clear or the customer wants to stop.""",
            """    return {"ok": True, "reason": reason}
"""),
    }
    names = [t_["name"] for t_ in cfg.get("tools", [])]
    return {f"{n}.py": src[n] for n in names if n in src}


EXPRESSIONS = {"booked": "(book_site_visit_ok == True)", "sent": "(send_brochure_ok == True)",
               "sold_out": "(check_units_available == False)"}
CK_TYPE = {"integer": "Number", "integer_inr": "Number", "boolean": "Boolean", "turn_index": "Number"}
GLOBAL_JUMPS = {
    "opt_out": "Whenever the customer asks not to be called again or to remove their number.",
    "ask_human": "Whenever the customer asks to speak to a human, a manager or a sales executive, or says they are ready to buy.",
    "ask_if_bot": "Whenever the customer asks if they are talking to a bot, an AI or a real person.",
    "refuse_recording": "Whenever the customer objects to the call being recorded.",
}


def callkaro_pathway(cfg: Dict[str, Any]) -> str:
    """Build sheet in the CallKaro Pathway editor's own vocabulary (Agent Persona, nodes, Conditions, global nodes,
    Extract Variables, Functions, Post Call Variables). Field names follow docs.callkaro.ai (Mode 4 — Pathway)."""
    intents = {i["name"]: i for i in cfg.get("intents", [])}
    out = ["# CallKaro Pathway build sheet", "",
           "Generated from the same config the tests ran. Field names follow the Pathway editor (docs.callkaro.ai, Mode 4).", "",
           "## Agent Persona", ""]
    out += [f"{i + 1}. {r}" for i, r in enumerate(cfg.get("global_rules", []))]
    out += ["", f"Start node: `{cfg.get('initial_state')}`", ""]
    for s in cfg.get("states", []):
        out += [f"## Node `{s['name']}`", f"- System Prompt: {s['instructions']}",
                f"- Functions: {', '.join(s.get('allowed_actions', [])) or 'none'}",
                "- Message While Switching: Dynamic — one short connecting line, no facts",
                f"- Fallback line (when the auditor blocks a draft): {s.get('fallback', '')}"]
        for cond, target in s.get("transitions", {}).items():
            if cond in EXPRESSIONS:
                out.append(f"- Condition (Expression): `{EXPRESSIONS[cond]}` → `{target}`")
                continue
            desc = intents.get(cond, {}).get("description") or cond.replace("_", " ")
            out.append(f"- Condition (Prompt): \"The customer {desc}.\" → `{target}`")
        out.append("")
    out += ["## Global nodes", ""]
    for name, when in GLOBAL_JUMPS.items():
        if name in intents:
            out.append(f"- `{name}` — When to jump: \"{when}\" → resolves with {intents[name].get('resolves_with', '')}")
    out += ["", "## Extract Variables (captured during the call)", "", "| Type | Name | Description | Required |", "|---|---|---|---|"]
    for v in cfg.get("variables", []):
        if v.get("source") == "customer":
            out.append(f"| {CK_TYPE.get(v.get('type', ''), 'String')} | {v['name'].replace('.', '_')} | "
                       f"{v.get('validation') or v.get('description', '')} | {'yes' if v.get('required') else 'no'} |")
    out += ["", "## Post Call Variables", "", "| Type | Name | Description |", "|---|---|---|"]
    for v in cfg.get("variables", []):
        if v.get("source") == "post_call":
            kind = "Selector" if v.get("type", "").startswith("enum") else CK_TYPE.get(v.get("type", ""), "Text")
            out.append(f"| {kind} | {v['name'].replace('.', '_')} | {v.get('type', '')} {v.get('description', '')} |")
    out += ["", "## Expression Conditions used for consent gates", "",
            "- `book_site_visit` is called only after `record_consent` returned `accepted == True` for purpose `site_visit` "
            "in the same node (`visit_booking`).",
            "- `send_brochure` is called only after `record_consent` returned `accepted == True` for purpose `whatsapp`."]
    return "\n".join(out) + "\n"


def export_all(cfg: Dict[str, Any], out_dir: str, catalog: Dict[str, Any] = None) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    fn_dir = os.path.join(out_dir, "callkaro_functions")
    os.makedirs(fn_dir, exist_ok=True)
    paths = []

    def write(name: str, text: str) -> None:
        p = os.path.join(out_dir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        paths.append(p)

    write("agent_config.json", json.dumps(cfg, ensure_ascii=False, indent=1))
    write("prompt.md", _numbered_prompt(cfg))
    write("variables.md", _variables_md(cfg))
    write("pathway.md", _pathway_mermaid(cfg))
    write("callkaro_pathway_build_sheet.md", callkaro_pathway(cfg))
    if catalog is not None:
        for name, src in callkaro_functions(cfg, catalog).items():
            write(os.path.join("callkaro_functions", name), src)
    return paths
