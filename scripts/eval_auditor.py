"""Auditor precision/recall on the hand-labelled set eval/auditor_labelled.jsonl -> eval/auditor_eval.md."""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from proofcall.domain.consent import ConsentLedger  # noqa: E402
from proofcall.domain.guardrails import audit_turn  # noqa: E402
from proofcall.domain.model import AgentConfig  # noqa: E402
from proofcall.domain.store import VariableStore  # noqa: E402


def evaluate(config_path: str, labelled_path: str):
    cfg = AgentConfig.from_dict(json.load(open(config_path, encoding="utf-8")))
    rows = [json.loads(l) for l in open(labelled_path, encoding="utf-8") if l.strip()]
    stats, misses = {}, []
    for i, r in enumerate(rows):
        store = VariableStore()
        for k, v in r["store"].items():
            store.set(k, v, source="tool")
        ledger = ConsentLedger()
        if r.get("consent"):
            purpose, quote, last = r["consent"]
            ledger.record(purpose, quote, last)
        got = {v.code for v in audit_turn(cfg, r.get("state", "pitch"), r["text"], r.get("action"), store, ledger,
                                          r["turn_index"], r["customer_texts"], r.get("agent_texts", []))}
        exp = set(r["expected"])
        for c in got | exp:
            s = stats.setdefault(c, {"tp": 0, "fp": 0, "fn": 0})
            s["tp" if c in got and c in exp else "fp" if c in got else "fn"] += 1
        if got != exp:
            misses.append({"case": i, "text": r["text"], "expected": sorted(exp), "got": sorted(got)})
    return rows, stats, misses


def markdown(rows, stats, misses, title: str, note: str) -> str:
    lines = [f"# {title}", "", f"Cases: {len(rows)}. Exact-match cases: {len(rows) - len(misses)}/{len(rows)}.", "", note, "",
             "| code | TP | FP | FN | precision | recall |", "|---|---|---|---|---|---|"]
    for c, s in sorted(stats.items()):
        p = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else None
        r = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else None
        lines.append(f"| {c} | {s['tp']} | {s['fp']} | {s['fn']} | {p if p is None else round(p, 3)} | {r if r is None else round(r, 3)} |")
    if misses:
        lines += ["", "Misses:", ""] + [f"- case {m['case']}: “{m['text']}” expected {m['expected']} got {m['got']}" for m in misses]
    return "\n".join(lines) + "\n"


DEV_NOTE = ("Written and labelled by the authors (Hinglish and Devanagari included). Used during development, so not held out. "
            "First run: 48/52 exact; the 4 misses ('₹2 lakh' matched the 2 in '2BHK', 'BHK' digits allowed as numbers, two "
            "Hinglish customers read as English) were fixed in the auditor.")
HELD_NOTE = ("Written and labelled by a separate labeller who saw only the rule definitions, never the code. Because its "
             "first-run misses were then fixed, it is no longer held out. First run (auditor unchanged): 53/60 exact, precision 1.0 for every code, recall gaps in offer, booking and "
             "availability phrasings (now fixed) and in spelled-out non-money numbers (not fixed: a known limit). "
             "First-run table: eval/auditor_heldout_eval_first_run.md.")


if __name__ == "__main__":
    cfg = os.path.join(ROOT, "configs/rehearsal_realestate.json")
    a = markdown(*evaluate(cfg, os.path.join(ROOT, "eval/auditor_labelled.jsonl")), "Auditor evaluation — development set", DEV_NOTE)
    b = markdown(*evaluate(cfg, os.path.join(ROOT, "eval/auditor_heldout_independent.jsonl")),
                 "Auditor evaluation — development set 2 (independently labelled, then used for fixes)", HELD_NOTE)
    open(os.path.join(ROOT, "eval/auditor_eval.md"), "w", encoding="utf-8").write(a + "\n" + b)
    print(a + "\n" + b)
