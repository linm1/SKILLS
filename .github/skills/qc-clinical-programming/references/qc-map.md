# QC Map and Decision Tickets

The findings log is the **record** — every observation, in one table, for
traceability. The QC map is the **worklist** — the open questions that block
progress, ordered, one surfaced to the human at a time.

They are not the same artifact and neither replaces the other. A findings log
cannot tell a resuming session which question to ask next; a map that held
every finding would duplicate the log and run to forty tickets.

## Governance first — where a map may live

A QC map holds **metadata, questions, and pointers only**:

- No patient-level data, no listings, no extracted values.
- No unblinded information: no treatment assignments, randomization codes,
  interim results, or DMC content.
- No verbatim sponsor text: cite the document and section, do not paste it.
- No confidential sponsor IP beyond what the governance gate already permits
  for this environment.

Default location is the **study working area**, beside the QC program:

```
<study working area>/
  qc_adsl.sas
  qc_adsl_findings.md        <- the record (existing convention)
  qc_adsl_map.md             <- the worklist
  qc_adsl_tickets/
    01-aestdt-partial-date-rule.md
    02-saffl-mis-dosed-subject.md
```

Before writing the first file, confirm the location is **not version-controlled
and not cloud-synced**, and is approved for the content the map will discuss.
A map file inherits every restriction the governance gate placed on that
material.

Many study areas are plain directories on a validated server, where this needs
no action. Where the location *is* under version control or file sync, either
exclude these files from it — adding `qc_*_map.md` and `qc_*_tickets/` to a
`.gitignore` where the tool is git — or choose a different location. If you
cannot confirm which, say so and ask before writing.

**Never write a QC map into the directory this skill itself lives in**, nor
into any shared or synced folder that is not the sponsor-approved study area.

If the user's SOP mandates a controlled QC tracking system, that system wins.
Use the formats below inside it; do not create a parallel filesystem map.

## When a map is warranted

One map per QC target — matching the existing one-log-per-QC-target
convention. Not one map per study, not one per submission package.

A map earns its place when the QC target has open questions that outlive a
single session: a spec with material ambiguities, a target awaiting documents,
or work resumed across days. A small target against a clean, complete spec
does not need one. Say so rather than charting an empty map.

## Map body

```markdown
## Destination

Sign-off on <deliverable> version <version> under <QC mode>.

Done when the frontier is empty AND every Phase 4 residual-risk question is
resolved or explicitly accepted.

## Governance & intake

- QC mode:
- Source documents and versions:
- Unavailable documents:
- Restrictions in force:

## Decisions so far

<!-- index only: name + link + one-line gist. Never restate the answer. -->

- [01 AESTDT partial-date rule](qc_adsl_tickets/01-aestdt-partial-date-rule.md)
  — first-of-month, per sponsor convention; confirmed by DM 2026-03-04.

## Not yet specified

<!-- the fog: questions you can see coming but cannot yet phrase sharply.
     These are the unknown-knowns and unknown-unknowns quadrants of the
     unknowns table in SKILL.md, written down as they surface. -->

## Out of scope

<!-- ruled beyond the destination; closed, never graduates -->
```

**Decisions so far is an index, not a store.** One line per resolved ticket:
its name, a link, and a gist short enough to judge relevance. The answer itself
lives in the ticket. Restating it in the map re-creates, one level up, exactly
the duplication this design avoids.

**An empty frontier is not sign-off authorization.** A clean state proves the
questions you asked are answered — not that you asked the right ones. Phase 4
exists precisely because agreement is not correctness.

## Ticket format

`qc_<target>_tickets/NN-<slug>.md`, numbered from `01`:

```markdown
Type: grilling
Status: open
Blocked by: 01
Severity: Major

## Question

Which imputation rule applies to a partial AE start date of `2026-03` when the
subject's first dose is 2026-03-15? The SAP is silent; sponsor convention and
the conservative-early principle disagree here.

## Answer

<!-- written on resolution -->
```

- **Type**: `grilling` (HITL, the default — a decision the human must make),
  `research` (AFK — a fact recoverable from the IG, CT, business-rule
  references, or sponsor documents), or `task` (manual work that unblocks a
  decision: obtaining a document, requesting a transfer, provisioning access).
  There is no `prototype` type; it does not fit QC work.
- **Status**: `open` | `claimed` | `resolved`.
- **Blocked by**: ticket numbers, comma-separated. Omit when unblocked.
- **Severity**: from the severity table in SKILL.md. Drives which ticket is
  surfaced first.

**No `Class:` field.** The triage classes describe findings, and an unresolved
question frequently cannot be classified yet — that is what makes it a
question. Class is assigned when the resolution writes the findings-log row.

## The ticket-vs-log test

Before creating a ticket, ask: **could this be a findings-log row instead?**
If yes, it is not a ticket.

A ticket is a question whose resolution is a **human decision** that gates
further QC work. A log row is an observation you can already classify.

| Ticket-worthy | Stays log-only |
|---|---|
| Spec ambiguity where two implementations are defensible (resolves to class `S`) | Production error with reproducible evidence (`P`) |
| An assumption you applied that needs confirming (resolves to class `A`) | Your own QC error, found and fixed (`Q`) |
| A governing document or version you do not have | Data issue routed to data management (`D`) |
| Phase 4 boundary question you cannot answer from the spec | Metadata inconsistency to correct (`M`) |
| A convention the spec is silent on and evidence does not settle | Conformance finding triaged against a rule config (`C`) |

If a candidate does not survive this test, log it and move on.

## Operations

**Frontier** — scan the tickets directory for tickets that are open,
unblocked (every ticket in `Blocked by:` is `resolved`), and unclaimed. First
by number wins; among several, prefer the highest severity.

**Claim** — set `Status: claimed` and save before any work.

**Reclaim** — a ticket with `Status: claimed` but no content under `## Answer`
may be reclaimed by a later session. Flat files record no assignee and no
staleness, so without this rule a session that dies mid-ticket would strand it
off the frontier permanently. Note the reclaim in the ticket.

**Resolve** — three writes, all of them:

1. Append the decision and its rationale under `## Answer`; set
   `Status: resolved`.
2. Append name + link + gist to the map's Decisions so far.
3. Add the corresponding row to `qc_<target>_findings.md` with its class,
   severity, evidence, and status — so the log remains the complete record.

**Graduate** — when an answer makes a fogged question sharp enough to state
precisely, create it as a ticket and clear that patch from Not yet specified,
so it lives in exactly one place. When an answer reveals a ticket sits past the
destination, close it into Out of scope rather than resolving it.

## Surfacing a ticket to the user

Present the question as an **explicit choice between named interpretations**,
and for each one state the **QC consequence** — what changes in the data,
denominator, population, or conformance if that reading is taken. That
consequence is what lets a human choose; the interpretations alone do not.

Always include an option meaning *neither — the answer is something else*, and
never present a single interpretation as though it were the only one. A
question with one option is a decision you already made.

Ask in plain markdown — this is the specification, and it works in every
environment:

```markdown
**Ticket 01 — AESTDT partial-date rule** (Severity: Major)

The SAP is silent on partial AE start dates. Which rule applies?

- **A. First of month.** Conservative-early; more AEs classify as
  treatment-emergent. Raises TEAE counts in Table 14.3.1.
- **B. Mid-month.** Sponsor convention on prior studies; some onsets fall
  after first dose and drop out of the TEAE denominator.
- **C. Leave missing, exclude from TEAE.** Understates TEAE counts; needs an
  ADRG explanation.
- **D. Something else — please specify.**

Reply with the letter and your rationale.
```

Where the environment offers a structured-choice affordance — a form, a
picker, a question tool — use it to carry the same content instead. The
requirement is the named options and their QC consequences, not any particular
presentation.

Record the chosen option **and** the user's rationale into `## Answer`. The
rationale is the part a reviewer needs; the letter alone does not survive
handover.

One **material** ticket per prompt — a question that could change data,
denominators, inference, submission conformance, or blinding status. Do not
batch material decisions; each deserves its own consideration.

Non-material assumption confirmations may be cleared several in one session.
A QC session legitimately clears a handful of minor confirmations in one pass,
and forcing them one-per-session would stall the work for no gain.
