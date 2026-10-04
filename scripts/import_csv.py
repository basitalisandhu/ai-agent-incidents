#!/usr/bin/env python3
"""Import the flat CSV (the paper's format) into one JSON record per event.

Usage:
    python3 scripts/import_csv.py [--csv data/incidents.csv] [--out incidents]
                                  [--enrichment FILE] [--overwrite]

Each CSV row becomes incidents/<id>-<slug>.json. The fourteen CSV columns map to
the record as follows: id, date, name, type, lens, vector, channel_in, authority,
channel_out, outcome are copied unchanged; adversarial becomes a boolean; cve
becomes a list (the token "multiple" is kept as a single list item); url becomes
the first entry of sources; notes becomes summary (whitespace collapsed, a final
full stop added).

Fields that exist only in the JSON records (source metadata, mappings, affected,
tags, status) are preserved from an existing record with the same id, otherwise
taken from the optional enrichment file (a JSON object keyed by id), otherwise
left empty. Standard library only.
"""
import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

COLUMNS = ["id", "date", "name", "type", "lens", "vector", "channel_in", "authority",
           "channel_out", "adversarial", "outcome", "cve", "url", "notes"]

KEY_ORDER = ["id", "date", "name", "type", "lens", "vector", "channel_in", "authority",
             "channel_out", "adversarial", "outcome", "cve", "sources", "summary",
             "mappings", "affected", "tags", "status"]

EMPTY_MAPPINGS = {"owasp_agentic": [], "owasp_llm": [], "mitre_atlas": []}
EMPTY_AFFECTED = {"vendors": [], "products": [], "frameworks": []}


def slugify(name, max_len=60):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    if len(s) > max_len:
        s = s[:max_len].rsplit("-", 1)[0]
    return s or "event"


def clean_summary(notes):
    s = re.sub(r"\s+", " ", notes).strip()
    if s and s[-1] not in ".!?":
        s += "."
    return s


def parse_cve(value):
    value = value.strip()
    if value in ("", "-"):
        return []
    return [x.strip() for x in value.split(";") if x.strip()]


def parse_bool(value):
    v = value.strip().lower()
    if v in ("yes", "true", "1"):
        return True
    if v in ("no", "false", "0"):
        return False
    raise ValueError("adversarial must be yes or no, got %r" % value)


def merge_sources(url, existing):
    if existing and existing[0].get("url") == url:
        return existing
    rest = [s for s in (existing or []) if s.get("url") != url]
    return [{"url": url}] + rest


def row_to_record(row, existing=None, enrich=None):
    existing = existing or {}
    enrich = enrich or {}

    def pick(key, default):
        if key in existing:
            return existing[key]
        if key in enrich:
            return enrich[key]
        return json.loads(json.dumps(default))

    rec = {
        "id": row["id"].strip(),
        "date": row["date"].strip(),
        "name": row["name"].strip(),
        "type": row["type"].strip(),
        "lens": row["lens"].strip(),
        "vector": row["vector"].strip(),
        "channel_in": row["channel_in"].strip(),
        "authority": row["authority"].strip(),
        "channel_out": row["channel_out"].strip(),
        "adversarial": parse_bool(row["adversarial"]),
        "outcome": row["outcome"].strip(),
        "cve": parse_cve(row["cve"]),
        "sources": merge_sources(row["url"].strip(), existing.get("sources") or enrich.get("sources")),
        "summary": clean_summary(row["notes"]),
        "mappings": pick("mappings", EMPTY_MAPPINGS),
        "affected": pick("affected", EMPTY_AFFECTED),
        "tags": pick("tags", []),
        "status": pick("status", "confirmed"),
    }
    return {k: rec[k] for k in KEY_ORDER}


def load_existing(out_dir):
    found = {}
    for p in sorted(out_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print("warning: cannot parse %s: %s" % (p, e), file=sys.stderr)
            continue
        if isinstance(data, dict) and "id" in data:
            found[data["id"]] = (p, data)
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="data/incidents.csv")
    ap.add_argument("--out", default="incidents")
    ap.add_argument("--enrichment", default=None, help="JSON object keyed by id with mappings/affected/tags/status/sources")
    ap.add_argument("--overwrite", action="store_true", help="ignore existing records instead of merging into them")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    enrichment = {}
    if args.enrichment:
        enrichment = json.loads(Path(args.enrichment).read_text(encoding="utf-8"))
    existing = {} if args.overwrite else load_existing(out_dir)

    with open(args.csv, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            print("error: CSV is missing columns: %s" % ", ".join(missing), file=sys.stderr)
            return 2
        rows = list(reader)

    written = 0
    seen = set()
    for row in rows:
        rid = row["id"].strip()
        if rid in seen:
            print("error: duplicate id %s in CSV" % rid, file=sys.stderr)
            return 2
        seen.add(rid)
        prev_path, prev = existing.get(rid, (None, None))
        rec = row_to_record(row, prev, enrichment.get(rid))
        path = prev_path or out_dir / ("%s-%s.json" % (rid, slugify(rec["name"])))
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1

    stale = [str(p) for i, (p, _) in existing.items() if i not in seen]
    if stale:
        print("note: %d existing record(s) not in CSV (kept): %s" % (len(stale), ", ".join(stale)), file=sys.stderr)
    print("wrote %d record(s) to %s" % (written, out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
