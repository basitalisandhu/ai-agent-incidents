"""Seeded fuzz tests for every script that reads incident records or the CSV.

Each case copies three real records, damages one of them in one place (a field deleted, or
set to a value of another type or outside the codebook) and runs validate, export_csv,
agentic_crosstab, check_sources (with the network stubbed out) and build_site. Every run
must end with exit code 0, 1 or 2, never a traceback. Damaged files (non-UTF-8, deep
nesting, wrong top level) and damaged CSV rows for import_csv must exit 2 naming the file.
Each test runs under an alarm so a hang fails instead of stalling CI.
"""
import copy
import io
import json
import random
import signal
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agentic_crosstab  # noqa: E402
import build_site  # noqa: E402
import check_sources  # noqa: E402
import export_csv  # noqa: E402
import import_csv  # noqa: E402
import validate  # noqa: E402

SEED = 20261028
SECONDS = 60
BASE = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "incidents").glob("*.json"))]
JUNK = [None, 5, True, "", -1.5, [], {}, ["x"], {"x": 1}, [{"x": 1}], [None], "not-a-code"]


@pytest.fixture(autouse=True)
def _alarm():
    if not hasattr(signal, "SIGALRM"):  # pragma: no cover - Windows
        yield
        return

    def fail(signum, frame):
        raise TimeoutError("test ran longer than %ds" % SECONDS)

    old = signal.signal(signal.SIGALRM, fail)
    signal.alarm(SECONDS)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _paths(value, prefix=()):
    if prefix:
        yield prefix
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _paths(item, prefix + (key,))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _paths(item, prefix + (i,))


def _damage(rng, record):
    path = rng.choice(list(_paths(record)))
    parent = record
    for key in path[:-1]:
        parent = parent[key]
    if rng.random() < 0.4:
        del parent[path[-1]]
    else:
        parent[path[-1]] = copy.deepcopy(rng.choice(JUNK))


def _call(fn, argv):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
        try:
            rc = fn(argv)
        except SystemExit as exc:
            rc = exc.code
    return rc, err.getvalue()


def test_damaged_records_never_crash_a_script(tmp_path, monkeypatch):
    monkeypatch.setattr(check_sources, "check_url", lambda url: ("ok", "200"))
    monkeypatch.chdir(tmp_path)
    rng = random.Random(SEED)
    inc = tmp_path / "inc"
    for _ in range(120):
        for old in inc.glob("*.json"):
            old.unlink()
        inc.mkdir(exist_ok=True)
        records = [copy.deepcopy(r) for r in rng.sample(BASE, 3)]
        for i, r in enumerate(records):
            r["id"] = "%03d" % (i + 1)
        _damage(rng, rng.choice(records))
        for i, r in enumerate(records):
            (inc / ("%03d-x.json" % (i + 1))).write_text(json.dumps(r), encoding="utf-8")
        schema = str(ROOT / "schema" / "incident.schema.json")
        for fn, argv in (
            (validate.main, ["--incidents", str(inc), "--schema", schema]),
            (export_csv.main, ["--incidents", str(inc), "--out", str(tmp_path / "o.csv")]),
            (agentic_crosstab.main, ["--incidents", str(inc), "--stdout"]),
            (check_sources.main, ["--incidents", str(inc)]),
            (build_site.main, ["--incidents", str(inc), "--schema", schema, "--site", str(tmp_path / "site"),
                               "--docs", str(tmp_path / "docs")]),
        ):
            rc, err = _call(fn, argv)
            assert rc in (0, 1, 2), (fn.__module__, rc)
            assert "Traceback" not in err


@pytest.mark.parametrize(
    "content",
    [b"\xff\xfe{}", b"[" * 100_000, b"[1, 2]", b'{"id": ' + b"7" * 5000 + b"}", b"{not json"],
    ids=["utf16", "deep", "list", "huge-int", "broken"],
)
def test_damaged_files_exit_2_naming_the_file(content, tmp_path):
    inc = tmp_path / "inc"
    inc.mkdir()
    bad = inc / "001-x.json"
    bad.write_bytes(content)
    for fn, argv in (
        (export_csv.main, ["--incidents", str(inc), "--out", str(tmp_path / "o.csv")]),
        (agentic_crosstab.main, ["--incidents", str(inc), "--stdout"]),
        (check_sources.main, ["--incidents", str(inc)]),
        (build_site.main, ["--incidents", str(inc), "--site", str(tmp_path / "s"), "--docs", str(tmp_path / "d")]),
    ):
        rc, err = _call(fn, argv)
        assert rc == 2 and str(bad) in err, (fn.__module__, err)
    rc, err = _call(validate.main, ["--incidents", str(inc), "--schema", str(ROOT / "schema" / "incident.schema.json")])
    assert rc == 1 and str(bad) in err


CSV_LINES = (ROOT / "data" / "incidents.csv").read_text(encoding="utf-8").splitlines()[:6]


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        (CSV_LINES[:2] + [CSV_LINES[2][:40]], "line 3: expected 14 fields"),
        (CSV_LINES[:2] + [CSV_LINES[2].replace(",yes,", ",maybe,").replace(",no,", ",maybe,")], "adversarial"),
        ([CSV_LINES[0].replace("notes", "nope")] + CSV_LINES[1:3], "missing columns: notes"),
        ([], "missing columns"),
    ],
    ids=["short-row", "bad-bool", "renamed-column", "empty"],
)
def test_import_csv_bad_rows_exit_2_and_write_nothing(lines, message, tmp_path):
    src = tmp_path / "in.csv"
    src.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    rc, err = _call(import_csv.main, ["--csv", str(src), "--out", str(out)])
    assert rc == 2 and message in err
    assert not list(out.glob("*.json")) if out.exists() else True


def test_import_csv_unreadable_inputs_exit_2(tmp_path):
    src = tmp_path / "in.csv"
    src.write_bytes(b"\xff\xfeid,date\n")
    rc, err = _call(import_csv.main, ["--csv", str(src), "--out", str(tmp_path / "o")])
    assert rc == 2 and "not UTF-8" in err
    rc, err = _call(import_csv.main, ["--csv", str(tmp_path / "missing.csv"), "--out", str(tmp_path / "o")])
    assert rc == 2 and "cannot read" in err
    enrich = tmp_path / "e.json"
    enrich.write_text("[1]", encoding="utf-8")
    rc, err = _call(import_csv.main, ["--csv", str(ROOT / "data" / "incidents.csv"), "--out", str(tmp_path / "o"),
                                      "--enrichment", str(enrich)])
    assert rc == 2 and "enrichment" in err
