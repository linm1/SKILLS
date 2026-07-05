# SDTM Domain QC Reference

Read this before QCing any SDTM domain. Order of operations: structure →
content → cross-domain → conformance.

## Structural checks (every domain)

- Required/expected/permissible variables per the applicable SDTM IG
  version — confirm the IG version from the SDRG or spec before checking;
  variable core designations shift between versions.
- Variable attributes: name ≤8 chars, label ≤40 chars, character lengths
  match the spec (and no trailing-blank padding inflating lengths).
- Key structure: one record per the stated key set. Verify with
  `proc sort nodupkey` into a scratch dataset and compare counts — do not
  trust the spec's claim; test it.
- --SEQ: unique within USUBJID, positive integer, no gaps required but
  order should follow the spec's stated sort. The sort order behind --SEQ
  is a classic unknown-known: specs often omit it, sponsors always have a
  convention. Flag if unstated.

## Content checks

- Controlled terminology: every CT-bound variable checked against the CT
  version named in the spec/define. Values outside CT are findings even if
  clinically sensible.
- Dates: ISO 8601 format, and partial-date handling per convention.
  Partial dates are the highest-yield ambiguity in SDTM QC:
  - SDTM stores partials as-is (`2026-03`), no imputation in SDTM.
    If you find imputed dates in an SDTM domain, that is a finding —
    imputation belongs in ADaM.
  - --DTC vs --STDTC/--ENDTC consistency: end ≥ start where both complete.
- --DY derivations: verify against RFSTDTC with the +1 convention
  (no day 0). Check specifically the subjects whose event date equals
  RFSTDTC and those before it — boundary subjects expose off-by-one bugs.
- Baseline flags (--BLFL): "last non-missing before first dose" hides at
  least three decisions — tie-breaking on same-date records, whether
  unscheduled visits qualify, and what "before" means when only a partial
  date is available. All three are blindspot-pass items.
- EPOCH: consistent with SE (subject elements); records outside any epoch
  window are findings or documented exceptions.

## Cross-domain checks

- DM as anchor: every USUBJID in every domain exists in DM; RFSTDTC/RFENDTC
  consistent with EX first/last dose (or the sponsor's stated definition —
  RFSTDTC's exact definition is another unknown-known; confirm whether it
  is first dose, randomization, or informed consent per study convention).
- SUPPQUAL: RDOMAIN/USUBJID/IDVAR/IDVARVAL resolve back to a unique parent
  record. Orphan SUPP records are findings.
- RELREC: relationships resolve in both directions.
- Trial design domains (TA/TE/TV/TI/TS): TS completeness matters for
  submission; check required TS parameters against the technical
  conformance guide in use.

## Common unknown-known traps in SDTM

- Character case of CT values (sponsor may submit CT in a specific case).
- Handling of "OTHER, SPECIFY" — whether free text lands in the parent
  domain or SUPPQUAL.
- Screen failures: in DM only, or in other domains too? Spec rarely says;
  convention governs.
- Multiple races → RACE="MULTIPLE" + SUPPDM, or collapsed? Check the aCRF
  annotation and define before assuming.
- Unscheduled visit VISITNUM numbering scheme.

## SAS technique

- Compare against production with `id usubjid <domain seq var>;` so diffs
  align by record, not by position.
- For CT checks, build format catalogs or hash lookups from the CT file
  rather than hardcoding value lists — the CT version is an input, and
  hardcoding hides which version you actually tested against.
- Profile before deriving: `proc freq` on every CT-bound variable of the
  *source* data reveals unmapped raw values (unknown unknowns) before they
  become silent drops.
