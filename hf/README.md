---
pretty_name: AI Agent Incidents
license: cc-by-4.0
language:
  - en
tags:
  - ai-security
  - llm-security
  - agent-security
  - prompt-injection
  - security-incidents
  - incident-database
  - owasp
  - mitre-atlas
  - threat-intelligence
  - ai-agents
  - mcp
size_categories:
  - n<1K
task_categories:
  - text-classification
  - tabular-classification
annotations_creators:
  - expert-generated
source_datasets:
  - original
configs:
  - config_name: default
    data_files:
      - split: train
        path: incidents.csv
  - config_name: json
    data_files:
      - split: train
        path: incidents.json
dataset_info:
  - config_name: default
    features:
      - name: id
        dtype: string
      - name: date
        dtype: string
      - name: name
        dtype: string
      - name: type
        dtype: string
      - name: lens
        dtype: string
      - name: vector
        dtype: string
      - name: channel_in
        dtype: string
      - name: authority
        dtype: string
      - name: channel_out
        dtype: string
      - name: adversarial
        dtype: bool
      - name: outcome
        dtype: string
      - name: cve
        dtype: string
      - name: url
        dtype: string
      - name: notes
        dtype: string
    splits:
      - name: train
        num_examples: 80
  - config_name: json
    features:
      - name: id
        dtype: string
      - name: date
        dtype: string
      - name: name
        dtype: string
      - name: type
        dtype: string
      - name: lens
        dtype: string
      - name: vector
        dtype: string
      - name: channel_in
        dtype: string
      - name: authority
        dtype: string
      - name: channel_out
        dtype: string
      - name: adversarial
        dtype: bool
      - name: outcome
        dtype: string
      - name: cve
        sequence: string
      - name: sources
        list:
          - name: url
            dtype: string
          - name: title
            dtype: string
          - name: publisher
            dtype: string
          - name: accessed
            dtype: string
      - name: summary
        dtype: string
      - name: mappings
        struct:
          - name: owasp_llm
            sequence: string
          - name: owasp_agentic
            sequence: string
          - name: mitre_atlas
            sequence: string
      - name: affected
        struct:
          - name: vendors
            sequence: string
          - name: products
            sequence: string
          - name: frameworks
            sequence: string
      - name: tags
        sequence: string
      - name: status
        dtype: string
    splits:
      - name: train
        num_examples: 80
---

# AI Agent Incidents

Open, structured dataset of publicly documented security incidents, vulnerability disclosures and threat reports involving LLM applications and AI agents, from February 2023 onwards. One record per event, coded under a written codebook by the role AI plays (weapon, target or surface), vector, input channel, authority held, output channel, whether an attack technique is involved, and outcome, and cross-referenced to the OWASP Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and MITRE ATLAS.

Canonical source and contribution rules: https://github.com/basitalisandhu/ai-agent-incidents. Browsable site with one page per event, RSS feed, stats and a machine-readable summary (llms.txt): https://basitalisandhu.github.io/ai-agent-incidents/. This mirror is regenerated from the repository by `scripts/push_to_hf.py`; open issues and pull requests there, not here.

## Files

- `incidents.csv` (config `default`): the flat export in the paper's fourteen columns, one row per event. `cve` is a semicolon-separated list, `url` is the primary source, `notes` is the summary.
- `incidents.json` (config `json`): every record as one JSON array with the nested fields (`sources`, `mappings`, `affected`, `tags`).
- `incident.schema.json`: JSON Schema 2020-12 for one record.

## Fields

`id`, `date` (YYYY-MM or YYYY-MM-DD, the month of the public report), `name`, `type` (incident, vulnerability-disclosure, threat-report), `lens` (surface, weapon, target), `vector`, `channel_in`, `authority`, `channel_out`, `adversarial`, `outcome`, `cve`, `sources` (url, title, publisher, accessed), `summary`, `mappings` (owasp_llm, owasp_agentic, mitre_atlas), `affected` (vendors, products, frameworks), `tags`, `status`. Definitions and the list of allowed values: https://github.com/basitalisandhu/ai-agent-incidents/blob/main/docs/codebook.md

## Collection and limitations

Every event was coded from a primary source that was opened and read. The dataset is a convenience sample of what was made public; it over-represents what vendors and researchers chose to disclose, and no share computed from it estimates a population share. Mappings are the maintainer's reading of the source against the published frameworks; an empty list means no confident mapping, not that none applies. The paper behind the seed data reports two further blind codings and their agreement.

## Licence and citation

Data: CC BY 4.0. Attribution: Muhammad Basit Ali, https://github.com/basitalisandhu/ai-agent-incidents. Commercial use is allowed with attribution.

Muhammad Basit Ali. AI Agent Incidents: an open dataset of publicly documented AI-agent and LLM-application security incidents. Version 1.0.0, 2026. https://github.com/basitalisandhu/ai-agent-incidents

Muhammad Basit Ali. AI as Weapon, Target, and Surface: A Threat Taxonomy and a Deterministic Control Plane for Securing LLM Agents. 2026. Manuscript.
