"""The OWASP Agentic cross-tab is deterministic, committed and consistent with the records."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agentic_crosstab as ac  # noqa: E402


def test_committed_crosstab_is_current():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "agentic_crosstab.py"), "--check"],
                            capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr


def test_mapped_plus_unmapped_equals_events():
    records = ac.load()
    mapped = [r for r in records if ac.asi(r)]
    text = ac.render(records)
    assert f"- Events: **{len(records)}**" in text
    assert f"Mapped to at least one ASI category: **{len(mapped)}**" in text
    assert f"Mapped to none: **{len(records) - len(mapped)}**" in text


def test_category_counts_match_records():
    records = ac.load()
    text = ac.render(records)
    for code, name in ac.ASI:
        n = sum(1 for r in records if code in ac.asi(r))
        assert f"| `{code}` | {name} | {n} |" in text


def test_render_on_a_tiny_sample(tmp_path):
    base = {"type": "incident", "vector": "indirect-injection", "channel_out": "code exec",
            "outcome": "code-execution", "name": "x"}
    rows = [
        {**base, "id": "001", "date": "2025-01", "lens": "surface", "authority": "shell/exec",
         "mappings": {"owasp_agentic": ["ASI01", "ASI05"]}},
        {**base, "id": "002", "date": "2026-02", "lens": "weapon", "authority": "none", "mappings": {}},
    ]
    for r in rows:
        (tmp_path / f"{r['id']}.json").write_text(json.dumps(r))
    text = ac.render(ac.load(tmp_path))
    assert "Mapped to at least one ASI category: **1** (50.0%)" in text
    assert "| `ASI01` + `ASI05` | 1 |" in text
    assert "| 002 | `weapon` | `indirect-injection` | x |" in text
