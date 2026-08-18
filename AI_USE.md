# AI-assisted research engineering disclosure

This repository is a **human-directed, AI-assisted implementation** and an example of human-directed, AI-assisted research engineering.

## Responsibilities

The human researcher supplied and retained responsibility for:

- the MCAB research concept and distinction between reporting materiality and operational authority;
- the research questions, claim boundaries, acceptance criteria, and publication decision;
- approval of the four-condition mechanism design, entity anchors, common safety factor, recurrence rules, scenario scaling, sensitivity grids, and anti-tuning rule;
- decisions about how the synthetic results may and may not be interpreted; and
- scholarly responsibility for any proposal integration or later empirical extension.

AI assistance was used to draft and revise Python implementation components, tests, deterministic data generation, output reconciliation, package metadata, the comparison figure, workflow configuration, and documentation. AI assistance also performed source-level reviews and executed the local validation commands. The repository does not call an external language-model API.

Human approval of the concept, assumptions, acceptance criteria, generated evidence, and release direction is distinct from line-by-line human source-code review. This disclosure does not claim that the human researcher personally reviewed every source line.

## Design-revision record

An external methodological review observed that the initial two-policy comparison did not separate cumulative state, entity-relative calibration, and post-error tightening. The findings were checked against the implementation rather than accepted automatically. The human researcher approved a revised design containing:

- a stateless fixed threshold;
- a stateful uniform cumulative cap;
- an entity-calibrated no-tightening MCAB ablation;
- full MCAB with prospective tightening;
- three synthetic entity scales and matched aggregation patterns;
- a non-monetary recurrence oracle; and
- prespecified scenario-subset mechanism comparisons.

The qualitative mappings, entity anchors, amount templates, recurrence boundaries, sensitivity grids, and isolated-significance amount sequence were frozen before the first revised experiment run. They were not altered in response to the resulting policy metrics.

## Supplementary-evaluation workflow

After the original absolute-dollar results were public, the human researcher approved supplementary anchor-relative exposure measures, a five-setting oracle-recurrence sensitivity, an absolute-dollar decomposition, exact interpretation branches, and an anti-retuning rule. AI assistance read the committed artifacts for the Phase 1 dollar decomposition without computing the new scale-relative measures. The complete definitions, alternative interpretations, exact branch rules, and limitations were then committed and pushed publicly as commit `1c4237d5e465092323adeafc19e3578212ca71bb` before formal supplementary computation.

This sequence was human-directed and auditable, but neither blinded nor formally preregistered. The existing dataset, anchors, and dollar decomposition made likely directions inferable, and selection of the supplementary metrics occurred after the original results were known. AI assistance subsequently implemented exact-arithmetic calculations, generated the approved outputs, selected only the predeclared branches, added reconciliation tests, and retained mixed findings without modifying the frozen design.

A subsequent human-directed corrective review identified that the public pre-declaration had not explicitly assigned the Calibration and Tightening branch labels to mechanism-subset populations. AI assistance compared the working interpretation with the public commit, verified row-level isolated-significance, false-escalation, and proportional-scaling explanations, and revised the generated reporting and tests. The conservative correction selects all canonical policy-contrast branches from exact repository-level metrics while retaining mechanism-subset calculations separately. No frozen transaction, decision, oracle label, parameter, metric, branch wording, or mechanism subset was changed.

## Validation record

The revised implementation was checked using:

| Validation | Result |
|---|---|
| Complete pytest suite | 67 passed on Python 3.12.13 |
| Complete deterministic demo | Passed; all documented artifacts regenerated |
| Package dependency check | `pip check` reported no broken requirements |
| Decision-to-summary reconciliation | Passed for four policies, three entities, confusion counts, mechanism subsets, and supplementary tables |
| Independent supplementary reconciliation | A standard-library calculation importing no repository package reconciled four policies, five oracle configurations, and four decomposition partitions |
| Oracle isolation | Behavioural parameter-invariance, forbidden-column, and source-import tests passed |
| Structural design checks | Reference-policy equivalence, pre-signal equivalence, distinct cells, and fresh post-error recurrence tests passed |
| Frozen base integrity | Dataset, base decisions, primary metrics, entity metrics, mechanism, sensitivity, and confusion SHA-256 hashes remained unchanged |
| Consecutive same-environment rerun | All 13 generated README, CSV, Markdown, and PNG artifacts matched one another and the tracked artifacts byte for byte |
| Exact branch application | Repository-level rational comparisons selected Overall A, Calibration B, Tightening A, and Sensitivity B; mechanism-subset values remain separately reported |
| Accounting-analogy boundary | ASA 600 paragraph 35(a) was checked against the official AUASB text and used only as an audit-planning analogy |
| Chart validation | Source values, labels, existence, dimensions, and non-empty rendering tested |
| Visual chart inspection | Completed during AI-assisted release review |
| GitHub Actions workflow | Least-privilege structure checked locally; hosted execution not yet observed |

The original package configuration previously passed a clean repository-local installation smoke test. The revised package and direct dependency versions are unchanged. A second fresh installation was not repeated during this revision because no repository-local wheelhouse was available and network access was outside the approved validation boundary.

The hosted workflow cannot be confirmed until a separately approved commit is pushed and GitHub Actions runs. The presence of the workflow file and badge is not represented here as evidence of a hosted pass.

## Interpretation and review boundaries

- Automated tests establish consistency with encoded rules; they do not validate the rules professionally.
- AI-assisted review can miss implementation or framing errors despite the test suite.
- The oracle and scenarios remain authored rather than independently expert validated.
- Human review of the concept, assumptions, outputs, interpretation, and publication decision does not substitute for future expert adjudication or empirical validation.
- Responsibility for accuracy, interpretation, scholarly use, and publication remains with the human researcher.
