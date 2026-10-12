"""Build an anonymised text packet for mock / blind judging: README, export, report, two transcripts."""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def transcript(call):
    out = [f"### Call {call['scenario_id']} ({call['mode']}, run {call['run']}) — outcome {call['outcome']}, expected {call['expected']}"]
    for t in call["turns"]:
        if t["role"] == "agent":
            flag = " [blocked draft replaced]" if t.get("blocked") else ""
            out.append(f"AGENT ({t.get('model_ms')} ms){flag}: {t['text']}")
        else:
            out.append(f"CUSTOMER: {t['text']}")
    return "\n".join(out)


def main(run_dir, calls, out):
    parts = [open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()]
    for name in ["prompt.md", "variables.md", "pathway.md"]:
        parts.append(open(os.path.join(ROOT, "export", name), encoding="utf-8").read())
    for f in sorted(glob.glob(os.path.join(ROOT, "export", "callkaro_functions", "*.py")))[:5]:
        parts.append(f"# {os.path.basename(f)}\n```python\n" + open(f, encoding="utf-8").read() + "```")
    parts.append(open(os.path.join(run_dir, "report.md"), encoding="utf-8").read())
    data = json.load(open(os.path.join(run_dir, "results.json"), encoding="utf-8"))
    for key in calls:
        sid, mode, run = key.split(":")
        c = next(c for c in data["calls"] if c["scenario_id"] == sid and c["mode"] == mode and str(c["run"]) == run)
        parts.append(transcript(c))
    open(out, "w", encoding="utf-8").write("\n\n---\n\n".join(parts))
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2].split(","), sys.argv[3])
