# Materiality-Calibrated Authority Budget prototype

This synthetic research prototype examines a fixed-threshold aggregation problem: individually small transactions can remain below a per-transaction limit while accumulating consequential authority exposure. MCAB is tested here as a stateful design idea that tracks cumulative autonomous authority and prospectively tightens it after a confirmed error. In the authored simulation, MCAB reduces missed escalation and its gross authority-exposure proxy while increasing non-autonomous intervention. The prototype demonstrates an implementable comparison under synthetic assumptions; it does not professionally or empirically validate MCAB.

**Current evidence:** [generated results summary](outputs/results_summary.md) · [decision-level CSV](outputs/policy_decisions.csv) · [comparison chart](outputs/policy_comparison.png)

The results summary is regenerated from the CSV outputs by the demo command and checked against those files by the test suite. Numerical findings are not maintained manually in this README.

## Primary matched A$50,000 results

The following compact table is generated from `outputs/policy_comparison.csv` whenever the demo runs and is validated by the test suite.

<!-- BEGIN GENERATED PRIMARY RESULTS -->
| Policy | Conditional miss rate | Gross authority-exposure proxy | Combined non-autonomous intervention |
|---|---|---|---|
| Fixed threshold | 22/43 (51.16%) | A$167,900 | 21/240 (8.75%) |
| MCAB | 2/43 (4.65%) | A$17,100 | 41/240 (17.08%) |
<!-- END GENERATED PRIMARY RESULTS -->

![Primary synthetic policy comparison](outputs/policy_comparison.png)

## Research problem

A fixed per-transaction approval threshold can treat each transaction in isolation. An agent may therefore execute a series of individually small transactions while cumulative exposure becomes consequential across an account, counterparty, workflow, entity, or reporting period.

Financial-statement materiality concerns whether information or misstatement could influence users of financial statements. Operational authority concerns how much economic value an AI agent may exercise without independent review. MCAB uses a provisional reporting-materiality amount only as an illustrative anchor for an operational authority budget. It is not an ASA 320 formula, an auditing standard, a legal threshold, or professional guidance.

MCAB is defined here as a research design construct that limits cumulative autonomous financial authority within specified risk cells and permits prospective tightening after a confirmed control error.

## Demonstration design

The deterministic synthetic dataset covers procure-to-pay and journal-entry/month-end-close workflows. It contains ordinary activity, repeated sub-threshold sequences, qualitative-risk cases, isolated large transactions, and a later sequence following confirmation of an earlier control error. All entities, accounts, counterparties, periods, and amounts are synthetic.

The policies receive the same ordered transactions and the same qualitative flags:

- **Fixed comparator:** escalates an unflagged transaction only when its amount is strictly above the fixed threshold. It does not retain cumulative exposure.
- **MCAB treatment:** derives an illustrative initial cell budget from a provisional anchor and safety factor, tracks autonomous utilisation by `(entity, reporting_period, workflow, account)`, and prospectively tightens later budgets in the affected entity-workflow scope after a confirmed error.

Exact equality remains within authority. Only autonomously executed amounts consume MCAB authority; reviewed or blocked amounts do not. Tightening retains existing utilisation, affects later decisions only, and remains active for the rest of the demonstration.

All policy values are configurable research parameters. They were selected to make the treatment logic inspectable, not to recommend professional approval limits.

## Independent adjudication oracle

The oracle is a separately implemented expected-control-action schedule for the authored synthetic vignettes. It does not import either policy, consult policy configuration, or observe policy decisions. Policies are passed only operational columns; oracle labels and scenario-only metadata are excluded from their data interface. Tests verify that oracle labels remain unchanged when either policy configuration changes.

In each original aggregation sequence, the independently specified oracle begins requiring escalation one transaction before the default MCAB budget is exceeded. That rule was fixed independently of policy execution. The residual MCAB misses therefore arise from a difference between the oracle's conservative escalation schedule and MCAB's budget-exhaustion rule, not from changed oracle labels. The oracle remains simplified synthetic ground truth rather than a validated professional-judgement protocol.

For the consequential-failure measures, `INDEPENDENT_REVIEW` counts as adequate escalation when the oracle requires either review or blocking: autonomous authority has been removed and the reviewer can subsequently block execution. Review and block counts remain separate, and [the generated confusion table](outputs/action_confusion.csv) preserves action-severity differences.

## Outcomes

The evaluator reports:

- overall consequential failure incidence: missed escalations divided by all transactions;
- conditional miss rate: missed escalations divided by oracle-required escalations;
- unauthorised economic exposure: gross transaction amount associated with missed escalations, used only as an authority-exposure proxy;
- independent-review, block, and combined non-autonomous intervention burden;
- false escalation rate, aggregation-related failures, and qualitative overrides correctly escalated.

Every rate is accompanied by its numerator and denominator. The [generated results summary](outputs/results_summary.md) also explains the qualitative-case denominator and the sparse fixed-policy support between the lower matched-budget thresholds.

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

The final command regenerates:

- `data/synthetic_transactions.csv`;
- `outputs/policy_decisions.csv`;
- `outputs/policy_comparison.csv`;
- `outputs/action_confusion.csv`;
- `outputs/sensitivity_analysis.csv`;
- `outputs/results_summary.md`; and
- `outputs/policy_comparison.png`.

## Interpretation

The current run illustrates a trade-off. In this authored simulation, cumulative authority tracking reduces aggregation-related missed escalations and their associated exposure proxy while increasing non-autonomous intervention. Sensitivity results show that this comparison depends materially on the initial budget and post-error multiplier; more restrictive settings can introduce false escalations without a corresponding reduction in misses.

These simulated results demonstrate that the proposed construct can be implemented, tested, and compared under explicit assumptions. They do not validate MCAB, establish causal effectiveness, show universal superiority, measure realised financial loss, or determine a professionally appropriate threshold.

## Limitations

- The adjudication oracle is authored synthetic ground truth and has not been expert validated.
- Scenario composition, ordering, parameter values, and risk-cell granularity influence the results.
- The fixed-policy sensitivity has sparse transaction support between its lower matched thresholds, as quantified in the generated summary.
- Qualitative flags are assumed to be observed accurately and without cost.
- Gross transaction amount represents authority exposure, not realised loss or financial-statement misstatement.
- Strategic adaptation, reviewer error and dependence, processing delay, recovery effectiveness, and control operating cost are omitted.
- Account-level cells can fragment exposure that might be consequential at a higher hierarchy.
- A single deterministic dataset supports reproducibility, not statistical inference or external validity.
- The proposal itself was unavailable in the project sources, so exact proposal section numbering requires human verification.

## Proposal-to-prototype mapping

| Proposal topic | Prototype evidence |
|---|---|
| Fixed-threshold aggregation weakness | Scripted accumulation scenarios in `generate_data.py` and decision-level outputs |
| MCAB research construct | Configurable state transition and authority cells in `policies.py` |
| Independent expected-action adjudication | Isolated `oracle.py`, restricted policy interface, and direct independence tests |
| Comparative evaluation design | Common evaluator, primary outcomes, sensitivities, confusion table, and chart |
| Reproducibility and research engineering | Fixed seed, generated artifacts, package metadata, tests, and AI-use disclosure |
| §7.2 implementation evidence | Executable local harness and generated evidence suitable for linkage once public |
| Limitations and future validation | Explicit limitations here and proposed research extensions below |

Only §7.2 was identified in the supplied instructions. The human researcher should verify other section references against the final proposal before publication.

## Future research

Proposed extensions include:

- a confidence-based escalation baseline;
- multiple model and reviewer-independence conditions;
- repeated stochastic agent runs;
- expert-validated adjudication; and
- hierarchical statistical analysis across transactions, cells, workflows, agents, and reviewers.

## AI-assisted research engineering

Development responsibilities and validation procedures are disclosed in [AI_USE.md](AI_USE.md). The work is described as human-directed, AI-assisted research engineering; responsibility for the research claims and interpretation remains with the human researcher.

## Publication metadata

Suggested repository description:

> Reproducible synthetic Python evaluation harness comparing fixed transaction controls with a materiality-calibrated cumulative authority budget.

Suggested GitHub topics: `accounting-information-systems`, `auditing-research`, `internal-controls`, `ai-governance`, `reproducible-research`, `synthetic-data`, `python`, `pytest`.

Suggested sentence for proposal §7.2:

> An executable, human-directed, AI-assisted prototype of the MCAB evaluation harness, including synthetic data, independent adjudication, comparator policies, tests and generated outputs, is available at [GITHUB URL].

## Licence

Released under the [MIT License](LICENSE). This prototype is research software and carries no professional assurance or accounting guidance.
