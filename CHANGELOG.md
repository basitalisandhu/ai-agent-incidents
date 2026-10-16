# Changelog

All notable changes to the dataset, its schema and its tooling are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [semantic versioning](https://semver.org/): a new major version changes
the record schema incompatibly, a minor version adds records or fields, a patch fixes
data or tooling.

## [Unreleased]

### Added

- `scripts/agentic_crosstab.py` and the generated `docs/owasp-agentic-crosstab.md`:
  the OWASP Top 10 for Agentic Applications mappings cross-tabulated against lens,
  year, type, authority, channel_out, vector and outcome, with co-occurring pairs and
  the events mapped to no category. A test fails when the committed file is stale.

## [1.0.0] - 2026-10-13

First tagged release of the dataset (88 records) and its tooling.

### Added

- 88 incident records (001 to 088), from February 2023 to October 2026, each one
  schema-validated JSON file coded under `docs/codebook.md` and mapped to the OWASP
  Top 10 for LLM Applications, the OWASP Top 10 for Agentic Applications and MITRE
  ATLAS. Eight of them (081 to 088, August to October 2026) were added after the
  first publication (#10).
- `schema/incident.schema.json`, `scripts/validate.py` and a pytest suite run in CI.
- A generated static site with a searchable table, one page per event, an RSS feed,
  JSON, CSV and stats exports, a sitemap and `llms.txt`, deployed to GitHub Pages.
- `data/incidents.csv` and `scripts/export_csv.py`, with inclusive `--since` and
  `--until` month filters (#12, thanks @nawaaaaaAaar).
- A by-vendor statistics table on the stats page (#13, thanks @ruthraguru248), with a note that the counts
  are a sample of public disclosures, not a measure of risk.
- `scripts/check_sources.py`, which requests every source URL and reports dead ones
  with the newest archived copy, and a weekly workflow that runs it.
- Dependabot for Python and GitHub Actions dependencies.
- `docs/verification-log.md` records a 2026-10-13 check: all 96 source URLs resolved.

### Changed

- Every GitHub Action is pinned by commit SHA, and CI checkouts no longer keep the token.
- The README's setup steps start from a clone and a virtual environment.
- The project stands alone, without the earlier umbrella branding (#1, #8).

### Fixed

- GitHub links on the site join the repository URL with a slash (#9).

[Unreleased]: https://github.com/basitalisandhu/ai-agent-incidents/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/basitalisandhu/ai-agent-incidents/releases/tag/v1.0.0
