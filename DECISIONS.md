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
