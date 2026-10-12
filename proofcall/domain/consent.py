"""Consent ledger: explicit consent = a verbatim affirmative customer quote, per purpose, revocable."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

AFFIRMATIVE = re.compile(
    r"\b(yes|yeah|yep|sure|okay|ok|go ahead|please do|do it|book it|send it|sounds good|fine|alright|no problem|"
    r"haan|haanji|han|ji haan|theek hai|thik hai|kar dijiye|kar do|bhej do|chalega|bilkul)\b|हाँ|हां|जी हाँ|ठीक है|कर दीजिए", re.I)
# Phrase-level negation is checked first; "no problem" and "don't worry" are not negations.
NEGATIVE = re.compile(
    r"\b(no(?! problem)|nope|not|don'?t(?! worry)|do not|nahi|nahin|mat|never|stop|wait|cancel|maybe|later)\b"
    r"|नहीं|मत|रुकिए", re.I)
REVOCATION = re.compile(
    r"\b(cancel|don'?t (?:book|send|want)|do not (?:book|send|call)|i changed my mind|remove my|stop calling|"
    r"take back|withdraw|mat (?:karo|kijiye)|nahi chahiye|cancel kar)\b|रद्द|मत कीजिए|नहीं चाहिए", re.I)
OPT_OUT = re.compile(
    r"\b(don'?t call (?:me )?again|stop calling|remove my (?:number|name)|do not call|never call|"
    r"call mat karna|dobara call mat)\b|दोबारा कॉल मत", re.I)


def detect_opt_out(text: str) -> bool:
    return bool(OPT_OUT.search(text or ""))


def _contains(haystack: str, needle: str) -> bool:
    h = " ".join(re.sub(r"[^\w\s']", " ", (haystack or "").lower()).split())
    n = " ".join(re.sub(r"[^\w\s']", " ", (needle or "").lower()).split())
    return bool(n) and n in h


def is_affirmative(text: str) -> bool:
    return bool(AFFIRMATIVE.search(text or "")) and not NEGATIVE.search(text or "")


def detect_revocation(text: str) -> bool:
    return bool(REVOCATION.search(text or ""))


@dataclass
class ConsentEntry:
    purpose: str
    quote: str
    revoked: bool = False
    revoked_by: str = ""


class ConsentLedger:
    def __init__(self) -> None:
        self._entries: Dict[str, ConsentEntry] = {}
        self.rejections: List[Dict[str, str]] = []

    def record(self, purpose: str, quote: str, last_customer_text: str) -> bool:
        """Accept only a quote that is literally in the last customer utterance and affirmative."""
        if not _contains(last_customer_text, quote):
            self.rejections.append({"purpose": purpose, "quote": quote, "reason": "quote not in last customer utterance"})
            return False
        if not is_affirmative(quote) or not is_affirmative(last_customer_text):
            self.rejections.append({"purpose": purpose, "quote": quote, "reason": "not an affirmative answer"})
            return False
        self._entries[purpose] = ConsentEntry(purpose=purpose, quote=quote)
        return True

    def has(self, purpose: str) -> bool:
        e = self._entries.get(purpose)
        return bool(e and not e.revoked)

    def get(self, purpose: str) -> Optional[ConsentEntry]:
        return self._entries.get(purpose)

    def revoke_all(self, customer_text: str) -> List[str]:
        revoked = []
        for e in self._entries.values():
            if not e.revoked:
                e.revoked, e.revoked_by = True, customer_text
                revoked.append(e.purpose)
        return revoked

    def snapshot(self) -> Dict[str, Dict[str, object]]:
        return {k: {"quote": e.quote, "revoked": e.revoked, "revoked_by": e.revoked_by} for k, e in self._entries.items()}
