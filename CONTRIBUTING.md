# Contributing

Thank you for helping keep the record straight. The most useful contribution is a new,
well-sourced event; the second most useful is a correction to an existing one.

## Adding an incident: one JSON file, one pull request

1. **Check it is not already here.** Search the [site](https://basitalisandhu.github.io/ai-agent-incidents/)
   and `incidents/` by product, vendor, CVE and researcher name. One event is one
   primary source's account of an incident, an advisory or a report; a source that
   bundles several flaws counts once.
2. **Read [docs/codebook.md](docs/codebook.md).** Every coded value must follow it,
   including the lens tie-break.
3. **Copy a similar record** from `incidents/` to `incidents/<id>-<slug>.json`:
   - `id`: the next free three-digit number (never reuse or renumber; new events take
     the next number even if their date is earlier than existing ones).
   - `slug`: lowercase words of the name joined by hyphens, at most about 60 characters.
4. **Fill every field from the primary source.** Put that source first in `sources`.
   Write `summary` as one or two factual sentences that let a reviewer check the
   coding (what happened, what was reached, what the vendor did), not an opinion.
5. **Map only what you are sure of.** `mappings` may be empty lists. If you add an
   OWASP or ATLAS id, be ready to say in the pull request which sentence of the source
   supports it.
6. **Validate locally.**
   ```sh
   pip install -r requirements-dev.txt
   python3 scripts/validate.py
   python3 -m pytest -q
   python3 scripts/export_csv.py && python3 scripts/build_site.py
   ```
   Commit the regenerated `data/incidents.csv`, `docs/stats.md` and `site/` with your
   record; CI fails if they are stale.
7. **Open the pull request** with the checklist below. One event per pull request.

If you would rather not write JSON, open an issue with the
[new incident form](.github/ISSUE_TEMPLATE/new_incident.yml) and a maintainer will
create the record.

## Pull request checklist

- [ ] The primary source is public, is the first entry in `sources`, and I read it in full.
- [ ] The event is not already in the dataset.
- [ ] `date` is the month (or day) of public report or confirmation, not of the attack or the fix.
- [ ] `type`, `lens`, `vector`, `channel_in`, `authority`, `channel_out`, `adversarial` and `outcome` follow the codebook, and the lens tie-break was applied.
- [ ] `cve` lists only identifiers that the source or the CVE record assigns to this event.
- [ ] `summary` contains only facts from the sources, no speculation, no model identifiers.
- [ ] `mappings` contain only ids I can justify from the source; otherwise they are empty.
- [ ] `affected` names vendors, products and frameworks as the source does.
- [ ] `python3 scripts/validate.py` and `python3 -m pytest -q` pass.
- [ ] `data/incidents.csv`, `docs/stats.md` and `site/` were regenerated and committed.
- [ ] Nothing in the record discloses an unpublished vulnerability or private data.

## Source requirements

- **Public and stable.** A vendor advisory, CVE record, researcher write-up, court or
  regulator document, or an article from an established outlet. Social-media posts may
  be added as further sources but not as the primary one unless they are the vendor's
  or researcher's own official account of the event.
- **https URLs only.** The schema rejects anything else.
- **Primary first.** The first source is the one the coding is based on. Add further
  sources (vendor confirmation, CVE record, follow-up) after it, each with a `title`
  where possible.
- **Record when you checked.** Set `accessed` to the date you last confirmed the URL
  loads. If a page disappears and no replacement is found, set `status` to
  `reported` rather than removing the record; add an archived copy as a further source
  when one exists.
- **No unpublished vulnerabilities.** See [SECURITY.md](SECURITY.md).

## Corrections and disputes

Open a pull request that changes the field and explains, in the description, which part
of the source supports the new value. If a party named in a record disputes the facts
or the coding, set `status` to `disputed` and link the dispute as a further source; the
record stays, with both readings visible.

## Changing the schema or the codebook

The eight coded fields and their values are those of the paper; changing them would
break comparability with the published analysis, so they are not open to extension
without a strong case. New optional fields (for example controls or affected versions)
are welcome: propose them in an issue first, then update `schema/incident.schema.json`,
the codebook, the builder and the tests in one pull request.

## Code

Scripts are standard-library Python 3.9 or later (only `validate.py` and the tests need
`jsonschema`). Keep them that way. The site must keep working from a local file with no
network access and no external scripts, fonts or styles.

By contributing you agree that your data contributions are licensed under CC BY 4.0 and
your code contributions under MIT.
