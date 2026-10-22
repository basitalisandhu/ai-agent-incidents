"""The streaming export preserves every JSON record and is deterministic."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site  # noqa: E402


def test_jsonl_matches_array_in_id_order_and_rebuilds_identically(tmp_path):
    site = tmp_path / "site"
    args = ["--incidents", str(ROOT / "incidents"), "--schema", str(ROOT / "schema" / "incident.schema.json"),
            "--assets", str(ROOT / "assets"), "--site", str(site), "--docs", str(tmp_path / "docs")]
    assert build_site.main(args) == 0
    original = (site / "incidents.jsonl").read_bytes()
    records = json.loads((site / "incidents.json").read_text(encoding="utf-8"))
    assert [json.loads(line) for line in original.decode("utf-8").splitlines()] == records
    assert [r["id"] for r in records] == sorted((r["id"] for r in records), key=lambda x: (len(x), x))
    assert original.endswith(b"\n") and len(original.splitlines()) == len(records)
    assert 'href="incidents.jsonl"' in (site / "index.html").read_text(encoding="utf-8")
    assert "incidents.jsonl" in (site / "llms.txt").read_text(encoding="utf-8")
    assert build_site.main(args) == 0
    assert (site / "incidents.jsonl").read_bytes() == original


def test_jsonl_preserves_unicode_and_embedded_newlines(tmp_path):
    incidents = tmp_path / "incidents"
    incidents.mkdir()
    record = json.loads(next((ROOT / "incidents").glob("*.json")).read_text(encoding="utf-8"))
    record["summary"] = "A café record.\nA second line."
    (incidents / "record.json").write_text(json.dumps(record), encoding="utf-8")
    site = tmp_path / "site"
    assert build_site.main(["--incidents", str(incidents), "--site", str(site),
                            "--schema", str(ROOT / "schema" / "incident.schema.json"),
                            "--docs", str(tmp_path / "docs")]) == 0
    lines = (site / "incidents.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0]) == record
    assert "café" in lines[0] and "\\n" in lines[0]
