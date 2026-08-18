"""Common evaluation, mechanism decomposition, sensitivity, and charting."""

import os
from pathlib import Path

import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib"))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from .domain import Action, POLICY_VISIBLE_COLUMNS
from .policies import (
    CumulativeCapConfig,
    CumulativeCapPolicy,
    FixedPolicyConfig,
    FixedThresholdPolicy,
    MCABConfig,
    MCABPolicy,
)


POLICY_ORDER = ("fixed", "uniform_cap", "mcab_no_tightening", "mcab_full")
ENTITY_ORDER = ("ENTITY_SMALL", "ENTITY_REFERENCE", "ENTITY_LARGE")
POLICY_LABELS = {
    "fixed": "Fixed threshold",
    "uniform_cap": "Uniform cumulative cap",
    "mcab_no_tightening": "MCAB no tightening",
    "mcab_full": "Full MCAB",
}
PRIMARY_CHART_POLICIES = ("fixed", "uniform_cap", "mcab_full")
MECHANISM_LABELS = {
    "statefulness": "Statefulness",
    "entity_relative_calibration": "Entity-relative calibration",
    "prospective_error_tightening": "Prospective error tightening",
}


def apply_policies(
    transactions: pd.DataFrame,
    fixed_config: FixedPolicyConfig = FixedPolicyConfig(),
    cap_config: CumulativeCapConfig = CumulativeCapConfig(),
    no_tightening_config: MCABConfig = MCABConfig(post_error_multiplier=1.0),
    full_mcab_config: MCABConfig = MCABConfig(post_error_multiplier=0.50),
) -> pd.DataFrame:
    """Run all policy conditions on one ordered, restricted dataframe."""

    policy_input = transactions.loc[:, POLICY_VISIBLE_COLUMNS].copy()
    policy_runs = {
        "fixed": FixedThresholdPolicy(fixed_config).run(policy_input),
        "uniform_cap": CumulativeCapPolicy(cap_config).run(policy_input),
        "mcab_no_tightening": MCABPolicy(no_tightening_config).run(policy_input),
        "mcab_full": MCABPolicy(full_mcab_config).run(policy_input),
    }
    prefixed: list[pd.DataFrame] = []
    expected_ids = transactions["transaction_id"].to_numpy()
    for policy in POLICY_ORDER:
        result = policy_runs[policy]
        if not (result["transaction_id"].to_numpy() == expected_ids).all():
            raise ValueError(f"{policy} decision order changed")
        prefixed.append(result.add_prefix(f"{policy}_"))
    return pd.concat([transactions.reset_index(drop=True), *prefixed], axis=1)


def summarise_policy(decisions: pd.DataFrame, policy: str) -> dict[str, object]:
    """Compute transparent metrics for one policy over supplied rows."""

    action = decisions[f"{policy}_action"]
    oracle = decisions["oracle_required_action"]
    oracle_escalation = oracle.ne(Action.AUTO_EXECUTE.value)
    false_negative = action.eq(Action.AUTO_EXECUTE.value) & oracle_escalation
    oracle_auto = ~oracle_escalation
    intervention = action.ne(Action.AUTO_EXECUTE.value)
    false_escalation = intervention & oracle_auto
    qualitative = decisions["qualitative_flag"].ne("none")
    aggregation = decisions["scenario_type"].isin(["aggregation_pressure", "post_error_accumulation"])
    total = len(decisions)
    escalation_n = int(oracle_escalation.sum())
    miss_n = int(false_negative.sum())
    oracle_auto_n = int(oracle_auto.sum())
    review_n = int(action.eq(Action.INDEPENDENT_REVIEW.value).sum())
    block_n = int(action.eq(Action.BLOCK.value).sum())
    qualitative_n = int(qualitative.sum())
    qualitative_correct_n = int((qualitative & intervention & oracle_escalation).sum())

    def pct(numerator: int, denominator: int) -> float:
        return 100.0 * numerator / denominator if denominator else 0.0

    return {
        "policy": policy,
        "transactions_n": total,
        "oracle_escalations_n": escalation_n,
        "consequential_failures_n": miss_n,
        "overall_failure_numerator": miss_n,
        "overall_failure_denominator": total,
        "overall_failure_incidence_pct": pct(miss_n, total),
        "conditional_miss_numerator": miss_n,
        "conditional_miss_denominator": escalation_n,
        "conditional_miss_rate_pct": pct(miss_n, escalation_n),
        "unauthorised_economic_exposure": float(decisions.loc[false_negative, "amount"].sum()),
        "independent_review_n": review_n,
        "independent_review_denominator": total,
        "independent_review_pct": pct(review_n, total),
        "block_n": block_n,
        "block_denominator": total,
        "block_pct": pct(block_n, total),
        "non_autonomous_intervention_n": review_n + block_n,
        "non_autonomous_intervention_denominator": total,
        "non_autonomous_intervention_pct": pct(review_n + block_n, total),
        "false_escalations_n": int(false_escalation.sum()),
        "false_escalation_denominator": oracle_auto_n,
        "false_escalation_rate_pct": pct(int(false_escalation.sum()), oracle_auto_n),
        "aggregation_failures_n": int((false_negative & aggregation).sum()),
        "qualitative_override_cases_n": qualitative_n,
        "qualitative_correctly_escalated_n": qualitative_correct_n,
        "qualitative_correctly_escalated_pct": pct(qualitative_correct_n, qualitative_n),
    }


def compare_policies(decisions: pd.DataFrame) -> pd.DataFrame:
    """Return repository-level metrics for all four policy conditions."""

    return pd.DataFrame([summarise_policy(decisions, policy) for policy in POLICY_ORDER])


def compare_policies_by_entity(decisions: pd.DataFrame) -> pd.DataFrame:
    """Return the same metrics separately for every synthetic entity."""

    rows: list[dict[str, object]] = []
    for entity in ENTITY_ORDER:
        subset = decisions[decisions["entity"].eq(entity)]
        for policy in POLICY_ORDER:
            rows.append({"entity": entity, **summarise_policy(subset, policy)})
    return pd.DataFrame(rows)


def action_confusion(decisions: pd.DataFrame) -> pd.DataFrame:
    """Return complete policy-versus-oracle three-action counts."""

    actions = [action.value for action in Action]
    rows: list[dict[str, object]] = []
    for policy in POLICY_ORDER:
        counts = pd.crosstab(decisions["oracle_required_action"], decisions[f"{policy}_action"])
        for oracle_action in actions:
            for policy_action in actions:
                count = int(counts.get(policy_action, pd.Series(dtype=int)).get(oracle_action, 0))
                rows.append({
                    "policy": policy,
                    "oracle_action": oracle_action,
                    "policy_action": policy_action,
                    "count": count,
                })
    return pd.DataFrame(rows)


def _mechanism_pair(
    subset: pd.DataFrame,
    *,
    mechanism: str,
    subset_name: str,
    entity: str,
    baseline_policy: str,
    comparison_policy: str,
) -> dict[str, object]:
    baseline = summarise_policy(subset, baseline_policy)
    comparison = summarise_policy(subset, comparison_policy)
    disagreements = int(
        subset[f"{baseline_policy}_action"].ne(subset[f"{comparison_policy}_action"]).sum()
    )
    row: dict[str, object] = {
        "mechanism": mechanism,
        "subset": subset_name,
        "entity": entity,
        "baseline_policy": baseline_policy,
        "comparison_policy": comparison_policy,
        "transactions_n": len(subset),
        "oracle_escalations_n": baseline["oracle_escalations_n"],
        "decision_disagreements_n": disagreements,
    }
    metric_names = (
        "consequential_failures_n",
        "overall_failure_incidence_pct",
        "conditional_miss_rate_pct",
        "unauthorised_economic_exposure",
        "non_autonomous_intervention_n",
        "false_escalations_n",
    )
    for metric in metric_names:
        baseline_value = baseline[metric]
        comparison_value = comparison[metric]
        row[f"baseline_{metric}"] = baseline_value
        row[f"comparison_{metric}"] = comparison_value
        row[f"difference_{metric}"] = float(comparison_value) - float(baseline_value)
    return row


def mechanism_decomposition(decisions: pd.DataFrame) -> pd.DataFrame:
    """Compare mechanisms only on prespecified scenario subsets."""

    rows: list[dict[str, object]] = []
    pre_error = decisions[decisions["scenario_type"].eq("aggregation_pressure")]
    rows.append(_mechanism_pair(
        pre_error,
        mechanism="statefulness",
        subset_name="matched_pre_error_aggregation",
        entity="ALL",
        baseline_policy="fixed",
        comparison_policy="uniform_cap",
    ))
    for entity in ENTITY_ORDER:
        rows.append(_mechanism_pair(
            pre_error[pre_error["entity"].eq(entity)],
            mechanism="entity_relative_calibration",
            subset_name="matched_pre_error_aggregation",
            entity=entity,
            baseline_policy="uniform_cap",
            comparison_policy="mcab_no_tightening",
        ))
    post_error = decisions[decisions["scenario_type"].eq("post_error_accumulation")]
    rows.append(_mechanism_pair(
        post_error,
        mechanism="prospective_error_tightening",
        subset_name="post_error_rows_only",
        entity="ALL",
        baseline_policy="mcab_no_tightening",
        comparison_policy="mcab_full",
    ))
    return pd.DataFrame(rows)


def sensitivity_analysis(transactions: pd.DataFrame) -> pd.DataFrame:
    """Run the frozen primary design and predeclared one-factor grids."""

    rows: list[dict[str, object]] = []

    def add_condition(
        analysis: str,
        condition: str,
        *,
        fixed_threshold: float = 50_000.0,
        uniform_cap: float = 50_000.0,
        safety_factor: float = 0.10,
        full_multiplier: float = 0.50,
    ) -> None:
        decisions = apply_policies(
            transactions,
            FixedPolicyConfig(fixed_threshold),
            CumulativeCapConfig(uniform_cap),
            MCABConfig(safety_factor=safety_factor, post_error_multiplier=1.0),
            MCABConfig(safety_factor=safety_factor, post_error_multiplier=full_multiplier),
        )
        for policy in POLICY_ORDER:
            rows.append({
                "analysis": analysis,
                "condition": condition,
                "fixed_threshold": fixed_threshold,
                "uniform_cap": uniform_cap,
                "mcab_safety_factor": safety_factor,
                "reference_mcab_budget": 500_000.0 * safety_factor,
                "full_post_error_multiplier": full_multiplier,
                **summarise_policy(decisions, policy),
            })

    add_condition("primary_frozen", "default")
    for threshold in (25_000.0, 50_000.0, 100_000.0):
        add_condition("fixed_threshold_grid", f"fixed_{threshold:.0f}", fixed_threshold=threshold)
    for cap in (25_000.0, 50_000.0, 100_000.0):
        add_condition("uniform_cap_grid", f"cap_{cap:.0f}", uniform_cap=cap)
    for safety in (0.05, 0.10, 0.15):
        add_condition("mcab_safety_grid", f"safety_{safety:.2f}", safety_factor=safety)
    for multiplier in (0.25, 0.50, 0.75, 1.00):
        add_condition("tightening_grid", f"multiplier_{multiplier:.2f}", full_multiplier=multiplier)
    for safety in (0.05, 0.10, 0.15):
        reference_budget = 500_000.0 * safety
        add_condition(
            "matched_reference_grid",
            f"safety_{safety:.2f}_cap_{reference_budget:.0f}",
            uniform_cap=reference_budget,
            safety_factor=safety,
        )
    return pd.DataFrame(rows)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


README_RESULTS_START = "<!-- BEGIN GENERATED PRIMARY RESULTS -->"
README_RESULTS_END = "<!-- END GENERATED PRIMARY RESULTS -->"


def readme_primary_results_text(comparison_path: Path) -> str:
    """Render the compact public comparison from repository-level metrics."""

    metrics = pd.read_csv(comparison_path).set_index("policy")
    rows = []
    for policy in PRIMARY_CHART_POLICIES:
        row = metrics.loc[policy]
        rows.append([
            POLICY_LABELS[policy],
            f"{int(row['conditional_miss_numerator'])}/{int(row['conditional_miss_denominator'])} ({row['conditional_miss_rate_pct']:.2f}%)",
            f"A${row['unauthorised_economic_exposure']:,.0f}",
            f"{int(row['non_autonomous_intervention_n'])}/{int(row['non_autonomous_intervention_denominator'])} ({row['non_autonomous_intervention_pct']:.2f}%)",
        ])
    table = _markdown_table(
        ["Policy", "Conditional miss rate", "Gross authority-exposure proxy", "Combined non-autonomous intervention"],
        rows,
    )
    lowest_misses = POLICY_LABELS[str(metrics["consequential_failures_n"].idxmin())]
    lowest_exposure = POLICY_LABELS[str(metrics["unauthorised_economic_exposure"].idxmin())]
    lowest_intervention = POLICY_LABELS[str(metrics["non_autonomous_intervention_n"].idxmin())]
    interpretation = (
        f"In this authored run, the lowest miss count occurs under {lowest_misses}, "
        f"the lowest exposure proxy under {lowest_exposure}, and the lowest intervention burden under "
        f"{lowest_intervention}. These descriptive outcomes do not define a universal policy ranking."
    )
    return f"{table}\n\n{interpretation}"


def write_and_validate_readme_results(readme_path: Path, comparison_path: Path) -> None:
    """Replace the delimited README table and verify it against the CSV."""

    readme = readme_path.read_text(encoding="utf-8")
    if readme.count(README_RESULTS_START) != 1 or readme.count(README_RESULTS_END) != 1:
        raise ValueError("README must contain exactly one generated-results block")
    before, remainder = readme.split(README_RESULTS_START, maxsplit=1)
    _, after = remainder.split(README_RESULTS_END, maxsplit=1)
    generated = readme_primary_results_text(comparison_path)
    updated = f"{before}{README_RESULTS_START}\n{generated}\n{README_RESULTS_END}{after}"
    readme_path.write_text(updated, encoding="utf-8", newline="\n")
    if f"{README_RESULTS_START}\n{generated}\n{README_RESULTS_END}" not in readme_path.read_text(encoding="utf-8"):
        raise ValueError("README primary results do not match policy_comparison.csv")


def results_summary_text(
    decisions_path: Path,
    comparison_path: Path,
    entity_path: Path,
    mechanism_path: Path,
    confusion_path: Path,
) -> str:
    """Render public result values from generated summary CSV artifacts."""

    decisions = pd.read_csv(decisions_path)
    metrics = pd.read_csv(comparison_path).set_index("policy")
    entities = pd.read_csv(entity_path)
    mechanisms = pd.read_csv(mechanism_path)
    confusion = pd.read_csv(confusion_path)
    qualitative_scenarios = int(decisions["scenario_type"].eq("qualitative_risk").sum())
    confirmed_error_flags = int(
        (decisions["scenario_type"].eq("confirmed_error_signal") & decisions["qualitative_flag"].ne("none")).sum()
    )

    primary_rows: list[list[str]] = []
    secondary_rows: list[list[str]] = []
    for policy in POLICY_ORDER:
        row = metrics.loc[policy]
        primary_rows.append([
            POLICY_LABELS[policy],
            f"{int(row['overall_failure_numerator'])}/{int(row['overall_failure_denominator'])} ({row['overall_failure_incidence_pct']:.2f}%)",
            f"{int(row['conditional_miss_numerator'])}/{int(row['conditional_miss_denominator'])} ({row['conditional_miss_rate_pct']:.2f}%)",
            f"A${row['unauthorised_economic_exposure']:,.0f}",
            f"{int(row['independent_review_n'])}/{int(row['independent_review_denominator'])}",
            f"{int(row['block_n'])}/{int(row['block_denominator'])}",
            f"{int(row['non_autonomous_intervention_n'])}/{int(row['non_autonomous_intervention_denominator'])} ({row['non_autonomous_intervention_pct']:.2f}%)",
        ])
        secondary_rows.append([
            POLICY_LABELS[policy],
            f"{int(row['false_escalations_n'])}/{int(row['false_escalation_denominator'])} ({row['false_escalation_rate_pct']:.2f}%)",
            str(int(row["aggregation_failures_n"])),
            f"{int(row['qualitative_correctly_escalated_n'])}/{int(row['qualitative_override_cases_n'])} ({row['qualitative_correctly_escalated_pct']:.2f}%)",
        ])

    entity_rows: list[list[str]] = []
    for row in entities.itertuples(index=False):
        entity_rows.append([
            row.entity,
            POLICY_LABELS[row.policy],
            f"{int(row.conditional_miss_numerator)}/{int(row.conditional_miss_denominator)} ({row.conditional_miss_rate_pct:.2f}%)",
            f"A${row.unauthorised_economic_exposure:,.0f}",
            f"{int(row.non_autonomous_intervention_n)}/{int(row.non_autonomous_intervention_denominator)}",
        ])

    mechanism_rows: list[list[str]] = []
    for row in mechanisms.itertuples(index=False):
        mechanism_rows.append([
            MECHANISM_LABELS[row.mechanism],
            row.entity,
            f"{POLICY_LABELS[row.baseline_policy]} → {POLICY_LABELS[row.comparison_policy]}",
            str(int(row.transactions_n)),
            f"{int(row.baseline_consequential_failures_n)} → {int(row.comparison_consequential_failures_n)}",
            f"A${row.baseline_unauthorised_economic_exposure:,.0f} → A${row.comparison_unauthorised_economic_exposure:,.0f}",
            f"{int(row.baseline_non_autonomous_intervention_n)} → {int(row.comparison_non_autonomous_intervention_n)}",
        ])

    confusion_rows: list[list[str]] = []
    for policy in POLICY_ORDER:
        subset = confusion[confusion["policy"].eq(policy)]
        for oracle_action in [action.value for action in Action]:
            counts = subset[subset["oracle_action"].eq(oracle_action)].set_index("policy_action")["count"]
            confusion_rows.append([
                POLICY_LABELS[policy],
                oracle_action,
                str(int(counts.get(Action.AUTO_EXECUTE.value, 0))),
                str(int(counts.get(Action.INDEPENDENT_REVIEW.value, 0))),
                str(int(counts.get(Action.BLOCK.value, 0))),
            ])

    sections = [
        "# Generated results summary",
        "",
        "> Generated by `python -m mcab_prototype.run_demo` from current CSV outputs. Do not edit numerical values manually.",
        "",
        "## Repository-level descriptive results",
        "",
        _markdown_table(
            ["Policy", "Overall failure incidence", "Conditional miss rate", "Gross authority-exposure proxy", "Review", "Block", "Combined intervention"],
            primary_rows,
        ),
        "",
        "Overall failure incidence uses all transactions as its denominator. Conditional miss rate uses only oracle-required escalation rows; the two percentages therefore answer different questions.",
        "",
        "The exposure measure is gross transaction amount associated with missed escalations. It is an authority-exposure proxy, not realised financial loss.",
        "",
        "## Secondary outcomes",
        "",
        _markdown_table(["Policy", "False escalations", "Aggregation failures", "Qualitative cases correctly escalated"], secondary_rows),
        "",
        f"The qualitative denominator contains {qualitative_scenarios} qualitative-risk rows plus {confirmed_error_flags} confirmed-error signals carrying management-override flags.",
        "",
        "## Results by entity",
        "",
        _markdown_table(["Entity", "Policy", "Conditional miss rate", "Exposure proxy", "Combined intervention"], entity_rows),
        "",
        "## Prespecified mechanism decomposition",
        "",
        _markdown_table(["Mechanism", "Entity", "Comparison", "Subset rows", "Failures", "Exposure proxy", "Interventions"], mechanism_rows),
        "",
        "Mechanism rows use only the prespecified scenario subsets. Repository-level differences above are descriptive and are not treated as additive mechanism effects.",
        "",
        "## Action confusion counts",
        "",
        _markdown_table(["Policy", "Oracle action", "Policy AUTO_EXECUTE", "Policy INDEPENDENT_REVIEW", "Policy BLOCK"], confusion_rows),
        "",
        "For binary missed-escalation metrics, review is adequate escalation when the oracle requires review or blocking because autonomous authority is removed. The confusion table retains severity differences.",
        "",
        "The oracle is procedurally isolated and does not use policy monetary parameters. The oracle and scenarios remain authored research-design components and have not been independently expert validated.",
        "",
        "These tables are simulated evidence from a deterministic demonstration. They do not validate MCAB or establish professional thresholds.",
        "",
    ]
    return "\n".join(sections)


def write_and_validate_results_summary(
    decisions_path: Path,
    comparison_path: Path,
    entity_path: Path,
    mechanism_path: Path,
    confusion_path: Path,
    summary_path: Path,
) -> None:
    """Write generated Markdown and verify exact agreement with CSV inputs."""

    expected = results_summary_text(decisions_path, comparison_path, entity_path, mechanism_path, confusion_path)
    summary_path.write_text(expected, encoding="utf-8", newline="\n")
    if summary_path.read_text(encoding="utf-8") != expected:
        raise ValueError("Generated result summary does not match current CSV outputs")


def chart_source_values(metrics: pd.DataFrame) -> pd.DataFrame:
    """Return the exact portable values and labels used by the chart."""

    indexed = metrics.set_index("policy")
    rows = []
    for policy in PRIMARY_CHART_POLICIES:
        rows.append({
            "policy": policy,
            "label": POLICY_LABELS[policy],
            "overall_failure_incidence_pct": indexed.loc[policy, "overall_failure_incidence_pct"],
            "unauthorised_economic_exposure": indexed.loc[policy, "unauthorised_economic_exposure"],
            "non_autonomous_intervention_pct": indexed.loc[policy, "non_autonomous_intervention_pct"],
        })
    return pd.DataFrame(rows)


def save_comparison_chart(metrics: pd.DataFrame, path: Path) -> None:
    """Save a descriptive three-panel chart from validated source values."""

    source = chart_source_values(metrics)
    colours = ["#667085", "#8A6F3D", "#2F6B5F"]
    panels = [
        ("overall_failure_incidence_pct", "Failure incidence", "Percent"),
        ("unauthorised_economic_exposure", "Authority-exposure proxy", "A$ gross amount"),
        ("non_autonomous_intervention_pct", "Intervention burden", "Percent"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.0))
    for axis, (column, title, ylabel) in zip(axes, panels, strict=True):
        values = source[column]
        bars = axis.bar(source["label"], values, color=colours, width=0.62)
        axis.set_title(title, fontsize=10)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.tick_params(axis="x", labelrotation=15, labelsize=8)
        axis.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, values, strict=True):
            label = f"{value:,.1f}" if column == "unauthorised_economic_exposure" else f"{value:.1f}%"
            axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=8)
        axis.margins(y=0.18)
    fig.suptitle("Illustrative comparison under authored aggregation scenarios", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", metadata={"Software": "MCAB prototype"})
    plt.close(fig)
