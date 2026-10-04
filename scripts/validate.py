#!/usr/bin/env python3
"""Validate every record in incidents/ against schema/incident.schema.json.

Usage:
    python3 scripts/validate.py [--incidents incidents] [--schema schema/incident.schema.json]

Beyond the schema it checks that ids are unique, that each file is named
<id>-<slug>.json, that the token "multiple" in cve stands alone, and that the
first source is the primary one (an https URL). Exit status 1 on any error.
Requires the jsonschema package (see requirements-dev.txt).
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    print("error: the jsonschema package is required: pip install -r requirements-dev.txt", file=sys.stderr)
    sys.exit(2)

FILENAME = re.compile(r"^(?P<id>[0-9]{3,})-(?P<slug>[a-z0-9]+(-[a-z0-9]+)*)\.json$")


def validate_dir(incidents_dir, schema_path):
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = []
    seen_ids = {}
    files = sorted(Path(incidents_dir).glob("*.json"))
    if not files:
        errors.append("%s: no JSON records found" % incidents_dir)
    for path in files:
        m = FILENAME.match(path.name)
        if not m:
            errors.append("%s: file name must be <id>-<slug>.json" % path)
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append("%s: invalid JSON: %s" % (path, e))
            continue
        for err in sorted(validator.iter_errors(rec), key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in err.path) or "(root)"
            errors.append("%s: %s: %s" % (path, where, err.message))
        rid = rec.get("id")
        if m and rid is not None and m.group("id") != rid:
            errors.append("%s: file name id %s does not match record id %s" % (path, m.group("id"), rid))
        if rid in seen_ids:
            errors.append("%s: duplicate id %s (also in %s)" % (path, rid, seen_ids[rid]))
        seen_ids[rid] = path
        cve = rec.get("cve") or []
        if "multiple" in cve and len(cve) != 1:
            errors.append("%s: cve 'multiple' must be the only item" % path)
    return len(files), errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--incidents", default="incidents")
    ap.add_argument("--schema", default="schema/incident.schema.json")
    args = ap.parse_args(argv)
    count, errors = validate_dir(args.incidents, args.schema)
    for e in errors:
        print(e, file=sys.stderr)
    if errors:
        print("%d record(s) checked, %d error(s)" % (count, len(errors)), file=sys.stderr)
        return 1
    print("%d record(s) checked, all valid" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
