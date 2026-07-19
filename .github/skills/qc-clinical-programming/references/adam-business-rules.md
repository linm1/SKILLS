# ADaM Validation Business Rules

ADaMIG conformance rules and industry conventions restated as testable check
logic, complementing `adam-qc.md` (process) with rules (content). Same tagging
as `sdtm-business-rules.md`:

- **[V]** — conformance engines (P21 AD-rules, CDISC CORE ADaM rules)
  typically fire; QC triages.
- **[QC]** — engines don't reliably catch it; independent QC must test it.

The ADaMIG version (1.1/1.2/1.3) is an input — variable requirements and CT
bindings shift between versions. Confirm from the define/ADRG before checking.

## Fundamental principles as checks

The four ADaM principles are testable, not aspirational:

1. **Traceability** — every AVAL is walkable to SDTM or to a documented
   derivation. Test: sample records incl. edge cases, hand-trace (see
   `adam-qc.md`).
2. **Analysis-ready** — the primary analysis runs "one PROC away" without
   further derivation. Test: write the SAP's primary analysis directly against
   the dataset; every extra data step you need is a finding.
3. **Metadata-complete** — define.xml describes every variable/derivation.
4. **Machine-readable structure** — conformant names, types, structure below.

## Naming and structure rules

- **[V]** Dataset named AD------ (≤8 chars), no underscores or special
  characters; ADSL present; ADSL is one record per subject (test it, don't
  trust it).
- **[QC]** Dataset carries a descriptive label; variable names ≤8 chars;
  character variable content ≤200 chars (XPT transport constraints the spec
  review, not just the P21/CORE ruleset, must catch).
- **[QC]** All variable attributes present (label, length, type, format
  where applicable); no user-defined formats — SAS-supplied formats only.
- **[V]** Standard variable names carry standard meanings: AVAL, AVALC, PARAM,
  PARAMCD, PARAMN, ABLFL, BASE, CHG, PCHG, DTYPE, ADT/ADTM/ADY, ASTDT/AENDT,
  APERIOD/APHASE, ASEQ, TRTxxP/TRTxxA. Never repurpose a standard name.
- **[V]** SDTM variables copied into ADaM keep name, label, and *values*
  unmodified — a "lightly cleaned" AEDECOD is a conformance error; derive a
  new variable instead.
- **[V]** Flag conventions: record-level *FL flags are "Y"/null (or "Y"/"N"
  where the IG defines both); subject-level population flags in ADSL are
  "Y"/"N", never null; length 1.
- **[QC]** PARAMCD/PARAM/PARAMN triple maps 1:1:1 across the *whole dataset*
  (not per-subject); PARAM text embeds the unit where applicable so the
  parameter is self-describing in outputs.

## Date and imputation rules

- **[V]** *DT numeric SAS date; *DTM datetime; *TM time; ADY/ASTDY use the
  no-day-0, +1 convention.
- **[V]** *DTF/*TMF imputation flags use CT values (Y/M/D; H/M/S) meaning the
  *most imprecise component imputed*.
- **[QC]** The highest-yield imputation check engines cannot do: cross the
  imputation flag against the **SDTM partial-date pattern**. For every ADT
  with null ADTF, the source --DTC must be complete; for every ADTF="D", the
  source must have year+month only; etc. Disagreement means the flag lies
  about what was imputed — a Major finding that survives clean compares,
  because production and QC both read the same flag.
- **[QC]** Imputation *direction* per variable class matches the SAP
  convention (typically early/conservative for AE onset, late for last
  contact) — verify by comparing imputed ADT against the theoretical
  earliest/latest completion of the partial.

## ADSL rules

- **[V]** TRTSDT ≤ TRTEDT; TRTxxP populated for randomized subjects.
- **[QC]** Population flag implications — encode the SAP's population algebra
  and test every implication as a rule sweep:
  - SAFFL="Y" ⇒ subject treated (TRTSDT non-null);
  - ITTFL="Y" ⇒ randomized (RANDDT non-null);
  - typically FASFL ⊆ ITTFL and PPROTFL ⊆ FASFL — but the inclusion
    hierarchy is *SAP-specific*; confirm before encoding, then test set
    membership with a cross-tab of all flags. Any cell the SAP says is
    impossible must be zero.
- **[QC]** TRTSDT/TRTEDT vs SDTM EX reconciliation, including the boundary
  subjects: single dose record, missing end date, dose interruption spanning
  the cut, and treated-but-not-randomized.
- **[QC]** RANDDT vs the DS randomization milestone and (if available) the
  randomization system export — three sources, one date.
- **[QC]** ADSL carries all subject-level content: baseline demographics and
  characteristics, plus any TLF grouping variable together with its *N
  ordering counterpart.

## BDS rules

- **[V]** At least one of AVAL/AVALC populated per record; where both, they
  correspond 1:1 within PARAMCD.
- **[V]** ABLFL="Y" at most once per subject × PARAMCD × BASETYPE; BASETYPE
  required whenever multiple baseline definitions coexist.
- **[V]** BASE equals AVAL of the ABLFL="Y" record, propagated to all records
  of that subject-parameter(-basetype); CHG = AVAL − BASE; PCHG = 100 ×
  CHG/BASE.
- **[QC]** The conventions inside those formulas: CHG on the baseline record
  itself (null or 0?); PCHG when BASE=0 (null? not derived? special value?);
  CHG for records *before* baseline. All three are sponsor conventions
  engines don't know — blindspot-pass items feeding directly into TLF
  denominators.
- **[V]** DTYPE in CT (LOCF, WOCF, AVERAGE, PHANTOM...) on derived records.
- **[QC]** DTYPE-derived records: exactly the records the SAP's imputation
  method implies — re-derive the LOCF chain independently for a sample of
  subjects with intermittent missingness; off-by-one-visit LOCF errors
  survive validators because the structure is conformant.
- **[QC]** Visit windowing: ADY of every record with an assigned AVISIT falls
  inside [AWLO, AWHI]; records in overlapping windows resolved by the SAP's
  tie-break (closest to target? earliest? worst?). Windows and tie-breaks are
  the classic shared-wrong-assumption zone — see the residual-risk quiz.
- **[QC]** ANLzzFL: within each subject × PARAMCD × AVISIT (per the SAP's
  selection unit), exactly one record has ANL01FL="Y" when the SAP says "one
  record per..."; the selected record is the one the stated rule picks.
- **[V]** CRITy/CRITyFL pairing; MCRITy/MCRITyML structure per IG version.
- **[QC]** SHIFTy consistent with the categories it claims to combine
  (BNRIND→ANRIND etc.) — recompute the shift from its components.
- **[QC]** ASEQ unique within subject; SRCDOM/SRCVAR/SRCSEQ resolve to real
  SDTM records — full anti-join, not a sample, when volumes allow.

## OCCDS rules (ADAE, ADCM, ADMH)

- **[V]** Dictionary-coded variables carried from SDTM unmodified; dictionary
  version consistent with TS/define.
- **[QC]** TRTEMFL re-derived from the SAP definition (window endpoints
  inclusive? last dose + N days? partial onset dates treated as emergent?) —
  see `adam-qc.md` and `high-risk-domains.md`.
- **[QC]** Occurrence flags (AOCCFL, AOCCSFL, AOCCPFL, AOCCzzFL): for each
  subject, exactly one "Y" at each hierarchy level (overall / SOC / PT), and
  the flagged record is the *first* by the documented sort order. Wrong sort
  order produces conformant-looking flags that shift AE table first-occurrence
  counts — re-derive flags from your own sort and compare.
- **[QC]** Worst-severity / most-related selection per level consistent with
  how the AE tables count (subject counted once at worst severity): the
  flag logic in ADAE and the counting logic in the table must implement the
  same rule — QC them together, not separately.

## ADTTE rules

- **[V]** Typically one record per subject × PARAMCD; PARAM describes the
  endpoint including its unit.
- **[QC]** CNSR convention: 0 = event, positive integers = censoring reasons
  (industry-dominant convention; confirm the SAP didn't invert it). Then:
  - every CNSR=0 record traces to a real qualifying event in source;
  - every censor value maps to one documented reason (EVNTDESC/CNSDTDSC
    populated and consistent with the censoring hierarchy in the SAP);
  - the censor-reason frequency by arm matches the SAP's censoring hierarchy
    applied to the data (see `high-risk-domains.md` TTE section).
- **[QC]** STARTDT is the SAP's time origin (randomization vs first dose —
  wrong origin shifts every AVAL); ADT ≥ STARTDT; AVAL = ADT − STARTDT + 1
  or the SAP's unit conversion (30.4375-day months etc.) — recompute exactly.
- **[QC]** Subjects in the analysis population with *no* record in ADTTE:
  each one is either an error or a documented exclusion; list them.

## Cross-dataset rules

- **[QC]** Every USUBJID in every ADaM dataset exists in ADSL (anti-join).
- **[QC]** ADSL-sourced variables (treatment, population flags, strata)
  merged into other datasets are byte-identical to ADSL's values — a stale
  merge from an earlier ADSL version is invisible to conformance engines and
  poisons every downstream output.
- **[QC]** N(ADSL) vs N(DM): equal, or the difference is exactly the
  documented exclusion set.
- **[QC]** CT/dictionary versions consistent across SDTM, ADaM, define, ADRG.

## Metadata rules

- **[V]** Labels ≤40 chars; standard variables carry the IG's standard labels;
  types/lengths match define.
- **[V]** Character lengths minimized to max actual value (the 200-length
  merge artifact — see `adam-qc.md`).
- **[QC]** No all-null variables without a define comment justifying presence;
  no variables in the data missing from define (both directions).
- **[QC]** Source dataset and variable named for every derived variable; no
  circular variable references; datasets sorted by the unique record
  identifiers stated in the dataset structure — engines don't reliably trace
  spec-declared provenance or sort-key intent, only actual sort order.
