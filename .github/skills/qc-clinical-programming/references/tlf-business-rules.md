# TLF Validation Business Rules

Industry display conventions and cross-output consistency rules, restated as
testable checks. Complements `tlf-qc.md` (method) with rules (content). No
conformance engine covers TLFs — everything here is **[QC]**: either an
automatable consistency sweep or a convention to confirm against the sponsor
style guide before flagging. Conventions below are the *dominant* industry
patterns; where marked "confirm", the sponsor style guide or shell wins.

## Universal display rules

**Counts and denominators**

- Big N in each column header equals the ADSL population-flag count for that
  arm. Same population ⇒ same big N on every output — build a one-page big-N
  reconciliation across the whole TLF package; it is the cheapest global check
  in TLF QC.
- Category counts within a variable sum to ≤ N; if the shell shows a
  "Missing" row, they sum to exactly N. A sum > N means double-counting —
  subjects must count once per category level unless the shell says
  "events, not subjects".
- Percentages: denominator is what the shell says (big N vs subjects with
  non-missing vs subjects assessed at that visit). Percentages of mutually
  exclusive categories sum to 100 ± rounding; flag sums outside 99.9–100.1
  when they should be exhaustive.
- n-per-statistic (the small n above mean/SD blocks) equals the non-missing
  count, not big N — and the same subject set feeds every statistic in that
  block.

**Numeric display conventions (confirm against style guide)**

- Decimal places: min/max at the raw data's precision; mean and median at
  +1; SD at +2 (the dominant convention — some sponsors use +1 for SD).
  Within a statistic, decimals are constant down the column.
- Rounding: half-away-from-zero (SAS `round()`); if any part of the pipeline
  is R, its default `round()` is banker's rounding — a systematic
  0.1-in-the-last-digit disagreement pattern across many cells is this, not
  many bugs (see `tlf-qc.md`).
- Percentages: typically 1 dp; whether 0-count cells show "0", "0 (0.0%)",
  or blank is shell-governed — flag if the shell is silent.
- P-values: 3 or 4 dp; floor as "<0.001" (or "<.001"); never display
  "0.000"; some styles also cap ">0.999". Confirm floor/cap convention.
- Confidence intervals: level per SAP (95% default, but non-inferiority and
  interim analyses often differ); one-sided vs two-sided p-values per SAP —
  a doubled or halved p-value is this error.

**Structure**

- Titles, population statement, footnotes match the shell and the SAP TLF
  index verbatim; table numbers unique and consistent with the index.
- Data cutoff / snapshot date in the footnote matches the transfer actually
  used (check the data, not the intention).
- Sort orders per shell: AE tables descending frequency (confirm *which
  column* drives the sort — total, active arm, or pooled — and the
  alphabetical tie-break); visits in chronological order including correctly
  placed unscheduled/early-termination rows.

## AE table monotonicity rules

The AE table family obeys an arithmetic that can be verified without touching
production — violations are certain errors regardless of convention:

- "Any AE" count ≥ every SOC count; every SOC count ≥ every PT count under it
  (subject-level counting).
- SAE count ≤ AE count; related-AE count ≤ AE count; related-SAE ≤ both;
  grade ≥3 count ≤ any-grade count — for every row, every column.
- Severity breakdown: subjects at worst severity sum to the any-AE count for
  that row (each subject exactly once at exactly one severity).
- AE-leading-to-discontinuation count ≤ any-AE count, and reconciles with
  disposition-table discontinuations due to AE and with ADSL DCSREAS.
- Deaths row = the death-consistency triple count from
  `sdtm-business-rules.md` = disposition table deaths = death listing rows.
- PT appears under its *primary* SOC only (multi-axial MedDRA trap) unless
  the shell requests otherwise.

Automate these as a sweep over the results datasets (or parsed outputs) for
every AE table in the package — they catch counting-logic errors that clean
compares of a single table miss.

## Table-family rules

**Demographics/baseline**

- Age groups, sex, race categories sum to N per column; continuous and
  categorical versions of the same variable describe the same subject set.
- Baseline values consistent with ADSL/BDS baseline derivations — the table
  is one PROC away from the dataset; any extra derivation inside the table
  program is a finding (analysis-ready principle).

**Disposition**

- Randomized = completed + discontinued + ongoing (per the shell's
  arithmetic); discontinuation reasons sum to discontinued; each row
  reconciles to ADSL (EOSSTT/DCSREAS frequencies).
- Screen-failure handling (included row? excluded entirely?) per shell.

**Exposure**

- Duration statistics consistent with ADSL TRTSDT/TRTEDT and the SAP's
  duration convention (+1? excluding interruptions? — see
  `high-risk-domains.md`); subjects-with-any-exposure = safety N.

**Labs / shift tables**

- Shift table marginals: row totals = subjects with a baseline value; each
  cell subject has both baseline and post-baseline in that window; grand
  total consistent with the visit-level table's n.
- Worst-grade tables monotone: grade ≥3 ⊆ grade ≥1; shifts to worse grade
  consistent between the shift table and the worst-grade summary.

**Efficacy / model-based outputs**

- Model N = subjects contributing (non-missing response and covariates) —
  reconcile the "n" the model reports against the population flag count and
  name the excluded subjects.
- Model specification per SAP text: covariates, strata, covariance
  structure, denominator-DF method, non-convergence handling. Match the SAP,
  not whatever converges (`tlf-qc.md`).
- Hazard/odds/risk ratios: confirm the **reference arm direction** — an
  inverted ratio (1/x) with its mirrored CI is among the most damaging
  reproducible TLF errors, and both programs can make it independently if
  the SAP's phrasing ("A vs B") is ambiguous. Blindspot-pass any ratio's
  direction against a hand-computed crude estimate.
- KM outputs: median with CI method per SAP (Brookmeyer–Crowley default);
  numbers-at-risk rows monotone non-increasing; censor tick counts equal the
  ADTTE CNSR>0 frequencies by arm; event counts equal CNSR=0 frequencies.

**Listings**

- Row count equals the qualifying-record count from an independent selection
  (the selection rule, not the rendering, is where listings fail —
  `tlf-qc.md`); sort keys and date display format per style guide; every
  column in the shell present and populated or intentionally blank.

## Cross-output reconciliation matrix

Run once per package, after individual outputs pass. Every number that
appears in more than one place must agree everywhere it appears:

| Quantity | Must agree across |
|---|---|
| Randomized / population Ns | Every table header, disposition, ADSL counts, ADRG statements |
| Deaths | AE tables, disposition, death listing, DM DTHFL, narratives |
| Discontinuations (overall and due-to-AE) | Disposition, AE table, ADSL DCSREAS, listings |
| Exposure duration summary | Exposure table, safety narratives, ADSL |
| Primary endpoint result | Primary table, forest/KM figure, in-text summary, top-line consistency |
| Data cutoff date | Every footnote, ADRG, define/SDRG statements |

Any disagreement is class S, D, or P — a package that disagrees with itself
invites information requests regardless of which output is "right" (same
principle as `esub-qc.md`).

## Sign-off additions for TLF packages

Beyond the per-output quiz in `tlf-qc.md`:

- "Which of these consistency sweeps did I run programmatically vs eyeball?"
- "Name one number that appears in three or more outputs and show the three
  values."
- "Which convention in this package did I *assume* rather than find in the
  style guide or shell?" — each assumption goes in the findings log as
  class A.
