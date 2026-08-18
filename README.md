# Materiality-Calibrated Authority Budget prototype

[![Tests](https://github.com/skk-dotcom/mcab-authority-budget-prototype/actions/workflows/tests.yml/badge.svg)](https://github.com/skk-dotcom/mcab-authority-budget-prototype/actions/workflows/tests.yml)

This repository is a synthetic research prototype for examining operational authority controls. It illustrates how repeated transactions can remain individually below a fixed threshold while accumulating within a risk cell, and how a materiality-calibrated authority budget can vary across differently scaled synthetic entities. It does not validate MCAB professionally or empirically.

## Research problem

A stateless per-transaction threshold cannot recognise cumulative exposure from repeated small transactions. Adding cumulative state can address that specific weakness, but it does not by itself demonstrate the value of calibrating authority to entity scale. This prototype therefore separates cumulative state, entity-relative calibration, and prospective post-error tightening into four policy conditions.

## Financial-statement materiality and operational authority

Financial-statement materiality concerns whether information or misstatement could influence users of financial statements. Operational authority concerns how much economic value an AI agent may exercise without independent review. MCAB uses illustrative materiality anchors to calibrate operational authority budgets. It is not an ASA 320 formula, an auditing standard, a legal approval threshold, or professional guidance.

## MCAB as a research construct

MCAB is defined here as a stateful research design construct that limits cumulative autonomous authority within specified risk cells. Full MCAB can also tighten later budgets after confirmation of an earlier control error. Only autonomously executed amounts consume authority; independently reviewed or blocked amounts do not.

## Synthetic design and entity scales

The deterministic dataset contains 270 positive-amount transactions across procure-to-pay and journal-entry/month-end-close workflows. All identifiers and values are synthetic.

| Entity | Illustrative anchor | Scenario scale | Initial MCAB budget |
|---|---:|---:|---:|
| `ENTITY_SMALL` | A$250,000 | 0.5 | A$25,000 |
| `ENTITY_REFERENCE` | A$500,000 | 1.0 | A$50,000 |
| `ENTITY_LARGE` | A$1,000,000 | 2.0 | A$100,000 |

The common safety factor is `0.10`. The uniform cumulative cap is A$50,000 and therefore matches MCAB for `ENTITY_REFERENCE`. The cumulative risk cell is `(entity, reporting_period, workflow, account, counterparty)`.

Matched aggregation and post-error amount templates are multiplied by the entity scale factors. Qualitative and isolated-significance cases are kept outside the mechanism-identification subsets. Parameters and templates were frozen before revised execution and were not altered in response to the results.

## Policy conditions and mechanism decomposition

| Condition | Cumulative state | Entity calibration | Prospective tightening |
|---|---:|---:|---:|
| Fixed per-transaction threshold | No | No | No |
| Uniform cumulative cap | Yes | No | No |
| MCAB no-tightening ablation | Yes | Yes | No |
| Full MCAB | Yes | Yes | Yes |

The prespecified mechanism comparisons are deliberately narrower than the repository-level comparison:

- fixed threshold → uniform cap uses matched pre-error aggregation rows;
- uniform cap → MCAB no tightening uses those rows separately for each entity; and
- MCAB no tightening → full MCAB uses post-error rows only.

Overall metric differences are descriptive and are not presented as additive mechanism effects.

## Independent oracle and remaining dependence

The oracle applies a separately authored qualitative mapping and non-monetary recurrence rules. In matched pre-error aggregation cells, review begins at occurrence six. After a confirmed control error, later transactions in a fresh post-error cell require review from occurrence three. The signal row affects later adjudication only and does not count as a post-error occurrence.

The oracle module imports no policy implementation or configuration and does not use fixed thresholds, cumulative caps, entity anchors, safety factors, tightening multipliers, policy decisions, or scenario-step boundaries. Policies receive no scenario identifiers, scenario labels, steps, or oracle actions.

The oracle is procedurally isolated and does not use policy monetary parameters. However, both the oracle and the synthetic scenarios remain authored research-design components and have not been independently expert validated.

## Evaluation metrics

The primary measures are:

- overall consequential-failure incidence: missed escalations divided by all transactions;
- conditional miss rate: missed escalations divided by oracle-required escalation transactions;
- gross authority-exposure proxy: gross amount associated with missed escalations; and
- review, block, and combined non-autonomous intervention burden.

Secondary outputs include false escalation rate, aggregation-related failures, qualitative cases correctly escalated, three-action confusion counts, results by entity, sensitivity analysis, and prespecified mechanism decomposition. Every rate is accompanied by its numerator and denominator.

`INDEPENDENT_REVIEW` counts as adequate escalation for the binary miss measure when the oracle requires review or blocking because autonomous authority has been removed. Review and block remain separate in the generated tables.

## Illustrative comparison under authored aggregation scenarios

[The complete generated results summary](outputs/results_summary.md) reports all four conditions, entity results, action confusion, and mechanism subsets. The compact table below and the chart use repository-level descriptive results; the no-tightening ablation remains visible in the generated summary and decomposition output.

<!-- BEGIN GENERATED PRIMARY RESULTS -->
| Policy | Conditional miss rate | Gross authority-exposure proxy | Combined non-autonomous intervention |
|---|---|---|---|
| Fixed threshold | 54/84 (64.29%) | A$485,975 | 30/270 (11.11%) |
| Uniform cumulative cap | 25/84 (29.76%) | A$122,725 | 64/270 (23.70%) |
| Full MCAB | 10/84 (11.90%) | A$317,550 | 74/270 (27.41%) |

In this authored run, the lowest miss count occurs under Full MCAB, the lowest exposure proxy under Uniform cumulative cap, and the lowest intervention burden under Fixed threshold. These descriptive outcomes do not define a universal policy ranking.
<!-- END GENERATED PRIMARY RESULTS -->

![Descriptive synthetic policy comparison](outputs/policy_comparison.png)

The table's conditional rate uses only oracle-required escalations as its denominator. The chart's failure-incidence percentage uses all 270 transactions. The values therefore answer different questions and should not be compared as if they shared a denominator.

## Sensitivity and ablation analysis

The generated sensitivity table varies fixed thresholds, uniform cumulative caps, MCAB safety factors, and full-MCAB tightening multipliers over predeclared grids. It also includes matched-reference conditions in which the uniform cap equals the reference entity's MCAB budget. Multiplier `1.00` represents no tightening.

Sensitivity analysis is descriptive. It is not used to select a preferred result after observing the experiment.

## Installation and reproduction

Python 3.11 or later is required. No external service, API key, database, or real company data is used.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m mcab_prototype.run_demo
```

### POSIX shell

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
.venv/bin/python -m pytest
.venv/bin/python -m mcab_prototype.run_demo
```

The demo regenerates the synthetic dataset, decision-level policy output, repository- and entity-level metrics, mechanism decomposition, sensitivity table, action confusion table, generated Markdown summary, README results block, and chart.

## Limitations

- The oracle and synthetic scenarios are authored and have not been independently expert validated.
- Entity anchors, the safety factor, recurrence counts, cell granularity, scenario order, and sensitivity grids are illustrative choices.
- Proportional entity scaling and authored matched scenarios are constructive design choices. The calibration comparison illustrates policy behaviour under this design and does not empirically validate the selected anchors or scale ratios.
- Isolated-significance judgements remain authored and are excluded from mechanism decomposition.
- The frozen dataset has no individual amounts above A$25,000 and at or below A$50,000, so the fixed-threshold sensitivity has sparse support in that interval.
- Qualitative flags are assumed to be observed accurately and without cost.
- Gross transaction amount represents authority exposure, not realised loss or financial-statement misstatement.
- Reviewer error and dependence, strategic adaptation, delay, operating cost, containment, recovery, and realised outcomes are omitted.
- One deterministic dataset supports reproducibility, not statistical inference, causal attribution, external validity, or generalisation to real organisations or autonomous agents.
- A committed PNG may render differently across operating systems because the complete font and rendering stack is not pinned; tests validate source values and rendering structure instead of cross-platform byte identity.

## Future research

Proposed extensions include a confidence-based escalation baseline, multiple model and reviewer-independence conditions, repeated stochastic agent runs, expert-validated adjudication, and hierarchical statistical analysis across transactions, cells, workflows, agents, and reviewers.

## AI-assisted research engineering

Development responsibilities and validation procedures are disclosed in [AI_USE.md](AI_USE.md). This repository is a human-directed, AI-assisted implementation; responsibility for assumptions, interpretation, and scholarly use remains with the human researcher.

## Licence

Released under the [MIT License](LICENSE). This research software provides no professional assurance or accounting guidance.
