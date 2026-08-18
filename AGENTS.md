# Contributor guidance

- Treat `RESEARCH_SPEC.md` as the current methodological source of truth.
- Preserve the frozen entity anchors, amount templates, qualitative mappings, recurrence rules, and sensitivity grids unless a documented research-design revision is approved.
- Keep the oracle separate from policy code and monetary policy parameters. Policies must never receive oracle labels or scenario-only adjudication fields.
- Generate datasets, summaries, figures, and README result values from code; never hand-edit empirical values.
- Apply identical ordered data and qualitative semantics to every policy condition.
- Use only synthetic identifiers and positive gross transaction magnitudes. Do not add real, confidential, personal, or credential-bearing data.
- Describe results as an authored synthetic demonstration, not professional guidance, a validated threshold, causal evidence, or proof of superiority.
- Run focused tests during changes and the complete test and demo commands before proposing a release.
