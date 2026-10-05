#!/usr/bin/env python3
"""Export the JSON records back to the flat CSV used by the paper.

Usage:
    python3 scripts/export_csv.py [--incidents incidents] [--out data/incidents.csv]

Writes the fourteen original columns (id, date, name, type, lens, vector,
channel_in, authority, channel_out, adversarial, outcome, cve, url, notes),
one row per record, sorted by id. The inverse of import_csv.py: adversarial
becomes yes/no, cve is joined with semicolons or written as "-", url is the
first source, notes is the summary without its final full stop. Only the
columns of the original dataset are exported; mappings, affected, tags and
status live in the JSON records. Standard library only.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

COLUMNS = ["id", "date", "name", "type", "lens", "vector", "channel_in", "authority",
           "channel_out", "adversarial", "outcome", "cve", "url", "notes"]


def load_records(incidents_dir):
    recs = []
    for p in sorted(Path(incidents_dir).glob("*.json")):
        recs.append(json.loads(p.read_text(encoding="utf-8")))
    recs.sort(key=lambda r: (len(r["id"]), r["id"]))
    return recs


def record_to_row(rec):
    notes = rec["summary"].strip()
    if notes.endswith(".") and not notes.endswith(".."):
        notes = notes[:-1]
    return {
        "id": rec["id"],
        "date": rec["date"],
        "name": rec["name"],
        "type": rec["type"],
        "lens": rec["lens"],
        "vector": rec["vector"],
        "channel_in": rec["channel_in"],
        "authority": rec["authority"],
        "channel_out": rec["channel_out"],
        "adversarial": "yes" if rec["adversarial"] else "no",
        "outcome": rec["outcome"],
        "cve": ";".join(rec["cve"]) if rec["cve"] else "-",
        "url": rec["sources"][0]["url"],
        "notes": notes,
    }


def write_csv(records, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)  # csv default CRLF, as in the original file
        w.writeheader()
        for rec in records:
            w.writerow(record_to_row(rec))


def month(value):
    """Parse a month without accepting unpadded or out-of-range values."""
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", value):
        raise argparse.ArgumentTypeError("expected a month in YYYY-MM format")
    return value


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--incidents", default="incidents")
    ap.add_argument("--out", default="data/incidents.csv")
    ap.add_argument("--since", type=month, help="Include records from this month (YYYY-MM).")
    ap.add_argument("--until", type=month, help="Include records through this month (YYYY-MM).")
    args = ap.parse_args(argv)
    if args.since and args.until and args.since > args.until:
        ap.error("--since must not be later than --until")
    records = load_records(args.incidents)
    records = [
        rec for rec in records
        if (args.since is None or rec["date"][:7] >= args.since)
        and (args.until is None or rec["date"][:7] <= args.until)
    ]
    write_csv(records, args.out)
    print("wrote %d row(s) to %s" % (len(records), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
