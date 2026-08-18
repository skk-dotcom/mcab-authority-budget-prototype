# Implementation plan

## Gate discipline

Functional experiment code, data generation, empirical outputs, and public-facing interpretation will not begin until Gate 1 is explicitly approved. Numerical results will only be reported after code execution.

| Milestone | Work | Verification | Status |
| --- | --- | --- | --- |
| 0. Research design | Inspect local sources/environment; define schema, policies, oracle, scenarios, metrics, sensitivity, risks, and structure; incorporate approved amendments | Human Gate 1 review and amendment check | Complete — Gate 1 approved |
| 1. Core implementation | Add package configuration, domain types, independent oracle, deterministic generator, fixed policy, and MCAB policy | Focused unit tests and source review | Complete |
| 2. Evaluation harness | Add common evaluator, tidy CSV outputs, three-part sensitivity runs, chart, and one-command demo | Dataset/output invariants; rerun checksum comparison | Complete |
| 3. Empirical evidence | Run full tests and experiment; inspect computed metrics and edge/sensitivity behaviour; repair failures | Human Gate 2 review | Complete — Gate 2 approved |
| 4. Release documentation | Finalise README, AI disclosure, licence/package metadata, generated public results, limitations, proposal mapping, and publication instructions | Human Gate 3 review | Complete — Gate 3 approved |
| 5. Final local QA | Recreate environment commands, rerun tests/demo, inspect tree, scan for secrets/private data/absolute paths/remotes, and confirm clean reproducibility | Final status: local delivery only | Complete — final review accepted; local delivery complete; nothing published |

## Planned repository structure

```text
.
├── .gitignore
├── AGENTS.md
├── AI_USE.md
├── DECISIONS.md
├── LICENSE
├── PLAN.md
├── README.md
├── RESEARCH_SPEC.md
├── STATUS.md
├── pyproject.toml
├── data/
│   └── synthetic_transactions.csv
├── outputs/
│   ├── policy_comparison.csv
│   ├── policy_comparison.png
│   ├── policy_decisions.csv
│   ├── action_confusion.csv
│   ├── results_summary.md
│   └── sensitivity_analysis.csv
├── src/
│   └── mcab_prototype/
│       ├── __init__.py
│       ├── domain.py
│       ├── evaluate.py
│       ├── generate_data.py
│       ├── oracle.py
│       ├── policies.py
│       └── run_demo.py
└── tests/
    ├── test_evaluate.py
    ├── test_generate_data.py
    ├── test_oracle.py
    └── test_policies.py
```

No separate `scripts/` directory is planned: the package entry point will run the complete experiment, and an extra wrapper would add no research value. The README's generated result block will be refreshed by the demo command so reported values cannot drift from `policy_comparison.csv`.

## Planned validation sequence after Gate 1

1. Create a project-local virtual environment with the available Python 3.12 runtime.
2. Install the exact dependencies in `requirements.txt`, including the authorised setuptools and wheel build dependencies, and complete a normal editable installation.
3. Run focused tests during each implementation milestone.
4. Run `pytest` for the full suite.
5. Run the complete demo twice and compare generated file hashes where byte-level determinism is expected.
6. Inspect CSV schemas/row counts, reconcile metric numerators to the decision table, and visually inspect the PNG.
7. Present generated evidence at Gate 2 before writing the final interpretive README language.

## Approved implementation invariants

- MCAB cell: `(entity, reporting_period, workflow, account)`.
- Exact equality is within fixed and MCAB authority; projected usage strictly above the threshold or budget escalates.
- Only `AUTO_EXECUTE` amounts consume MCAB authority. Reviewed or blocked amounts do not.
- Confirmed-error tightening is applied after the signal row's decision, retains existing utilisation, and remains active for the affected entity-workflow scope through the demonstration.
- The policy input dataframe excludes oracle labels and all scenario-only metadata.
- Overall failure incidence and conditional miss rate are both reported with numerators and denominators.
- Review and block counts are reported separately, with their sum identified only as combined non-autonomous intervention burden.
- Sensitivity output distinguishes the primary A$50,000 comparison, MCAB-only design sensitivity, and matched-budget sensitivity.
