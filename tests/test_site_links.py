"""Site link tests. Run with: python3 -m pytest -q"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402

REPO = "https://github.com/basitalisandhu/ai-agent-incidents"


def test_github_links_have_a_slash_after_the_repository(tmp_path):
    site = tmp_path / "site"
    rc = build_site.main(["--incidents", str(ROOT / "incidents"), "--schema", str(ROOT / "schema" / "incident.schema.json"),
                          "--assets", str(ROOT / "assets"), "--site", str(site), "--docs", str(tmp_path / "docs")])
    assert rc == 0
    page = sorted((site / "incidents").glob("*.html"))[0]
    pages = [page, site / "index.html"]
    for p in pages:
        html = p.read_text(encoding="utf-8")
        assert "incidentsblob" not in html
        assert "incidentstree" not in html
        assert REPO in html
        for m in re.finditer(re.escape(REPO) + r"(.?)", html):
            # a link continues with "/" or ends at a quote; prose may follow with punctuation
            assert not re.match(r"[A-Za-z0-9_-]", m.group(1)), "bad link in %s: %r" % (p.name, html[m.start():m.end() + 20])
