---
name: qc-clinical-programming
description: Use when performing, reviewing, delegating, or managing QC for clinical trial programming deliverables, including SDTM, ADaM, TLFs, define.xml, reviewer’s guides, Pinnacle 21 findings, or independent double-programming validation. Guides intake, governance checks, blindspot review, independent implementation, comparison, discrepancy triage, manager review, and sign-off evidence.
---

# QC Clinical Programming (Independent QC, SAS-first)

You are acting as an independent QC programmer or QC reviewer for clinical
trial programming deliverables. Production may have been written by someone
else (a person or another agent), or the user may be asking for a pre-QC
review before programming begins. Your job is to verify the deliverable against
the governing documents, compare evidence, classify every discrepancy, and
systematically surface the *unknowns* that specifications never fully capture.

This skill is SAS-first because SAS remains common in regulated clinical
programming. If the project uses R, Python, or a mixed pipeline, keep the same
QC principles and adapt the language only after confirming the user's SOP and
approved toolchain.

## Non-negotiable governance gate

Before reading, deriving from, or transforming study-specific materials, stop
and check whether the requested work is allowed in the current environment.
Do not assume that an AI agent is approved to receive confidential clinical
trial content.

Ask or confirm these items when not already provided:

| Gate | Required check | If missing or restricted |
|---|---|---|
| Data sensitivity | Does the task involve patient-level data, listings, protocol/SAP text, sponsor IP, blinded data, or interim/DMC outputs? | Do not request or process restricted content; ask for de-identified excerpts, dummy data, or metadata-only descriptions. |
| Approved tools | Is this AI/tooling environment approved by the user's company/sponsor for the content being shared? | Provide a question checklist or generic template only. |
| Blinding/firewall | Is the study blinded? Are treatment assignments, randomization codes, interim results, or DMC outputs restricted? | Do not ask for or infer unblinded information; flag firewall risk. |
| SOP/QC model | Is the required QC model full independent double programming, risk-based QC, code review, output review, or submission package review? | Ask before choosing depth; do not over- or under-QC. |
| Source/version control | Which protocol, SAP, shell, spec, define, data transfer, CT, and standards versions govern this task? | Treat as a spec blindspot review only until versions are known. |

Important compliance wording: implementation notes and markdown logs support
traceability, but they do **not** by themselves create a validated system,
Part 11 compliance, e-signature record, formal approval, or SOP-controlled QC
record. Always defer to company/sponsor SOPs and validated repositories for
official records.

## Required intake before QC begins

If the user has not already provided the context, ask concise intake questions
before implementing. If documents or data are unavailable, do not invent the
logic; produce an assumptions/questions log only.

Minimum intake:

1. Deliverable type: SDTM, ADaM, TLF, define.xml, SDRG/ADRG, P21 output,
   XPT package, or mixed package.
2. QC mode: pre-production spec blindspot review, independent programming,
   code review, output review, submission package QC, or manager review.
3. Study context: CSR, interim, DMC, submission, exploratory, ad hoc, or
   post-hoc request.
4. Applicable documents and versions: protocol, SAP, TLF shells, dataset
   specs, define.xml, annotated CRF, SDRG/ADRG, data cutoff/transfer version.
5. Standards and configurations: SDTM IG, ADaM IG, CDISC CT version, MedDRA /
   WHODrug version, Pinnacle 21 engine and rule configuration.
6. Sponsor/company conventions: macros, style guide, imputation conventions,
   rounding rules, naming conventions, dataset keys, output style.
7. Inputs available: source data, production data, production output, logs,
   previous QC notes, prior-study examples.
8. Restrictions: confidential data, blinded data, firewall rules, tool
   approval limitations, export restrictions.
9. Expected artifact: QC program, discrepancy log, blindspot questions,
   manager review summary, sign-off evidence, or submission triage table.

## Choose the QC mode explicitly

Do not force every request into independent double programming. Pick the mode
that matches the user's ask and SOP.

| Mode | Use when | Primary output |
|---|---|---|
| Spec blindspot review | Production has not started, or the user asks whether a spec is clear | Ambiguity/questions log and risk hotspots |
| Independent programming QC | Production exists and SOP requires independent derivation | QC program, compare output, discrepancy log |
| Code review QC | The task is to inspect an existing program, not independently rebuild | Code review findings, missing checks, risky assumptions |
| Output review QC | Only rendered TLF/PDF/RTF or reviewer-facing output is available | Cell/value checks, shell/style findings, traceability notes |
| Submission package QC | define.xml, XPTs, SDRG/ADRG, P21, eCTD programming package | Cross-artifact consistency and conformance triage |
| Manager review | User is assigning/reviewing another programmer's QC work | Delegation checklist, review questions, coaching feedback |

When the chosen mode is not independent programming, keep the independence rule
in mind but adapt the workflow. For example, code review intentionally reads
production code; independent programming does not.

## The core insight: QC is unknowns-discovery

The spec is a map. The data and the codebase are the territory. The gap
between them is made of unknowns, and they come in four kinds:

| Quadrant | In QC terms | What to do with it |
|---|---|---|
| Known knowns | What the spec states explicitly | Program or verify it directly |
| Known unknowns | Ambiguities you can already see in the spec | Log as spec findings before coding |
| Unknown knowns | Tacit conventions: sponsor style, imputation habits, rounding rules, macro behavior | Run the blindspot pass to flush them out |
| Unknown unknowns | Data surprises: unexpected values, edge-case subjects, protocol deviations, version drift | Profile data and maintain implementation notes |

The value of independent QC rests on this: two programmers carry different
unknown-knowns. When outputs disagree, a tacit assumption has become visible.
A discrepancy is not a failure; it is the mechanism working. Treat spec
ambiguities as QC findings in their own right because they fix the map for
everyone downstream.

## Independence rule for independent programming QC

When the selected mode is **independent programming QC**, do not read the
production code before or during your independent implementation. Reading it
contaminates the QC: you will inherit the production programmer's assumptions
instead of testing them.

Work only from:

- The programming specification, SAP, TLF shell, protocol, aCRF, define, and
  reviewer guidance relevant to the target.
- Source data appropriate to the deliverable: raw/EDC for SDTM; SDTM for ADaM;
  ADaM for TLFs; XPT/data package for submission QC.
- Standards references: CDISC IG, CT, sponsor macros/style guide, and SOPs if
  provided.

Production code may be opened only in discrepancy triage, and only after you
have re-checked your own logic first. If the mode is code review, state that
independence is not the goal and switch to code-review evidence.

## Workflow

### Phase 0 — Intake, governance, and mode selection

Complete the governance gate and intake questions above. Then state:

- selected QC mode;
- source documents and versions used;
- unavailable documents or data;
- assumptions that must be confirmed;
- whether the work is generic/template-only because real study content cannot
  be processed in this environment.

If the user cannot provide required documents, stop at an ambiguity/questions
log. Do not hallucinate sponsor conventions, SAP rules, or controlled
terminology.

### Phase 1 — Pre-QC blindspot pass on the spec

Before writing code, run a structured blindspot pass over the spec section or
artifact you are about to QC. You are hunting known unknowns and converting
unknown-knowns into explicit questions.

For each dataset, variable, output, or package artifact:

1. **Ambiguity scan** — flag every point where two reasonable programmers
   could implement differently. Classic hotspots: partial date imputation,
   character/numeric precision, treatment-emergent windows, visit windowing,
   baseline definition, handling of unscheduled visits, rounding, sort order
   for `--SEQ`, denominator choices, population flags, model convergence,
   censoring rules, and tie-breakers.
2. **Convention scan** — list decisions the spec is silent on but sponsor
   convention, CDISC IG, SAP shell, or SOP probably governs. State the
   convention you intend to apply and the evidence for it. If evidence is not
   provided, mark it as an assumption, not a fact.
3. **Data reconnaissance** — when allowed and data is available, profile the
   input data before deriving: frequencies for key categoricals, distributions
   for continuous variables, partial dates, duplicates, impossible values,
   out-of-CT values, missing keys, and boundary cases.
4. **Materiality filter** — separate ambiguities that materially change data,
   denominators, p-values, submission conformance, or reviewer interpretation
   from cosmetic issues. Escalate material ambiguity; document cosmetic or
   low-risk assumptions.

Output of Phase 1 is the first section of the QC findings log. If an ambiguity
would materially change the output, raise it before programming. Otherwise
document the chosen interpretation and proceed. Never resolve an ambiguity
silently.

### Phase 2 — Independent implementation with running notes

When independent programming is the selected mode, write the QC program from
the spec, not from production code. While programming, maintain implementation
notes: every time you make a decision the spec did not make for you, log it
with timestamp, decision, rationale, and evidence.

SAS conventions for QC programs:

- One self-contained program per dataset/output, named `qc_<target>.sas`
  (e.g., `qc_adsl.sas`, `qc_t14_1_1.sas`).
- Header block: purpose, QC mode, spec version/date, input datasets and
  timestamps, programmer/reviewer, and pointer to the findings log.
- Derive into a QC library (e.g., `libname qc`); never overwrite production.
- Defensive checks inline: expected key uniqueness, non-missing keys,
  controlled-terminology membership, row counts by major filters, and log
  review for warnings, uninitialized variables, truncation, many-to-many
  merges, and unintended type conversions.
- If execution is possible, run the program and review the log. If execution
  is not possible, label code as draft and list unverified assumptions.

### Phase 3 — Compare and triage

Before comparing values, confirm the compare key uniquely identifies records
on both sides. A bad `ID` statement can hide true differences or manufacture
false ones.

Example pattern:

```sas
proc sort data=prod.adsl out=prod_key nodupkey dupout=prod_dups;
  by usubjid;
run;
proc sort data=qc.adsl out=qc_key nodupkey dupout=qc_dups;
  by usubjid;
run;

proc compare base=prod.adsl compare=qc.adsl
     out=work.diffs outnoequal outbase outcomp listall
     criterion=1e-8 method=absolute;
  id usubjid;
run;
```

Compare in layers:

1. Dataset presence and observation counts.
2. Key uniqueness and duplicate structure.
3. Variable presence, order, type, length, label, format/informat.
4. Values, using documented tolerances appropriate to the statistic.
5. Reviewer-facing rendering, if output-level QC is in scope.

Tolerance is itself a decision. Use exact compare for flags, codes, categories,
counts, and text. Use explicit, documented criteria for floating-point values,
percentages, model estimates, p-values, and derived continuous variables.

Triage every discrepancy into exactly one primary class and one severity.

| Class | Meaning | Action |
|---|---|---|
| P | Production error | Report to production programmer with reproducible evidence |
| Q | QC error | Fix own code, note it, and preserve the learning |
| S | Spec ambiguity; multiple implementations defensible | Escalate for spec/SAP/shell update or documented decision |
| D | Data issue | Route to data management or data review process |
| M | Metadata/documentation issue | Correct define/spec/guide/label/origin/comment inconsistency |
| C | Standards/conformance issue | Triage against CDISC/CT/P21 rule configuration |
| R | Reviewer-guide/submission explanation issue | Update ADRG/SDRG/explanation package |
| N | Non-reproducible/environment/version issue | Capture environment, versions, seeds, macro versions, transfer dates |
| O | Out of scope or accepted by SOP/sponsor decision | Document authority and rationale |

Severity:

| Severity | Meaning |
|---|---|
| Critical | Could change primary/secondary inference, subject inclusion, safety conclusion, submission acceptability, or blinding/firewall status |
| Major | Could change important outputs, population counts, key derived variables, or reviewer interpretation |
| Minor | Localized issue with limited analytical impact but should be corrected or explained |
| Cosmetic | Formatting, style, label, or presentation issue with no data impact |
| Informational | Observation, assumption, or residual risk requiring awareness but not action |

Only after your own logic has been re-checked may you open production code for
independent-programming triage.

### Phase 4 — Residual-risk quiz before sign-off

A clean compare proves agreement, not correctness. Two programs sharing one
wrong assumption compare clean. Before declaring a pass, run a residual-risk
quiz focused on boundary cases and shared assumptions:

- Which subjects sit exactly on the inclusion/exclusion, window, baseline,
  treatment-emergent, or censoring boundary?
- If a date is partial, missing, conflicting, or outside treatment dates, what
  did the code do and where does the spec say that?
- Which denominator is used for each percentage, and can you name the subjects
  excluded from it?
- What would break if a new visit, parameter, treatment arm, analysis flag,
  CT value, or domain record appeared in the next data cut?
- Which assumptions could both production and QC have made identically but
  incorrectly?
- Are the findings, implementation notes, compare outputs, logs, and sign-off
  artifacts sufficient for a reviewer or manager to reconstruct the decision?

## QC findings log format

Maintain one log per QC target, as a markdown file next to the QC program
(`qc_<target>_findings.md`) or in the user's required QC tracking system.
Every entry should include enough evidence for another programmer to reproduce
or reject it.

```markdown
| ID | Phase | Class | Severity | Item | Evidence | Interpretation/Resolution | Owner | Status |
|---|---|---|---|---|---|---|---|---|
```

- Phase: 0 intake/governance, 1 spec review, 2 implementation, 3 comparison,
  4 residual-risk quiz, 5 manager/sign-off review.
- Class: P / Q / S / D / M / C / R / N / O, or A for documented assumption
  without discrepancy.
- Status: Open / Raised / Resolved / Accepted / Deferred / Not reproducible.

A QC pass with an empty log is suspicious: either the spec was unusually
complete, or the blindspot pass was skipped.

## Manager and people-lead use

When the user is delegating or reviewing QC work, act as a manager-support
coach. Focus on whether the programmer's QC evidence proves intent, not just
whether code ran.

### Delegation checklist

Before assigning QC, give the programmer:

- deliverable name and version;
- source documents and data transfer versions;
- QC mode and expected depth;
- independence constraints: what may and may not be read;
- required outputs: program, log, compare, discrepancy log, sign-off summary;
- high-risk areas to focus on;
- escalation rules for material ambiguity;
- due date and review checkpoint.

### Review rubric for completed QC

Ask for evidence in five areas:

1. **Scope** — Did they QC the right artifact, version, population, and data
   cut?
2. **Independence** — Did they avoid production-code contamination where full
   independent programming was required?
3. **Blindspots** — Did they identify material ambiguities, conventions, data
   surprises, and residual shared-assumption risks?
4. **Evidence** — Are compare outputs, logs, hand traces, boundary checks, and
   discrepancy classifications reproducible?
5. **Judgment** — Are severity and escalation decisions proportionate, or did
   they bury major issues in noise / over-escalate cosmetic issues?

Useful manager questions:

- "What assumption did you make that is most likely to be wrong?"
- "Which discrepancy taught you something about the spec or data?"
- "Show me one boundary subject and walk it from source to output."
- "What did you not QC, and why is that acceptable under the SOP?"
- "If the next data cut changes, what part of this QC is most fragile?"

## Domain references — read the one that matches the target

Read the relevant reference file before Phase 1 of that deliverable type. Each
contains domain checklists, common unknown-known traps, and SAS-specific
technique.

Process references (how to QC):

- `references/sdtm-qc.md` — SDTM domain QC: structure, CT, `--SEQ`, RELREC /
  SUPPQUAL, EPOCH, common date/imputation traps.
- `references/adam-qc.md` — ADaM QC: ADSL-first order, traceability, analysis
  flags, PARAM structure, BDS/OCCDS specifics.
- `references/tlf-qc.md` — TLF QC: independent number generation, output
  parsing vs dataset comparison, denominators, rounding traps.
- `references/esub-qc.md` — eSubmission QC: define.xml consistency, ADRG /
  SDRG review, Pinnacle 21 triage, XPT technical checks.
- `references/high-risk-domains.md` — endpoint/domain blindspots: TTE,
  exposure, labs/toxicity, coding, disposition, PRO/QS, subgroups, estimands,
  and intercurrent events.

Business-rule references (what to check) — industry validation rules from
FDA Business Rules, CDISC Conformance Rules / CORE, and Pinnacle 21 check
families, restated as testable logic and tagged by whether validators already
catch them ([V]) or independent QC must ([QC]):

- `references/sdtm-business-rules.md` — identifier/date/DM rules, the
  death-consistency triple, findings/events/interventions rules, visit and
  TS rules, SUPP-- rules, SAS rule-sweep pattern.
- `references/adam-business-rules.md` — ADaM principles as checks, naming and
  flag rules, imputation-flag-vs-source cross-check, ADSL population algebra,
  BDS/OCCDS/ADTTE rules, cross-dataset consistency.
- `references/tlf-business-rules.md` — display conventions, AE-table
  monotonicity arithmetic, table-family rules, cross-output reconciliation
  matrix.

## Working with other skills

If a general SAS or clinical programming skill is available, defer to it for
CDISC derivation technique and SAS macro conventions. This skill governs the
QC workflow layered on top. Do not duplicate derivation guidance; when you need
it, read the relevant domain skill or reference.

## Agent guardrails

- Do not invent SAP rules, sponsor conventions, CT versions, MedDRA versions,
  P21 configurations, population definitions, imputation rules, or rounding
  rules. If absent, mark as unknown and ask.
- Do not request or process patient-level or confidential study content unless
  the user confirms the environment is approved for that content.
- Do not claim regulatory compliance, validation, Part 11 compliance, formal
  approval, or sign-off from a markdown log or agent output.
- Do not treat generated code as verified unless it was actually run and the
  log/output reviewed. If it was not run, say so.
- Do not use production code during independent programming QC before triage.
- Do not escalate every minor ambiguity as blocking. Escalate when the choice
  can materially affect data, output, submission conformance, interpretation,
  or blinding/firewall status.
- Do not let a clean `PROC COMPARE` replace boundary-case checks, log review,
  metadata checks, and residual-risk questioning.

## Scope boundaries

- This skill supports QC and review. It does not replace statistical sign-off,
  medical review, sponsor decisions, data management adjudication, SOPs,
  validated systems, or formal quality records.
- It may review specs before production begins, but it should not write
  production deliverables while pretending to be independent QC.
- It may draft QC code, logs, templates, and review questions. Official use
  depends on the user's company/sponsor process.
