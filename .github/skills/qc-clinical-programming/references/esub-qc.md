# eSubmission Package QC Reference

Read this before QCing submission deliverables: define.xml, reviewer's
guides (SDRG/ADRG), Pinnacle 21 (P21) validation output, and the dataset
transport files themselves. The organizing question for every check:
*will the FDA/EMA/PMDA reviewer see something inconsistent with something
else in the package?* Internal consistency across artifacts is the whole
game — each artifact is a map of the same territory, and reviewers diff
the maps.

## define.xml

Check define against the *data*, not against the spec — the data is what
ships. Three-way consistency (spec ↔ define ↔ data) where feasible.

- Every dataset in the package has a define entry and vice versa; dataset
  labels, structure ("one record per...") statements, and key variables
  match reality (re-verify the stated keys actually hold in the data).
- Variable-level: name, label, type, length, origin, and codelist for every
  variable, against actual dataset attributes. Origin is a classic drift
  point — "CRF" origins must have an aCRF page reference that actually
  contains the field; "Derived" origins need a derivation/comment.
- Value-level metadata: present where one variable's meaning shifts by
  context (e.g., VSORRES units by VSTESTCD; PARAMCD-dependent metadata in
  BDS). Check that VLM where-clauses actually partition the data.
- Codelists: every value in the data appears in the referenced codelist
  (or the codelist is marked extensible and extensions are legitimate);
  no codelist values contradicting the CT version declared.
- Computational methods / comments: readable, match what the code actually
  does. A derivation description that is subtly wrong is worse than a terse
  one — reviewers implement from these.
- External references: aCRF and CT document links resolve; define stylesheet
  renders (open it, do not just validate the XML).

## Reviewer's guides (SDRG / ADRG)

The guides exist to pre-answer reviewer questions — QC them as *the
explanation of record for every known anomaly*:

- Every P21 issue accepted-with-explanation appears in the guide's
  conformance section, and the explanation actually explains (a reviewer
  who reads it should not need to ask a follow-up).
- SDRG: data standards versions, source data description, domains list
  matches package, non-standard decisions (screen-failure handling, split
  datasets, custom domains) documented.
- ADRG: analysis population definitions match ADSL flags and SAP wording
  verbatim-consistent; data dependencies (which ADaM reads which SDTM);
  imputation conventions section consistent with what the datasets show
  (spot-check: does an *DTF flag distribution support the stated rule?).
- Cross-check every claim in the guide against an artifact. Guides drift
  from the data across versions — treat each guide statement as an
  assertion to test, not prose to proofread.

## Pinnacle 21 triage

P21 output is a finding *generator*, not a verdict. Triage each issue:

| Bucket | Meaning | Action |
|---|---|---|
| Fix | Genuine conformance error | Route to production, re-run after fix |
| Explain | Data is correct; rule fires anyway (known false positive or legitimate study-specific reason) | Written explanation into SDRG/ADRG conformance section |
| Escalate | Ambiguous — could be data issue or standards interpretation | Blindspot territory: raise, do not self-resolve |

- Zero unexplained Errors is the bar; Warnings need triage but not
  necessarily action; Notices reviewed once.
- Record the P21 engine version and validation config (FDA vs PMDA rule
  sets differ) in the findings log — a "clean" run against the wrong rule
  configuration is an unknown-unknown factory.
- Re-run after *any* dataset change; P21 results do not carry over.

## Transport file (XPT) technical checks

- SAS V5 transport format; one dataset per file; filename = dataset name,
  lowercase, ≤8 chars.
- File size limits per current FDA technical conformance guide — confirm
  the current threshold and split-dataset conventions from the guide in
  force, and check split datasets (e.g., LB) follow the naming/SUPP
  conventions and are documented in the SDRG.
- Variable lengths minimized (max actual length, not default 200) — this
  is both a P21 rule and a real reviewer irritant.
- No formats attached that the reviewer cannot resolve; character dates in
  ISO 8601, numeric dates avoided in SDTM.
- eCTD placement sanity check: datasets, define, guides in the expected
  module 5 folder structure per the sponsor's publishing plan (the
  publishing team owns this; QC just confirms the programming-side inputs
  landed where the plan says).

## Package-level consistency sweep (final gate)

Run once, after all component QC passes:

- N of subjects: DM = ADSL = disposition table = SDRG/ADRG statements.
- Standards versions: identical in define, guides, and TS domain.
- Dataset list: define = folder contents = guide inventory tables.
- Dates: data cutoff / database lock date consistent everywhere it appears.

Any mismatch here is class S or D — a package that disagrees with itself
invites information requests regardless of which artifact is "right".
