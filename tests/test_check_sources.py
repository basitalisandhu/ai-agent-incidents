"""Offline tests for scripts/check_sources.py: no request leaves the machine."""
import io
import json
import socket
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_sources  # noqa: E402


class FakeResponse(io.BytesIO):
    def __init__(self, status=200, body=b""):
        super().__init__(body)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_returning(status=None, exc=None, body=b""):
    def opener(req, timeout=None):
        if exc is not None:
            raise exc
        if status >= 400:
            raise urllib.error.HTTPError(getattr(req, "full_url", req), status, "x", {}, None)
        return FakeResponse(status, body)
    return opener


@pytest.mark.parametrize("status,verdict", [(200, "ok"), (204, "ok"), (404, "dead"), (410, "dead"),
                                            (403, "blocked"), (429, "blocked"), (503, "blocked"), (500, "error")])
def test_status_verdicts(status, verdict):
    assert check_sources.check_url("https://example.org/a", opener=opener_returning(status))[0] == verdict


def test_unresolvable_host_is_dead_and_timeout_is_error():
    dns = urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided"))
    assert check_sources.check_url("https://gone.invalid/", opener=opener_returning(exc=dns))[0] == "dead"
    assert check_sources.check_url("https://slow.example/", opener=opener_returning(exc=TimeoutError()))[0] == "error"


def test_request_sends_a_user_agent():
    seen = {}

    def opener(req, timeout=None):
        seen["ua"] = req.get_header("User-agent")
        return FakeResponse(200)
    check_sources.check_url("https://example.org/", opener=opener)
    assert "ai-agent-incidents" in seen["ua"]


def test_wayback_latest_builds_an_archive_url():
    body = b"20250101000000 https://example.org/a\n20261001120000 https://example.org/a\n"
    url = check_sources.wayback_latest("https://example.org/a", opener=opener_returning(200, body=body))
    assert url == "https://web.archive.org/web/20261001120000/https://example.org/a"
    assert check_sources.wayback_latest("https://example.org/a", opener=opener_returning(200, body=b"")) is None
    assert check_sources.wayback_latest("https://example.org/a", opener=opener_returning(exc=TimeoutError())) is None


def test_load_sources_reads_every_record_and_filters_by_id(tmp_path):
    for rid, urls in (("001", ["https://a.example/1"]), ("002", ["https://b.example/2", "https://c.example/3"])):
        (tmp_path / ("%s-x.json" % rid)).write_text(json.dumps({"id": rid, "sources": [{"url": u} for u in urls]}))
    assert list(check_sources.load_sources(tmp_path)) == [
        ("001", 0, "https://a.example/1"), ("002", 0, "https://b.example/2"), ("002", 1, "https://c.example/3")]
    assert [s[0] for s in check_sources.load_sources(tmp_path, {"002"})] == ["002", "002"]


def test_every_committed_source_is_an_https_url():
    sources = list(check_sources.load_sources(ROOT / "incidents"))
    assert sources
    assert all(url.startswith("https://") for _, _, url in sources)


def test_main_exits_1_only_when_a_url_is_dead(tmp_path, monkeypatch, capsys):
    (tmp_path / "001-x.json").write_text(json.dumps({"id": "001", "sources": [{"url": "https://a.example/"}]}))
    monkeypatch.setattr(check_sources, "check_url", lambda url: ("blocked", "403"))
    assert check_sources.main(["--incidents", str(tmp_path)]) == 0
    monkeypatch.setattr(check_sources, "check_url", lambda url: ("dead", "404"))
    assert check_sources.main(["--incidents", str(tmp_path)]) == 1
    assert "001\t0\tdead\t404\thttps://a.example/" in capsys.readouterr().out
