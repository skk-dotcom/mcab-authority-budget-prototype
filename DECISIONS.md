# Decision log

## D001 — Specification source

**Decision:** Use the supplied project brief as the conceptual source of truth because the empty repository contained no proposal file. Do not seek or copy proposal content from outside the repository.

**Reason:** This respects the repository boundary and avoids importing personal or irrelevant proposal material.

## D002 — Compact package design

**Decision:** Use a `src/` package with small modules for domain types, generation, oracle adjudication, policies, evaluation, and orchestration. Record exact runtime, test, and build dependencies in `requirements.txt`; use `pyproject.toml` for PEP 517 packaging and pytest configuration.

**Reason:** Separation makes oracle independence auditable while keeping the implementation compact and runnable without a notebook or service. Gate 2 release approval authorised the minimal setuptools build backend needed for a normal editable installation.

## D003 — Positive gross amounts

**Decision:** Generate positive transaction magnitudes rather than signed ledger balances.

**Reason:** The requested exposure measure should not be obscured by debit/credit netting. It remains a proxy for authority exercised, not realised loss.

## D004 — Illustrative policy parameters

**Decision:** Use a fixed threshold of A$50,000 and an MCAB base budget of A$500,000 × 0.10 = A$50,000 per `(entity, reporting_period, workflow, account)` cell. A confirmed error applies a prospective 0.50 multiplier within the same `(entity, workflow)` scope.

**Reason:** Equal initial monetary ceilings isolate the addition of cumulative state. The values are simple research parameters and will not be described as prescribed or optimal.

## D005 — Common qualitative treatment

**Decision:** Both treatment policies call the same qualitative-override function. Moderate synthetic flags require independent review; bank-detail change and management-override flags block execution pending resolution.

**Reason:** This controls the qualitative dimension and focuses comparison on aggregation and adaptation.

## D006 — Oracle independence

**Decision:** Assign oracle actions from a separate scenario/step adjudication schedule before policy execution. Duplicate the oracle's qualitative expectations explicitly rather than importing the policy override table. Prevent policies from consuming oracle or scenario-only columns.

**Reason:** Shared policy code would make fair treatment easier, but shared oracle logic would make outcome assessment circular.

## D007 — Budget accounting

**Decision:** Exact equality remains within authority for both policies; projected usage strictly above the threshold or budget escalates. Count only autonomously executed amounts against MCAB utilisation. Independently reviewed or blocked amounts do not consume it. Do not replenish within a reporting period. Recalculate the effective ceiling prospectively after a confirmed error, retaining past utilisation.

**Reason:** MCAB limits autonomous authority, so independently reviewed amounts do not exercise that authority. Retaining history makes tightening prospective without rewriting prior evidence.

## D008 — Metric denominators

**Decision:** Report both overall consequential-failure incidence over all transactions and conditional miss rate over oracle-required escalation transactions. Define false escalation rate over oracle-negative (`AUTO_EXECUTE`) transactions. Report independent-review and block counts and percentages separately; their sum is non-autonomous intervention burden. Always publish numerators and denominators with rates.

**Reason:** Explicit denominators prevent ambiguous interpretation, and separate action counts preserve the difference between review and prevention of execution.

## D009 — Reproducible outputs

**Decision:** Use seed `20260818`, deterministic ordering and serialization, and programmatic generation of data, decisions, metrics, sensitivity results, figure, and the README result table.

**Reason:** This avoids manually transcribed or hard-coded findings and allows byte-level checks where supported.

## D010 — Local Git only

**Decision:** Initialise local Git without staging or committing. Use a per-command `safe.directory` option if required by the sandbox; never change global Git settings or add a remote.

**Reason:** The execution identity differs from the workspace owner, and a command-local override preserves the user's configuration and publication boundary.

## D011 — Proposal mapping

**Decision:** Map prototype components to proposal topics and clearly flag exact section identifiers for human verification because the proposal is unavailable. Use the user-specified §7.2 only for the requested insertion sentence.

**Reason:** Inventing section numbers would undermine reproducibility review and public accuracy.

## D012 — Confirmed-error timing and persistence

**Decision:** A `confirmed_control_error` signal states that an earlier control error was confirmed immediately before that sequence position. The signal row is decided using the pre-existing state; tightening is applied only after that decision, does not alter earlier decisions, retains prior cell utilisation, and persists for later transactions in the affected `(entity, workflow)` scope for the remainder of the run.

**Reason:** This provides an explicit, auditable state transition and prevents retrospective treatment of earlier transactions.

## D013 — Policy data-interface isolation

**Decision:** Construct a policy-visible dataframe that excludes `oracle_required_action`, `scenario_id`, `scenario_type`, and `scenario_step` before calling either policy. Add behavioural parameter-invariance tests for oracle labels and a source-import boundary test for `oracle.py`.

**Reason:** Module separation alone does not prevent label leakage at runtime; the dataframe boundary makes isolation enforceable.

## D014 — Three-part sensitivity design

**Decision:** Separate (a) the primary matched A$50,000 comparison, (b) MCAB-only parameter sensitivity with the fixed threshold held at A$50,000, and (c) matched-budget sensitivity where the fixed threshold equals each MCAB initial budget. Treat post-error multiplier `1.00` as the no-tightening aggregation-only MCAB condition.

**Reason:** This distinguishes the effect of MCAB design parameters from comparisons caused merely by unequal initial authority limits.

## D015 — Exposure terminology

**Decision:** Define unauthorised economic exposure as gross transaction amount associated with missed escalations and describe it as an authority-exposure proxy, not realised financial loss.

**Reason:** The simulation observes transaction authority and control routing, not realised economic outcomes.

## D016 — PEP 517 release packaging

**Decision:** The initial Gate 2 editable-install probe failed because setuptools was absent under the then-approved dependency boundary. After explicit Gate 2 release approval, add pinned setuptools and wheel build dependencies, a PEP 517 build-system section, project metadata, package discovery, and a console entry point. Do not require `PYTHONPATH`.

**Reason:** A conventional `pip install -e .` is more portable and provides a genuine fresh-install test while keeping every dependency repository-local.

## D017 — Generated public results

**Decision:** Generate `outputs/results_summary.md` and `outputs/action_confusion.csv` from current CSV artifacts during every demo run. Tests compare the generated Markdown exactly with a fresh render from those CSVs.

**Reason:** This prevents public result values from drifting through manual transcription and keeps three-action severity visible alongside the binary missed-escalation measure.

## D018 — Sparse threshold support

**Decision:** Preserve the approved dataset and disclose the absence of authored transaction amounts in the interval that would distinguish the A$25,000 and A$50,000 fixed thresholds.

**Reason:** Identical fixed-policy sensitivity results in that interval reflect sparse dataset support, not threshold invariance; adding observations after seeing results would change the approved experiment.

## D019 — Final source line-count deviation

**Decision:** Retain the final implementation at 672 nonblank, non-comment source lines across seven Python modules (807 physical lines), rather than refactor solely to meet the earlier approximate 200–350-line aim.

**Reason:** The count includes explicit scenario construction, policy decision metadata, three sensitivity designs, charting, action confusion, CSV-derived public reporting, and README/result validation. The implementation remains separated by responsibility, readable, and without duplicated treatment-policy logic. A late compaction would add reproducibility risk after empirical approval without improving the research demonstration proportionately.

## D020 — Release dependency pinning scope

**Decision:** Keep direct dependencies version-pinned without adding a transitive dependency lock file. The documented fresh-install smoke test and `pip check` passed, and deterministic output hashes were verified. Defer a fully hashed, platform-specific lock file to a future formal release.

**Reason:** Maintaining such a lock across supported platforms would add maintenance and cross-platform complexity disproportionate to this minimal prototype. The current direct pins and recorded validation provide an appropriate reproducibility boundary for the local research demonstration.
