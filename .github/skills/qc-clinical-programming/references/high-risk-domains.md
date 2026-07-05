# High-Risk Clinical Domain and Endpoint Blindspots

Read this reference when the QC target touches endpoint logic, safety summaries,
analysis populations, or reviewer-facing interpretation. These areas are where
clean compares most often hide shared wrong assumptions.

## Time-to-event endpoints

Typical targets: progression-free survival, overall survival, time to treatment
failure, duration of response, time to response, event-free survival.

Blindspot-pass items:

- Event definition: which source records qualify, adjudicated vs investigator
  assessment, first event vs confirmed event.
- Censoring hierarchy: no event, new anticancer therapy, missed assessments,
  lost to follow-up, death after cutoff, withdrawal, competing event.
- Censoring date: last adequate assessment, last contact, randomization, first
  dose, data cutoff, or other SAP-defined date.
- Inclusivity: whether windows and cutoff dates are inclusive or exclusive.
- Assessment adequacy: what makes an assessment usable; handling of NE, not
  done, missing target lesions, unscheduled assessments.
- Time origin: randomization, first dose, informed consent, baseline
  assessment, or another anchor.
- Unit and convention: days, weeks, months; whether month conversion uses
  30.4375, 365.25/12, or exact dates.
- Boundary subjects: event/censor exactly on cutoff, event after new therapy,
  death after long gap, missing baseline, multiple records same day.

Evidence to require:

- Subject-level event/censor listing with reason.
- Hand trace of at least one event, one censor, and one ambiguous boundary
  subject.
- Frequency of censor reasons by treatment arm.

## Exposure, dosing, and compliance

Typical targets: EX, ADEX, treatment duration, cumulative dose, dose intensity,
relative dose intensity, dose modifications, interruptions.

Blindspot-pass items:

- Dose source priority: eCRF exposure, drug accountability, infusion records,
  diary, vendor data.
- Partial or missing dosing dates/times; overlapping intervals; same-day
  multiple doses.
- Treatment duration convention: last dose - first dose + 1, actual exposure
  days, excluding interruptions, including planned gaps.
- Cumulative dose units and conversions; strength vs administered amount;
  body-surface-area or weight-based dosing.
- Missed dose, reduced dose, delayed dose, interruption, permanent
  discontinuation definitions.
- Combination therapies: per-component vs regimen-level exposure.
- Treatment-emergent windows driven by first/last dose; inclusive endpoint.

Evidence to require:

- Reconciliation of first/last dose vs ADSL treatment dates.
- Listing of subjects with dose gaps, overlaps, reductions, missing dates,
  and planned vs actual treatment mismatch.

## Labs, vital signs, ECG, and toxicity grading

Typical targets: ADLB, ADVS, ADEG, shift tables, worst post-baseline,
clinically significant abnormality, CTCAE grading.

Blindspot-pass items:

- Baseline definition: last non-missing before first dose, before
  randomization, before treatment start date/time, scheduled only vs any.
- Unit conversion and standardization; lab normal range source and version.
- Local lab vs central lab precedence; repeated samples; unscheduled visits.
- Toxicity grade version and mapping; high/low direction; grade 0 vs missing.
- Worst post-baseline: worst by grade, severity, numeric value, or clinical
  direction; tie-breaking.
- Shift tables: denominator, baseline category, post-baseline window, missing
  category handling.
- Timepoint windows and boundary days.

Evidence to require:

- Frequencies of units, normal-range availability, baseline flags, and toxicity
  grades.
- Boundary traces for BASE, CHG/PCHG, worst post-baseline, and shift category.

## Adverse events and medical coding

Typical targets: ADAE, AE summaries, TEAE flags, AESI, deaths, serious AEs,
MedDRA hierarchy summaries.

Blindspot-pass items:

- MedDRA version and whether coding changed across transfers.
- Treatment-emergent definition: first dose to last dose + N days, inclusive
  endpoints, partial AE start dates, ongoing events at baseline.
- Relationship and severity summarization: worst severity, most related,
  first occurrence, subject-level vs event-level counting.
- SOC/PT sorting: descending frequency by which arm/overall, then alphabetic,
  primary SOC vs multi-axial considerations.
- AESI/grouped terms: source of grouping, SMQ narrow/broad, sponsor custom
  lists, versioning.
- Deaths and serious AEs: consistency across AE, DS, death CRF, and listings.

Evidence to require:

- Frequency of TEAE flags by partial-date status.
- Listing of boundary AEs: onset on first dose, onset on last dose + N,
  missing/partial start date, ongoing at baseline.

## Concomitant medications and WHODrug

Typical targets: CM, ADCM, prior/concomitant flags, medication class summaries.

Blindspot-pass items:

- WHODrug version and coding level used for summaries.
- Prior vs concomitant definition; partial dates and ongoing medications.
- Indication-based subsets; rescue medication flags; prohibited medication
  classification.
- Same medication split across records; duplicate therapies; route/form/dose
  normalization.

Evidence to require:

- Boundary medication listing around first dose and treatment end.
- Reconciliation of coding terms used in summaries to source/coding files.

## Disposition, protocol deviations, and populations

Typical targets: DS, ADDS, ADSL flags, disposition tables, analysis population
summaries, major protocol deviations.

Blindspot-pass items:

- Screen failures: included where, and whether they appear outside DM/DS.
- Randomized vs treated vs enrolled vs safety population definitions.
- Treatment assignment: planned vs actual, mis-randomized, never-treated,
  wrong-treatment, crossover.
- Protocol deviation source, major/minor cut, pre/post-randomization timing,
  adjudication status.
- Discontinuation reason hierarchy and reconciliation across EDC pages.

Evidence to require:

- Subject-level reconciliation of DM/DS/EX/ADSL population flags.
- Listing of subjects where planned treatment differs from actual treatment.

## Questionnaires, PROs, and scoring algorithms

Typical targets: QS, ADQS, PRO responder endpoints, composite scores.

Blindspot-pass items:

- Instrument version, licensing/copyright scoring rules, language/version
  equivalence.
- Item recoding, reverse scoring, subscale membership, allowed missing-item
  rules, prorating.
- Visit windows and repeated questionnaires at same visit.
- Responder definitions: absolute change, percent change, threshold crossing,
  sustained response.
- Handling of partially completed forms and not-done reasons.

Evidence to require:

- Item-level to score-level trace for a small sample, including missing-item
  edge cases.
- Frequency of missing items and derived missing-score reasons.

## Subgroups, stratification factors, and regions

Typical targets: subgroup summaries, forest plots, stratified analyses,
randomization strata reconciliation.

Blindspot-pass items:

- Randomization stratum vs derived baseline stratum; mismatch handling.
- Region/country/site pooling; small-cell handling; missing subgroup category.
- Baseline characteristic cutpoints; inclusive/exclusive boundary rules.
- Subgroup definitions copied across studies but not valid for this protocol.

Evidence to require:

- Cross-tab of randomization strata vs derived strata.
- Listing of subjects at subgroup cutpoint boundaries.

## Estimands and intercurrent events

Typical targets: efficacy endpoints affected by treatment discontinuation,
rescue therapy, death, COVID-era disruptions, alternative therapy, missing data.

Blindspot-pass items:

- Estimand strategy: treatment policy, hypothetical, composite, while-on-
  treatment, principal stratum.
- Intercurrent event detection source and timing.
- Post-ICE data inclusion/exclusion rules.
- Missing data handling: MAR/MNAR assumptions, multiple imputation inputs,
  tipping point analyses, LOCF/BOCF/WOCF.
- Sensitivity analyses: whether derivations intentionally differ from primary
  analysis.

Evidence to require:

- Subject-level ICE listing with date, type, strategy, and endpoint handling.
- Trace of primary vs sensitivity derivation differences.

## When to stop and ask

Stop and ask rather than proceed when:

- the endpoint rule affects primary/secondary inference and is not explicit;
- blinding/firewall status is unclear;
- treatment assignment, event status, censoring, or population membership would
  change under reasonable alternative interpretations;
- the applicable standard/version is unknown;
- the required patient-level content is not approved for the current tool;
- the output is for submission, DMC, interim, or regulatory response and the
  SOP/QC depth is unknown.
