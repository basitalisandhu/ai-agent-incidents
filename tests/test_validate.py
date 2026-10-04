"""Dataset integrity tests. Run with: python3 -m pytest -q"""
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_csv  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "incident.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
FILES = sorted((ROOT / "incidents").glob("*.json"))
RECORDS = [json.loads(p.read_text(encoding="utf-8")) for p in FILES]
FILENAME = re.compile(r"^([0-9]{3,})-([a-z0-9]+(?:-[a-z0-9]+)*)\.json$")


def test_schema_is_valid():
    Draft202012Validator.check_schema(SCHEMA)


def test_dataset_not_empty():
    assert len(FILES) >= 80


@pytest.mark.parametrize("path,record", list(zip(FILES, RECORDS)), ids=[p.name for p in FILES])
def test_every_incident_validates(path, record):
    errors = [e.message for e in VALIDATOR.iter_errors(record)]
    assert not errors, "%s: %s" % (path.name, errors)


@pytest.mark.parametrize("path,record", list(zip(FILES, RECORDS)), ids=[p.name for p in FILES])
def test_filename_matches_id(path, record):
    m = FILENAME.match(path.name)
    assert m, path.name
    assert m.group(1) == record["id"]


def test_ids_unique():
    ids = [r["id"] for r in RECORDS]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, "duplicate ids: %s" % sorted(dupes)


@pytest.mark.parametrize("record", RECORDS, ids=[r["id"] for r in RECORDS])
def test_dates_parse(record):
    d = record["date"]
    fmt = "%Y-%m-%d" if len(d) == 10 else "%Y-%m"
    parsed = dt.datetime.strptime(d, fmt)
    assert dt.datetime(2022, 11, 1) <= parsed <= dt.datetime.now() + dt.timedelta(days=31)


@pytest.mark.parametrize("record", RECORDS, ids=[r["id"] for r in RECORDS])
def test_every_source_has_https_url(record):
    assert record["sources"], "at least one source is required"
    for s in record["sources"]:
        assert s["url"].startswith("https://"), s["url"]
        assert " " not in s["url"]


@pytest.mark.parametrize("record", RECORDS, ids=[r["id"] for r in RECORDS])
def test_cve_multiple_stands_alone(record):
    if "multiple" in record["cve"]:
        assert record["cve"] == ["multiple"]


def test_export_round_trips_to_data_csv(tmp_path):
    out = tmp_path / "incidents.csv"
    export_csv.write_csv(export_csv.load_records(ROOT / "incidents"), out)
    assert out.read_bytes() == (ROOT / "data" / "incidents.csv").read_bytes(), \
        "data/incidents.csv is stale: run python3 scripts/export_csv.py"


def test_data_csv_has_original_columns():
    with open(ROOT / "data" / "incidents.csv", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == export_csv.COLUMNS
        assert len(list(reader)) == len(RECORDS)
