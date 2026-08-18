# Public research design

## Purpose and claim boundary

This repository is a deterministic synthetic demonstration of four operational-authority policies. It separates cumulative state, entity-relative calibration, and prospective post-error tightening. The experiment is a feasibility and research-engineering demonstration; it is not professional guidance, an audit-standard formula, an empirical validation of MCAB, or a causal-effect estimate.

Financial-statement materiality concerns the significance of information or misstatement to users of financial statements. Operational authority concerns how much economic value an AI agent may exercise without independent review. MCAB uses illustrative entity-level materiality anchors to calibrate operational authority budgets, without treating those anchors or safety factors as prescribed approval limits.

## Frozen entity design

| Entity | Illustrative anchor | Scale factor | Initial MCAB budget at 0.10 |
|---|---:|---:|---:|
| `ENTITY_SMALL` | A$250,000 | 0.5 | A$25,000 |
| `ENTITY_REFERENCE` | A$500,000 | 1.0 | A$50,000 |
| `ENTITY_LARGE` | A$1,000,000 | 2.0 | A$100,000 |

The common safety factor is `0.10`. The uniform cumulative cap is A$50,000 and is matched to `ENTITY_REFERENCE`. Proportional entity scaling is a constructive design choice for this authored experiment, not an empirical estimate of organisational scale.

## Policy conditions

| Condition | Cumulative state | Entity calibration | Error tightening | Monetary rule |
|---|---:|---:|---:|---|
| Fixed threshold | No | No | No | A$50,000 per transaction |
| Uniform cumulative cap | Yes | No | No | A$50,000 per risk cell |
| MCAB no tightening | Yes | Yes | No | Entity anchor × 0.10; multiplier `1.00` |
| Full MCAB | Yes | Yes | Yes | Entity anchor × 0.10; multiplier `0.50` after confirmed error |

The cumulative risk cell is `(entity, reporting_period, workflow, account, counterparty)`. Exact equality remains within authority. Projected use strictly above the applicable ceiling requires independent review. Only `AUTO_EXECUTE` amounts consume cumulative autonomous authority; reviewed and blocked amounts do not. No within-period replenishment is modelled.

The confirmed-error signal means an earlier control error was confirmed immediately before the signal position. Full MCAB decides the signal row under the prior state and tightens only later rows in the affected `(entity, workflow)` scope. Prior utilisation is retained. The other three conditions have no tightening mechanism.

The four conditions are not a complete calibration-by-tightening factorial:

| Calibration | No tightening | Tightening |
|---|---|---|
| No entity calibration | Uniform cap | Not implemented |
| Entity calibration | MCAB no tightening | Full MCAB |

The policy ladder is not a complete 2×2 factorial because it contains no uniform-cap-with-tightening condition. The no-tightening–Full-MCAB contrast therefore measures prospective tightening only within entity-calibrated conditions and cannot determine whether the observed tightening result requires, interacts with or generalises beyond entity calibration.

## Frozen qualitative mappings

All policies receive the same qualitative flags and treatment-side mapping. The oracle contains a separately authored copy.

| Flag | Action |
|---|---|
| `related_party_activity` | `INDEPENDENT_REVIEW` |
| `vendor_bank_detail_change` | `BLOCK` |
| `unusual_non_standard_journal` | `INDEPENDENT_REVIEW` |
| `management_override_indicator` | `BLOCK` |
| `period_end_adjustment` | `INDEPENDENT_REVIEW` |

These mappings were frozen before the revised experiment run and remain synthetic design choices.

## Synthetic transactions

Seed `20260818` generates 270 ordered positive-amount transactions, 90 per entity:

| Scenario family | Rows | Design role |
|---|---:|---|
| Ordinary low risk | 150 | Unique or separated cells outside recurrence mechanisms |
| Matched pre-error aggregation | 60 | Two ten-row workflow sequences per entity |
| Qualitative risk | 15 | One case per flag and entity; outside decomposition subsets |
| Isolated significance | 12 | Frozen original amount values; outside decomposition subsets |
| Confirmed-error signals | 3 | One per entity; distinct from post-error cells |
| Post-error accumulation | 30 | One fresh ten-row repeated cell per entity |

Matched aggregation and post-error amounts use reference templates multiplied by entity scale factors `0.5`, `1.0`, and `2.0`. Ordinary and qualitative values are also scaled. Every aggregation transaction remains below A$50,000 individually.

The isolated-significance amount sequence is frozen before revised execution as:

`55,000; 62,500; 71,000; 83,000; 95,000; 58,500; 76,000; 88,000; 55,000; 62,500; 71,000; 83,000`.

Every value comes from the original isolated-large vignettes; the first four repeat to provide four cases per revised entity. These cases are not used for mechanism decomposition.

## Pattern-based adjudication oracle

The oracle is implemented separately and contains no fixed threshold, cumulative cap, entity anchor, safety factor, tightening multiplier, policy decision, or policy import.

Frozen rules are:

1. Apply the separate qualitative mapping first.
2. Route authored isolated-significance vignettes to independent review without a monetary comparison.
3. Within matched pre-error aggregation risk cells, occurrences 1–5 are `AUTO_EXECUTE`; occurrence 6 onward requires `INDEPENDENT_REVIEW`.
4. A confirmed-error signal takes effect only after its own adjudication.
5. Within a fresh post-error repeated cell in the affected entity-workflow scope, occurrences 1–2 are `AUTO_EXECUTE`; occurrence 3 onward requires `INDEPENDENT_REVIEW`.
6. Ordinary, qualitative, isolated-significance, and signal rows do not contribute to aggregation recurrence counts.
7. Scenario step and policy monetary values do not determine the recurrence boundary.

The oracle is procedurally isolated and does not use policy monetary parameters. However, both the oracle and the synthetic scenarios remain authored research-design components and have not been independently expert validated.

Policies receive only operational fields. They do not receive scenario identifiers, scenario types, scenario steps, oracle labels, or policy decisions from other conditions.

## Prespecified mechanism decomposition

Mechanism comparisons are calculated only on frozen subsets:

| Mechanism | Comparison | Subset |
|---|---|---|
| Statefulness | Fixed threshold → Uniform cumulative cap | Matched pre-error aggregation rows |
| Entity calibration | Uniform cap → MCAB no tightening | Matched pre-error aggregation rows, separately by entity |
| Prospective tightening | MCAB no tightening → Full MCAB | Post-error rows only |

Repository-level metrics are reported separately as descriptive results. Their differences are not interpreted as additive mechanism effects.

Canonical supplementary branch labels use exact unrounded repository-level policy metrics. The public pre-declaration did not assign a separate mechanism-subset population to the Calibration or Tightening branches. Matched pre-error aggregation and post-error calculations remain separately reported mechanism-subset findings and cannot replace the repository-level branch inputs.

## Outcomes

Primary outcomes are overall consequential-failure incidence, conditional miss rate, gross authority-exposure proxy, and separate review/block/intervention burdens. Secondary outcomes are false escalation rate, aggregation-related failures, qualitative cases correctly escalated, entity-level results, and full action confusion counts. Every rate includes its numerator and denominator.

`INDEPENDENT_REVIEW` is adequate escalation for the binary missed-escalation measure when the oracle requires review or blocking because autonomous authority has been removed. The three-action confusion table retains action-severity differences.

Absolute-dollar authority exposure remains a primary outcome. Two supplementary scale-relative descriptions are calculated only for consequential failures:

- summed anchor-normalised exposure is `Σ(abs(amount_i) / entity_anchor_i)` across failed transactions; and
- each entity ratio divides failed gross amount in that entity by its authored anchor, with the maximum defined as the largest of the three ratios.

Calculations use integer cents and exact rational arithmetic for comparisons. Displayed ratios use four decimal places. Summed anchor equivalents are dimensionless, may exceed `1.0`, and combine failure incidence with relative failure size; an arbitrary total has no natural single-entity interpretation. The maximum ratio is the largest fraction of one synthetic entity's authored anchor exposed without independent review. Neither measure is realised loss, audit materiality, or a validated loss metric, and neither replaces the primary absolute-dollar proxy.

The Uniform-cap versus Full-MCAB absolute-dollar difference is also partitioned by entity, scenario type, pre/post-error status, and workflow. Each partition must reconcile independently to the same repository-level failure counts and exposure totals. This decomposition is descriptive and is not treated as an additive mechanism estimate.

## Predeclared sensitivity grids

- Fixed thresholds: A$25,000, A$50,000, A$100,000.
- Uniform caps: A$25,000, A$50,000, A$100,000.
- MCAB safety factors: `0.05`, `0.10`, `0.15`.
- Full-MCAB tightening multipliers: `0.25`, `0.50`, `0.75`, `1.00`.
- Matched-reference comparisons set the uniform cap equal to the reference entity's MCAB budget at each safety factor.

The oracle labels and dataset remain fixed throughout. Sensitivity results are descriptive and are not used to select a preferred condition retrospectively.

A separate oracle-recurrence sensitivity holds all transaction data and policy decisions fixed while re-adjudicating the authored ground truth at `4/3`, `6/3`, `8/3`, `6/2`, and `6/4`; `6/3` remains the sole base case. Every configuration reports rate numerators and denominators, absolute-dollar exposure, supplementary ratios, and intervention counts for all four policies. Policy intervention counts must remain invariant. Because oracle-required and oracle-auto denominators change, rate levels are not directly comparable across configurations; only within-configuration ordering and trade-offs are described. Exact conditional-miss fractions determine weak ordering, including ties.

Implementation isolation, monetary independence, and scenario-design coupling are distinct. The oracle imports no policy code or configuration and receives no policy parameters or decisions. Parametric coupling between the treatment's monetary logic and the oracle's recurrence rule is relocated from the oracle to the authored scenario templates rather than eliminated. Recurrences six and three are demonstration choices rather than values derived from ASA 240, ASA 320, legislation, or professional protocol.

## Revision 2 workflow boundary

The supplementary definitions, recurrence grid, exact branch rules, and alternative interpretations were publicly committed before formal supplementary computation. The process was not blinded or formally preregistered: the original dollar results, entity anchors, and Phase 1 decomposition made likely directions inferable, and the supplementary metrics were selected after the original results were known. The commit records workflow order but does not make the exercise confirmatory research; residual post hoc metric-selection risk remains.

## Corrected integrated interpretation boundary

In this authored dataset, entity-relative calibration improves the matched aggregation subset while weakening control over the isolated-significance vignettes. At repository level, MCAB no tightening slightly reduces conditional misses but increases absolute-dollar exposure, summed anchor-normalised exposure, and the maximum entity-anchor ratio relative to the uniform cap. Adding prospective tightening within the entity-calibrated conditions reduces repository-level summed exposure and failures relative to MCAB no tightening, but the absent uniform-cap-with-tightening condition prevents attribution of this result to an isolated tightening effect or assessment of a calibration-by-tightening interaction.

The mixed results motivate a sharper future question: under what risk compositions does entity-relative authority improve control, and what hierarchy of per-transaction, cumulative risk-cell and cross-entity constraints is required to prevent gains in aggregation control from weakening isolated-transaction control?

[ASA 600 paragraph 35(a)](https://standards.auasb.gov.au/asa-600-may-2022-0) requires component performance materiality to be lower than group performance materiality to address aggregation risk. This is an audit-planning analogy for investigating entity-relative authority budgets beneath an additional cross-entity constraint; it does not prescribe MCAB, operational approval thresholds, transaction caps, or authority budgets. The proposed hierarchy remains untested.

## Validity limitations

- The anchors, scale ratios, recurrence counts, scenario composition, and ordering are authored assumptions.
- Proportional entity scaling and matched scenarios are constructive identification choices, not empirical validation of entity scales or materiality anchors.
- The identical Fixed-threshold entity ratios arise from proportional scenario scaling and proportional anchors, not empirical invariance across organisation sizes.
- The oracle is not expert validated and may encode the researcher's control expectations.
- The oracle and policy remain implementation-separated, but the authored amount templates and recurrence rules retain scenario-design coupling.
- Cell granularity can fragment exposure that would be consequential at a higher hierarchy.
- Flags are treated as observed accurately and without cost.
- Reviewer error, dependence, delay, control cost, strategic adaptation, recovery, and realised financial loss are omitted.
- One deterministic dataset supports reproducibility but not statistical inference or external validity.
- Summed anchor equivalents aggregate across entities and depend jointly on failure incidence and relative failure size; the maximum ratio can depend on one entity and a small number of vignettes.
- Supplementary measures can change the descriptive interpretation without changing the underlying transactions, policy decisions, base oracle labels, or original evidence.
- The incomplete policy factorial cannot show whether tightening requires, interacts with, or generalises beyond entity calibration.
