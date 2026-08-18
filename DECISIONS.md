# Research design decisions

## D001 — Four-condition mechanism separation

Use a fixed threshold, a uniform cumulative cap, an entity-calibrated MCAB ablation without tightening, and full MCAB. This separates cumulative state, entity-relative calibration, and prospective tightening instead of attributing their combined descriptive difference to one construct.

## D002 — Frozen entity scales

Use illustrative anchors of A$250,000, A$500,000, and A$1,000,000 with a common safety factor of `0.10`. Match the A$50,000 uniform cap to the reference entity. These values are research parameters, not prescribed thresholds.

## D003 — Matched constructive scenarios

Use proportional scale factors `0.5`, `1.0`, and `2.0` for matched aggregation and post-error templates. Freeze all templates before execution and report mixed or null differences without retuning.

## D004 — Preserved qualitative and isolated cases

Retain the original five qualitative mappings. Freeze the isolated-significance sequence using only amount values from the original eight vignettes, repeating the first four to obtain four cases per revised entity. Exclude qualitative and isolated-significance rows from mechanism decomposition.

## D005 — Pattern oracle

Use non-monetary recurrence boundaries: review from occurrence six in pre-error aggregation cells and occurrence three in fresh post-error cells. Keep the oracle technically separate, exclude monetary policy parameters, and describe the oracle and scenarios as co-authored and non-expert-validated.

## D006 — Common cumulative accounting

Use `(entity, reporting_period, workflow, account, counterparty)` as the common cumulative risk cell. Exact equality is allowed. Only autonomous executions consume authority; reviewed or blocked rows do not. Tightening retains prior utilisation and affects later rows only.

## D007 — Subset-based mechanism decomposition

Estimate no additive overall mechanism effects. Compare statefulness on matched pre-error aggregation rows, calibration on those rows separately by entity, and tightening on post-error rows only.

## D008 — Transparent metric denominators

Report overall failure incidence over all transactions and conditional miss rate over oracle-required escalations. Report review and block separately, and describe gross missed-transaction amount only as an authority-exposure proxy.

## D009 — Portable chart validation

Validate chart source values, labels, existence, dimensions, and non-empty rendering across platforms. Do not require a committed PNG to be byte-identical across Windows and Linux; byte comparisons are limited to CSV and Markdown artifacts or same-environment diagnostic reruns.

## D010 — Reproducibility boundary

Pin direct dependencies, generate all empirical artifacts from code, reconcile summaries to decision rows, and run local tests plus `pip check`. A platform-specific transitive lock remains outside this minimal cross-platform prototype.

## D011 — Revision 2 frozen base and workflow order

The 270 base transactions, seed, amounts, scenario membership and order, templates, entities, anchors, fixed threshold, uniform cap, MCAB safety factor, tightening multiplier, qualitative mappings, policy rules, policy decisions, primary metric definitions, and prespecified mechanism subsets remain frozen. The base oracle continues to require review from recurrence six before a confirmed error and recurrence three after a confirmed error. The 6/3 configuration remains the sole base-case reporting configuration.

Alternative recurrence configurations are sensitivity analyses only. They do not replace the base oracle labels, dataset fields, decision rows, primary results, or README base results. The existing absolute-dollar authority-exposure proxy remains a primary outcome; scale-relative measures are supplementary and explanatory.

The interpretation branches in this record are publicly committed before formal supplementary computation. Formal calculation begins only after that public pre-declaration commit, and implementation remains uncommitted for independent review.

## D012 — Supplementary scale-relative measures

For consequential control failures only, summed anchor-normalised exposure is defined as:

`anchor_normalised_exposure = Σ(abs(amount_i) / entity_anchor_i)`

A consequential control failure occurs when the policy action is `AUTO_EXECUTE` and the oracle action is `INDEPENDENT_REVIEW` or `BLOCK`. Each transaction uses its own entity's authored anchor. The result is dimensionless aggregated entity-anchor equivalents, may exceed `1.0`, and reflects both failure incidence and relative failure size. An arbitrary aggregate value has no natural single-entity interpretation. It is not realised loss, audit materiality, or a validated loss metric.

For each policy and entity, the entity-anchor exposure ratio is:

`entity_anchor_exposure_ratio_e = Σ(abs(amount_i) for consequential failures in entity e) / entity_anchor_e`

The maximum entity-anchor exposure ratio is the maximum of the three entity ratios. An entity with no consequential failure receives a zero ratio. All three entity ratios and the maximum are reported. The maximum is the largest fraction of any single entity's authored anchor exposed without independent review and is not used alone to declare a policy winner.

Branch selection uses exact unrounded values. Calculations use `Decimal`, `Fraction`, integer cents, or exact cross-multiplication as appropriate. Displayed supplementary ratios use four decimal places. A comparison of exactly equal summed values selects the equal-or-higher Branch B.

## D013 — Oracle-recurrence sensitivity design

The five unique recurrence configurations are `4/3`, `6/3`, `8/3`, `6/2`, and `6/4`, where the first number is the pre-error review recurrence and the second is the post-error review recurrence. The frozen `6/3` configuration is the base case. Transaction data and policy decisions remain fixed across all five configurations.

For every configuration and policy, report oracle-required escalation numerator and denominator; consequential-failure numerator and total denominator; conditional-miss numerator and oracle-required denominator; false-escalation numerator and oracle-auto denominator; absolute-dollar exposure; summed anchor-normalised exposure; all entity ratios and their maximum; and review, block, and combined-intervention counts. Every rate includes its numerator and denominator.

Conditional-miss and false-escalation denominators change when oracle labels change. Rate levels are therefore not directly comparable across configurations. Comparisons concern policy ordering and trade-offs within each configuration. Cross-configuration values represent different authored ground truths, and stability across these five settings is local sensitivity rather than universal robustness. Policy decisions and intervention counts remain invariant across oracle configurations.

Policies are ranked by their exact conditional-miss fractions from lowest to highest. Fractions are compared by exact arithmetic rather than rounded percentages, and ties are preserved. An unchanged ordering requires the same weak ordering and identical tie structure in all five configurations. Any inversion, new tie, or removed tie selects Sensitivity Branch B.

## D014 — Oracle coupling and recurrence rationale

Implementation isolation, monetary independence, and authored scenario-design coupling are distinct. The oracle imports no policy implementation or policy configuration and uses no treatment monetary parameter. Nevertheless:

“Parametric coupling between the treatment's monetary logic and the oracle's recurrence rule is relocated from the oracle to the authored scenario templates rather than eliminated.”

This coupling is acceptable for constructive feasibility work but limits external validity. Recurrences six and three are authored demonstration parameters. They are not derived from ASA 240, ASA 320, legislation, or professional protocol and are only conceptually motivated by repeated or unusual patterns. Sensitivity analysis is required because no professional source supplies those numerical choices.

## D015 — Canonical interpretation branches

### Overall contrast: Uniform cap → Full MCAB

#### Overall Branch A — Full MCAB is lower

“Full MCAB has lower summed anchor-normalised exposure than the uniform cap while retaining higher absolute-dollar exposure. The measures diverge because one reports gross dollars and the other scales each consequential failure to its entity’s authored anchor. This divergence is consistent with the intended operation of entity-relative calibration, but it is not evidence that MCAB is effective or generally superior.”

#### Overall Branch B — Full MCAB is equal or higher

“Full MCAB reduces consequential-failure incidence relative to the uniform cap but does not reduce summed anchor-normalised exposure. The supplementary scale-relative measure therefore does not favour Full MCAB, and the result is retained as a policy trade-off rather than explained away or used to retune the design.”

### Calibration step: Uniform cap → MCAB no tightening

#### Calibration Branch A — MCAB no tightening is lower

“MCAB without tightening has lower summed anchor-normalised exposure than the uniform cap. In this authored design, changing from a common cumulative cap to entity-relative budgets changes the allocation of intervention and scale-relative exposure. This descriptive result does not establish the effectiveness or general superiority of entity calibration.”

#### Calibration Branch B — MCAB no tightening is equal or higher

“MCAB without tightening does not reduce summed anchor-normalised exposure relative to the uniform cap. The calibration step therefore does not favour MCAB on this supplementary measure, and the observed result is retained without changing entity anchors, scenario amounts or policy parameters.”

### Tightening step: MCAB no tightening → Full MCAB

#### Tightening Branch A — Full MCAB is lower

“Full MCAB has lower summed anchor-normalised exposure than MCAB without tightening. Within the authored post-error sequences, prospective tightening is associated descriptively with lower scale-relative exposure and a different intervention burden. This is not causal evidence that tightening is effective outside the constructed scenarios.”

#### Tightening Branch B — Full MCAB is equal or higher

“Full MCAB does not reduce summed anchor-normalised exposure relative to MCAB without tightening. Prospective tightening therefore does not favour Full MCAB on this supplementary measure. The result is reported as an observed trade-off, is not treated as a design defect, and does not trigger retuning.”

### Oracle-sensitivity policy ordering

#### Sensitivity Branch A — ordering unchanged

“The conditional-miss-rate policy ordering, including ties, is unchanged across the five authored recurrence configurations examined. This is local sensitivity to the selected recurrence points within one authored dataset, not evidence of robustness.”

#### Sensitivity Branch B — ordering changes

“The conditional-miss-rate policy ordering changes under [computed configuration or configurations]. The base-case ordering is therefore conditional on the authored 6/3 recurrence points. This dependence is retained as a limitation and is not resolved by selecting a preferred configuration or adjusting the recurrence grid.”

The bracketed configuration field in Sensitivity Branch B is the only fillable field. The surrounding canonical wording remains unchanged.

### Fixed maximum-ratio descriptive template

“Under the maximum entity-anchor exposure ratio, the ranking across the four conditions from lowest to highest is [computed ranking, including ties]. The highest single-entity figure is [computed value] for [computed policy–entity combination or combinations], meaning that this fraction of that entity’s authored anchor was exposed without independent review.”

The canonical template remains unchanged. A separate observed-results record fills only its bracketed factual fields and adds no causal, promotional, comparative, or evaluative language.

## D016 — Phase 1 absolute-dollar decomposition before supplementary computation

The following decomposition was obtained from the committed base decision rows before any supplementary scale-relative metric was formally computed. These are existing absolute-dollar base results, not anchor-normalised results.

### By entity

| Entity    | Uniform failures | Uniform exposure | Full failures | Full exposure | Full − Uniform exposure |
| --------- | ---------------: | ---------------: | ------------: | ------------: | ----------------------: |
| SMALL     |               18 |         A$69,425 |             2 |       A$7,150 |               −A$62,275 |
| REFERENCE |                6 |         A$40,900 |             2 |      A$14,300 |               −A$26,600 |
| LARGE     |                1 |         A$12,400 |             6 |     A$296,100 |              +A$283,700 |
| **Total** |           **25** |    **A$122,725** |        **10** | **A$317,550** |          **+A$194,825** |

### By scenario type

| Scenario                | Uniform failures | Uniform exposure | Full failures | Full exposure | Full − Uniform exposure |
| ----------------------- | ---------------: | ---------------: | ------------: | ------------: | ----------------------: |
| Aggregation pressure    |               11 |         A$50,775 |             3 |      A$28,350 |               −A$22,425 |
| Isolated significance   |                0 |              A$0 |             4 |     A$267,500 |              +A$267,500 |
| Post-error accumulation |               14 |         A$71,950 |             3 |      A$21,700 |               −A$50,250 |
| **Total**               |           **25** |    **A$122,725** |        **10** | **A$317,550** |          **+A$194,825** |

“The Uniform-cap–Full-MCAB absolute-dollar reversal is driven primarily by four isolated-significance vignettes in the LARGE entity, which contribute A$267,500 of Full MCAB exposure and A$0 under the uniform cap. This corrects the initial expectation that the reversal would mainly reflect cumulative-budget permissiveness. Across all entities, aggregation-pressure exposure is A$22,425 lower under Full MCAB and post-error-accumulation exposure is A$50,250 lower. LARGE remains the source of the positive entity contribution, but the dominant scenario driver is isolated significance rather than the prespecified cumulative-mechanism subsets. The existing MCAB-no-tightening–Full-MCAB comparison remains the cleaner tightening contrast and must not be conflated with this repository-level Uniform-cap–Full-MCAB decomposition.”

This decomposition preceded formal supplementary calculation but was not blinded. Because the entity anchors and absolute-dollar contributions were already public, the likely direction of normalised results was inferable.

## D017 — Future authority-hierarchy research question

“The Phase 1 decomposition identifies a future design question: whether per-transaction authority should be constrained separately from cumulative risk-cell authority, and whether entity-relative budgets should operate beneath an additional cross-entity or group-level ceiling. This architecture is not implemented or tested in the frozen prototype.”

No current policy rule, budget, scenario, oracle rule, parameter, dataset, or base output changes in response to this finding.

## D018 — Public interpretation and README wording

The approved later README interpretation is:

“The repository-level absolute-dollar difference between the uniform cap and Full MCAB is dominated by four isolated-significance vignettes in the LARGE entity. These vignettes sit outside the prespecified mechanism-identification subsets; consequently, calibration and tightening should be interpreted from the decomposition and ablation contrasts rather than inferred from the headline table alone.”

The final public interpretation integrates three distinct layers:

1. the observed aggregation-pressure and post-error absolute-dollar results;
2. the observed worsening in LARGE isolated-significance exposure; and
3. the applicable pre-declared anchor-normalised branch after formal computation.

A favourable Branch A result is not called a win, validation, effectiveness, or general superiority. An unfavourable or equal Branch B result is retained without retuning. The absolute-dollar authority-exposure proxy remains primary, and scale-relative measures remain supplementary.

The concise planned README disclosure is:

“The supplementary scale-relative measures were added after the original absolute-dollar results were known. Their alternative interpretations were publicly committed before formal computation, but the procedure was neither blinded nor formally preregistered because the existing data and anchors made the likely direction inferable. Full procedural detail is recorded in `DECISIONS.md`.”

## D019 — Approved Revision 2 output scope

The approved supplementary deliverables are:

- `outputs/supplementary_policy_metrics.csv`;
- `outputs/exposure_difference_decomposition.csv`; and
- `outputs/oracle_sensitivity_analysis.csv`.

`outputs/supplementary_policy_metrics.csv` is an approved Revision 2 deliverable rather than accidental scope expansion. These outputs are generated programmatically only after the pre-declaration commit is publicly pushed. Existing base outputs remain separate and retain their frozen values.

The generated main table contains Fixed threshold, Uniform cumulative cap, MCAB no tightening, and Full MCAB. It reports overall failure incidence; conditional-miss numerator, denominator, and rate; absolute-dollar exposure; summed anchor-normalised exposure; maximum entity-anchor ratio; and combined-intervention numerator, denominator, and rate.

The comparison chart uses four separate panels for failure incidence, absolute-dollar exposure, summed anchor-normalised exposure, and intervention burden. All four policies appear in every panel, incompatible units are kept on separate axes, and the maximum ratio remains in the table or text.

## D020 — Non-blinded pre-declaration and residual limitations

The supplementary metrics were selected after the original absolute-dollar results were known. The interpretation branches in this record are publicly committed before formal computation, but the process is not blinded. Public data, entity anchors, and the Phase 1 absolute-dollar decomposition made likely directions inferable. The procedure is not formal preregistration, and the public Git commit records workflow order without making the exercise confirmatory research. Residual post hoc metric-selection risk remains.

The summed index depends jointly on failure incidence and relative failure size, aggregates across entities without a natural single-entity interpretation, and may obscure distributional differences. The maximum ratio depends on one entity and potentially a small number of authored cases. Oracle-sensitivity denominators change across configurations. Recurrence points, templates, scenario coupling, and matched construction remain authored design choices. Supplementary measures may alter interpretation without altering the underlying transactions, decisions, oracle labels, or original evidence.

## D021 — Initial observed Revision 2 branch applications (superseded)

This record preserves the initial subset-scoped branch application for transparency. D022 supersedes its Calibration and Tightening population assignments after corrective review of the public pre-declaration.

Formal supplementary computation began only after the pre-declaration commit `1c4237d5e465092323adeafc19e3578212ca71bb` was pushed. Exact rational values, rather than displayed rounded values, selected the branches:

| Contrast | First exact value | Second exact value | Displayed values | Applied branch |
|---|---:|---:|---:|---|
| Overall: Uniform cap → Full MCAB | `3719/10000` | `3533/10000` | `0.3719 → 0.3533` | Overall A |
| Calibration subset: Uniform cap → MCAB no tightening | `1869/10000` | `243/5000` | `0.1869 → 0.0486` | Calibration A |
| Post-error subset: MCAB no tightening → Full MCAB | `123/625` | `93/2500` | `0.1968 → 0.0372` | Tightening A |

### Applied Overall Branch A

“Full MCAB has lower summed anchor-normalised exposure than the uniform cap while retaining higher absolute-dollar exposure. The measures diverge because one reports gross dollars and the other scales each consequential failure to its entity’s authored anchor. This divergence is consistent with the intended operation of entity-relative calibration, but it is not evidence that MCAB is effective or generally superior.”

### Applied Calibration Branch A

“MCAB without tightening has lower summed anchor-normalised exposure than the uniform cap. In this authored design, changing from a common cumulative cap to entity-relative budgets changes the allocation of intervention and scale-relative exposure. This descriptive result does not establish the effectiveness or general superiority of entity calibration.”

### Applied Tightening Branch A

“Full MCAB has lower summed anchor-normalised exposure than MCAB without tightening. Within the authored post-error sequences, prospective tightening is associated descriptively with lower scale-relative exposure and a different intervention burden. This is not causal evidence that tightening is effective outside the constructed scenarios.”

### Applied Sensitivity Branch B

Exact conditional-miss weak orderings were:

| Oracle configuration | Exact weak ordering from lowest to highest |
|---|---|
| `4/3` | Full MCAB < Uniform cumulative cap < MCAB no tightening < Fixed threshold |
| `6/3` | Full MCAB < MCAB no tightening < Uniform cumulative cap < Fixed threshold |
| `8/3` | Full MCAB < MCAB no tightening < Uniform cumulative cap < Fixed threshold |
| `6/2` | Full MCAB < MCAB no tightening < Uniform cumulative cap < Fixed threshold |
| `6/4` | Full MCAB < MCAB no tightening < Uniform cumulative cap < Fixed threshold |

“The conditional-miss-rate policy ordering changes under 4/3. The base-case ordering is therefore conditional on the authored 6/3 recurrence points. This dependence is retained as a limitation and is not resolved by selecting a preferred configuration or adjusting the recurrence grid.”

### Completed maximum-ratio statement

“Under the maximum entity-anchor exposure ratio, the ranking across the four conditions from lowest to highest is Fixed threshold = Uniform cumulative cap < Full MCAB < MCAB no tightening. The highest single-entity figure is 0.3493 (34.9300%) for MCAB no tightening–ENTITY_LARGE, meaning that this fraction of that entity’s authored anchor was exposed without independent review.”

## D022 — Corrective branch-population resolution

This decision supersedes the population assignments recorded in D021 without altering the canonical wording in D015. The public pre-declaration defines policy-level anchor-normalised exposure in D012 and labels policy contrasts in D015. Its population language states that “For consequential control failures only, summed anchor-normalised exposure is defined as” the policy-level sum and that “Branch selection uses exact unrounded values.” It does not state that the Calibration or Tightening branch labels use the prespecified mechanism subsets from D007.

“The public pre-declaration defined policy-level anchor-normalised exposure but did not explicitly state a separate comparison population for the calibration and tightening branch labels. The initial implementation applied those labels to prespecified mechanism subsets. To avoid adopting a favourable post hoc scope, the canonical branches are resolved conservatively from repository-level policy metrics, while the prespecified mechanism-subset calculations are reported separately. This resolution does not alter any transaction, policy action, oracle label, parameter, metric value, recurrence grid or canonical branch text.”

Exact repository-level values select the corrected branches:

| Contrast | First exact value | Second exact value | Displayed values | Correct branch |
|---|---:|---:|---:|---|
| Overall: Uniform cap → Full MCAB | `3719/10000` | `3533/10000` | `0.3719 → 0.3533` | Overall A |
| Calibration: Uniform cap → MCAB no tightening | `3719/10000` | `5129/10000` | `0.3719 → 0.5129` | Calibration B |
| Tightening: MCAB no tightening → Full MCAB | `5129/10000` | `3533/10000` | `0.5129 → 0.3533` | Tightening A |

Sensitivity Branch B remains selected by exact conditional-miss fractions because the weak ordering changes under `4/3`.

The mechanism-subset calculations remain separate descriptive findings:

| Prespecified subset | First exact value | Second exact value | Displayed values |
|---|---:|---:|---:|
| Matched pre-error aggregation: Uniform cap → MCAB no tightening | `1869/10000` | `243/5000` | `0.1869 → 0.0486` |
| Post-error calibrated conditions: MCAB no tightening → Full MCAB | `123/625` | `93/2500` | `0.1968 → 0.0372` |

The applicable Calibration Branch B text remains exactly as pre-declared:

“MCAB without tightening does not reduce summed anchor-normalised exposure relative to the uniform cap. The calibration step therefore does not favour MCAB on this supplementary measure, and the observed result is retained without changing entity anchors, scenario amounts or policy parameters.”

In this authored dataset, entity-relative calibration improves the matched aggregation subset while weakening control over the isolated-significance vignettes. Its repository-level result therefore depends on the authored mixture of cumulative-risk and isolated-transaction scenarios.

## D023 — Incomplete factorial and verified construction effects

The four conditions form an incomplete policy ladder:

| | No tightening | Tightening |
|---|---|---|
| No entity calibration | Uniform cap | Not implemented |
| Entity calibration | MCAB no tightening | Full MCAB |

The policy ladder is not a complete 2×2 factorial because it contains no uniform-cap-with-tightening condition. The no-tightening–Full-MCAB contrast therefore measures prospective tightening only within entity-calibrated conditions and cannot determine whether the observed tightening result requires, interacts with or generalises beyond entity calibration.

Row-level reconciliation confirms that the higher false-escalation counts under `8/3` arise from relabelling fixed policy interventions against a more permissive oracle configuration, not from any change in policy behaviour. Relative to `6/3`, seven uniform-cap interventions and nine interventions in each MCAB condition at pre-error recurrences six or seven change from oracle-required review to oracle-auto. The uniform cap also retains five false escalations already present under `6/3`, producing `12/198`; MCAB no tightening and Full MCAB each produce `9/198`.

The identical `0.2777` Fixed-threshold entity ratios are a product of proportional scenario scaling and proportional entity anchors, not evidence of empirical invariance across differently sized organisations. This matched construction makes the cross-entity comparison cleaner than would ordinarily be expected in operational data. Each entity has the same 18 Fixed-threshold consequential failures at proportionally scaled matched aggregation and post-error positions; gross failed amounts of A$69,425, A$138,850 and A$277,700 scale with anchors of A$250,000, A$500,000 and A$1,000,000.

The mixed results motivate a sharper future question: under what risk compositions does entity-relative authority improve control, and what hierarchy of per-transaction, cumulative risk-cell and cross-entity constraints is required to prevent gains in aggregation control from weakening isolated-transaction control?

ASA 600 requires component performance materiality to be lower than group performance materiality to address aggregation risk. This provides a conceptual accounting analogy for investigating a hierarchy in which entity-relative authority budgets operate beneath an additional cross-entity constraint. It is an audit-planning analogy only: ASA 600 does not prescribe MCAB, operational approval thresholds, transaction caps or authority budgets. The relevant requirement is paragraph 35(a) of the [official AUASB standard](https://standards.auasb.gov.au/asa-600-may-2022-0). The hierarchy remains an untested future-design hypothesis.
