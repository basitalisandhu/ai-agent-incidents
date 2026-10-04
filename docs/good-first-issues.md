# Good first issues

Issues the maintainer intends to open under the `good first issue` label, written out so
they can be filed in one sitting. Each one is self-contained, touches a small part of
the repository, and has acceptance criteria that CI can check. Read
[CONTRIBUTING.md](../CONTRIBUTING.md) first; every change that touches records or the
builder must leave `python3 -m pytest -q` green and the regenerated `site/`,
`docs/stats.md` and `data/incidents.csv` committed.

## 1. Add a "By vendor" table to the statistics

**Context.** `scripts/build_site.py` aggregates counts by lens, vector, channel,
authority, outcome, mapping id and tag into `docs/stats.md` and `site/stats.json`, but
not by `affected.vendors`, which every record carries. A reader who wants "how many
events name vendor X" has to run `jq`.

**Acceptance criteria.**

- `docs/stats.md` gains a `### By vendor` section with the same two-column layout as
  `### By tag`, sorted by count then name, one row per distinct vendor string.
- `site/stats.json` gains a `by_vendor` object with the same counts.
- A test in `tests/test_validate.py` checks that the sum of `by_vendor` equals the
  number of `(record, vendor)` pairs in `incidents/`.
- `site/` and `docs/stats.md` are regenerated and committed; CI stays green.

## 2. Add an issue form for corrections

**Context.** `.github/ISSUE_TEMPLATE/new_incident.yml` lets people propose a new
event without writing JSON, but CONTRIBUTING's "Corrections and disputes" section only
describes a pull request. People who spot a wrong field or a dead link need a
form too.

**Acceptance criteria.**

- New file `.github/ISSUE_TEMPLATE/correction.yml` with: record id (input, required),
  field name (dropdown of the record fields), current value, proposed value, the
  source URL and the sentence that supports the change (textarea, required), and a
  checkbox confirming the source is public.
- The form applies the label `correction`.
- The form parses as YAML and renders on GitHub's "New issue" page.
- README's "Adding an incident" section links the new form in one sentence.

## 3. Add a JSON Lines export

**Context.** The site publishes `incidents.json` (one array). Streaming tools and
data-frame loaders prefer one object per line.

**Acceptance criteria.**

- `scripts/build_site.py` writes `site/incidents.jsonl`: one record per line, same
  objects and order as `site/incidents.json`, `ensure_ascii=False`, trailing newline.
- A test checks that the line count equals the record count and that each line parses
  to the matching object in `incidents.json`.
- The file is listed in the README dataset card ("Formats"), the "Browse it at"
  paragraph and the site's index page next to the JSON and CSV links.
- `LICENSE-DATA` names the new file alongside the other exports.

## 4. Add `--since` and `--until` filters to the CSV export

**Context.** `scripts/export_csv.py` always exports every record. Analysts who want
"2025 onwards" filter afterwards in a spreadsheet.

**Acceptance criteria.**

- `--since YYYY-MM` and `--until YYYY-MM` (both optional, inclusive, compared on the
  first seven characters of `date`) restrict the rows written.
- The default output is byte-identical to today's `data/incidents.csv` so the CI drift
  check still passes.
- Tests cover: no filter, `--since` only, `--until` only, both, and an invalid value
  (exit code 2 with a message).
- The README "Working with the repository" block shows one filtered example.

## 5. Add archived copies for sources the build network could not reach

**Context.** `docs/verification-log.md` lists 68 primary sources that the maintainer's
build network could not reach on 2026-10-03. An archived copy as a second source
protects the record if the page moves.

**Acceptance criteria.** Pick ten consecutive ids from the "blocked by proxy" table.
For each:

- Open the primary URL and confirm the page still matches the record's `summary`;
  set `sources[0].accessed` to the date you checked and add `sources[0].title` if
  missing.
- Find or create a Wayback Machine snapshot and add it as a second source:
  `{"url": "https://web.archive.org/web/<timestamp>/<original url>", "title": "Archived copy", "accessed": "<date>"}`.
- If the page is gone and no archive exists, set `status` to `reported` instead and
  say so in the pull request.
- `python3 scripts/validate.py` and `python3 -m pytest -q` pass; `site/` and
  `docs/stats.md` are regenerated; the pull request lists the ten ids.

## 6. Add a "Cite this record" block to every event page

**Context.** The README explains how to cite the dataset as a whole. Each event page
(`site/incidents/<id>.html`) has a stable URL but no ready-made citation.

**Acceptance criteria.**

- `scripts/build_site.py` renders, at the bottom of each event page, a plain-text
  citation (`Muhammad Basit Ali. "<name>". AI Agent Incidents, record <id>, <date>.
  <page url>`) and a BibTeX `@misc` entry with the same fields, inside a `<pre>` so it
  can be copied.
- No external scripts, fonts or styles (the site must keep working from a local file).
- A test asserts that the citation block of one page contains the record's id, name
  and URL.
- `site/` is regenerated and committed.
