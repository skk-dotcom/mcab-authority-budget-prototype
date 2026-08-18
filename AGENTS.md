# Repository working rules

- Work only within this repository. Do not add remotes, publish, upload, stage, or commit without explicit human approval.
- Treat `RESEARCH_SPEC.md` and the approved gate record as the methodological source of truth. Do not copy personal or proposal-only information into the repository.
- Use Python 3.11+, a `src/` package layout, type hints, concise docstrings, pandas, matplotlib, pytest, and a fixed seed.
- Keep the oracle technically separate from both treatment policies. Policies must not read oracle labels or scenario-only adjudication metadata.
- Generate datasets, metrics, figures, and README result values from code. Never hard-code empirical results.
- Apply identical ordered data and qualitative-override semantics to both policies. Explain any asymmetry as part of the treatment definition.
- Use synthetic names and positive gross transaction magnitudes only. Never add real or confidential data, credentials, or absolute local paths.
- Describe MCAB as an illustrative research design construct, not an audit-standard formula, legal threshold, professional recommendation, or validated control.
- Refer to compensating reversal, containment, or recovery when discussing post-action responses for completed transactions.
- Run focused tests while developing and the complete test and demo commands before each evidence or release gate. Keep claims within the generated evidence.
