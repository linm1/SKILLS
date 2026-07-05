# SDTM Validation Business Rules

Common machine-testable business rules from industry validation frameworks —
FDA Business Rules / Validator Rules, CDISC Conformance Rules (CORE), Pinnacle
21 check families, and PMDA rules — restated as check logic you can implement
independently. Do **not** hardcode rule IDs or CT versions: the engine version
and regulatory rule configuration are inputs (record them in the findings log,
see `esub-qc.md`).

Each rule is tagged:
- **[V]** — validators typically fire on this; your QC job is triage, not
  re-detection (but re-check after any data change).
- **[QC]** — validators typically do *not* catch this reliably; independent
  QC must test it. These are where the value is.

## Identifiers and structure

- **[V]** STUDYID constant across all records and equal to TS.STUDYID and the
  define.xml study OID.
- **[V]** DOMAIN equals the dataset name (2 chars); SUPP-- RDOMAIN resolves.
- **[V]** USUBJID unique in DM; every USUBJID in every domain exists in DM.
- **[QC]** USUBJID construction follows the sponsor convention
  (e.g., STUDYID-SITEID-SUBJID) *consistently* — validators check existence,
  not construction. A subject re-screened or transferred between sites is the
  boundary case.
- **[V]** --SEQ unique within USUBJID per domain; non-missing; integer.
- **[QC]** --SEQ ordering follows the spec's stated sort — engines check
  uniqueness only. Unstated sort order is a blindspot-pass item.
- **[V]** No full-key duplicate records (test the *stated* key set, then test
  the key set that should be unique clinically — they can differ).
- **[QC]** Y/N response fields contain only "Y"/"N" (or "Y"/null where the IG
  says so) — never "Yes"/"No"/"y". Null-vs-"N" meaning is a convention item.

## Dates

- **[V]** ISO 8601 format; valid calendar dates; partials truncate right-to-
  left only (a day without a month is malformed, not partial).
- **[V]** --STDTC ≤ --ENDTC where both complete.
- **[V]** --DY, --STDY, --ENDY consistent with RFSTDTC using the +1, no-day-0
  convention.
- **[QC]** No record dates after the data cutoff / database lock date — engines
  don't know your cutoff. Records after cutoff are class D findings.
- **[QC]** No assessments dated after DTHDTC; no dates before RFICDTC (informed
  consent). Both are cheap `proc sql` sweeps with high yield.
- **[QC]** AGE consistent with BRTHDTC and the sponsor's reference date
  (screening? randomization? informed consent?) — the reference date is an
  unknown-known. AGE ≥ 0 is the validator's job; the anchor is yours.

## DM rules

- **[V]** One record per USUBJID; ARM/ARMCD and ACTARM/ACTARMCD pair 1:1 and
  exist in TA (with IG-version-specific conventions for "SCRNFAIL",
  "NOTASSGN", "NOTTRT").
- **[QC]** RFSTDTC definition matches the study convention (first dose?
  randomization?) and is *consistently* that thing: reconcile RFSTDTC against
  min(EX.EXSTDTC where dose administered) and RFENDTC against last exposure or
  last contact per the definition. Validators check presence, not meaning.
- **[V]** RFXSTDTC/RFXENDTC align with first/last study treatment exposure.
- **[QC]** Screen failures: ARMCD="SCRNFAIL", RFSTDTC null, and — the part
  engines skip — they appear only in the domains the sponsor convention allows.
- **[V]** COUNTRY in ISO 3166-1 alpha-3; SEX/RACE/ETHNIC in CT.
- **[QC]** RACE="MULTIPLE" ⇒ individual races in SUPPDM; verify the SUPPDM
  records actually exist for every MULTIPLE subject.

## The death-consistency triple [QC]

The highest-yield cross-domain check validators only partially cover. For
every subject with *any* evidence of death, all of these must agree:

1. DM.DTHFL="Y" and DM.DTHDTC populated (and vice versa — DTHDTC without
   DTHFL is a finding).
2. If death was due to an AE: an AE record with AESDTH="Y" and AEOUT="FATAL",
   and AEENDTC consistent with DTHDTC (convention: equal, or AE end ≤ death).
3. DS has a death disposition record (DSDECOD="DEATH") with DSSTDTC
   consistent with DTHDTC.
4. Downstream: the count of these subjects equals the deaths row of the
   disposition table and the death listing (see `tlf-business-rules.md`).

Build one subject-level reconciliation listing across DM/AE/DS; every
disagreement is class D or P, severity Major or Critical.

## Findings-class rules (LB, VS, EG, ...)

- **[V]** --TESTCD/--TEST 1:1; TESTCD ≤8 chars, starts with a letter, no
  special characters.
- **[V]** --ORRES populated ⇒ --STRESC populated; --STRESN populated only for
  numeric results and equal to the numeric of --STRESC.
- **[V]** --ORRES null and result expected ⇒ --STAT="NOT DONE"; --REASND
  expected when --STAT="NOT DONE".
- **[QC]** One standardized unit per --TESTCD across the whole study
  (--STRESU constant within test) and the *conversion factors* from --ORRESU
  are correct — engines flag unit CT membership, not conversion math. Recompute
  a sample: original value × factor = standardized value.
- **[V]** LBSTNRLO ≤ LBSTNRHI; LBNRIND consistent with value vs range.
- **[QC]** Normal-range *source and version* consistent across transfers — a
  mid-study lab range update shows up as an unexplained LBNRIND shift.
- **[V]** --BLFL="Y" at most once per subject-test (per timing granularity);
  baseline record dated on/before RFSTDTC. SDTMIG 3.4+: --LOBXFL rules differ
  from --BLFL — confirm the IG version before checking either.
- **[QC]** Plausibility sweeps engines don't run: SYSBP > DIABP on the same
  record; HEIGHT/WEIGHT unit-plausible (a 180 kg "height" is an unconverted
  cm); temperature route vs value range.

## Events and interventions rules (AE, CM, EX, DS)

- **[V]** AE: AETERM non-null; AEDECOD and AEBODSYS populated (MedDRA);
  AESER/AESEV/AEREL in CT; AESTDTC ≤ AEENDTC.
- **[QC]** AESDTH="Y" ⟺ AEOUT="FATAL" — engines check one direction at most;
  check both, then hand the subjects to the death triple above.
- **[QC]** MedDRA version identical in TS, define.xml, and the coding actually
  applied — recode drift across data transfers is invisible to validators
  because each artifact is internally valid.
- **[V]** CM: CMTRT non-null; CMSTDTC ≤ CMENDTC; WHODrug coding populated
  where required.
- **[QC]** Ongoing-medication representation (--ENRTPT/--ENTPT vs --ENRF) is
  used per the IG version and *consistently* — mixed conventions within one
  domain pass CT checks individually.
- **[V]** EX: EXDOSE ≥ 0; EXDOSU in CT; EXSTDTC ≤ EXENDTC; EXTRT in the
  protocol treatment list.
- **[QC]** Every subject with ARMCD not in (SCRNFAIL, NOTASSGN) has EX
  records, or the exception is documented (randomized-never-treated listing).
  The FDA business-rule family checks treated-vs-randomized consistency —
  verify against your study's actual randomization source, not just DM.
- **[QC]** Placebo representation convention (EXDOSE=0? EXTRT="PLACEBO"?
  blinded label?) matches the spec — and does not accidentally unblind.
- **[V]** DS: DSDECOD in CT (completion/discontinuation codelist); DSCAT in
  (DISPOSITION EVENT, PROTOCOL MILESTONE, OTHER EVENT); DSSTDTC populated.
- **[QC]** Exactly one end-of-study disposition record per subject per epoch
  convention; discontinuation reason hierarchy applied when EDC captured
  multiple reasons.

## Visits, epochs, and trial design

- **[V]** VISITNUM/VISIT 1:1; planned visits exist in TV; SV covers each
  subject-visit actually occurring.
- **[QC]** Unscheduled visit numbering scheme (x.1, x.01, 9xx...) matches the
  spec and sorts correctly as a *number* — engines check consistency, not
  whether 4.10 was intended to sort after 4.9.
- **[QC]** --DTC of findings consistent with the SV date span of the claimed
  VISIT — a lab dated outside its visit window is either a data issue or a
  visit-assignment error; engines rarely connect the two domains.
- **[V]** EPOCH values in CT and consistent with SE spans.
- **[QC]** TS contains the required parameter set for the target authority's
  current technical conformance guide (e.g., SSTDTC, STITLE, TPHASE, TRT,
  RANDOM, SDTMIG version parameters and dictionary version parameters). The
  *required list itself is version-dependent* — pull it from the TCG in force,
  never from memory.

## SUPP-- rules

- **[V]** QNAM ≤8 chars, valid name; QLABEL ≤40; IDVAR/IDVARVAL resolve to
  exactly one parent record; RDOMAIN/USUBJID valid.
- **[QC]** No SUPP variable that duplicates a standard variable's content or
  belongs in a standard variable — engines can't judge semantics.
- **[QC]** QNAM stability across data cuts (a renamed QNAM breaks downstream
  ADaM merges silently).

## Implementing rule sweeps in SAS

Accumulate violations into one findings dataset rather than eyeballing logs:

```sas
proc sql;
  create table qc.rule_hits as
  select "DTH_TRIPLE_AE" as ruleid length=20,
         usubjid, "AEOUT=FATAL without AESDTH=Y" as detail length=100
  from sdtm.ae
  where aeout="FATAL" and aesdth ne "Y"
  union all corr
  select "DY_DAY0", usubjid,
         "Study day 0 impossible under +1 convention"
  from sdtm.lb
  where lbdy = 0;
quit;
```

One row per violation, ruleid + subject + detail; feed counts into the
findings log. Zero hits is evidence only if the rule ran against the right
data cut — record dataset timestamps alongside.
