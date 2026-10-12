"""sc: README numbers equal results files (scripts/update_readme.py --check)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_readme_results_block_is_generated():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "update_readme.py"), "--check"])
    assert r.returncode == 0, "README results block is stale: run python3 scripts/update_readme.py"


def test_auditor_has_no_false_positives_on_both_labelled_sets():
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import eval_auditor as ev
    cfg = os.path.join(ROOT, "configs/rehearsal_realestate.json")
    for name, min_exact in (("auditor_labelled", 52), ("auditor_heldout_independent", 58), ("auditor_heldout_v2", 120)):
        rows, stats, misses = ev.evaluate(cfg, os.path.join(ROOT, "eval", name + ".jsonl"))
        assert sum(s["fp"] for s in stats.values()) == 0, name
        assert len(rows) - len(misses) >= min_exact, name


def test_readme_counts_match_config():
    import json
    import re
    import yaml
    cfg = json.load(open(os.path.join(ROOT, "configs/rehearsal_realestate.json"), encoding="utf-8"))
    sc = yaml.safe_load(open(os.path.join(ROOT, "scenarios/rehearsal_realestate.yaml"), encoding="utf-8"))
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert f"{len(cfg['intents'])} intents, {len(cfg['tools'])} functions" in readme
    assert f"{len(sc)} self-designed scenarios, {sum(1 for s in sc if s.get('edge_case'))} edge cases" in readme
