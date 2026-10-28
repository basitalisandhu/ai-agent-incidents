#!/usr/bin/env python3
"""Read incident records safely, for every script that loads incidents/*.json.

A damaged or hand-edited record must stop a script with one line that names the file, not a
traceback: bytes that are not UTF-8, invalid JSON, JSON nested too deeply to parse, a top level
that is not an object, or a field of the wrong type. The type check reads schema/incident.schema.json
and follows only `type`, `required`, `properties`, `items`, `minItems`, `enum` and `pattern`, so it
needs nothing outside the standard library; validate.py checks the full schema with jsonschema.
"""
import json
import re
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "incident.schema.json"
JSON_TYPES = {
    "string": str,
    "boolean": bool,
    "array": list,
    "object": dict,
    "integer": int,
    "number": (int, float),
}
HINT = "; run python3 scripts/validate.py for every problem"


class RecordError(ValueError):
    """A record file that cannot be read, parsed or used."""


def read_json(path):
    """Parse a JSON file. Raises RecordError naming the file on any read or parse failure."""
    path = Path(path)
    try:
        text = path.read_bytes().decode("utf-8")
    except OSError as exc:
        raise RecordError("%s: cannot read: %s" % (path, exc.strerror or exc)) from exc
    except UnicodeDecodeError as exc:
        raise RecordError("%s: not UTF-8 text (byte %d); save it as UTF-8" % (path, exc.start)) from exc
    try:
        return json.loads(text)
    except RecursionError as exc:
        raise RecordError("%s: invalid JSON: nested too deeply to read" % path) from exc
    except ValueError as exc:  # JSONDecodeError, or an integer longer than Python reads
        raise RecordError("%s: invalid JSON: %s" % (path, exc)) from exc


def shape_errors(value, schema, where="(root)", strict=False):
    """Type problems in `value` against the `type`/`properties`/`items` of `schema`.

    With `strict`, `enum`, `pattern`, nested `required` fields and `minItems` are checked too. Top-level required
    fields are `load_record`'s job, because each script needs a different set.
    """
    expected = schema.get("type")
    pytype = JSON_TYPES.get(expected)
    if pytype is not None:
        wrong = not isinstance(value, pytype) or (expected in ("integer", "number") and isinstance(value, bool))
        if wrong:
            return ["%s: expected %s, got %s" % (where, expected, type(value).__name__)]
    problems = []
    if strict and "enum" in schema and value not in schema["enum"]:
        problems.append("%s: %r is not one of the codebook values" % (where, value))
    if strict and isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        problems.append("%s: %r does not match %s" % (where, value, schema["pattern"]))
    if isinstance(value, dict):
        if strict and where != "(root)":
            problems += ["%s: missing field %r" % (where, k) for k in schema.get("required", []) if k not in value]
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                problems += shape_errors(value[key], sub, key if where == "(root)" else "%s/%s" % (where, key), strict)
    elif isinstance(value, list):
        if strict and len(value) < schema.get("minItems", 0):
            problems.append("%s: needs at least %d item(s)" % (where, schema["minItems"]))
        if isinstance(schema.get("items"), dict):
            for i, item in enumerate(value):
                problems += shape_errors(item, schema["items"], "%s/%d" % (where, i), strict)
    return problems


_schema_cache = {}


def _schema():
    if "s" not in _schema_cache:
        _schema_cache["s"] = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return _schema_cache["s"]


def load_record(path, require=None):
    """Read one record and check that every field present has the schema's type.

    `require` lists the top-level fields the caller uses; None means every field the schema requires.
    """
    record = read_json(path)
    if not isinstance(record, dict):
        raise RecordError("%s: a record must be a JSON object, got %s" % (path, type(record).__name__))
    schema = _schema()
    needed = schema.get("required", []) if require is None else require
    problems = ["missing field %r" % key for key in needed if key not in record]
    for key, sub in schema.get("properties", {}).items():
        if key in record:
            problems += shape_errors(record[key], sub, key, strict=key in needed)
    if problems:
        raise RecordError("%s: %s%s" % (path, problems[0], HINT))
    return record


def load_records(incidents_dir, require=None):
    """Every record in the directory, in file name order."""
    return [load_record(p, require) for p in sorted(Path(incidents_dir).glob("*.json"))]
