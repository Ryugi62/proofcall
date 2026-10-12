"""Assemble the Drive submission folder (one public link, per the round's submission field).

submission/
  00_README.md                      first page: what is different, rubric map, results (PDF made from this)
  01_agent_configuration/           platform export JSON (added by hand from CallKaro) + our export (prompt, variables, pathway, functions)
  02_call_recordings/               01_success.<ext>, 02_failure_mode.<ext> + transcripts
  03_testing/                       scenarios, report.md, results.json
  04_auditor_evaluation/            auditor_eval.md, held-out tables
Usage: python3 scripts/package_submission.py --run runs/<id> [--recordings dir] --out submission
Missing required parts are listed and the exit code is 1 (nothing is invented)."""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["01_agent_configuration/platform_export.json", "02_call_recordings/01_success.*",
            "02_call_recordings/02_failure_mode.*"]


def build(run_dir: str, recordings: str, out: str) -> list:
    os.makedirs(out, exist_ok=True)
    cfg = os.path.join(out, "01_agent_configuration")
    shutil.copytree(os.path.join(ROOT, "export"), os.path.join(cfg, "proofcall_export"), dirs_exist_ok=True)
    rec = os.path.join(out, "02_call_recordings")
    os.makedirs(rec, exist_ok=True)
    if recordings and os.path.isdir(recordings):
        for f in os.listdir(recordings):
            shutil.copy(os.path.join(recordings, f), rec)
    test = os.path.join(out, "03_testing")
    os.makedirs(test, exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "scenarios", "*.yaml")):
        shutil.copy(f, test)
    for f in ("report.md", "results.json"):
        if os.path.exists(os.path.join(run_dir, f)):
            shutil.copy(os.path.join(run_dir, f), test)
    ev = os.path.join(out, "04_auditor_evaluation")
    os.makedirs(ev, exist_ok=True)
    for f in glob.glob(os.path.join(ROOT, "eval", "*.md")):
        shutil.copy(f, ev)
    shutil.copy(os.path.join(ROOT, "README.md"), os.path.join(out, "00_README.md"))
    return [r for r in REQUIRED if not glob.glob(os.path.join(out, r))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--recordings", default="")
    ap.add_argument("--out", default=os.path.join(ROOT, "submission"))
    a = ap.parse_args()
    missing = build(a.run, a.recordings, a.out)
    for m in missing:
        print("MISSING", m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
