# Codebook

This is the coding scheme of the dataset, reproduced from the codebook of the paper
*AI as Weapon, Target, and Surface: A Threat Taxonomy and a Deterministic Control
Plane for Securing LLM Agents* (Muhammad Basit Ali, 2026). The definitions below
are the ones under which the 80 seed events were coded, and every new record must
follow them. The number in parentheses after a value is the number of seed events
that carry it. An asterisk after an event number (for example D-28\*) marks an event
on which the paper's second coding differed; the agreement table in the paper lists
them.

## Collection

The dataset records 80 events (25 incidents, 45 vulnerability disclosures and 10
threat reports), dated February 2023 to September 2026, that involve an LLM-based
system or an attacker's operational use of generative AI. Candidates were found in
four kinds of public source: vendor security advisories and incident reports, CVE
records, researcher write-ups and press coverage; each event carries one primary
source, which was opened and read to code it. There was no search protocol beyond
naming these source types, and no census was kept of the candidates that were
considered and excluded. The dataset is therefore a convenience sample of what was
public, not a census: it over-represents what vendors and researchers chose to
disclose, and no count or share computed from it estimates a share of any
population.

## Fields

Each event is one row of fourteen fields: six identify the event and eight are
coded and used in the analysis. The rules below are applied to the primary source
of the event. In the JSON records of this repository the fourteen fields keep their
names and values; `url` becomes the first entry of `sources`, `notes` becomes
`summary`, `adversarial` becomes a boolean, and `cve` becomes a list. The
additional JSON fields (`sources` metadata, `mappings`, `affected`, `tags`,
`status`) are described in the README and the schema; they are not part of the
paper's coding.

### Identifying fields

- **`id`**: Sequence number in the order of `date` and, within a month, of
  `name`; the paper cites event *n* as D-*n*. One event is one primary source's
  account of an incident, an advisory or a report: a source that bundles several
  flaws counts once.
- **`date`**: Month (YYYY-MM) in which the event was publicly reported or
  confirmed in the sources collected; not the month the attack began or was fixed.
- **`name`**: Short descriptive title, in the vendor's or researcher's wording
  where one exists.
- **`cve`**: CVE identifiers assigned to the event, separated by semicolons; `-`
  if none; `multiple` where the source reports several without listing them.
- **`url`**: The primary source that was opened and read to code the event
  (advisory, CVE record, write-up or article); one per event.
- **`notes`**: One line of free text with the facts needed to check the coding;
  not coded and not used in any analysis.

### Coded fields

#### `type`

What kind of record the event is; decided by the genre of the primary source.

- **`incident`** (25): A specific event that harmed or exposed a real user,
  victim or deployment, or put a malicious artefact into circulation, as reported
  by the victim, an investigator or the press. (e.g. D-1, D-2)
- **`vulnerability-disclosure`** (45): A flaw or attack path reported by a
  researcher or vendor (advisory, CVE record or write-up, usually with a proof of
  concept) with no real victim reported. (e.g. D-3, D-5)
- **`threat-report`** (10): A report by an AI vendor or threat-intelligence team
  on misuse or attacks it observed across accounts, targets or telemetry, rather
  than one victim's event. (e.g. D-16, D-27)

#### `lens`

The role AI plays in the event. Apply the tie-break at the end of this list in the
order given.

- **`surface`** (47): The AI component is a conduit to another party's assets: it
  is connected to that party's data, tools, code or accounts, or speaks for it, and
  the event reaches or harms those assets through the AI, by attacker content, by a
  user or by the AI's own action. (e.g. D-3, D-4)
- **`weapon`** (14): The AI is the attacker's instrument against a victim that is
  not its operator: an adversary uses generative AI or an AI agent to perform or
  enable the attack, or, with no adversary, an autonomous agent acts against third
  parties' assets. (e.g. D-14, D-16)
- **`target`** (19): Otherwise: the AI system itself (model, weights, training or
  retrieval data, prompts, serving stack, credentials to it, or its ecosystem) is
  what is attacked, exposed or disrupted. (e.g. D-1, D-2)
- *Tie-break*: AI as conduit to another party's assets is `surface`; AI as the
  attacker's instrument is `weapon`; otherwise `target`. Cases decided under it:
  chatbot output that harms its deployer without any tool authority is `surface`
  (D-10, D-12, D-13); a flaw in an AI product's own code or configuration,
  exploited without the model's obedience to injected content, is `target` (D-20,
  D-21, D-41, D-61\*, D-64, D-68). The events on which a second coding differed
  are listed in the agreement table of the paper.

#### `vector`

How the attacker content or the failure got in; one value, the main mechanism in
the primary source.

- **`indirect-injection`** (27): Attacker instructions arrive inside content the
  AI retrieves or is given to process (web page, document, e-mail, issue, ticket,
  invitation, third-party message), not from its principal. (e.g. D-5, D-8)
- **`direct-injection`** (4): The attacker types the instructions into the
  interface the AI itself exposes (chat or API prompt) and the model's obedience is
  the flaw. (e.g. D-3, D-10)
- **`jailbreak`** (1): A user talks the model out of its behavioural policy to make
  it say or do what the operator forbade, with no access gained. (e.g. D-12)
- **`extraction`** (3): The model is made to reveal what it holds: hidden prompt,
  memorised training data or its capabilities (distillation). (e.g. D-1, D-7)
- **`poisoning`** (2): Attacker-authored content is planted in a persistent input
  that conditions later behaviour (rules file, tool description, training or
  retrieval data). (e.g. D-28\*, D-29\*)
- **`retrieval-memory`** (2): The injection or the leak travels through the
  system's retrieval index or persistent memory. (e.g. D-22, D-23)
- **`generated-code`** (3): The harm originates in code or a package name that the
  model generated or hallucinated. (e.g. D-17\*, D-31)
- **`supply-chain`** (5): Attacker code or content is delivered through a
  dependency, model, extension, server or release channel of the AI system. (e.g.
  D-15\*, D-33)
- **`exploitation`** (7): A conventional software or configuration flaw around the
  AI component (traversal, SSRF, trust bypass, exposed endpoint, workflow
  permissions) is exploited. (e.g. D-20, D-21)
- **`exposure/misconfig`** (4): Data or access is exposed by a bug, configuration,
  default credential, open store or user act, with no attack technique involved.
  (e.g. D-2, D-4)
- **`nhi-secrets`** (4): A non-human-identity secret (API key, token, cloud
  credential) is stolen, exposed or misused. (e.g. D-9, D-18)
- **`excessive-agency`** (4): An AI with legitimate authority takes a damaging or
  unauthorised action or commitment on its own initiative, with no adversary. (e.g.
  D-13, D-36)
- **`social-engineering`** (3): AI-generated or AI-assisted content (deepfake,
  phishing, persona) is used to deceive a person. (e.g. D-14, D-16)
- **`autonomous-ops`** (10): An AI agent carries out reconnaissance, exploitation
  or other operations with little human involvement, whether directed by an
  attacker or acting by itself. (e.g. D-38, D-52)
- **`availability`** (1): The AI service is made unavailable. (e.g. D-6)

#### `channel_in`

The channel through which attacker content reached the AI component; for an event
without an adversary, the channel of the input that triggered the behaviour.

- **`chat message`** (22): A message in a conversation (chat, API prompt or call):
  the AI's own prompt, or a third-party message it reads.
- **`web page`** (11): Content fetched from a web page, search result or link the
  victim opens.
- **`document`** (8): A file the AI is asked to read or summarise (PDF, README,
  shared document).
- **`email`** (2): An e-mail message.
- **`repo issue/pr`** (8): An issue, pull request, comment or commit in a
  source-control repository.
- **`support ticket`** (2): A ticket or customer record in a help-desk, CRM or
  similar store.
- **`calendar invite`** (1): A calendar invitation or event.
- **`tool description`** (1): Metadata that a tool or MCP server supplies to the
  agent.
- **`rules file`** (2): A configuration or rules file that steers a coding
  assistant (rules, hooks, settings in a repository).
- **`package`** (8): A code or model artefact distributed through a package index,
  model hub or marketplace.
- **`none`** (15): No outside content was needed: the event arises from the system
  itself, from infrastructure or credentials, or from an autonomous agent's own
  actions.

#### `authority`

The capability that the compromised or misbehaving component, or the stolen or
exposed credential, gave the event: the one the attack exercised, or would have
exercised had it succeeded; one value, the one that produced the impact channel.

- **`none`** (9): No capability to act: the component only produced text for a
  person.
- **`read-only`** (14): Read data and render output (including images and links),
  with no other externally visible action.
- **`send-message`** (6): Send messages, post content or call outward-facing APIs
  on a user's behalf (e-mail, chat, comments, plugin calls).
- **`shell/exec`** (33): Run commands or code on a host (shell, interpreter, IDE
  terminal, CI step).
- **`database`** (7): Query or modify a database or record store (tables, tickets,
  key-value store).
- **`write-repo`** (4): Write to a repository or model hub (commits, pull requests,
  uploads).
- **`cloud-creds`** (5): Hold cloud or platform credentials or tokens (API keys,
  service tokens, metadata access).
- **`file-delete`** (1): Delete files on a user's machine through a file-system
  tool.
- **`payments`** (1): Move money.

#### `channel_out`

How the effect left the system or took hold.

- **`tool-call send`** (11): The AI makes a tool call (message, request, post,
  write) whose recipient, content or destination the attacker influenced, moving
  data or content out.
- **`image/link fetch`** (11): Data leaves when the client renders or fetches an
  image or link in the model's output; no tool call is made.
- **`code exec`** (31): Attacker-influenced code or a command runs on a host or in
  a sandbox.
- **`file publish`** (4): A file, package or commit is written to a shared or
  public location.
- **`data destruction`** (4): Data, files or infrastructure are deleted or
  overwritten.
- **`financial transfer`** (1): Money is moved.
- **`api-abuse`** (3): The AI service's API, credits or capabilities are consumed
  or abused.
- **`service-disruption`** (1): The AI service is made unavailable.
- **`disclosure-only`** (14): The effect is confined to what the model says or
  what leaks; no side-effecting action follows.

#### `adversarial`

Whether an attack technique is part of the event.

- **`yes`** (65): A deliberate actor (attacker, in-the-wild group, or a researcher
  demonstrating an attack technique) crafts input, code or content to cause the
  harm.
- **`no`** (15): The harm arises without an attack technique: a misconfiguration,
  default or bug, a user's own act, or an AI acting on its own initiative; also
  when a researcher found it.

#### `outcome`

The most severe harm class that the primary source reports as realised or
demonstrated.

- **`data-exfiltration`** (31): Data is, or in the demonstration could be, moved
  to an outsider's control.
- **`information-disclosure`** (11): Information is exposed or revealed beyond its
  intended audience without being taken (hidden prompt, memorised data, open
  store).
- **`code-execution`** (19): Attacker-chosen code runs and no further harm is
  reported.
- **`data-destruction`** (3): Data or infrastructure is lost.
- **`financial-loss`** (3): Money or liability is lost.
- **`fraud`** (3): Deceptive or illicit use for gain, without a single traceable
  loss.
- **`service-disruption`** (1): The service is unavailable.
- **`none-demo`** (9): No harm of the classes above is reported: a demonstration, a
  failed or unconfirmed attempt, or a policy violation without loss.

## Fields added by this repository

These are not part of the paper's coding and carry no counts above.

- **`sources[].title`, `publisher`, `accessed`**: Optional metadata on each
  source; `accessed` is the date on which the URL was last confirmed reachable.
- **`mappings.owasp_llm`**: OWASP Top 10 for LLM Applications, 2025 edition
  (`LLM01` Prompt Injection, `LLM02` Sensitive Information Disclosure, `LLM03`
  Supply Chain, `LLM04` Data and Model Poisoning, `LLM05` Improper Output Handling,
  `LLM06` Excessive Agency, `LLM07` System Prompt Leakage, `LLM08` Vector and
  Embedding Weaknesses, `LLM09` Misinformation, `LLM10` Unbounded Consumption).
- **`mappings.owasp_agentic`**: OWASP Top 10 for Agentic Applications, 2026
  edition (`ASI01` Agent Goal Hijack, `ASI02` Tool Misuse and Exploitation, `ASI03`
  Identity and Privilege Abuse, `ASI04` Agentic Supply Chain Vulnerabilities,
  `ASI05` Unexpected Code Execution, `ASI06` Memory and Context Poisoning, `ASI07`
  Insecure Inter-Agent Communication, `ASI08` Cascading Agent Failures, `ASI09`
  Human-Agent Trust Exploitation, `ASI10` Rogue Agents).
- **`mappings.mitre_atlas`**: MITRE ATLAS technique ids (`AML.T....`), as of
  ATLAS v5.6.0.
- Mappings are given only where the primary source supports them; an empty list
  means "no confident mapping", not "none applies". Events with no adversary carry
  no ATLAS techniques, because ATLAS describes adversary behaviour.
- **`affected.vendors`, `products`, `frameworks`**: As named in the primary
  source. Products are named as products; model identifiers are not recorded.
- **`tags`**: Free-form lowercase keywords for search.
- **`status`**: `confirmed` (the primary source was opened and read and supports
  the coding), `reported` (known second-hand, or the primary source is no longer
  reachable and no replacement was found) or `disputed` (a named party contests
  the facts or the coding).
