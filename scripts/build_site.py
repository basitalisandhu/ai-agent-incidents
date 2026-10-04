#!/usr/bin/env python3
"""Build the static site and the generated docs from incidents/*.json.

Usage:
    python3 scripts/build_site.py [--incidents incidents] [--site site] [--docs docs]
                                  [--schema schema/incident.schema.json]

Outputs (all written from scratch on every run):
    site/index.html             searchable, filterable, sortable table; inline CSS and
                                vanilla JS; no external resources; works from file://
    site/incidents/<id>.html    one page per record with sources and mappings
    site/incidents.json         every record, as an array
    site/incidents.csv          the flat CSV (same content as data/incidents.csv)
    site/incident.schema.json   copy of the schema
    site/stats.json             counts by year, type, lens, vector, channel, authority,
                                outcome, adversarial, status and mapping coverage
    site/feed.xml               RSS 2.0 feed, newest first
    site/sitemap.xml            the index and every record page, lastmod from record dates
    site/robots.txt             allows everything, names the AI crawlers and fetchers explicitly,
                                points at the sitemap and at llms.txt
    site/llms.txt               llms.txt (llmstxt.org): what the dataset is, licence, coding scheme,
                                citation, download URLs and the headline statistics, for AI assistants
    site/llms-full.txt          the same plus one line per record (id, date, name, lens, vector, URL)
    site/<key>.txt              IndexNow key file; the key is read from scripts/indexnow_key.txt
    site/og-image.png           copied from assets/og-image.png when present (link previews)
    site/.nojekyll              so GitHub Pages serves the files as they are
    docs/stats.md               the same counts as Markdown tables

The build is deterministic: the feed's build date is the newest record date, not
the wall clock, so rebuilding unchanged data gives identical files. Standard
library only.

Every page carries a canonical URL, Open Graph and Twitter card tags and JSON-LD:
a schema.org Dataset on the index (what Google Dataset Search reads) and an
Article plus a Dataset subset on each record page.
"""
import argparse
import datetime as dt
import html
import json
import shutil
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_csv  # noqa: E402

SITE_URL = "https://basitalisandhu.github.io/ai-agent-incidents/"
REPO_URL = "https://github.com/basitalisandhu/ai-agent-incidents"
SITE_TITLE = "AI Agent Incidents"
TAGLINE = ("An open, structured dataset of publicly documented AI-agent and LLM-application "
           "security incidents, coded by the role AI plays: weapon, target or surface.")
INDEX_TITLE = "AI Agent Incidents: open dataset of AI agent and LLM security incidents"
INDEX_DESCRIPTION = ("Open dataset of AI agent and LLM security incidents from 2023 onwards: schema-validated "
                     "records of prompt injection, data exfiltration, supply-chain and agent-misuse events, "
                     "coded by the role AI plays and mapped to the OWASP LLM and Agentic Top 10 and MITRE ATLAS. "
                     "JSON, CSV and RSS, CC BY 4.0.")
DATASET_VERSION = "1.0.0"   # keep in step with CITATION.cff
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
PAPER_CITATION = ("Muhammad Basit Ali. AI as Weapon, Target, and Surface: A Threat Taxonomy and a Deterministic "
                  "Control Plane for Securing LLM Agents. 2026. Manuscript.")
AUTHOR = OrderedDict([("@type", "Person"), ("name", "Muhammad Basit Ali"),
                      ("alternateName", "basitalisandhu"), ("url", "https://github.com/basitalisandhu")])
KEYWORDS = ["AI security", "LLM security", "AI agent security", "prompt injection", "security incidents",
            "incident database", "OWASP Top 10 for LLM Applications", "OWASP Top 10 for Agentic Applications",
            "MITRE ATLAS", "threat intelligence", "dataset"]
ASSETS_DIR = "assets"
OG_IMAGE = "og-image.png"

CODED_FIELDS = ["type", "lens", "vector", "channel_in", "authority", "channel_out", "adversarial", "outcome"]

HF_URL = "https://huggingface.co/datasets/basitalisandhu/ai-agent-incidents"
INDEXNOW_KEY_FILE = Path(__file__).resolve().parent / "indexnow_key.txt"

# Crawlers and fetchers named explicitly in robots.txt. Everything is allowed anyway; the explicit
# entries make the intent unambiguous to operators that look for their own token.
AI_CRAWLERS = [
    ("OpenAI", ["GPTBot", "ChatGPT-User", "OAI-SearchBot"]),
    ("Anthropic", ["ClaudeBot", "Claude-User", "Claude-SearchBot", "anthropic-ai"]),
    ("Perplexity", ["PerplexityBot", "Perplexity-User"]),
    ("Google", ["Googlebot", "Google-Extended"]),
    ("Microsoft (Bing powers ChatGPT search, Copilot and DuckDuckGo)", ["Bingbot"]),
    ("Apple", ["Applebot", "Applebot-Extended"]),
    ("Common Crawl", ["CCBot"]),
    ("DuckDuckGo", ["DuckAssistBot"]),
    ("Meta", ["meta-externalagent"]),
    ("Amazon", ["Amazonbot"]),
    ("Cohere", ["cohere-ai"]),
    ("You.com", ["YouBot"]),
    ("Mistral", ["MistralAI-User"]),
]

# Question-shaped entries for the index page and its FAQPage JSON-LD; the README repeats them.
# Each entry is (question, answer as HTML, answer as plain text); %(...)s fields come from stats.
FAQ = [
    ("Is there a public dataset of AI agent security incidents?",
     "Yes, this one: %(total)d publicly documented events from %(from)s to %(to)s (%(incident)d incidents, %(vuln)d vulnerability disclosures, %(report)d threat reports), one schema-validated JSON record each, coded under a written codebook and mapped to the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and MITRE ATLAS. Download it as <a href=\"incidents.json\">JSON</a> or <a href=\"incidents.csv\">CSV</a>, subscribe to the <a href=\"feed.xml\">RSS feed</a>, or read the <a href=\"%(repo)s\">repository</a>. The data is CC BY 4.0.",
     "Yes, this one: %(total)d publicly documented events from %(from)s to %(to)s (%(incident)d incidents, %(vuln)d vulnerability disclosures, %(report)d threat reports), one schema-validated JSON record each, coded under a written codebook and mapped to the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and MITRE ATLAS. Download it as JSON (%(site)sincidents.json) or CSV (%(site)sincidents.csv), subscribe to the RSS feed, or read the repository at %(repo)s. The data is CC BY 4.0."),
    ("How are incidents coded?",
     "Every event is coded from a primary source that was opened and read, on eight fields defined in the <a href=\"%(repo)s/blob/main/docs/codebook.md\">codebook</a>: type (incident, vulnerability disclosure or threat report), lens (the role AI plays: weapon, target or surface), vector (how the attack or failure got in), channel_in, authority (what the AI component could do), channel_out (how the effect left the system), adversarial (whether an attack technique is involved) and outcome (the most severe harm realised or demonstrated). Each record also carries mappings to the OWASP LLM Top 10, the OWASP Agentic Top 10 and MITRE ATLAS, given only where the source supports them. The paper behind the seed data reports two further blind codings and their agreement.",
     "Every event is coded from a primary source that was opened and read, on eight fields defined in the codebook (%(repo)s/blob/main/docs/codebook.md): type (incident, vulnerability disclosure or threat report), lens (the role AI plays: weapon, target or surface), vector (how the attack or failure got in), channel_in, authority (what the AI component could do), channel_out (how the effect left the system), adversarial (whether an attack technique is involved) and outcome (the most severe harm realised or demonstrated). Each record also carries mappings to the OWASP LLM Top 10, the OWASP Agentic Top 10 and MITRE ATLAS, given only where the source supports them. The paper behind the seed data reports two further blind codings and their agreement."),
    ("Can I use it commercially?",
     "Yes. The data is licensed <a href=\"%(license)s\">CC BY 4.0</a>: use, copy, modify and redistribute it, including in commercial products, as long as you credit the dataset (name it and link to the repository) and say if you changed it. The build and validation code is MIT. There is no warranty, and the dataset is a convenience sample of what was made public, so no share computed from it estimates a population share.",
     "Yes. The data is licensed CC BY 4.0: use, copy, modify and redistribute it, including in commercial products, as long as you credit the dataset (name it and link to the repository) and say if you changed it. The build and validation code is MIT. There is no warranty, and the dataset is a convenience sample of what was made public, so no share computed from it estimates a population share."),
    ("How do I add an incident?",
     "One event is one JSON file and one pull request: copy an existing record, give it the next free id, fill every field from a public primary source, run <code>python3 scripts/validate.py</code>, and open the pull request. If you would rather not write JSON, use the <a href=\"%(repo)s/issues/new/choose\">issue form</a>. Only events with a public primary source are accepted; this is not a place to disclose new vulnerabilities. The checklist is in <a href=\"%(repo)s/blob/main/CONTRIBUTING.md\">CONTRIBUTING.md</a>.",
     "One event is one JSON file and one pull request: copy an existing record, give it the next free id, fill every field from a public primary source, run python3 scripts/validate.py, and open the pull request. If you would rather not write JSON, use the issue form at %(repo)s/issues/new/choose. Only events with a public primary source are accepted; this is not a place to disclose new vulnerabilities. The checklist is in CONTRIBUTING.md."),
    ("How do I cite the dataset?",
     "Use the citation in <a href=\"%(repo)s/blob/main/CITATION.cff\">CITATION.cff</a> (GitHub shows it under \"Cite this repository\"): Muhammad Basit Ali, AI Agent Incidents: an open dataset of publicly documented AI-agent and LLM-application security incidents, version %(version)s, 2026, %(repo)s. The coding scheme comes from the paper <em>AI as Weapon, Target, and Surface: A Threat Taxonomy and a Deterministic Control Plane for Securing LLM Agents</em> (Ali, 2026), whose codebook is reproduced in <a href=\"%(repo)s/blob/main/docs/codebook.md\">docs/codebook.md</a>; cite both when you use the coding.",
     "Use the citation in CITATION.cff (GitHub shows it under \"Cite this repository\"): Muhammad Basit Ali, AI Agent Incidents: an open dataset of publicly documented AI-agent and LLM-application security incidents, version %(version)s, 2026, %(repo)s. The coding scheme comes from the paper AI as Weapon, Target, and Surface: A Threat Taxonomy and a Deterministic Control Plane for Securing LLM Agents (Ali, 2026), whose codebook is reproduced in %(repo)s/blob/main/docs/codebook.md; cite both when you use the coding."),
    ("What can the dataset not tell you?",
     "It is a convenience sample of events that were made public, so it over-represents what vendors and researchers chose to disclose and says nothing about how common any class of event is in the population. Mappings are the maintainer's reading of each source against the published frameworks; an empty mapping list means no confident mapping, not that none applies. Dates are the month of the public report, not of the event. Each record links its primary source so every claim can be checked.",
     "It is a convenience sample of events that were made public, so it over-represents what vendors and researchers chose to disclose and says nothing about how common any class of event is in the population. Mappings are the maintainer's reading of each source against the published frameworks; an empty mapping list means no confident mapping, not that none applies. Dates are the month of the public report, not of the event. Each record links its primary source so every claim can be checked."),
]

OWASP_LLM = OrderedDict([
    ("LLM01", "Prompt Injection"),
    ("LLM02", "Sensitive Information Disclosure"),
    ("LLM03", "Supply Chain"),
    ("LLM04", "Data and Model Poisoning"),
    ("LLM05", "Improper Output Handling"),
    ("LLM06", "Excessive Agency"),
    ("LLM07", "System Prompt Leakage"),
    ("LLM08", "Vector and Embedding Weaknesses"),
    ("LLM09", "Misinformation"),
    ("LLM10", "Unbounded Consumption"),
])
OWASP_LLM_URL = "https://genai.owasp.org/llm-top-10/"

OWASP_ASI = OrderedDict([
    ("ASI01", "Agent Goal Hijack"),
    ("ASI02", "Tool Misuse and Exploitation"),
    ("ASI03", "Identity and Privilege Abuse"),
    ("ASI04", "Agentic Supply Chain Vulnerabilities"),
    ("ASI05", "Unexpected Code Execution"),
    ("ASI06", "Memory and Context Poisoning"),
    ("ASI07", "Insecure Inter-Agent Communication"),
    ("ASI08", "Cascading Agent Failures"),
    ("ASI09", "Human-Agent Trust Exploitation"),
    ("ASI10", "Rogue Agents"),
])
OWASP_ASI_URL = "https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/"

# Names from MITRE ATLAS v5.6.0 (atlas.mitre.org); ids not listed here are shown bare.
ATLAS = {
    "AML.T0010": "AI Supply Chain Compromise",
    "AML.T0010.001": "AI Supply Chain Compromise: AI Software",
    "AML.T0010.003": "AI Supply Chain Compromise: Model",
    "AML.T0010.005": "AI Supply Chain Compromise: AI Agent Tool",
    "AML.T0011.000": "User Execution: Unsafe AI Artifacts",
    "AML.T0011.001": "User Execution: Malicious Package",
    "AML.T0011.002": "User Execution: Poisoned AI Agent Tool",
    "AML.T0011.003": "User Execution: Malicious Link",
    "AML.T0012": "Valid Accounts",
    "AML.T0016.002": "Obtain Capabilities: Generative AI",
    "AML.T0021": "Establish Accounts",
    "AML.T0024.002": "Exfiltration via AI Inference API: Extract AI Model",
    "AML.T0029": "Denial of AI Service",
    "AML.T0040": "AI Model Inference API Access",
    "AML.T0048.000": "External Harms: Financial Harm",
    "AML.T0049": "Exploit Public-Facing Application",
    "AML.T0050": "Command and Scripting Interpreter",
    "AML.T0051": "LLM Prompt Injection",
    "AML.T0051.000": "LLM Prompt Injection: Direct",
    "AML.T0051.001": "LLM Prompt Injection: Indirect",
    "AML.T0052.000": "Phishing: Spearphishing via Social Engineering LLM",
    "AML.T0052.001": "Phishing: Deepfake-Assisted Phishing",
    "AML.T0053": "AI Agent Tool Invocation",
    "AML.T0054": "LLM Jailbreak",
    "AML.T0055": "Unsecured Credentials",
    "AML.T0056": "Extract LLM System Prompt",
    "AML.T0057": "LLM Data Leakage",
    "AML.T0058": "Publish Poisoned Models",
    "AML.T0060": "Publish Hallucinated Entities",
    "AML.T0062": "Discover LLM Hallucinations",
    "AML.T0070": "RAG Poisoning",
    "AML.T0072": "Reverse Shell",
    "AML.T0077": "LLM Response Rendering",
    "AML.T0080": "AI Agent Context Poisoning",
    "AML.T0080.000": "AI Agent Context Poisoning: Memory",
    "AML.T0081": "Modify AI Agent Configuration",
    "AML.T0083": "Credentials from AI Agent Configuration",
    "AML.T0086": "Exfiltration via AI Agent Tool Invocation",
    "AML.T0088": "Generate Deepfakes",
    "AML.T0093": "Prompt Infiltration via Public-Facing Application",
    "AML.T0098": "AI Agent Tool Credential Harvesting",
    "AML.T0100": "AI Agent Clickbait",
    "AML.T0101": "Data Destruction via AI Agent Tool Invocation",
    "AML.T0102": "Generate Malicious Commands",
    "AML.T0104": "Publish Poisoned AI Agent Tool",
    "AML.T0105": "Escape to Host",
    "AML.T0108": "AI Agent",
    "AML.T0110": "AI Agent Tool Poisoning",
}
ATLAS_URL = "https://atlas.mitre.org/techniques/"

CSS = """
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#57534e;--line:#e7e5e4;--card:#ffffff;--accent:#0f766e;--accent-fg:#ffffff;--chip:#f5f5f4;
--surface:#dbeafe;--weapon:#fee2e2;--target:#fef3c7;--surface-fg:#1e3a8a;--weapon-fg:#7f1d1d;--target-fg:#78350f}
@media (prefers-color-scheme: dark){:root{--bg:#121110;--fg:#e7e5e4;--muted:#a8a29e;--line:#2a2726;--card:#1b1918;--accent:#2dd4bf;--accent-fg:#042f2e;--chip:#232020;
--surface:#1e3a8a;--weapon:#7f1d1d;--target:#78350f;--surface-fg:#dbeafe;--weapon-fg:#fee2e2;--target-fg:#fef3c7}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}a:hover{text-decoration-thickness:2px}
.wrap{max-width:1280px;margin:0 auto;padding:0 16px}
header.top{padding:28px 0 12px;border-bottom:1px solid var(--line)}
header.top h1{margin:0 0 6px;font-size:1.7rem;letter-spacing:-.01em}
header.top p{margin:0;color:var(--muted);max-width:70ch}
.nav{display:flex;flex-wrap:wrap;gap:4px 14px;margin:10px 0 0;font-size:.9rem;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}
.chip{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:3px 11px;font-size:.85rem;color:var(--muted)}
.chip b{color:var(--fg)}
.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:16px 0}
.controls input,.controls select,.controls button{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);font:inherit}
.controls input{grid-column:1/-1}
.controls button{cursor:pointer}
.count{color:var(--muted);font-size:.9rem;margin:0 0 8px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--card);cursor:pointer;user-select:none;white-space:nowrap;font-weight:600}
th .dir{color:var(--muted);font-size:.75rem;margin-left:3px}
tbody tr:hover{background:var(--chip)}
td.id,td.date,td.cve{white-space:nowrap;font-variant-numeric:tabular-nums}
td.name{min-width:220px}td.name a{font-weight:600;text-decoration:none}td.name a:hover{text-decoration:underline}
.lens{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.78rem;font-weight:600}
.lens-surface{background:var(--surface);color:var(--surface-fg)}.lens-weapon{background:var(--weapon);color:var(--weapon-fg)}.lens-target{background:var(--target);color:var(--target-fg)}
.code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.85em}
.empty{padding:24px;text-align:center;color:var(--muted)}
footer{margin:28px 0 40px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted);font-size:.88rem}
footer a{margin-right:12px}
@media (max-width:760px){.col-channel_in,.col-authority,.col-channel_out,.col-cve{display:none}}
.faq{margin:26px 0 0;max-width:86ch}
.faq h2{font-size:1.15rem;margin:0 0 4px}
.faq dl{margin:0}.faq dt{font-weight:600;margin-top:12px}.faq dd{margin:4px 0 0;color:var(--fg)}
/* record page */
.record h1{font-size:1.5rem;margin:18px 0 6px}
.meta{color:var(--muted);margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:14px 0}
.card h2{font-size:1.05rem;margin:0 0 10px}
dl.fields{display:grid;grid-template-columns:minmax(110px,max-content) minmax(0,1fr);gap:6px 16px;margin:0}
dl.fields dd,dl.fields li{overflow-wrap:anywhere}
@media (max-width:560px){dl.fields{grid-template-columns:1fr;gap:2px 0}dl.fields dt{margin-top:8px}}
dl.fields dt{color:var(--muted)}dl.fields dd{margin:0}
ul.plain{margin:0;padding-left:18px}
.pager{display:flex;justify-content:space-between;gap:12px;margin:18px 0;flex-wrap:wrap}
.record p.meta,.record h1{overflow-wrap:anywhere}
"""

JS = r"""
(function () {
  'use strict';
  var DATA = window.__INCIDENTS__;
  var FILTERS = ['type', 'lens', 'vector', 'channel_in', 'authority', 'channel_out', 'outcome', 'year', 'adversarial', 'status'];
  var COLS = ['id', 'date', 'name', 'type', 'lens', 'vector', 'channel_in', 'authority', 'channel_out', 'outcome', 'cve'];
  var state = { q: '', sort: 'id', dir: 1, f: {} };
  DATA.forEach(function (r) {
    r.year = r.date.slice(0, 4);
    r.adversarial_s = r.adversarial ? 'yes' : 'no';
    r.cve_s = r.cve.join('; ');
    var bag = [r.id, r.name, r.summary, r.date, r.type, r.lens, r.vector, r.channel_in, r.authority,
      r.channel_out, r.outcome, r.status, r.cve_s, r.tags.join(' '),
      r.affected.vendors.join(' '), r.affected.products.join(' '), r.affected.frameworks.join(' '),
      r.mappings.owasp_llm.join(' '), r.mappings.owasp_agentic.join(' '), r.mappings.mitre_atlas.join(' '),
      r.sources.map(function (s) { return s.url; }).join(' ')];
    r.bag = bag.join(' \n ').toLowerCase();
  });

  function $(id) { return document.getElementById(id); }
  function fieldOf(r, k) { return k === 'adversarial' ? r.adversarial_s : String(r[k]); }

  function buildOptions() {
    FILTERS.forEach(function (k) {
      var sel = $('f-' + k);
      if (!sel) { return; }
      var counts = {};
      DATA.forEach(function (r) { var v = fieldOf(r, k); counts[v] = (counts[v] || 0) + 1; });
      var keys = Object.keys(counts).sort(function (a, b) {
        if (k === 'year') { return a < b ? 1 : -1; }
        return counts[b] - counts[a] || (a < b ? -1 : 1);
      });
      keys.forEach(function (v) {
        var o = document.createElement('option');
        o.value = v; o.textContent = v + ' (' + counts[v] + ')';
        sel.appendChild(o);
      });
    });
  }

  function readHash() {
    var h = location.hash.replace(/^#/, '');
    if (!h) { return; }
    var p = new URLSearchParams(h);
    state.q = p.get('q') || '';
    FILTERS.forEach(function (k) { var v = p.get(k); if (v) { state.f[k] = v; } });
    var s = p.get('sort'); if (s && COLS.indexOf(s) >= 0) { state.sort = s; }
    state.dir = p.get('dir') === 'desc' ? -1 : 1;
  }

  function writeHash() {
    var p = new URLSearchParams();
    if (state.q) { p.set('q', state.q); }
    FILTERS.forEach(function (k) { if (state.f[k]) { p.set(k, state.f[k]); } });
    if (state.sort !== 'id') { p.set('sort', state.sort); }
    if (state.dir === -1) { p.set('dir', 'desc'); }
    var s = p.toString();
    try { history.replaceState(null, '', s ? '#' + s : location.pathname + location.search); } catch (e) { /* file:// */ }
  }

  function syncControls() {
    $('q').value = state.q;
    FILTERS.forEach(function (k) { var sel = $('f-' + k); if (sel) { sel.value = state.f[k] || ''; } });
  }

  function visible() {
    var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    return DATA.filter(function (r) {
      for (var i = 0; i < FILTERS.length; i++) {
        var k = FILTERS[i];
        if (state.f[k] && fieldOf(r, k) !== state.f[k]) { return false; }
      }
      for (var j = 0; j < terms.length; j++) {
        if (r.bag.indexOf(terms[j]) < 0) { return false; }
      }
      return true;
    });
  }

  function sorted(rows) {
    var k = state.sort, d = state.dir;
    return rows.slice().sort(function (a, b) {
      var x = k === 'cve' ? a.cve_s : fieldOf(a, k);
      var y = k === 'cve' ? b.cve_s : fieldOf(b, k);
      if (k === 'name') { x = x.toLowerCase(); y = y.toLowerCase(); }
      if (x === y) { return (a.id < b.id ? -1 : 1) * d; }
      return (x < y ? -1 : 1) * d;
    });
  }

  function cell(tr, cls, text) {
    var td = document.createElement('td');
    td.className = cls + ' col-' + cls;
    td.textContent = text;
    tr.appendChild(td);
    return td;
  }

  function render() {
    var rows = sorted(visible());
    var tbody = $('rows');
    while (tbody.firstChild) { tbody.removeChild(tbody.firstChild); }
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      cell(tr, 'id', r.id);
      cell(tr, 'date', r.date);
      var td = document.createElement('td'); td.className = 'name col-name';
      var a = document.createElement('a'); a.href = 'incidents/' + r.id + '.html'; a.textContent = r.name;
      td.appendChild(a); tr.appendChild(td);
      cell(tr, 'type', r.type);
      var tl = document.createElement('td'); tl.className = 'lens-cell col-lens';
      var sp = document.createElement('span'); sp.className = 'lens lens-' + r.lens; sp.textContent = r.lens;
      tl.appendChild(sp); tr.appendChild(tl);
      cell(tr, 'vector', r.vector);
      cell(tr, 'channel_in', r.channel_in);
      cell(tr, 'authority', r.authority);
      cell(tr, 'channel_out', r.channel_out);
      cell(tr, 'outcome', r.outcome);
      cell(tr, 'cve', r.cve_s || '-');
      tbody.appendChild(tr);
    });
    $('empty').style.display = rows.length ? 'none' : 'block';
    $('count').textContent = 'Showing ' + rows.length + ' of ' + DATA.length + ' events';
    document.querySelectorAll('th[data-key]').forEach(function (th) {
      var dir = th.querySelector('.dir');
      dir.textContent = th.getAttribute('data-key') === state.sort ? (state.dir === 1 ? '▲' : '▼') : '';
    });
    writeHash();
  }

  function bind() {
    $('q').addEventListener('input', function (e) { state.q = e.target.value; render(); });
    FILTERS.forEach(function (k) {
      var sel = $('f-' + k);
      if (sel) { sel.addEventListener('change', function (e) { state.f[k] = e.target.value; render(); }); }
    });
    $('clear').addEventListener('click', function () {
      state.q = ''; state.f = {}; state.sort = 'id'; state.dir = 1; syncControls(); render();
    });
    document.querySelectorAll('th[data-key]').forEach(function (th) {
      th.addEventListener('click', function () {
        var k = th.getAttribute('data-key');
        if (state.sort === k) { state.dir = -state.dir; } else { state.sort = k; state.dir = 1; }
        render();
      });
    });
    window.addEventListener('hashchange', function () { state.f = {}; readHash(); syncControls(); render(); });
  }

  buildOptions();
  readHash();
  syncControls();
  bind();
  render();
})();
"""


def esc(s):
    return html.escape(str(s), quote=True)


def load_records(incidents_dir):
    return export_csv.load_records(incidents_dir)


def lens_badge(lens):
    return '<span class="lens lens-%s">%s</span>' % (esc(lens), esc(lens))


def counts(records, key, order=None):
    c = Counter(fieldval(r, key) for r in records)
    if order == "key":
        return OrderedDict(sorted(c.items()))
    return OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def fieldval(r, key):
    if key == "year":
        return r["date"][:4]
    if key == "adversarial":
        return "yes" if r["adversarial"] else "no"
    return r[key]


def build_stats(records):
    s = OrderedDict()
    s["title"] = SITE_TITLE
    s["source"] = REPO_URL
    s["total"] = len(records)
    dates = sorted(r["date"] for r in records)
    s["period"] = {"from": dates[0] if dates else None, "to": dates[-1] if dates else None}
    s["by_year"] = counts(records, "year", "key")
    for k in CODED_FIELDS:
        s["by_" + k] = counts(records, k)
    s["by_status"] = counts(records, "status")
    s["by_lens_and_type"] = OrderedDict()
    for lens in ["surface", "weapon", "target"]:
        s["by_lens_and_type"][lens] = counts([r for r in records if r["lens"] == lens], "type")
    s["by_year_and_lens"] = OrderedDict()
    for year, _ in s["by_year"].items():
        s["by_year_and_lens"][year] = OrderedDict(
            (lens, sum(1 for r in records if r["date"][:4] == year and r["lens"] == lens))
            for lens in ["surface", "weapon", "target"])
    s["with_cve"] = sum(1 for r in records if r["cve"])
    s["mapped"] = OrderedDict([
        ("owasp_llm", sum(1 for r in records if r["mappings"]["owasp_llm"])),
        ("owasp_agentic", sum(1 for r in records if r["mappings"]["owasp_agentic"])),
        ("mitre_atlas", sum(1 for r in records if r["mappings"]["mitre_atlas"])),
        ("any", sum(1 for r in records if any(r["mappings"].values()))),
    ])
    s["by_owasp_llm"] = OrderedDict(sorted(Counter(i for r in records for i in r["mappings"]["owasp_llm"]).items()))
    s["by_owasp_agentic"] = OrderedDict(sorted(Counter(i for r in records for i in r["mappings"]["owasp_agentic"]).items()))
    s["by_mitre_atlas"] = OrderedDict(sorted(Counter(i for r in records for i in r["mappings"]["mitre_atlas"]).items(), key=lambda kv: (-kv[1], kv[0])))
    s["by_tag"] = OrderedDict(sorted(Counter(t for r in records for t in r["tags"]).items(), key=lambda kv: (-kv[1], kv[0])))
    return s


def md_table(title, mapping, label="value", names=None):
    out = ["### %s" % title, "", "| %s | events |" % label, "|---|---:|"]
    for k, v in mapping.items():
        name = (" " + names[k]) if names and k in names else ""
        out.append("| `%s`%s | %d |" % (k, name, v))
    out.append("")
    return "\n".join(out)


def build_stats_md(stats):
    lines = ["# Dataset statistics", "",
             "Generated by `scripts/build_site.py` from `incidents/*.json`; do not edit by hand.", "",
             "- Events: **%d**" % stats["total"],
             "- Period: %s to %s" % (stats["period"]["from"], stats["period"]["to"]),
             "- Events with at least one CVE: %d" % stats["with_cve"],
             "- Events mapped to OWASP LLM Top 10: %d; to OWASP Agentic Top 10: %d; to MITRE ATLAS: %d; to any: %d" % (
                 stats["mapped"]["owasp_llm"], stats["mapped"]["owasp_agentic"], stats["mapped"]["mitre_atlas"], stats["mapped"]["any"]),
             ""]
    lines.append(md_table("By year", stats["by_year"], "year"))
    yl = ["### By year and lens", "", "| year | surface | weapon | target | total |", "|---|---:|---:|---:|---:|"]
    for year, d in stats["by_year_and_lens"].items():
        yl.append("| %s | %d | %d | %d | %d |" % (year, d["surface"], d["weapon"], d["target"], sum(d.values())))
    lines.append("\n".join(yl) + "\n")
    for k in CODED_FIELDS:
        lines.append(md_table("By %s" % k, stats["by_" + k], k))
    lt = ["### By lens and type", "", "| lens | incident | vulnerability-disclosure | threat-report |", "|---|---:|---:|---:|"]
    for lens, d in stats["by_lens_and_type"].items():
        lt.append("| %s | %d | %d | %d |" % (lens, d.get("incident", 0), d.get("vulnerability-disclosure", 0), d.get("threat-report", 0)))
    lines.append("\n".join(lt) + "\n")
    lines.append(md_table("By status", stats["by_status"], "status"))
    lines.append(md_table("By OWASP Top 10 for LLM Applications (2025)", stats["by_owasp_llm"], "id", OWASP_LLM))
    lines.append(md_table("By OWASP Top 10 for Agentic Applications (2026)", stats["by_owasp_agentic"], "id", OWASP_ASI))
    lines.append(md_table("By MITRE ATLAS technique", stats["by_mitre_atlas"], "id", ATLAS))
    lines.append(md_table("By tag", stats["by_tag"], "tag"))
    return "\n".join(lines).rstrip() + "\n"


def page_head(title, depth=0, description=None, canonical=None, jsonld=None, og_type="website", og_image=None):
    desc = description or TAGLINE
    canonical = canonical or SITE_URL
    parts = ["<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n",
             "<title>%s</title>\n" % esc(title),
             "<meta name=\"description\" content=\"%s\">\n" % esc(desc),
             "<link rel=\"canonical\" href=\"%s\">\n" % esc(canonical),
             "<meta property=\"og:type\" content=\"%s\">\n" % esc(og_type),
             "<meta property=\"og:site_name\" content=\"%s\">\n" % esc(SITE_TITLE),
             "<meta property=\"og:title\" content=\"%s\">\n" % esc(title),
             "<meta property=\"og:description\" content=\"%s\">\n" % esc(desc),
             "<meta property=\"og:url\" content=\"%s\">\n" % esc(canonical),
             "<meta name=\"twitter:card\" content=\"%s\">\n" % ("summary_large_image" if og_image else "summary"),
             "<meta name=\"twitter:title\" content=\"%s\">\n" % esc(title),
             "<meta name=\"twitter:description\" content=\"%s\">\n" % esc(desc)]
    if og_image:
        parts.append("<meta property=\"og:image\" content=\"%s\">\n" % esc(og_image))
        parts.append("<meta property=\"og:image:width\" content=\"1280\">\n<meta property=\"og:image:height\" content=\"640\">\n")
        parts.append("<meta name=\"twitter:image\" content=\"%s\">\n" % esc(og_image))
    parts.append("<link rel=\"alternate\" type=\"application/rss+xml\" title=\"%s\" href=\"%sfeed.xml\">\n"
                 % (esc(SITE_TITLE), "../" * depth))
    parts.append("<link rel=\"alternate\" type=\"text/plain\" title=\"llms.txt: machine-readable summary of this dataset for AI assistants\" href=\"%sllms.txt\">\n"
                 % ("../" * depth))
    parts.append("<link rel=\"alternate\" type=\"text/plain\" title=\"llms-full.txt: the summary plus one line per record\" href=\"%sllms-full.txt\">\n"
                 % ("../" * depth))
    if jsonld is not None:
        for block in (jsonld if isinstance(jsonld, list) else [jsonld]):
            parts.append("<script type=\"application/ld+json\">\n%s\n</script>\n"
                         % json.dumps(block, ensure_ascii=False, indent=1).replace("</", "<\\/"))
    parts.append("<style>%s</style>\n</head>\n<body>\n<div class=\"wrap\">\n" % CSS)
    return "".join(parts)


def page_foot():
    return ("<footer>CC BY 4.0 data, MIT code. "
            "<a href=\"%s\">Source repository</a> "
            "<a href=\"%s\">Codebook</a></footer>\n"
            "</div>\n</body>\n</html>\n" % (esc(REPO_URL), esc(REPO_URL + "/blob/main/docs/codebook.md")))


def dataset_jsonld(stats, og_image=None):
    """schema.org Dataset for the index page (Google Dataset Search reads this)."""
    period = stats["period"]
    d = OrderedDict()
    d["@context"] = "https://schema.org"
    d["@type"] = "Dataset"
    d["@id"] = SITE_URL + "#dataset"
    d["name"] = "AI Agent Incidents"
    d["alternateName"] = ["ai-agent-incidents", "Open dataset of AI agent and LLM security incidents"]
    d["description"] = INDEX_DESCRIPTION + " %d records from %s to %s." % (stats["total"], period["from"], period["to"])
    d["url"] = SITE_URL
    d["sameAs"] = [REPO_URL]
    d["identifier"] = REPO_URL
    d["license"] = LICENSE_URL
    d["isAccessibleForFree"] = True
    d["version"] = DATASET_VERSION
    d["creator"] = AUTHOR
    d["keywords"] = KEYWORDS
    d["inLanguage"] = "en"
    d["temporalCoverage"] = "%s/%s" % (period["from"], period["to"])
    d["dateModified"] = period["to"]
    d["size"] = "%d records" % stats["total"]
    d["measurementTechnique"] = "Manual coding of public primary sources under a written codebook"
    d["variableMeasured"] = [OrderedDict([("@type", "PropertyValue"), ("name", k)]) for k in CODED_FIELDS]
    d["citation"] = PAPER_CITATION
    d["distribution"] = [
        OrderedDict([("@type", "DataDownload"), ("name", "All records as JSON"),
                     ("contentUrl", SITE_URL + "incidents.json"), ("encodingFormat", "application/json")]),
        OrderedDict([("@type", "DataDownload"), ("name", "Flat export as CSV"),
                     ("contentUrl", SITE_URL + "incidents.csv"), ("encodingFormat", "text/csv")]),
    ]
    if og_image:
        d["image"] = og_image
    return d


def record_jsonld(r, url, filename, og_image=None):
    """Article plus a Dataset subset for one record page."""
    keywords = list(r["tags"]) + [r["type"], r["lens"], r["vector"], r["outcome"]]
    article = OrderedDict()
    article["@type"] = "Article"
    article["@id"] = url + "#article"
    article["headline"] = "%s %s" % (r["id"], r["name"])
    article["description"] = r["summary"]
    article["url"] = url
    article["mainEntityOfPage"] = url
    article["datePublished"] = r["date"]
    article["dateModified"] = r["date"]
    article["author"] = AUTHOR
    article["inLanguage"] = "en"
    article["keywords"] = keywords
    article["isPartOf"] = OrderedDict([("@id", SITE_URL + "#dataset")])
    article["license"] = LICENSE_URL
    if og_image:
        article["image"] = og_image
    subset = OrderedDict()
    subset["@type"] = "Dataset"
    subset["@id"] = url + "#record"
    subset["name"] = "AI Agent Incidents record %s: %s" % (r["id"], r["name"])
    subset["description"] = r["summary"]
    subset["url"] = url
    subset["identifier"] = r["id"]
    subset["isPartOf"] = OrderedDict([("@id", SITE_URL + "#dataset")])
    subset["license"] = LICENSE_URL
    subset["isAccessibleForFree"] = True
    subset["creator"] = AUTHOR
    subset["temporalCoverage"] = r["date"]
    subset["keywords"] = keywords
    subset["sameAs"] = ["%s/blob/main/incidents/%s" % (REPO_URL, filename)]
    subset["distribution"] = [OrderedDict([
        ("@type", "DataDownload"), ("name", "This record as JSON"),
        ("contentUrl", "https://raw.githubusercontent.com/basitalisandhu/ai-agent-incidents/main/incidents/%s" % filename),
        ("encodingFormat", "application/json")])]
    return OrderedDict([("@context", "https://schema.org"), ("@graph", [article, subset])])


def faq_fields(stats):
    return {"total": stats["total"], "from": stats["period"]["from"], "to": stats["period"]["to"],
            "incident": stats["by_type"].get("incident", 0),
            "vuln": stats["by_type"].get("vulnerability-disclosure", 0),
            "report": stats["by_type"].get("threat-report", 0),
            "repo": REPO_URL, "site": SITE_URL, "license": LICENSE_URL,
            "version": DATASET_VERSION}


def faq_entries(stats):
    f = faq_fields(stats)
    return [(q, a_html % f, a_text % f) for q, a_html, a_text in FAQ]


def faq_jsonld(stats):
    d = OrderedDict()
    d["@context"] = "https://schema.org"
    d["@type"] = "FAQPage"
    d["@id"] = SITE_URL + "#faq"
    d["url"] = SITE_URL + "#faq"
    d["name"] = "Questions about the AI Agent Incidents dataset"
    d["inLanguage"] = "en"
    d["about"] = OrderedDict([("@id", SITE_URL + "#dataset")])
    d["mainEntity"] = [OrderedDict([("@type", "Question"), ("name", q),
                                    ("acceptedAnswer", OrderedDict([("@type", "Answer"), ("text", a_text)]))])
                       for q, _, a_text in faq_entries(stats)]
    return d


def build_faq_html(stats):
    out = ["<section class=\"faq\" id=\"faq\"><h2>Frequently asked questions</h2><dl>"]
    for q, a_html, _ in faq_entries(stats):
        out.append("<dt>%s</dt><dd>%s</dd>" % (esc(q), a_html))
    out.append("</dl></section>")
    return "".join(out)


def build_index(records, stats, og_image=None):
    chips = [
        ("events", stats["total"]),
        ("incidents", stats["by_type"].get("incident", 0)),
        ("vulnerability disclosures", stats["by_type"].get("vulnerability-disclosure", 0)),
        ("threat reports", stats["by_type"].get("threat-report", 0)),
        ("surface lens", stats["by_lens"].get("surface", 0)),
        ("weapon lens", stats["by_lens"].get("weapon", 0)),
        ("target lens", stats["by_lens"].get("target", 0)),
    ]
    chip_html = "".join("<span class=\"chip\"><b>%d</b> %s</span>" % (v, esc(k)) for k, v in chips)
    chip_html += "<span class=\"chip\">%s to %s</span>" % (esc(stats["period"]["from"]), esc(stats["period"]["to"]))
    selects = []
    for k in ["type", "lens", "vector", "channel_in", "authority", "channel_out", "outcome", "year", "adversarial", "status"]:
        selects.append("<select id=\"f-%s\" aria-label=\"Filter by %s\"><option value=\"\">%s: all</option></select>" % (k, k, k))
    cols = [("id", "id"), ("date", "date"), ("name", "name"), ("type", "type"), ("lens", "lens"), ("vector", "vector"),
            ("channel_in", "channel in"), ("authority", "authority"), ("channel_out", "channel out"), ("outcome", "outcome"), ("cve", "cve")]
    ths = "".join("<th class=\"col-%s\" data-key=\"%s\" scope=\"col\">%s<span class=\"dir\"></span></th>" % (k, k, esc(label)) for k, label in cols)
    data_json = json.dumps(records, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = [page_head(INDEX_TITLE, description=INDEX_DESCRIPTION, canonical=SITE_URL,
                     jsonld=[dataset_jsonld(stats, og_image), faq_jsonld(stats)], og_image=og_image)]
    out.append("<header class=\"top\"><h1>%s</h1><p>%s</p>" % (esc(SITE_TITLE), esc(TAGLINE)))
    out.append("<p class=\"nav\"><a href=\"%s\">GitHub</a><a href=\"incidents.json\">JSON</a><a href=\"incidents.csv\">CSV</a>"
               "<a href=\"stats.json\">Stats</a><a href=\"feed.xml\">RSS</a><a href=\"incident.schema.json\">Schema</a>"
               "<a href=\"%s/blob/main/docs/codebook.md\">Codebook</a><a href=\"%s/blob/main/CONTRIBUTING.md\">Add an incident</a></p>" % (esc(REPO_URL), esc(REPO_URL), esc(REPO_URL)))
    out.append("<div class=\"chips\">%s</div></header>" % chip_html)
    out.append("<div class=\"controls\"><input id=\"q\" type=\"search\" placeholder=\"Search name, summary, CVE, vendor, tag, mapping id\" aria-label=\"Search\">%s<button id=\"clear\" type=\"button\">Clear filters</button></div>" % "".join(selects))
    out.append("<p class=\"count\" id=\"count\"></p>")
    out.append("<div class=\"tablewrap\"><table id=\"t\"><thead><tr>%s</tr></thead><tbody id=\"rows\"></tbody></table><div class=\"empty\" id=\"empty\" style=\"display:none\">No events match.</div></div>")
    out[-1] = out[-1] % ths
    out.append("<noscript><p class=\"empty\">This table needs JavaScript. The data is also available as <a href=\"incidents.json\">JSON</a> and <a href=\"incidents.csv\">CSV</a>.</p></noscript>")
    out.append(build_faq_html(stats))
    out.append(page_foot().replace("</div>\n</body>", "</div>\n<script>window.__INCIDENTS__=%s;</script>\n<script>%s</script>\n</body>" % (data_json, JS)))
    return "".join(out)


def ref_list(ids, names, base, mode):
    if not ids:
        return "<dd>none</dd>"
    items = []
    for i in ids:
        name = names.get(i)
        label = "%s %s" % (i, name) if name else i
        href = base + i if mode == "atlas" else base
        items.append("<li><a href=\"%s\" rel=\"noopener\">%s</a></li>" % (esc(href), esc(label)))
    return "<dd><ul class=\"plain\">%s</ul></dd>" % "".join(items)


def build_record_page(r, prev_r, next_r, filename, og_image=None):
    desc = r["summary"]
    url = "%sincidents/%s.html" % (SITE_URL, r["id"])
    out = [page_head("%s %s | %s" % (r["id"], r["name"], SITE_TITLE), depth=1, description=desc, canonical=url,
                     jsonld=record_jsonld(r, url, filename, og_image), og_type="article", og_image=og_image)]
    out.append("<p class=\"nav\"><a href=\"../index.html\">All events</a><a href=\"../feed.xml\">RSS</a><a href=\"%s\">GitHub</a></p>" % esc(REPO_URL))
    out.append("<article class=\"record\"><h1>%s</h1>" % esc(r["name"]))
    out.append("<p class=\"meta\">D-%d &middot; %s &middot; %s &middot; %s &middot; status: %s</p>" % (
        int(r["id"]), esc(r["date"]), esc(r["type"]), lens_badge(r["lens"]), esc(r["status"])))
    out.append("<div class=\"card\"><h2>Summary</h2><p>%s</p></div>" % esc(r["summary"]))
    out.append("<div class=\"card\"><h2>Coding</h2><dl class=\"fields\">")
    for k in CODED_FIELDS:
        v = "yes" if k == "adversarial" and r[k] else ("no" if k == "adversarial" else r[k])
        if k == "lens":
            out.append("<dt>%s</dt><dd>%s</dd>" % (k, lens_badge(v)))
        else:
            out.append("<dt>%s</dt><dd><span class=\"code\">%s</span></dd>" % (k, esc(v)))
    out.append("<dt>cve</dt><dd>%s</dd>" % (esc("; ".join(r["cve"])) if r["cve"] else "none"))
    out.append("</dl><p class=\"meta\" style=\"margin-top:10px\">Definitions: <a href=\"%s/blob/main/docs/codebook.md\">codebook</a>.</p></div>" % esc(REPO_URL))
    out.append("<div class=\"card\"><h2>Sources</h2><ul class=\"plain\">")
    for s in r["sources"]:
        label = s.get("title") or s["url"]
        extra = []
        if s.get("publisher"):
            extra.append(esc(s["publisher"]))
        if s.get("accessed"):
            extra.append("confirmed reachable %s" % esc(s["accessed"]))
        out.append("<li><a href=\"%s\" rel=\"noopener nofollow\">%s</a>%s</li>" % (esc(s["url"]), esc(label), (" (%s)" % ", ".join(extra)) if extra else ""))
    out.append("</ul></div>")
    m = r["mappings"]
    out.append("<div class=\"card\"><h2>Mappings</h2><dl class=\"fields\">")
    out.append("<dt>OWASP LLM Top 10 (2025)</dt>%s" % ref_list(m["owasp_llm"], OWASP_LLM, OWASP_LLM_URL, "owasp"))
    out.append("<dt>OWASP Agentic Top 10 (2026)</dt>%s" % ref_list(m["owasp_agentic"], OWASP_ASI, OWASP_ASI_URL, "owasp"))
    out.append("<dt>MITRE ATLAS</dt>%s" % ref_list(m["mitre_atlas"], ATLAS, ATLAS_URL, "atlas"))
    out.append("</dl></div>")
    a = r["affected"]
    out.append("<div class=\"card\"><h2>Affected</h2><dl class=\"fields\">")
    for k in ["vendors", "products", "frameworks"]:
        out.append("<dt>%s</dt><dd>%s</dd>" % (k, esc(", ".join(a[k])) if a[k] else "none listed"))
    out.append("<dt>tags</dt><dd>%s</dd>" % (" ".join("<span class=\"chip\">%s</span>" % esc(t) for t in r["tags"]) if r["tags"] else "none"))
    out.append("</dl></div>")
    out.append("<p class=\"meta\">Record: <a href=\"%s/blob/main/incidents/%s\">incidents/%s</a> &middot; <a href=\"../incidents.json\">all records as JSON</a></p>" % (esc(REPO_URL), esc(filename), esc(filename)))
    out.append("<div class=\"pager\">")
    out.append("<span>%s</span>" % ("<a href=\"%s.html\">&larr; %s %s</a>" % (esc(prev_r["id"]), esc(prev_r["id"]), esc(prev_r["name"])) if prev_r else ""))
    out.append("<span>%s</span>" % ("<a href=\"%s.html\">%s %s &rarr;</a>" % (esc(next_r["id"]), esc(next_r["id"]), esc(next_r["name"])) if next_r else ""))
    out.append("</div></article>")
    out.append(page_foot())
    return "".join(out)


def rfc822(date_str):
    d = dt.datetime.strptime(date_str, "%Y-%m-%d" if len(date_str) == 10 else "%Y-%m")
    return d.strftime("%a, %d %b %Y 00:00:00 +0000")


def build_feed(records):
    newest = sorted(records, key=lambda r: (r["date"], r["id"]), reverse=True)
    build_date = rfc822(newest[0]["date"]) if newest else rfc822("2023-01")
    out = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
           "<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">",
           "<channel>",
           "<title>%s</title>" % esc(SITE_TITLE),
           "<link>%s</link>" % esc(SITE_URL),
           "<description>%s</description>" % esc(TAGLINE),
           "<language>en</language>",
           "<lastBuildDate>%s</lastBuildDate>" % build_date,
           "<atom:link href=\"%sfeed.xml\" rel=\"self\" type=\"application/rss+xml\"/>" % esc(SITE_URL)]
    for r in newest:
        link = "%sincidents/%s.html" % (SITE_URL, r["id"])
        body = "%s Type: %s. Lens: %s. Vector: %s. Outcome: %s.%s Dates are months unless a day is given; the feed date is the first of that month." % (
            r["summary"], r["type"], r["lens"], r["vector"], r["outcome"], (" CVE: %s." % "; ".join(r["cve"])) if r["cve"] else "")
        out += ["<item>",
                "<title>%s</title>" % esc("%s %s" % (r["id"], r["name"])),
                "<link>%s</link>" % esc(link),
                "<guid isPermaLink=\"true\">%s</guid>" % esc(link),
                "<pubDate>%s</pubDate>" % rfc822(r["date"]),
                "<category>%s</category><category>%s</category><category>%s</category>" % (esc(r["type"]), esc(r["lens"]), esc(r["vector"])),
                "<description>%s</description>" % esc(body),
                "</item>"]
    out += ["</channel>", "</rss>", ""]
    return "\n".join(out)


def iso_date(date_str):
    return date_str if len(date_str) == 10 else date_str + "-01"


def build_robots():
    out = ["# AI Agent Incidents: %s" % SITE_URL,
           "# Everything here is public data (CC BY 4.0). Search engines, AI training crawlers,",
           "# AI search crawlers and user-triggered AI fetchers are all welcome.",
           "# Machine-readable summary for assistants: %sllms.txt and %sllms-full.txt" % (SITE_URL, SITE_URL),
           "", "User-agent: *", "Allow: /", ""]
    for operator, agents in AI_CRAWLERS:
        out.append("# %s" % operator)
        for agent in agents:
            out += ["User-agent: %s" % agent, "Allow: /", ""]
    out.append("Sitemap: %ssitemap.xml" % SITE_URL)
    return "\n".join(out) + "\n"


def read_indexnow_key():
    key = INDEXNOW_KEY_FILE.read_text(encoding="utf-8").strip()
    if len(key) < 8 or len(key) > 128 or not all(c.isalnum() or c == "-" for c in key):
        raise SystemExit("error: %s must hold an IndexNow key of 8 to 128 letters, digits or dashes" % INDEXNOW_KEY_FILE)
    return key


def llms_header(stats):
    period = stats["period"]
    lines = ["# AI Agent Incidents", "",
             "> Open, structured dataset of publicly documented security incidents, vulnerability disclosures and "
             "threat reports involving LLM applications and AI agents: %d events from %s to %s, one schema-validated "
             "JSON record per event, coded under a written codebook by the role AI plays (weapon, target or surface), "
             "vector, input channel, authority held, output channel, whether an attack technique is involved, and outcome, "
             "and cross-referenced to the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and "
             "MITRE ATLAS. Data CC BY 4.0, code MIT. Maintained by Muhammad Basit Ali (GitHub: basitalisandhu)." % (stats["total"], period["from"], period["to"]),
             "",
             "Key facts:", "",
             "- Size on the last build: %d events (%d incidents, %d vulnerability disclosures, %d threat reports); "
             "%d carry at least one CVE; %d are mapped to the OWASP LLM Top 10, %d to the OWASP Agentic Top 10 and %d to MITRE ATLAS." % (
                 stats["total"], stats["by_type"].get("incident", 0), stats["by_type"].get("vulnerability-disclosure", 0),
                 stats["by_type"].get("threat-report", 0), stats["with_cve"], stats["mapped"]["owasp_llm"],
                 stats["mapped"]["owasp_agentic"], stats["mapped"]["mitre_atlas"]),
             "- Lens counts: surface %d (the AI is a conduit to another party's assets), weapon %d (the AI is the attacker's instrument), "
             "target %d (the AI system itself is attacked, exposed or disrupted)." % (
                 stats["by_lens"].get("surface", 0), stats["by_lens"].get("weapon", 0), stats["by_lens"].get("target", 0)),
             "- Most common vectors: " + ", ".join("%s (%d)" % kv for kv in list(stats["by_vector"].items())[:6]) + ".",
             "- Licence: data CC BY 4.0 (%s), attribution to Muhammad Basit Ali and %s; code MIT. Commercial use is allowed with attribution." % (LICENSE_URL, REPO_URL),
             "- Unit and sampling: one primary source's account of one event; dates are the month of the public report; a convenience sample of "
             "what was made public, so shares computed from it do not estimate population shares.",
             "- Coding: by the author of the paper under the codebook; every source was opened and read; the paper reports two further blind "
             "codings and their agreement. Mappings are given only where the source supports them; an empty list means no confident mapping.",
             "- Record fields: id, date (YYYY-MM or YYYY-MM-DD), name, type, lens, vector, channel_in, authority, channel_out, adversarial, outcome, "
             "cve, sources (url, title, publisher), summary, mappings (owasp_llm, owasp_agentic, mitre_atlas), affected (vendors, products, frameworks), tags, status.",
             "- Citation: Muhammad Basit Ali. AI Agent Incidents: an open dataset of publicly documented AI-agent and LLM-application security incidents. "
             "Version %s, 2026. %s. The coding scheme is from: %s" % (DATASET_VERSION, REPO_URL, PAPER_CITATION),
             "",
             "## Downloads", "",
             "- [All records as JSON](%sincidents.json): one array, the schema is incidents.schema.json next to it." % SITE_URL,
             "- [Flat CSV](%sincidents.csv): the paper's fourteen columns, one row per event." % SITE_URL,
             "- [JSON Schema](%sincident.schema.json): JSON Schema 2020-12 for one record." % SITE_URL,
             "- [Statistics](%sstats.json): counts by year, type, lens, vector, channel, authority, outcome, status, tag and mapping id." % SITE_URL,
             "- [RSS feed](%sfeed.xml): newest records first." % SITE_URL,
             "- [Hugging Face mirror](%s): the same files, regenerated from the repository." % HF_URL,
             "",
             "## Documentation", "",
             "- [Repository and contribution rules](%s): one JSON file and one pull request per event; public primary source required." % REPO_URL,
             "- [Codebook](%s/blob/main/docs/codebook.md): definitions of every coded field and value." % REPO_URL,
             "- [Statistics as Markdown](%s/blob/main/docs/stats.md): the same counts as stats.json." % REPO_URL,
             "- [Verification log](%s/blob/main/docs/verification-log.md): which source URLs were re-checked and when." % REPO_URL,
             "- [CITATION.cff](%s/blob/main/CITATION.cff): dataset and paper citations." % REPO_URL,
             "- [Frequently asked questions](%s#faq): is there a public dataset, how incidents are coded, commercial use, adding an incident, citing, limits." % SITE_URL,
             "- [Browse the dataset](%s): searchable table with one page per event at incidents/<id>.html." % SITE_URL]
    return lines


def build_llms_txt(stats):
    lines = llms_header(stats)
    lines += ["", "## Optional", "",
              "- [Every record, one line each](%sllms-full.txt): id, date, name, type, lens, vector, outcome and URL." % SITE_URL]
    return "\n".join(lines) + "\n"


def build_llms_full_txt(records, stats):
    lines = llms_header(stats)
    lines += ["", "## Frequently asked questions", ""]
    for q, _, a_text in faq_entries(stats):
        lines += ["### %s" % q, "", a_text, ""]
    lines += ["## Records", "",
              "One line per event: id, date, name, type, lens, vector, authority, outcome, CVE if any, page URL. "
              "The page holds the summary, sources, full coding, mappings and affected products.", ""]
    for r in records:
        cve = (" CVE: %s." % "; ".join(r["cve"])) if r["cve"] else ""
        lines.append("- %s (%s) %s. %s; lens %s; vector %s; authority %s; outcome %s.%s %sincidents/%s.html" % (
            r["id"], r["date"], r["name"], r["type"], r["lens"], r["vector"], r["authority"], r["outcome"], cve, SITE_URL, r["id"]))
    return "\n".join(lines) + "\n"


def build_sitemap(records, stats):
    out = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
           "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
           "<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>"
           % (esc(SITE_URL), iso_date(stats["period"]["to"]))]
    for r in records:
        out.append("<url><loc>%sincidents/%s.html</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>"
                   % (esc(SITE_URL), esc(r["id"]), iso_date(r["date"])))
    out += ["</urlset>", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--incidents", default="incidents")
    ap.add_argument("--site", default="site")
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--schema", default="schema/incident.schema.json")
    ap.add_argument("--assets", default=ASSETS_DIR, help="directory that may hold %s" % OG_IMAGE)
    args = ap.parse_args(argv)

    inc_dir = Path(args.incidents)
    site = Path(args.site)
    docs = Path(args.docs)
    files = sorted(inc_dir.glob("*.json"))
    records = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    by_id = {r["id"]: p.name for r, p in zip(records, files)}
    records.sort(key=lambda r: (len(r["id"]), r["id"]))
    if not records:
        print("error: no records in %s" % inc_dir, file=sys.stderr)
        return 1

    if site.exists():
        shutil.rmtree(site)
    (site / "incidents").mkdir(parents=True)
    docs.mkdir(parents=True, exist_ok=True)

    stats = build_stats(records)
    og_src = Path(args.assets) / OG_IMAGE
    og_image = None
    if og_src.is_file():
        shutil.copyfile(og_src, site / OG_IMAGE)
        og_image = SITE_URL + OG_IMAGE
    (site / "index.html").write_text(build_index(records, stats, og_image), encoding="utf-8")
    for i, r in enumerate(records):
        prev_r = records[i - 1] if i > 0 else None
        next_r = records[i + 1] if i + 1 < len(records) else None
        (site / "incidents" / ("%s.html" % r["id"])).write_text(
            build_record_page(r, prev_r, next_r, by_id[r["id"]], og_image), encoding="utf-8")
    (site / "incidents.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    export_csv.write_csv(records, site / "incidents.csv")
    shutil.copyfile(args.schema, site / "incident.schema.json")
    (site / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (site / "feed.xml").write_text(build_feed(records), encoding="utf-8")
    (site / "sitemap.xml").write_text(build_sitemap(records, stats), encoding="utf-8")
    (site / "robots.txt").write_text(build_robots(), encoding="utf-8")
    (site / "llms.txt").write_text(build_llms_txt(stats), encoding="utf-8")
    (site / "llms-full.txt").write_text(build_llms_full_txt(records, stats), encoding="utf-8")
    key = read_indexnow_key()
    (site / (key + ".txt")).write_text(key, encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")
    (docs / "stats.md").write_text(build_stats_md(stats), encoding="utf-8")
    print("built %s (%d records) and %s" % (site, len(records), docs / "stats.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
