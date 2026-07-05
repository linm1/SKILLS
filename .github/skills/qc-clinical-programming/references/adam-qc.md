# ADaM Dataset QC Reference

Read this before QCing any ADaM dataset. Always QC ADSL first — every other
ADaM dataset inherits from it, and an ADSL error propagates everywhere.

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
