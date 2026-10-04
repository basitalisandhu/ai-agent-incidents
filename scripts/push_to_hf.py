#!/usr/bin/env python3
"""Upload the dataset to its Hugging Face mirror.

Usage:
    HF_TOKEN=hf_... python3 scripts/push_to_hf.py [--repo basitalisandhu/ai-agent-incidents] [--dry-run]

Uploads data/incidents.csv, site/incidents.json, site/incident.schema.json and
hf/README.md (the dataset card) to the dataset repository, creating it if it does
not exist. Run scripts/build_site.py first so site/ is current. The token comes from
the HF_TOKEN environment variable and is never written to disk or printed.

Requires: pip install huggingface_hub
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "basitalisandhu/ai-agent-incidents"
FILES = [
    (ROOT / "data" / "incidents.csv", "incidents.csv"),
    (ROOT / "site" / "incidents.json", "incidents.json"),
    (ROOT / "site" / "incident.schema.json", "incident.schema.json"),
    (ROOT / "hf" / "README.md", "README.md"),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=DEFAULT_REPO, help="dataset repository id on huggingface.co")
    ap.add_argument("--dry-run", action="store_true", help="list what would be uploaded and exit")
    args = ap.parse_args(argv)

    missing = [str(src) for src, _ in FILES if not src.is_file()]
    if missing:
        print("error: missing files (run scripts/build_site.py first): %s" % ", ".join(missing), file=sys.stderr)
        return 2
    for src, dst in FILES:
        print("%s -> %s/%s (%d bytes)" % (src.relative_to(ROOT), args.repo, dst, src.stat().st_size))
    if args.dry_run:
        return 0

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("error: set HF_TOKEN in the environment (a write token from https://huggingface.co/settings/tokens)", file=sys.stderr)
        return 2
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("error: pip install huggingface_hub", file=sys.stderr)
        return 2

    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo, repo_type="dataset", exist_ok=True)
    for src, dst in FILES:
        api.upload_file(path_or_fileobj=str(src), path_in_repo=dst, repo_id=args.repo, repo_type="dataset",
                        commit_message="Update %s from %s" % (dst, "https://github.com/" + DEFAULT_REPO))
        print("uploaded %s" % dst)
    print("done: https://huggingface.co/datasets/%s" % args.repo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
