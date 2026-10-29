# ADaM Dataset QC Reference

Read this before QCing any ADaM dataset. Always QC ADSL first — every other
ADaM dataset inherits from it, and an ADSL error propagates everywhere. For
the enumerable ADaMIG conformance rules and industry check logic, see
`adam-business-rules.md`.

## ADS specification review (before programming)

Under a typical CRO/sponsor process the analysis dataset specification is
drafted, reviewed, and stabilized before ADaM programming starts. A
programming review and a statistical review run in parallel on the internal
draft; both clear before programming commences. Distinct phase from dataset
QC below — QCs the spec document, not derived data. Adapt to the governing
process; the checks matter more than the document names.

### Structural and programming review

- Cover Page: document versions current; Define-XML version and its CT
  current.
- Dataset Metadata, Standards, Documents tabs complete; footer on every tab.
  - Dataset Metadata (v2.1): if a subclass is specified, the dataset
    structure in the variable tab conforms strictly to that subclass's
    principles; otherwise leave subclass blank.
  - Standards (v2.1): metadata at dataset, variable and codelist level that
    does not conform to the default standard is marked non-standard.
  - Documents: reflects the latest document versions as of define.xml
    creation.
- Dataset-, variable- and value-level metadata flagged as having no data
  (v2.1) carries a stated reason.
- Every SAP/TLF-shell table, figure, listing producible from ADS variables;
  no analysis derivation that affects results left to output programs.
  Presentation-only steps (formatting, ordering, layout) are fine. Transposes
  and merges an output would need belong in the dataset; otherwise a
  single-programmed output carries that logic unverified.
- Origin: v2.1 uses 'Origin - Type'/'Origin - Source'; v2.0 uses single
  'Origin'. Variables copied from SDTM have Origin 'Predecessor'; label,
  meaning and values unchanged (ADaMIG); length and display format also kept
  identical to SDTM unless the governing process allows otherwise.
- Sort variables match the unique record identifiers stated for the dataset.
- Codelists present where a determinate value set exists, CT-matched
  including version (v2.1).
- Variable ordering logical (not alphabetic), consistent across datasets,
  e.g. population flags grouped together.
- Concatenated subject-header variables (for listing headers) unique across
  the whole spec, not just within one dataset.
- Every TLF-shell group/subgroup needing order has a corresponding *N
  variable matching shell presentation order.
- 'Validation checks' column populated with protocol-specific checks; at
  minimum every check agreed with the sponsor.
- Variable type sensible: float/integer/datetime/date/time/text.
- Derivation has no SAS code beyond trivial (CHG=AVAL-BASE); pseudo-code
  readable without SAS.
- Pseudo-code, if used, is brief, traceable to the SAP/shell section it
  implements, and not copy-pasteable as program code — copying spec code
  into a program undermines independent double programming.
- Every flag the SAP/shells need (subject-level, record-level, analysis
  flags) is present in the spec.
- Spec checked against ADaMIG and any sponsor-specific standards (see
  `adam-business-rules.md`).
- Automated spec-check report (where the organization provides one) run, and
  its findings resolved, before the spec goes to reviewers.
- Data-cut rules, where defined, cover every applicable dataset: generic
  subject-selection and data-selection criteria, plus per-dataset detail.
  State whether the cut is applied at SDTM or ADaM level.

### Statistical review

- Primary/secondary endpoint derivations traceable to and consistent with
  the SAP.
- Where the SAP is silent, the derivation must still be sensible; raise with
  programming lead/statistician and decide whether the SAP should be
  amended — do not settle it in the spec alone.
- Analysis-set/population definitions match the SAP.
- Covariates present, correctly typed (categorical/continuous), labelled.
- Subgroups defined in ADSL and every applicable dataset.
- Visit-windowing algorithms explicit and accurate.
- Duration/TTE variables defined, with censoring rules described.
- Event flags (treatment-emergent, AESI, etc.) defined and accurate.
- SMQ/CMQ match SAP/documentation, same MedDRA version as coding.
- Marked-abnormality criteria for labs and vital signs match the SAP.
- Imputation described accurately, applied to correct parameters, DTYPE
  specified.
- CM/MH identification criteria clear, no gaps or conflicts.
- Baseline derivation and associated flags consistent with the SAP.
- Derivations need no SAS knowledge to follow — seeds the ADaM Reviewer's
  Guide.

### Applies to both passes

- PK component: PK concentration dataset metadata merged into the main
  variable metadata rather than left on a separate tab; where the analysis
  needs dose-relative timing, the last-dose datetime and relative-time
  variables (with their unit) are present and correctly derived in the
  occurrence datasets that reference them. Confirm exact names against the
  sponsor convention or ADaM PK guidance.
- Later versions: re-review may be limited to the spreadsheet-compare diff
  rather than the whole document.
- Spec change control: every change after programming starts is recorded
  (what changed and why) and classed major or minor. A major change goes
  back through review, with an impact check on the SAP and timelines. Both
  production and QC are notified.

## ADSL

- One record per subject, full stop. Test it.
- Population flags (SAFFL, ITTFL, FASFL, PPROTFL...): re-derive each from
  its SAP definition, not from one another. The denominator of every TLF
  hangs on these; a flag discrepancy is high-severity.
- Treatment variables: TRT01P vs TRT01A divergence only where the SAP
  allows (mis-randomized/mis-dosed subjects). Check the specific subjects
  where planned ≠ actual — they are the boundary cases.
- TRTSDT/TRTEDT vs EX: confirm the derivation convention for subjects with
  a single dose record, missing end dates, or dose interruptions.
- Date imputation happens here (not SDTM). The imputation rule per variable
  (first day of month? mid-month? conservative direction per context —
  early for AE onset, late for last contact?) is the single richest source
  of spec ambiguity in ADaM. Blindspot-pass every imputed date variable and
  log the rule you applied, with the *DTF/*TMF imputation flags checked for
  consistency with the imputation actually performed.

## BDS datasets (ADLB, ADVS, ADEG, ADEFF...)

- PARAM/PARAMCD: 1:1 mapping, PARAMCD ≤8 chars, no PARAM text variation
  for the same code.
- AVAL vs AVALC: exactly one populated unless spec says otherwise; if both,
  they must be consistent.
- Baseline: ABLFL logic re-derived independently; then BASE, CHG, PCHG
  recomputed from AVAL and ABLFL. Check PCHG where BASE=0 — division
  convention (missing? zero?) is an unknown-known.
- ANLzzFL analysis flags: re-derive from the SAP's stated record-selection
  rule (e.g., "last on-treatment value per window"). Tie-breaking within a
  window (latest date? highest --SEQ? worst value?) is a blindspot item.
- Visit windowing: re-implement windows from the SAP table, then compare
  AVISIT assignment. Subjects with assessments exactly on window boundaries
  are the quiz cases.
- LOCF/BOCF/WOCF or multiple imputation: verify against SAP method,
  and verify DTYPE is populated on derived records.
- Treatment-emergent logic (ADAE): TRTEMFL window (first dose to last dose
  \+ N days — confirm N and whether the endpoint is inclusive), handling of
  AEs with partial onset dates (usually "assume treatment-emergent unless
  provably not" — confirm).

## Traceability

- SRCDOM/SRCVAR/SRCSEQ (or --SEQ retention) let a reviewer walk any AVAL
  back to SDTM. Spot-check a sample of derived records end-to-end: pick 3–5
  subjects including at least one edge case and hand-trace them.
- Every record in the ADaM dataset should be explainable: either directly
  from SDTM or via a documented derivation (DTYPE populated).
- SUPP qualifiers merged back to the parent domain before use.
- Record counts reconciled against the source domain.

## Metadata conformance

- Dataset and variable metadata match the define/spec: labels, types,
  lengths, order.
- Character length inflation (SAS default 200-length from raw merges) is a
  recurring finding — check actual max lengths against defined lengths.

## Comparison technique

- `id usubjid paramcd avisitn adt;` (adapt keys per dataset) so PROC COMPARE
  aligns records structurally.
- Compare derived numerics with an explicit, documented criterion; compare
  flags and codes with criterion 0 (exact).
- Row-count differences: reconcile with a frequency of the filter variables
  (population flag × analysis flag × window) on both sides before diving
  into values — the mismatch is usually one interpretation bit, not many
  bugs.
- Compare hygiene:
  - one compare per dataset in the deliverable;
  - every non-exact compare annotated; only data issues are acceptable
    reasons;
  - variable order compared too;
  - helper sort variables excluded by name and listed;
  - QC dataset timestamp newer than its inputs and than the production run.

## Data cut-off and unblinding

- Cut-off: production and QC each write the cut independently. Keep both the
  cut and full versions. Where the cut dataset is a record subset of the full
  one under the same derivation, check N(cut) ≤ N(full) per dataset. Where
  selection or derivation logic differs, reconcile counts against that logic
  instead. List removed records per dataset for review before TLF work.
- Unblinding: when real treatment codes arrive, re-verify the
  treatment-assignment logic against the actual randomization file. Compare
  blinded vs unblinded datasets; differences should appear only in expected
  variables. Whoever changes anything re-QCs it. Re-run conformance on the
  unblinded deliverable. Respect the firewall rules in `SKILL.md`.

## Code-review QC (when not double programming)

- Code review is always paired with input/output testing.
- Complex datasets get extended review: stepwise execution, interim
  datasets, and a random input-to-output trace (see Traceability for the
  hand-trace sample).
- Search for and verify every hardcode: documented, approved, echoed to the
  log.
- Input/output sample: a subject with multiple complete records; all
  visits/timepoints; subjects in every disposition state (screen failure,
  ongoing, completed, discontinued).
