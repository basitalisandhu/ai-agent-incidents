# AI Agent Incidents: an open dataset of AI agent and LLM security incidents

[![CI](https://github.com/basitalisandhu/ai-agent-incidents/actions/workflows/ci.yml/badge.svg)](https://github.com/basitalisandhu/ai-agent-incidents/actions/workflows/ci.yml)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-blue.svg)](LICENSE-DATA)
[![Code: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)

An open, structured dataset (an incident database) of publicly documented security
incidents, vulnerability disclosures and threat reports involving LLM applications and
AI agents, for security engineers, researchers and policy teams who need evidence about
prompt injection, data exfiltration, supply-chain compromise and agent misuse rather
than headlines. Every event is one schema-validated JSON file, coded under a written codebook by the role AI plays
in it (**weapon**, **target** or **surface**), how the attack got in, what authority the
AI held, how the effect got out, and what harm resulted, and cross-referenced to the
OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and
MITRE ATLAS.

Browse it at **https://basitalisandhu.github.io/ai-agent-incidents/** (searchable
table, one page per event, [RSS feed](https://basitalisandhu.github.io/ai-agent-incidents/feed.xml),
[JSON](https://basitalisandhu.github.io/ai-agent-incidents/incidents.json),
[CSV](https://basitalisandhu.github.io/ai-agent-incidents/incidents.csv),
[stats](https://basitalisandhu.github.io/ai-agent-incidents/stats.json)).

Part of **Masoon**, open-source trust infrastructure for AI agents: who they are, what
they may touch, and proof of what they did.

## Why this exists

Security discussion treats "AI" as one problem. The public record says it is at least
three: AI as a *weapon* that lowers the cost of established attacks, AI as a *target*
whose data, prompts, credentials and serving stack can be extracted or disrupted, and
AI as an *attack surface*, because organisations now wire instruction-following models
to privileged tools, private data and untrusted content at once. Reasoning about which
controls matter, and arguing with vendors and auditors about them, needs evidence that
is structured, sourced and reproducible, not a list of headlines. Until now no such
dataset existed in a form that can be queried, diffed, validated in CI and cited.

The seed data and the coding scheme come from the paper *AI as Weapon, Target, and
Surface: A Threat Taxonomy and a Deterministic Control Plane for Securing LLM Agents*
(Muhammad Basit Ali, 2026), whose code, experiments and original CSV live at
[llm-agent-control-plane](https://github.com/basitalisandhu/llm-agent-control-plane).
This repository turns that dataset into a maintained, contributor-friendly record.

## Who it is for

- **Security engineers and architects** deciding which controls an agent deployment
  needs: filter by `authority` and `channel_out` to see what actually caused harm.
- **Researchers** who need a coded, citable sample of real events, with a codebook and
  a reproducible build.
- **Vendors and policy teams** mapping incidents to OWASP and ATLAS for risk
  registers, threat models and compliance narratives.
- **Journalists and educators** who want the facts of each event with its primary
  source, in one place.

## Use cases

- **Which AI agent security incidents involved prompt injection, and what did the attacker get?** Filter `vector = indirect-injection` on the site and read `authority` and `outcome`.
- **Is there a dataset of LLM security incidents mapped to the OWASP LLM Top 10, the OWASP Agentic Top 10 and MITRE ATLAS?** Every record carries the three mappings; `stats.json` counts them.
- **What has gone wrong with MCP servers, coding agents and AI IDEs in practice?** Search the site for a product name, or filter by `affected.products` in the JSON.
- **How do I cite real AI agent incidents in a threat model, a risk register or a paper?** Each record has a primary source, a stable id and a permanent page; `CITATION.cff` gives the dataset citation.
- **How do I get notified of new AI agent incidents?** Subscribe to the [RSS feed](https://basitalisandhu.github.io/ai-agent-incidents/feed.xml).

## Frequently asked questions

**Is there a public dataset of AI agent security incidents?**
Yes, this one: 80 publicly documented events from February 2023 to September 2026 (25 incidents, 45 vulnerability disclosures, 10 threat reports), one schema-validated JSON record each, coded under a written codebook and mapped to the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and MITRE ATLAS. Download it as [JSON](https://basitalisandhu.github.io/ai-agent-incidents/incidents.json) or [CSV](https://basitalisandhu.github.io/ai-agent-incidents/incidents.csv), browse it on the [site](https://basitalisandhu.github.io/ai-agent-incidents/), subscribe to the [RSS feed](https://basitalisandhu.github.io/ai-agent-incidents/feed.xml), or load the [Hugging Face mirror](https://huggingface.co/datasets/basitalisandhu/ai-agent-incidents). The data is CC BY 4.0. Current counts are in [docs/stats.md](docs/stats.md).

**How are incidents coded?**
Every event is coded from a primary source that was opened and read, on eight fields defined in [docs/codebook.md](docs/codebook.md): `type` (incident, vulnerability disclosure or threat report), `lens` (the role AI plays: weapon, target or surface), `vector` (how the attack or failure got in), `channel_in`, `authority` (what the AI component could do), `channel_out` (how the effect left the system), `adversarial` (whether an attack technique is involved) and `outcome` (the most severe harm realised or demonstrated). Each record also carries mappings to the OWASP LLM Top 10, the OWASP Agentic Top 10 and MITRE ATLAS, given only where the source supports them. The paper behind the seed data reports two further blind codings and their agreement (kappa 0.82 for lens and 0.87 for vector with the second coder).

**Can I use it commercially?**
Yes. The data is licensed [CC BY 4.0](LICENSE-DATA): use, copy, modify and redistribute it, including in commercial products, as long as you credit the dataset (name it and link to this repository) and say if you changed it. The build and validation code is [MIT](LICENSE). There is no warranty, and the dataset is a convenience sample of what was made public, so no share computed from it estimates a population share.

**How do I add an incident?**
One event is one JSON file and one pull request: copy an existing record, give it the next free id, fill every field from a public primary source, run `python3 scripts/validate.py`, and open the pull request. If you would rather not write JSON, use the [issue form](.github/ISSUE_TEMPLATE/new_incident.yml). Only events with a public primary source are accepted; this is not a place to disclose new vulnerabilities. The checklist is in [CONTRIBUTING.md](CONTRIBUTING.md).

**How do I cite the dataset?**
Use [CITATION.cff](CITATION.cff) (GitHub shows it under "Cite this repository"): Muhammad Basit Ali, *AI Agent Incidents: an open dataset of publicly documented AI-agent and LLM-application security incidents*, version 1.0.0, 2026, https://github.com/basitalisandhu/ai-agent-incidents. The coding scheme comes from the paper *AI as Weapon, Target, and Surface: A Threat Taxonomy and a Deterministic Control Plane for Securing LLM Agents* (Ali, 2026), whose code and original data are at [llm-agent-control-plane](https://github.com/basitalisandhu/llm-agent-control-plane); cite both when you use the coding.

**What can the dataset not tell you?**
It is a convenience sample of events that were made public, so it over-represents what vendors and researchers chose to disclose and says nothing about how common any class of event is in the population. Mappings are the maintainer's reading of each source against the published frameworks; an empty mapping list means no confident mapping, not that none applies. Dates are the month of the public report, not of the event. Each record links its primary source so every claim can be checked.

## Dataset card

| | |
|---|---|
| Records | 80 events (25 incidents, 45 vulnerability disclosures, 10 threat reports) |
| Period | February 2023 to September 2026 (month of public report) |
| Unit | One primary source's account of one incident, advisory or report |
| Coded fields | `type`, `lens`, `vector`, `channel_in`, `authority`, `channel_out`, `adversarial`, `outcome` |
| Identifying fields | `id`, `date`, `name`, `cve`, `sources`, `summary` |
| Added fields | `mappings` (OWASP LLM Top 10 2025, OWASP Agentic Top 10 2026, MITRE ATLAS), `affected` (vendors, products, frameworks), `tags`, `status` |
| Formats | JSON (one file per event, [schema](schema/incident.schema.json)), flat CSV ([data/incidents.csv](data/incidents.csv), the paper's original column set), site exports (JSON array, CSV, RSS, stats) |
| Coding | By the author of the paper under [docs/codebook.md](docs/codebook.md); the paper reports two further blind codings and their agreement |
| Sampling | Convenience sample of what was public; it over-represents what vendors and researchers chose to disclose, and no share computed from it estimates a population share |
| Licence | Data CC BY 4.0, code MIT |

### The coding scheme in brief

Full definitions, with the number of seed events per value, are in
[docs/codebook.md](docs/codebook.md). Current counts are in [docs/stats.md](docs/stats.md).

- **lens**: the role AI plays. `surface` (47): the AI is a conduit to another party's
  assets. `weapon` (14): the AI is the attacker's instrument. `target` (19): the AI
  system itself is attacked, exposed or disrupted.
- **vector**: how the attacker content or the failure got in, for example
  `indirect-injection` (27), `autonomous-ops` (10), `exploitation` (7), `supply-chain`
  (5), `excessive-agency` (4), `nhi-secrets` (4).
- **channel_in**: where the content came from (`chat message`, `web page`, `document`,
  `email`, `repo issue/pr`, `support ticket`, `calendar invite`, `tool description`,
  `rules file`, `package`, `none`).
- **authority**: the capability the component or credential gave the event (`none`,
  `read-only`, `send-message`, `shell/exec`, `database`, `write-repo`, `cloud-creds`,
  `file-delete`, `payments`).
- **channel_out**: how the effect left the system (`tool-call send`, `image/link fetch`,
  `code exec`, `file publish`, `data destruction`, `financial transfer`, `api-abuse`,
  `service-disruption`, `disclosure-only`).
- **adversarial**: whether an attack technique is part of the event (65 yes, 15 no).
- **outcome**: the most severe harm class realised or demonstrated (`data-exfiltration`,
  `information-disclosure`, `code-execution`, `data-destruction`, `financial-loss`,
  `fraud`, `service-disruption`, `none-demo`).

### Mappings

Each record carries `mappings.owasp_llm`, `mappings.owasp_agentic` and
`mappings.mitre_atlas`. They are the maintainer's reading of the primary source
against the published frameworks, given only where the source supports them; an empty
list means "no confident mapping", not "none applies". Events with no adversary carry
no ATLAS techniques, because ATLAS describes adversary behaviour. Coverage of the seed
data: 62 events mapped to the OWASP LLM Top 10, 51 to the OWASP Agentic Top 10, 66 to
ATLAS. Mapping suggestions are welcome as pull requests with a one-line justification.

### Verification

Every seed event was coded from a primary source that was opened and read. On
2026-10-03 the maintainer re-checked the 80 URLs from a network that allows only some
hosts: 12 were reachable and matched their records; 68 could not be reached because the
proxy refused the connection, which says nothing about the pages themselves. Details
per URL are in [docs/verification-log.md](docs/verification-log.md). No record was
downgraded from `confirmed`.

## Record format

```json
{
  "id": "032",
  "date": "2025-06",
  "name": "EchoLeak zero-click exfiltration from Microsoft 365 Copilot",
  "type": "vulnerability-disclosure",
  "lens": "surface",
  "vector": "indirect-injection",
  "channel_in": "email",
  "authority": "read-only",
  "channel_out": "image/link fetch",
  "adversarial": true,
  "outcome": "data-exfiltration",
  "cve": ["CVE-2025-32711"],
  "sources": [{"url": "https://thehackernews.com/2025/06/zero-click-ai-vulnerability-exposes.html"}],
  "summary": "Zero-click via crafted email, CVSS 9.3; fixed server-side; no known exploitation.",
  "mappings": {"owasp_agentic": ["ASI01"], "owasp_llm": ["LLM01", "LLM02"], "mitre_atlas": ["AML.T0051.001", "AML.T0077"]},
  "affected": {"vendors": ["Microsoft"], "products": ["Microsoft 365 Copilot"], "frameworks": []},
  "tags": ["zero-click", "email", "markdown-image-exfiltration"],
  "status": "confirmed"
}
```

## Using the data

```python
import json, urllib.request
url = "https://basitalisandhu.github.io/ai-agent-incidents/incidents.json"
events = json.load(urllib.request.urlopen(url))
exfil_by_tool = [e for e in events if e["channel_out"] == "tool-call send"]
print(len(exfil_by_tool), "events exfiltrated through a tool call the attacker influenced")
```

```sh
# Events where an agent with shell access was steered by content it read
jq '[.[] | select(.authority == "shell/exec" and .vector == "indirect-injection") | .name]' site/incidents.json
```

Subscribe to [feed.xml](https://basitalisandhu.github.io/ai-agent-incidents/feed.xml)
to be notified of new records.

## Repository layout

```
incidents/            one JSON record per event: <id>-<slug>.json (source of truth)
schema/               incident.schema.json (JSON Schema 2020-12)
data/incidents.csv    flat export in the paper's fourteen columns (generated)
docs/                 codebook.md, stats.md (generated), verification-log.md
scripts/              import_csv.py, export_csv.py, validate.py, build_site.py, push_to_hf.py, indexnow_key.txt
assets/               og-image.png, copied into the site for link previews
site/                 generated static site (index, per-event pages, feed, JSON, CSV, stats, sitemap, robots, llms.txt, IndexNow key)
tests/                pytest suite
hf/                   README.md, the dataset card for the Hugging Face mirror
.github/              CI (validate, test, build), Pages deployment with an IndexNow ping, issue form
```

## Working with the repository

```sh
pip install -r requirements-dev.txt
python3 scripts/validate.py          # schema and integrity checks
python3 -m pytest -q                 # the same, plus round-trip and date checks
python3 scripts/build_site.py        # regenerates site/ and docs/stats.md
python3 scripts/export_csv.py        # regenerates data/incidents.csv from the JSON records
python3 scripts/import_csv.py --csv some.csv   # imports rows from a CSV in the paper's format
HF_TOKEN=... python3 scripts/push_to_hf.py       # uploads the CSV, JSON, schema and card to the Hugging Face mirror
```

The scripts use only the standard library, except `validate.py` and the tests, which
need `jsonschema`. The site has no external dependencies and works when opened from a
local file.

## Adding an incident

One event is one JSON file and one pull request. Copy an existing record, give it the
next free id, fill every field from the primary source, run `validate.py`, and open the
pull request. [CONTRIBUTING.md](CONTRIBUTING.md) has the checklist and the source
requirements; the [issue form](.github/ISSUE_TEMPLATE/new_incident.yml) is the way to
propose an event without writing JSON. Only events with a public primary source are
accepted; this is not a place to disclose new vulnerabilities (see
[SECURITY.md](SECURITY.md)).

## How to cite

Cite the dataset and the paper it was created for. [CITATION.cff](CITATION.cff) is
machine-readable (GitHub shows a "Cite this repository" button).

```
Muhammad Basit Ali. AI Agent Incidents: an open dataset of publicly documented
AI-agent and LLM-application security incidents. Version 1.0.0, 2026.
https://github.com/basitalisandhu/ai-agent-incidents

Muhammad Basit Ali. AI as Weapon, Target, and Surface: A Threat Taxonomy and a
Deterministic Control Plane for Securing LLM Agents. 2026.
https://github.com/basitalisandhu/llm-agent-control-plane
```

## To-do

- Re-verify the 68 source URLs that the build network could not reach, and add
  archived copies where a page has moved.
- Review the OWASP Agentic Top 10 mappings against the published document at
  genai.owasp.org once it can be fetched; the ids were cross-checked against the
  OWASP GenAI Security Project's GitHub repositories.
- Add a `controls` field: the control (provenance, approval, least authority, egress
  mediation) that would have stopped each event, tied to the Masoon components below.
- Keep adding events after September 2026.

## Licence

Data (`incidents/`, `data/`, and the site's JSON, CSV and feed exports) is licensed
under [CC BY 4.0](LICENSE-DATA). Code (`scripts/`, `tests/`, workflows, site
templates) is licensed under [MIT](LICENSE). Attribution: Muhammad Basit Ali,
https://github.com/basitalisandhu/ai-agent-incidents.

## Related repositories (Masoon)

- [masoon](https://github.com/basitalisandhu/masoon): the platform front door, with the
  [docs site](https://basitalisandhu.github.io/masoon/).
- [Masoon Broker](https://basitalisandhu.github.io/masoon/masoon-broker.html): scoped, short-lived
  credentials for AI agents with human approvals, kill switch and tamper-evident audit.
- [llm-agent-control-plane](https://github.com/basitalisandhu/llm-agent-control-plane):
  the paper, its deterministic policy enforcement point, the evaluation and the original
  dataset.
- [agentic-semgrep-rules](https://github.com/basitalisandhu/agentic-semgrep-rules):
  Semgrep rule pack for insecure agent code: unbounded tool permissions, eval of model
  output, SSRF through tool URLs, prompt interpolation, MCP servers without auth.
- [agent-threat-model](https://github.com/basitalisandhu/agent-threat-model): CLI that
  turns a YAML description of an agent system into a STRIDE + OWASP Agentic threat
  model, control checklist and Mermaid diagram.
- [agent-security-skills](https://github.com/basitalisandhu/agent-security-skills):
  Claude Code plugin and agentskills-compatible skill pack for agent security reviews:
  threat modelling, config audits, policy generation, incident lookup.
