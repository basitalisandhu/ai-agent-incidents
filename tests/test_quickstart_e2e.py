"""End-to-end: run the README "Working with the repository" block in a fresh copy and venv.

The `git clone` is a clone of this checkout (HEAD, with its history, which digest.py needs;
CI checks out with fetch-depth 0), a new venv is created and `pip install -r
requirements-dev.txt` runs in it, then every command of the block that needs no network or
token runs as written. The regenerated site/, docs/stats.md, data/incidents.csv and
digest/2026-10.md must equal the committed ones. Installing needs
the network, so this runs only when AI_INCIDENTS_E2E=1; CI sets it in the quickstart job.
"""
import filecmp
import os
import re
import subprocess
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(os.environ.get("AI_INCIDENTS_E2E") != "1", reason="set AI_INCIDENTS_E2E=1 to run")
README = (ROOT / "README.md").read_text(encoding="utf-8")
SKIP = ("git clone", "cd ai-agent-incidents", "python3 -m venv", "import_csv.py --csv some.csv", "check_sources.py",
        "push_to_hf.py")


def _block():
    section = README[README.index("## Working with the repository"):]
    return re.search(r"```sh\n(.*?)```", section, re.S).group(1)


def test_readme_block_on_a_fresh_copy(tmp_path):
    work = tmp_path / "ai-agent-incidents"
    subprocess.run(["git", "clone", "--quiet", str(ROOT), str(work)], check=True, capture_output=True)
    venv.create(tmp_path / "venv", with_pip=True)
    bin_dir = tmp_path / "venv" / ("Scripts" if os.name == "nt" else "bin")
    env = {"PATH": "%s%s/usr/bin:/bin" % (bin_dir, os.pathsep), "HOME": str(tmp_path), "LC_ALL": "C.UTF-8"}
    commands = [line.split("  #")[0].strip() for line in _block().splitlines()]
    commands = [c for c in commands if c and not c.startswith(SKIP) and not any(s in c for s in SKIP)]
    assert commands[0] == "pip install -r requirements-dev.txt"
    for command in commands:
        command = command.replace("python3 ", "python ")
        proc = subprocess.run(["bash", "-c", command], cwd=work, env=env, capture_output=True, text=True)
        assert proc.returncode == 0, (command, proc.stdout[-2000:], proc.stderr[-2000:])
    assert (work / "data" / "incidents.csv").read_bytes() == (ROOT / "data" / "incidents.csv").read_bytes()
    assert (work / "docs" / "stats.md").read_bytes() == (ROOT / "docs" / "stats.md").read_bytes()
    assert (work / "digest" / "2026-10.md").read_bytes() == (ROOT / "digest" / "2026-10.md").read_bytes()
    diff = filecmp.dircmp(work / "site", ROOT / "site")
    assert not diff.left_only and not diff.right_only and not diff.diff_files
    assert (work / "2025.csv").read_text(encoding="utf-8").count("\n") > 1

