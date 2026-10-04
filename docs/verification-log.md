# Source verification log

Date of check: 2026-10-03. Checker: the maintainer, from a build environment whose
outbound web access runs through an organisation egress proxy that allows only
some hosts. Every one of the 80 primary-source URLs was requested once. The result
column means:

- **reachable**: the page loaded, and its title and content match the record
  (opened and read with a web fetch tool; title recorded in `sources[0].title`
  and `accessed` set to 2026-10-03).
- **blocked by proxy**: the egress proxy refused the connection to that host
  (HTTP CONNECT denied, no bytes received). This says nothing about whether the
  page exists; the record keeps `status: "confirmed"` as coded in the paper,
  where every source was opened and read.

No URL returned a "not found" or "gone" response, so no record was moved to
`status: "reported"`. Hosts marked blocked should be re-checked from an
unrestricted network; see the to-do in the README.

## Reachable and read (12 of 80)

| id | host | title as shown on the page | note |
|---|---|---|---|
| 003 | github.com | Security concerns (langchain-ai/langchain issue #1026) | Opened 13 Feb 2023; discusses LLM-generated code reaching exec in LLMMathChain. |
| 016 | microsoft.com | Staying ahead of threat actors in the age of AI | Published 14 Feb 2024. |
| 038 | anthropic.com | Detecting and countering misuse of AI: August 2025 | Published 27 Aug 2025. |
| 040 | github.com | Arbitrary code execution from Cursor Agent through a prompt injection via MCP Special Files | CVE-2025-54135, published 2 Aug 2025. |
| 044 | github.com | Malicious versions of Nx and some supporting plugins were published | Published 27 Aug 2025. The advisory page shows no CVE id; CVE-2025-10894 is kept as coded in the paper and was not re-verified here. |
| 052 | anthropic.com | Disrupting the first reported AI-orchestrated cyber espionage campaign | Published 13 Nov 2025. |
| 053 | cloud.google.com | GTIG AI Threat Tracker: Advances in Threat Actor Usage of AI Tools | Published 5 Nov 2025. |
| 060 | anthropic.com | Detecting and preventing distillation attacks | Published 23 Feb 2026. |
| 069 | securitylabs.datadoghq.com | LiteLLM and Telnyx compromised on PyPI: Tracing the TeamPCP supply chain campaign | Published 24 Mar 2026. |
| 072 | microsoft.com | When prompts become shells: RCE vulnerabilities in AI agent frameworks | Published 7 May 2026; CVE-2026-26030 and CVE-2026-25592. |
| 074 | anthropic.com | Investigating three real-world incidents in our cybersecurity evaluations | Published 30 Jul 2026. |
| 078 | anthropic.com | Detecting and countering misuse of AI: September 2026 | Covers December 2025 to August 2026. |

## Blocked by the proxy, not verified (68 of 80)

Hosts: adnanthekhan.com, aikido.dev, appomni.com, aws.amazon.com, blog.checkpoint.com,
blogs.microsoft.com, brave.com, cnn.com, codeintegrity.ai, depthfirst.com,
embracethered.com, generalanalysis.com, gizmodo.com, ian.sh,
infosecurity-magazine.com, invariantlabs.ai, jfrog.com, kb.cert.org, lasso.security,
legitsecurity.com, mattpalmer.io, noma.security, not-just-memorization.github.io,
openai.com, pillar.security, promptarmor.substack.com, research.checkpoint.com,
research.jfrog.com, safebreach.com, siliconangle.com, stepsecurity.io, sysdig.com,
techcrunch.com, tenable.com, theautopian.com, theguardian.com, thehackernews.com,
theregister.com, theverge.com, tracebit.com, unit42.paloaltonetworks.com,
varonis.com, wiz.io.

Records: 001, 002, 004 to 015, 017 to 037, 039, 041 to 043, 045 to 051, 054 to 059,
061 to 068, 070, 071, 073, 075 to 077, 079, 080.

The Internet Archive (web.archive.org) was also blocked, so no archived copies
could be consulted.

## Reference lists

- OWASP Top 10 for Agentic Applications: genai.owasp.org was blocked. The ten
  identifiers and titles were taken from the OWASP GenAI Security Project's own
  GitHub organisation (`GenAI-Security-Project/crosswalk`, files `CROSSREF.md`
  and `docs/llms.txt`), which lists ASI01 to ASI10 with the titles used in
  `docs/codebook.md`.
- MITRE ATLAS: atlas.mitre.org was blocked. Technique ids and names were taken
  from `mitre-atlas/atlas-data` on GitHub (`dist/ATLAS.yaml`, version 5.6.0),
  and each technique's description was read before it was used in a mapping.
- OWASP Top 10 for LLM Applications 2025: ids and titles from the maintainer's
  knowledge of the published list; the 2026 edition renumbers several entries,
  which is why the edition is stated in the schema and the codebook.
