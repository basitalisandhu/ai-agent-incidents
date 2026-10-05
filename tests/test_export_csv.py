"""Offline CLI export boundaries and byte-compatible default output."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_csv.py"


def run_export(path, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--incidents", str(ROOT / "incidents"),
         "--out", str(path), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_default_export_is_byte_identical(tmp_path):
    out = tmp_path / "all.csv"
    assert run_export(out).returncode == 0
    assert out.read_bytes() == (ROOT / "data" / "incidents.csv").read_bytes()


@pytest.mark.parametrize(
    "flags",
    [
        ("--since", "2025-01"),
        ("--until", "2025-01"),
        ("--since", "2025-01", "--until", "2025-12"),
        ("--since", "2099-01"),
    ],
)
def test_month_filters_are_inclusive_and_preserve_id_order(tmp_path, flags):
    out = tmp_path / "filtered.csv"
    result = run_export(out, *flags)
    assert result.returncode == 0, result.stderr
    options = dict(zip(flags[::2], flags[1::2]))
    records = [json.loads(p.read_text()) for p in (ROOT / "incidents").glob("*.json")]
    expected = sorted(
        [
            r for r in records
            if r["date"][:7] >= options.get("--since", "0000-01")
            and r["date"][:7] <= options.get("--until", "9999-12")
        ],
        key=lambda r: (len(r["id"]), r["id"]),
    )
    with out.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [r["id"] for r in rows] == [r["id"] for r in expected]


@pytest.mark.parametrize("value", ["2025", "2025-00", "2025-13", "2025-1", "2025-01-01", "abcd-01"])
def test_invalid_month_is_rejected_without_touching_output(tmp_path, value):
    out = tmp_path / "existing.csv"
    out.write_bytes(b"keep me\n")
    result = run_export(out, "--since", value)
    assert result.returncode == 2 and "YYYY-MM" in result.stderr
    assert out.read_bytes() == b"keep me\n"


def test_reversed_range_is_a_usage_error(tmp_path):
    out = tmp_path / "out.csv"
    result = run_export(out, "--since", "2026-01", "--until", "2025-12")
    assert result.returncode == 2 and "since" in result.stderr and "until" in result.stderr
    assert not out.exists()
