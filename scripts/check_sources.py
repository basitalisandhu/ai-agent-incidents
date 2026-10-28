#!/usr/bin/env python3
"""Check that every source URL in incidents/ still resolves.

Usage:
    python3 scripts/check_sources.py [--incidents incidents] [--ids 001,002] [--wayback]

Each URL is requested once (GET, redirects followed, 25 s timeout) and given
one verdict:

- ok: the final response was 2xx.
- blocked: 401, 403, 429 or 503. Usually a bot wall in front of a live page;
  open it in a browser or pass --wayback to look for an archived copy.
- dead: 404 or 410, or the host does not resolve. Replace the URL with an
  archived copy (https://web.archive.org/web/<timestamp>/<url>) as a second
  source, or set the record's status to "reported" if none exists.
- error: anything else (timeouts, other status codes). Re-run before acting.

With --wayback, every URL that is not ok is looked up in the Internet Archive
and the newest capture that returned 200 is printed. Exit status 1 if any URL
is dead, 0 otherwise. Standard library only.
"""
import argparse
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from records import RecordError, load_record  # noqa: E402

USER_AGENT = "Mozilla/5.0 (compatible; ai-agent-incidents source check; +https://github.com/basitalisandhu/ai-agent-incidents)"
BLOCKED = {401, 403, 429, 503}
DEAD = {404, 410}


def load_sources(incidents_dir, ids=None):
    """Yield (id, index, url) for every source of every record, in id order."""
    for path in sorted(Path(incidents_dir).glob("*.json")):
        record = load_record(path, require=("id",))
        if ids and record["id"] not in ids:
            continue
        for index, source in enumerate(record.get("sources", [])):
            if not isinstance(source.get("url"), str):
                raise RecordError("%s: sources/%d has no url" % (path, index))
            yield record["id"], index, source["url"]


def classify(status=None, exc=None):
    """Turn an HTTP status or a request exception into a verdict."""
    if exc is not None:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.gaierror):
            return "dead"
        return "error"
    if 200 <= status < 300:
        return "ok"
    if status in DEAD:
        return "dead"
    if status in BLOCKED:
        return "blocked"
    return "error"


def check_url(url, opener=urllib.request.urlopen, timeout=25):
    """Return (verdict, detail) for one URL. `opener` is injectable for tests."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    try:
        with opener(req, timeout=timeout) as resp:
            status = resp.status
            return classify(status=status), str(status)
    except urllib.error.HTTPError as err:
        return classify(status=err.code), str(err.code)
    except (urllib.error.URLError, OSError) as err:
        return classify(exc=err), type(getattr(err, "reason", err)).__name__


def wayback_latest(url, opener=urllib.request.urlopen, timeout=40):
    """Newest archived copy of url that returned 200, as a web.archive.org URL, or None."""
    query = urllib.parse.urlencode({"url": url, "filter": "statuscode:200", "limit": "-1", "fl": "timestamp,original"})
    try:
        with opener("https://web.archive.org/cdx/search/cdx?" + query, timeout=timeout) as resp:
            lines = resp.read().decode("utf-8", "replace").strip().splitlines()
    except (urllib.error.URLError, OSError):
        return None
    if not lines or " " not in lines[-1]:
        return None
    timestamp, original = lines[-1].split(" ", 1)
    if not timestamp.isdigit():
        return None
    return "https://web.archive.org/web/%s/%s" % (timestamp, original)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--incidents", default="incidents")
    parser.add_argument("--ids", help="comma-separated record ids to check (default: all)")
    parser.add_argument("--wayback", action="store_true", help="look up an archived copy for every URL that is not ok")
    args = parser.parse_args(argv)
    ids = set(args.ids.split(",")) if args.ids else None
    counts = {}
    try:
        sources = list(load_sources(args.incidents, ids))
    except RecordError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    for record_id, index, url in sources:
        verdict, detail = check_url(url)
        counts[verdict] = counts.get(verdict, 0) + 1
        line = "%s\t%s\t%s\t%s\t%s" % (record_id, index, verdict, detail, url)
        if args.wayback and verdict != "ok":
            time.sleep(2)  # the archive rate-limits bursts
            line += "\t" + (wayback_latest(url) or "no archived copy")
        print(line)
    print("summary: " + ", ".join("%s %d" % kv for kv in sorted(counts.items())), file=sys.stderr)
    return 1 if counts.get("dead") else 0


if __name__ == "__main__":
    sys.exit(main())
