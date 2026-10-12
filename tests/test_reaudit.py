"""Re-audit of an exported platform transcript (UC-6)."""
import json
import os

from proofcall.application.reaudit import reaudit
from proofcall.domain.model import AgentConfig

ROOT = os.path.dirname(os.path.dirname(__file__))
CFG = AgentConfig.from_dict(json.load(open(os.path.join(ROOT, "configs/rehearsal_realestate.json"), encoding="utf-8")))


def test_reaudit_flags_hallucinated_booking_and_passes_backed_one():
    turns = [
        {"role": "agent", "text": "Hi Rahul, this is Asha, an AI assistant. This call is recorded; is that okay?"},
        {"role": "customer", "text": "Yes. Book Saturday."},
        {"role": "agent", "text": "Done, your visit is booked!"},
        {"role": "customer", "text": "Great."},
        {"role": "agent", "text": "Done. Your site visit is booked for Saturday 10:30 AM.",
         "functions": [{"name": "book_site_visit", "args": {"slot": "Saturday 10:30 AM"},
                        "result": {"ok": True, "booking_id": "GL-1234", "slot": "Saturday 10:30 AM"}}]},
    ]
    r = reaudit(CFG, turns)
    codes = [[v["code"] for v in t["violations"]] for t in r["turns"]]
    assert codes[0] == []
    assert "BOOKING_UNBACKED" in codes[1]
    assert "ACTION_WITHOUT_CONSENT" in codes[2]      # booked without a recorded yes
