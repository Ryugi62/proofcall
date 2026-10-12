"""sc: README numbers equal results files (scripts/update_readme.py --check)."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_readme_results_block_is_generated():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "update_readme.py"), "--check"])
    assert r.returncode == 0, "README results block is stale: run python3 scripts/update_readme.py"
