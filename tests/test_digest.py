"""Monthly digest: counts and links from record fields, months taken from git history."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
import digest  # noqa: E402
from records import load_record  # noqa: E402


def _record(rid, lens, vendors):
    rec = load_record(sorted((ROOT / "incidents").glob("*.json"))[0])
    rec = dict(rec, id=rid, lens=lens)
    rec["affected"] = dict(rec["affected"], vendors=vendors)
    return rec


def test_render_counts_and_links():
    text = digest.render("2026-10", [_record("001", "surface", ["Acme", "Beta"]),
                                     _record("002", "weapon", ["Acme"])])
    assert text.startswith("# AI agent incidents digest: October 2026\n")
    assert "2 record(s) were added to the dataset in October 2026" in text
    assert "| `surface` | 1 |" in text and "| `weapon` | 1 |" in text
    assert "- Acme: 2" in text and "- 1 other vendor(s) named once" in text
    assert "(https://basitalisandhu.github.io/ai-agent-incidents/incidents/002.html)" in text


def test_render_empty_month():
    assert "No records were added to the dataset in March 2026." in digest.render("2026-03", [])


def test_bad_month_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exc:
        digest.main(["--month", "2026-13"])
    assert exc.value.code == 2


def test_added_months_reads_git_history(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True,
                       env={"GIT_AUTHOR_DATE": "2026-09-15T12:00:00", "GIT_COMMITTER_DATE": "2026-09-15T12:00:00",
                            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})

    git("init", "-q")
    (tmp_path / "incidents").mkdir()
    (tmp_path / "incidents" / "001-a.json").write_text("{}", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "add")
    assert digest.added_months(tmp_path / "incidents", repo=tmp_path) == {"001-a.json": "2026-09"}


def test_committed_october_digest_lists_every_record():
    text = (ROOT / "digest" / "2026-10.md").read_text(encoding="utf-8")
    ids = [p.name.split("-")[0] for p in sorted((ROOT / "incidents").glob("*.json"))]
    # Every record in the repository was first committed in October 2026, and the digest is frozen.
    assert "88 record(s) were added to the dataset in October 2026" in text
    for rid in ids[:88]:
        assert "[%s](" % rid in text


def test_site_index_links_the_digests(tmp_path):
    assert "digest/2026-10.md\">October 2026</a>" in build_site.digest_links(ROOT / "digest")
    assert build_site.digest_links(tmp_path) == ""
