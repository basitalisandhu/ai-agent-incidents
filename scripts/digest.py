#!/usr/bin/env python3
"""Write a monthly digest of the records added to the dataset in one month.

Usage:
    python3 scripts/digest.py --month 2026-10 [--incidents incidents] [--out digest]
    python3 scripts/digest.py --month 2026-10 --stdout

A record counts as added in the month in which its file was first committed to this
repository (git log --diff-filter=A), not by its event date, so a late-coded 2023 event
shows up in the digest of the month it joined the dataset. The digest uses only fields
in the records: how many were added, the role AI played (lens), type, vector, outcome,
the affected vendors, and one line per record with a link to its page on the site.

Needs the full git history: in a shallow clone (CI checkouts are shallow by default)
it stops with exit code 2. Writes digest/YYYY-MM.md. Standard library only.
"""
import argparse
import calendar
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from records import RecordError, load_record  # noqa: E402

SITE_URL = "https://basitalisandhu.github.io/ai-agent-incidents/"
MONTH = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
# One-line summaries of the lens definitions in docs/codebook.md.
LENS_NOTE = {
    "surface": "the AI is a conduit to another party's data, tools, code or accounts",
    "weapon": "the AI is the attacker's instrument against a victim that is not its operator",
    "target": "the AI system itself is what is attacked, exposed or disrupted",
}


class DigestError(Exception):
    pass


def month_arg(value):
    if not MONTH.match(value):
        raise argparse.ArgumentTypeError("expected a month in YYYY-MM format")
    return value


def added_months(incidents_dir, repo="."):
    """Map each record file name to the YYYY-MM in which it was first committed."""
    def git(*args):
        try:
            proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DigestError("cannot run git: %s" % exc) from exc
        if proc.returncode != 0:
            raise DigestError("git %s failed: %s" % (args[0], proc.stderr.strip() or proc.returncode))
        return proc.stdout

    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        raise DigestError("the clone is shallow, so first-commit dates are unknown; run git fetch --unshallow")
    top = Path(git("rev-parse", "--show-toplevel").strip()).resolve()
    try:
        rel = Path(incidents_dir).resolve().relative_to(top)
    except ValueError as exc:
        raise DigestError("%s is not inside the git repository %s" % (incidents_dir, top)) from exc
    out = git("log", "--diff-filter=A", "--format=@%cs", "--name-only", "--", str(rel))
    months, current = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            current = line[1:8]
        elif line.strip():
            months[Path(line).name] = current  # git log is newest first; keep the oldest add
    return months


def ranked(counter, limit=None):
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:limit] if limit else items


def render(month, records):
    year, mon = int(month[:4]), int(month[5:])
    title = "%s %d" % (calendar.month_name[mon], year)
    n = len(records)
    out = ["# AI agent incidents digest: %s" % title, ""]
    if not n:
        out += ["No records were added to the dataset in %s." % title, ""]
        return "\n".join(out)
    types = Counter(r["type"] for r in records)
    out += [
        "%d record(s) were added to the dataset in %s (counted by the month each record's file was first "
        "committed, not by event date): %d incident(s), %d vulnerability disclosure(s) and %d threat report(s). "
        "Event dates range from %s to %s." % (
            n, title, types["incident"], types["vulnerability-disclosure"], types["threat-report"],
            min(r["date"] for r in records), max(r["date"] for r in records)),
        "",
        "The dataset is a convenience sample of what was public, so these counts describe the records, not a "
        "share of all incidents. Definitions: [codebook](../docs/codebook.md).",
        "",
        "## The role AI played (lens)",
        "",
        "| lens | records | meaning |",
        "|---|---:|---|",
    ]
    out += ["| `%s` | %d | %s |" % (k, v, LENS_NOTE.get(k, "")) for k, v in ranked(Counter(r["lens"] for r in records))]
    for field, heading in (("vector", "How it got in (vector)"), ("outcome", "Outcome")):
        out += ["", "## %s" % heading, "", "| %s | records |" % field, "|---|---:|"]
        out += ["| `%s` | %d |" % kv for kv in ranked(Counter(r[field] for r in records))]
    vendors = Counter(v for r in records for v in sorted(set(r.get("affected", {}).get("vendors", []))))
    out += ["", "## Affected vendors", ""]
    if vendors:
        out += ["Vendors named in two or more of the records added this month, then the count of the rest.", ""]
        repeat = [(v, c) for v, c in ranked(vendors) if c > 1]
        out += ["- %s: %d" % kv for kv in repeat] or ["- none named more than once"]
        once = sum(1 for c in vendors.values() if c == 1)
        if once:
            out.append("- %d other vendor(s) named once" % once)
    else:
        out.append("No vendors are recorded for these records.")
    out += ["", "## Records", "", "| id | date | name | lens | vector |", "|---|---|---|---|---|"]
    for r in sorted(records, key=lambda r: (len(r["id"]), r["id"])):
        name = r["name"].replace("|", "\\|")
        out.append("| [%s](%sincidents/%s.html) | %s | %s | `%s` | `%s` |" % (
            r["id"], SITE_URL, r["id"], r["date"], name, r["lens"], r["vector"]))
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month", required=True, type=month_arg, help="YYYY-MM")
    ap.add_argument("--incidents", default="incidents")
    ap.add_argument("--out", default="digest", help="directory for YYYY-MM.md")
    ap.add_argument("--stdout", action="store_true", help="print the digest instead of writing it")
    args = ap.parse_args(argv)
    try:
        months = added_months(args.incidents)
        files = sorted(Path(args.incidents).glob("*.json"))
        records = [load_record(p) for p in files if months.get(p.name) == args.month]
    except (DigestError, RecordError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    text = render(args.month, records)
    if args.stdout:
        sys.stdout.write(text)
        return 0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / ("%s.md" % args.month)).write_text(text, encoding="utf-8")
    print("wrote %s (%d record(s))" % (out / ("%s.md" % args.month), len(records)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
