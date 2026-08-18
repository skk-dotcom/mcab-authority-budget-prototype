# MCAB prototype research specification

## Status and source

No PhD proposal file was present in the repository at Gate 1. This document therefore distils only the non-personal methodological requirements supplied in the project brief. It does not reproduce a proposal and must not be treated as professional accounting or auditing guidance.

## Research purpose

The prototype asks whether a stateful, aggregation-aware authority budget can expose a weakness in a fixed per-transaction control: individually small transactions can remain below a monetary threshold while producing consequential cumulative exposure. The comparison is a deterministic synthetic demonstration, not a validation of MCAB or a causal-effect estimate.

Financial-statement materiality concerns the significance of misstatement to users of financial statements. Operational authority concerns how much cumulative economic value an AI agent may exercise without independent review. MCAB uses a provisional reporting-materiality amount only as an anchor from which an illustrative operational authority budget is derived; it is not an ASA 320 formula or prescribed threshold.

## Ordered synthetic data

The main dataset will contain 240 positive-amount transactions and use seed `20260818`. Names will be neutral synthetic identifiers. `amount` will represent gross economic magnitude so exposure is not reduced by debit/credit netting.

| Field | Type | Purpose |
| --- | --- | --- |
| `transaction_id` | string | Stable synthetic identifier |
| `sequence_number` | integer | Global processing order |
| `workflow` | string | `procure_to_pay` or `journal_entry_month_end_close` |
| `entity` | string | Synthetic entity identifier |
| `account` | string | Synthetic account/risk-cell component |
| `transaction_type` | string | Invoice, payment, accrual, adjustment, or similar type |
| `counterparty` | string | Synthetic counterparty or `INTERNAL` |
| `reporting_period` | string | Synthetic monthly reporting period |
| `amount` | number | Positive gross economic magnitude |
| `qualitative_flag` | string | Observable qualitative risk flag or `none` |
| `reversible` | boolean | Whether a compensating reversal is feasible in the vignette |
| `confirmed_control_error` | boolean | Exogenous confirmed-error signal, applied prospectively by MCAB |
| `scenario_id` | string | Synthetic vignette identifier |
| `scenario_type` | string | Scenario family used only for generation and evaluation slicing |
| `scenario_step` | integer | Position within a scripted scenario |
| `oracle_required_action` | string | Independently adjudicated expected response |

The policy interfaces will consume only operational fields. They will not use `scenario_id`, `scenario_type`, `scenario_step`, or `oracle_required_action` to decide an action.

## Decision vocabulary

- `AUTO_EXECUTE`: autonomous processing is permitted.
- `INDEPENDENT_REVIEW`: independent human review is required before execution.
- `BLOCK`: execution is stopped pending resolution.

## Comparator: fixed threshold

The illustrative default per-transaction threshold is AUD 50,000. This value is a research parameter, not professional guidance.

The fixed policy will validate the row, apply the common qualitative override, route an unflagged amount strictly greater than AUD 50,000 to independent review, and otherwise permit autonomous execution. It will hold no cumulative state. An amount exactly equal to the threshold is permitted unless a qualitative override applies; boundary behaviour will be tested explicitly.

## Treatment: MCAB

The illustrative default provisional reporting-materiality anchor is A$500,000 and the safety factor is 0.10, giving an initial A$50,000 authority budget for each `(entity, reporting_period, workflow, account)` risk cell. Entity is included to prevent exposure in one synthetic entity from consuming another entity's budget. Workflow is also included because account labels may overlap across workflows. Parameters will live in an immutable configuration object and will be labelled illustrative.

For each ordered transaction, MCAB will:

1. validate the row and apply exactly the same qualitative override used by the fixed comparator;
2. determine the currently effective budget for the transaction's risk cell;
3. compare the transaction's gross amount with the remaining autonomous budget;
4. permit and accumulate the amount when projected autonomous utilisation is exactly equal to or less than the budget; projected usage strictly above the budget requires independent review;
5. record a transparent route, cell, budget, utilisation, and tightening state; and
6. after processing a row marked as a confirmed control error, apply a 0.50 multiplier to budgets for later transactions in the same `(entity, workflow)` scope.

The confirmed-error signal means that an earlier control error has been confirmed immediately before that sequence position. The row at that position is decided under the state that existed before tightening. After that decision, the multiplier changes the effective ceiling for later decisions only. It does not retrospectively alter any earlier decision. Tightening retains prior cumulative utilisation rather than resetting it and remains active for subsequent transactions in the affected `(entity, workflow)` scope for the remainder of the demonstration. Independent-review and blocked amounts do not consume autonomous authority because the budget measures authority exercised without independent review. No within-period replenishment is assumed in the minimum viable design.

The fixed comparator uses the same boundary convention: exact equality remains within authority, while an amount strictly above its threshold requires escalation. Only MCAB maintains utilisation state.

## Common qualitative overrides

Both policies will share one treatment-side override function and receive identical flags:

| Qualitative flag | Policy action |
| --- | --- |
| `related_party_activity` | `INDEPENDENT_REVIEW` |
| `vendor_bank_detail_change` | `BLOCK` |
| `unusual_non_standard_journal` | `INDEPENDENT_REVIEW` |
| `management_override_indicator` | `BLOCK` |
| `period_end_adjustment` | `INDEPENDENT_REVIEW` |
| `none` | no override |

These responses are synthetic design choices, not claims about universally appropriate professional treatment.

## Independent adjudication oracle

The oracle is an expected-control-action oracle for the synthetic vignettes. It will assign `AUTO_EXECUTE`, `INDEPENDENT_REVIEW`, or `BLOCK` from a separately authored scenario adjudication schedule before either policy runs. It is not a monetary expected-loss model and is not a validated professional-judgement protocol.

Technical and logical independence will be preserved as follows:

- `oracle.py` will not import `policies.py`, policy configuration, threshold values, budget utilisation, or policy outputs.
- Scripted scenario type and step, not policy decisions, will determine aggregation and post-error oracle actions.
- The oracle will contain its own explicit qualitative adjudication table rather than calling the treatment-side override helper.
- The generated dataset will contain the oracle label before evaluation starts.
- A dedicated policy-visible dataframe will be selected before either policy is called. It will exclude `oracle_required_action`, `scenario_id`, `scenario_type`, and `scenario_step`.
- Tests will change both fixed and MCAB treatment configurations and verify oracle labels are unchanged, inspect the oracle module's imports to confirm it does not import policy code or configuration, and verify representative oracle vignettes directly.

This deliberate separation prevents circular scoring. It does not solve construct validity: expert adjudication remains future work.

## Scenario design

The 240 rows will be assembled in an explicit global order:

| Scenario | Planned rows | Expected synthetic pattern |
| --- | ---: | --- |
| Ordinary low risk | 185 | Small, unflagged transactions spread across entities, periods, and accounts |
| Aggregation pressure | 20 | Two ten-row sequences of individually sub-threshold values; scenario-step adjudication begins requiring review part-way through each sequence |
| Qualitative risk | 12 | Low-value examples spanning all five qualitative flags |
| Isolated large | 8 | Unflagged transactions above the fixed threshold, expected to require review |
| Confirmed control-error signal | 1 | A severe flagged row expected to be blocked and to tighten later MCAB authority |
| Post-error accumulation | 14 | Sub-threshold transactions after the signal, with a stricter separately specified oracle schedule |

Ordinary transactions will use seeded variation. Scripted scenarios will preserve their internal order. The generator will assert the row count, uniqueness, allowed categories, and positive amounts.

## Evaluation outcomes

All metrics will be computed from the same ordered dataset and one joined decision table.

### Primary outcomes

1. **Overall consequential failure incidence:** count of rows where the policy returns `AUTO_EXECUTE` while the oracle requires `INDEPENDENT_REVIEW` or `BLOCK`, divided by all evaluated rows.
2. **Conditional miss rate:** the same false-negative count divided by the number of oracle-required escalation rows.
3. **Unauthorised economic exposure:** sum of positive gross transaction `amount` associated with missed escalations. This is an authority-exposure proxy, not realised financial loss.
4. **Intervention burden:** report `INDEPENDENT_REVIEW` and `BLOCK` counts and percentages separately. Their combined count and percentage may be described as non-autonomous intervention burden.

Every rate will be accompanied by its numerator and denominator.

### Secondary outcomes

- **False escalation rate:** policy escalations when the oracle says `AUTO_EXECUTE`, divided by all oracle-`AUTO_EXECUTE` rows.
- **Aggregation-related failures:** consequential failures in `aggregation_pressure` or `post_error_accumulation` scenarios.
- **Qualitative overrides correctly escalated:** count and percentage of flagged rows for which both oracle and policy require escalation.
- `INDEPENDENT_REVIEW` and `BLOCK` counts will remain separate in both decision summaries and public reporting.

The chart will be one three-panel bar figure comparing the two policies on control-failure percentage, unauthorised exposure, and review-burden percentage without placing incompatible units on one axis.

## Sensitivity and edge checks

Sensitivity reporting will separate three designs:

1. **Primary matched A$50,000 comparison:** fixed threshold A$50,000 versus MCAB initial budget A$50,000 (`0.10` safety factor), using the default `0.50` post-error multiplier.
2. **MCAB-only design sensitivity:** hold the fixed comparator at A$50,000 while varying MCAB safety factors `0.05`, `0.10`, and `0.15` and post-error multipliers `0.25`, `0.50`, `0.75`, and `1.00`. Multiplier `1.00` is the no-tightening, aggregation-only MCAB condition.
3. **Matched-budget sensitivity:** for each safety factor, set the fixed threshold equal to the MCAB initial budget and use the default `0.50` post-error multiplier.

The main ordered dataset remains fixed in every condition. Results will be written programmatically to a sensitivity CSV. Tests will also cover threshold boundary values, cumulative exhaustion, repeated small transactions, an unusually large transaction, empty input, deterministic reproduction, and malformed data.

Sensitivity analysis is descriptive. It will show parameter dependence and policy trade-offs; it will not be used to select a retrospectively optimal result.

## Principal validity risks

- The oracle is authored synthetic ground truth and may encode the researcher's assumptions.
- Parameter values, risk-cell granularity, scenario mix, and ordering can materially change results.
- Observed flags are assumed accurate and costless; detection error is not modelled.
- Transaction amounts proxy authority exposure, not realised loss or financial-statement misstatement.
- The simulation omits strategic adaptation, reviewer error, reviewer dependence, processing delay, control cost, and recovery effectiveness.
- Separate account cells can fragment cross-account exposure; a hierarchy is future work.
- A deterministic single run supports reproducibility but not sampling inference or external validity.
