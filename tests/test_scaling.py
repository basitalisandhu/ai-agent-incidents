"""Scaling checks: ten times the records must take roughly ten times as long, not a hundred.

The 88 real records are copied 2 and 20 times over with new ids and every script that reads
them is timed on both (best of three). The ratio must stay under 30.
"""
import io
import json
import sys
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agentic_crosstab  # noqa: E402
import build_site  # noqa: E402
import export_csv  # noqa: E402
import import_csv  # noqa: E402
import validate  # noqa: E402

LIMIT = 30
BASE = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "incidents").glob("*.json"))]


def _dataset(tmp, copies):
    d = tmp / ("inc%d" % copies)
    d.mkdir()
    n = 0
    for _ in range(copies):
        for r in BASE:
            n += 1
            (d / ("%05d-x.json" % n)).write_text(json.dumps({**r, "id": "%05d" % n}), encoding="utf-8")
    return d


def _best(fn, argv):
    times = []
    for _ in range(3):
        start = time.perf_counter()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            assert fn(argv) == 0
        times.append(time.perf_counter() - start)
    return max(min(times), 1e-3)


@pytest.mark.parametrize("name", ["validate", "export", "crosstab", "site", "import"])
def test_ten_times_the_records_stays_near_linear(name, tmp_path):
    timings = []
    for copies in (2, 20):
        d = _dataset(tmp_path, copies)
        csv_path = tmp_path / ("o%d.csv" % copies)
        export_csv.main(["--incidents", str(d), "--out", str(csv_path)])
        fn, argv = {
            "validate": (validate.main, ["--incidents", str(d), "--schema", str(ROOT / "schema" / "incident.schema.json")]),
            "export": (export_csv.main, ["--incidents", str(d), "--out", str(csv_path)]),
            "crosstab": (agentic_crosstab.main, ["--incidents", str(d), "--stdout"]),
            "site": (build_site.main, ["--incidents", str(d), "--site", str(tmp_path / ("s%d" % copies)),
                                       "--docs", str(tmp_path / ("d%d" % copies))]),
            "import": (import_csv.main, ["--csv", str(csv_path), "--out", str(tmp_path / ("i%d" % copies)),
                                         "--overwrite"]),
        }[name]
        timings.append(_best(fn, argv))
    small, large = timings
    assert large / small < LIMIT, "%s: 176 records %.3fs, 1,760 records %.3fs" % (name, small, large)
