# TLF QC Reference

Read this before QCing a table, listing, or figure. The governing principle:
QC the numbers, not the typesetting — but confirm with the user which
elements are in QC scope (some sponsors require footnote/layout QC too).
For display conventions, AE-table monotonicity arithmetic, and the
cross-output reconciliation matrix, see `tlf-business-rules.md`.

## Method selection

Two legitimate approaches; choose per output and document the choice:

1. **Dataset-level QC (preferred).** Independently derive the analysis
   results into a dataset (one row per table cell or statistic), have the
   production side output its pre-formatting results dataset, and PROC
   COMPARE the two. Cleanest, most automatable, and the diff is precise.
2. **Output-level QC.** When production only delivers the rendered RTF/PDF,
   parse or transcribe the reported values and compare against your
   independently derived numbers. Higher effort, reserve for outputs where
   no results dataset exists. When parsing RTF programmatically, validate
   the parser on a known cell before trusting it at scale.

Never QC a table by re-running the production program and comparing to
itself. That verifies the machine, not the logic.

## Independent derivation rules

- Start from the ADaM datasets named in the shell, apply the population and
  selection criteria as written in the SAP/shell — not as you remember the
  production team doing it.
- Big N (column headers): re-derive from ADSL population flags. Verify every
  percentage in the table uses the denominator the shell specifies. The
  denominator question — big N, subjects with any assessment, non-missing
  at that visit? — is the highest-yield TLF ambiguity; blindspot-pass it
  per section of the table.
- Rounding: SAS `round()` rounds half away from zero; other tools and some
  SAP conventions differ (banker's rounding in R's `round()`). Confirm the
  convention and the decimal places per statistic (mean vs SD often differ
  by one place per sponsor style). Percentages: rounded from the exact
  ratio, or from rounded counts? Both exist in the wild.
- Zero-count categories: displayed as 0, 0 (0.0%), or suppressed? Sponsor
  style governs; flag if the shell is silent.
- Sorting: AE tables sorted by descending frequency in which column, with
  what tie-break, at which SOC/PT level — three unknown-knowns per table.
- P-values and model-based statistics: re-fit independently (PROC MIXED /
  GLM / FREQ as the SAP specifies), matching the stated covariance
  structure, denominator DF method, and handling of non-convergence. Match
  to the SAP text, not to whatever converges.

## Listings

- Re-derive the selection (which records qualify) and the sort order;
  spot-check content of a sample of rows against source.
- Listings look trivial and hide selection ambiguities (e.g., "listing of
  serious AEs" — by AESER, or by seriousness criteria flags?).

## Figures

- QC the plotted dataset, not pixels: derive the input dataset for the
  figure and compare. Confirm axis-relevant derivations (e.g., time on
  x-axis — days since first dose vs randomization).

## Cross-output consistency (cheap, high-yield)

- Big Ns identical across all tables using the same population.
- The same statistic appearing in multiple outputs (e.g., ITT n in the
  disposition table and the demographics table) must match exactly.
- Table numbers/titles/populations against the SAP TLF index.

## Sign-off quiz prompts for TLFs

- "Take one cell mid-table: reproduce its count by an independent filter
  and hand-count in a PROC FREQ. Does it match both programs?"
- "Which subjects are excluded from this denominator, and can I name them?"
- "If the same subject has two qualifying records, how many times are they
  counted, and where does the shell say that?"
