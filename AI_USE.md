# AI-assisted development disclosure

This repository is a **human-directed, AI-assisted implementation** and an example of human-directed, AI-assisted research engineering.

## Responsibilities

The human researcher supplied and retained responsibility for:

- the MCAB research concept and research question;
- the distinction between reporting materiality and operational authority;
- requirements, approval gates, acceptance criteria, and release amendments;
- decisions about what claims the simulation may and may not support; and
- final interpretation, proposal integration, publication, and scholarly responsibility.

AI-assisted coding was used to draft and revise implementation components, tests, generated-output logic, package metadata, and documentation. The resulting code was executed locally, tests were run, failures were repaired, and generated artifacts were checked against explicit acceptance criteria. No external language-model API is called by the repository.

## Initial specification summary

The human-directed specification requested a compact Python 3.11+ repository that:

- generates deterministic synthetic financial transactions across two workflow families;
- compares a fixed monetary and qualitative policy with a stateful, aggregation-aware MCAB policy;
- uses a logically and technically independent synthetic adjudication oracle;
- measures missed escalations, gross authority-exposure proxy, intervention burden, false escalations, aggregation failures, and qualitative overrides;
- includes sensitivity analysis, tests, generated CSV outputs, a chart, restrained academic documentation, and publication safeguards; and
- proceeds through explicit research-design, empirical-evidence, and local-release approval gates.

The full private proposal was not present in the repository and was not sought outside it. Only non-personal methodological content from the supplied specification was used.

## Major implementation decisions

- Use a fixed seed and an ordered 240-row synthetic dataset with positive gross transaction magnitudes.
- Give both policies the same qualitative override function while keeping the oracle's adjudication table separate.
- Restrict policy inputs to operational columns so oracle labels and scenario metadata cannot leak into decisions.
- Match the primary fixed threshold and initial MCAB budget at A$50,000, while labelling all parameters illustrative.
- Track MCAB utilisation by entity, reporting period, workflow, and account.
- Apply confirmed-error tightening only after the signal row, retain existing utilisation, and keep tightening active for later affected transactions.
- Treat review as adequate removal of autonomous authority for the binary consequential-failure measure while preserving full three-action confusion counts.
- Generate the public results summary from CSV artifacts and validate it against those artifacts.
- Use a PEP 517 setuptools package and exact dependency versions for a reproducible local installation.

Further methodological reasoning and amendments are recorded in `RESEARCH_SPEC.md` and `DECISIONS.md`.

## Validation commands

Portable reproduction commands are documented in `README.md`. The principal validation sequence is:

```text
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest
python -m mcab_prototype.run_demo
python -m pip check
```

Validation included:

- clean execution of the complete pytest suite;
- package installation and demonstration execution in a second temporary virtual environment;
- consecutive-run SHA-256 comparison of generated artifacts;
- reconciliation of metric numerators, denominators, and exposure sums to decision rows;
- behavioural and import-boundary tests for oracle independence;
- exact comparison of the generated Markdown results summary with the current CSVs;
- visual inspection of the comparison chart; and
- scans for credentials, personal information, absolute paths, Git remotes, and unintended publication state.

## Known limitations

- The oracle and scenario schedule remain authored synthetic assumptions rather than expert-validated professional judgements.
- The fixed dataset offers sparse support for some threshold comparisons.
- One deterministic run cannot establish causal effectiveness, statistical generalisability, or external validity.
- The prototype omits reviewer error, strategic behaviour, operating cost, latency, and realised recovery outcomes.
- AI assistance can introduce implementation or framing errors despite tests; human code and research review remain necessary.

## Human review checklist

- [ ] Verify that the final proposal's terminology and section numbering match the repository.
- [ ] Confirm that the independently authored oracle rules are defensible for the intended research vignette.
- [ ] Review parameter choices and sensitivity interpretation without treating them as prescribed thresholds.
- [ ] Review the source code, tests, generated decision rows, confusion counts, and chart.
- [ ] Confirm that the generated results summary matches the CSV outputs after any future change.
- [ ] Obtain expert adjudication and any required ethics or governance review before empirical extension.
- [ ] Replace `[GITHUB URL]` only after manual publication.
- [ ] Confirm no personal, confidential, proprietary, or credential-bearing material is added before publication.

Responsibility for the accuracy, interpretation, scholarly use, and publication of this repository remains with the human researcher.
