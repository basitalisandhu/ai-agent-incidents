# Changelog

All notable changes to the dataset, its schema and its tooling are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [semantic versioning](https://semver.org/): a new major version changes
the record schema incompatibly, a minor version adds records or fields, a patch fixes
data or tooling.

## [Unreleased]

## [1.2.0] - 2026-10-28

No records changed in this release; it adds tooling.

### Added

- `scripts/digest.py` writes a monthly digest, `digest/YYYY-MM.md`, of the records added to the
  dataset in a month (by first commit): counts by type, lens, vector and outcome, vendors named
  more than once and a linked list of the records. The first digest, `digest/2026-10.md`, covers
  October 2026, and the site's front page links every digest (#21).
- `site/incidents.jsonl`, a deterministic JSONL export for ingestion (#29, thanks @nawaaaaaAaar).
- `scripts/records.py`, one safe reader for every script: a damaged record now stops
  `export_csv.py`, `build_site.py`, `agentic_crosstab.py` and `check_sources.py` with one line
  naming the file and the first problem (exit 2), instead of a traceback.
- A Troubleshooting section in the README.
- Tests: seeded, time-bounded fuzz tests that damage records one field at a time and run every
  script; 1x/10x scaling tests; an end-to-end test that runs the README "Working with the
  repository" block in a fresh copy and venv, in a new CI job.

### Fixed

- `validate.py` crashed on a record file that is not UTF-8, is nested too deeply to parse, is
  not a JSON object, or has a non-string `id`; each is now reported as an error for that file.
- `import_csv.py` crashed on a short row, a bad `adversarial` value, a missing or non-UTF-8 CSV,
  and an enrichment file that is not an object; it now exits 2 with the file and line, and
  writes nothing until every row is valid (it used to write the rows before the bad one).
- `check_sources.py` crashed on a source without a `url`.

## [1.1.0] - 2026-10-18

### Added

- `scripts/agentic_crosstab.py` and the generated `docs/owasp-agentic-crosstab.md`:
  the OWASP Top 10 for Agentic Applications mappings cross-tabulated against lens,
  year, type, authority, channel_out, vector and outcome, with co-occurring pairs and
  the events mapped to no category. A test fails when the committed file is stale.
- `ROADMAP.md`, a Contributors section and links to the Discussions boards (#23, #26).

### Changed

- Dependency updates: jsonschema, pytest and the GitHub Actions group (#15 to #17).
- Harden the workflows and repository policy for the OpenSSF Scorecard (#27).

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

[Unreleased]: https://github.com/basitalisandhu/ai-agent-incidents/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/basitalisandhu/ai-agent-incidents/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/basitalisandhu/ai-agent-incidents/releases/tag/v1.0.0
