"""Submission folder: required parts are reported missing, never invented."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_package_lists_missing_platform_parts(tmp_path):
    out = tmp_path / "submission"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "package_submission.py"),
                        "--run", os.path.join(ROOT, "runs", "rehearsal-2026-10-12"), "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "MISSING 01_agent_configuration/platform_export.json" in r.stdout
    assert (out / "00_README.md").exists() and (out / "03_testing" / "report.md").exists()
    assert (out / "01_agent_configuration" / "proofcall_export" / "callkaro_functions" / "book_site_visit.py").exists()
