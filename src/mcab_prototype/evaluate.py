"""Common evaluation, sensitivity analysis, and chart generation."""

import os
from pathlib import Path

import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib"))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from .domain import Action, POLICY_VISIBLE_COLUMNS
from .policies import FixedPolicyConfig, FixedThresholdPolicy, MCABConfig, MCABPolicy


def apply_policies(
    transactions: pd.DataFrame,
    fixed_config: FixedPolicyConfig = FixedPolicyConfig(),
    mcab_config: MCABConfig = MCABConfig(),
) -> pd.DataFrame:
    """Run both policies using an identical, restricted data interface."""

    policy_input = transactions.loc[:, POLICY_VISIBLE_COLUMNS].copy()
    fixed = FixedThresholdPolicy(fixed_config).run(policy_input).add_prefix("fixed_")
    mcab = MCABPolicy(mcab_config).run(policy_input).add_prefix("mcab_")
    if not (fixed["fixed_transaction_id"].to_numpy() == transactions["transaction_id"].to_numpy()).all():
        raise ValueError("Fixed-policy decision order changed")
    if not (mcab["mcab_transaction_id"].to_numpy() == transactions["transaction_id"].to_numpy()).all():
        raise ValueError("MCAB decision order changed")
    return pd.concat([transactions.reset_index(drop=True), fixed, mcab], axis=1)


def summarise_policy(decisions: pd.DataFrame, policy: str) -> dict[str, object]:
    """Compute transparent metrics for one policy decision column."""

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
    """Return one computed metric row for each treatment policy."""

    return pd.DataFrame([summarise_policy(decisions, "fixed"), summarise_policy(decisions, "mcab")])


def action_confusion(decisions: pd.DataFrame) -> pd.DataFrame:
    """Return a complete policy-versus-oracle action table, including zeros."""

    actions = [action.value for action in Action]
    rows: list[dict[str, object]] = []
    for policy in ("fixed", "mcab"):
        counts = pd.crosstab(decisions["oracle_required_action"], decisions[f"{policy}_action"])
        for oracle_action in actions:
            for policy_action in actions:
                count = int(counts.get(policy_action, pd.Series(dtype=int)).get(oracle_action, 0))
                rows.append({
                    "policy": policy, "oracle_action": oracle_action,
                    "policy_action": policy_action, "count": count,
                })
    return pd.DataFrame(rows)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


README_RESULTS_START = "<!-- BEGIN GENERATED PRIMARY RESULTS -->"
README_RESULTS_END = "<!-- END GENERATED PRIMARY RESULTS -->"


def readme_primary_results_text(comparison_path: Path) -> str:
    """Render the compact README comparison directly from the metric CSV."""

    metrics = pd.read_csv(comparison_path).set_index("policy")
    rows = []
    for policy, label in (("fixed", "Fixed threshold"), ("mcab", "MCAB")):
        row = metrics.loc[policy]
        rows.append([
            label,
            f"{int(row['conditional_miss_numerator'])}/{int(row['conditional_miss_denominator'])} ({row['conditional_miss_rate_pct']:.2f}%)",
            f"A${row['unauthorised_economic_exposure']:,.0f}",
            f"{int(row['non_autonomous_intervention_n'])}/{int(row['non_autonomous_intervention_denominator'])} ({row['non_autonomous_intervention_pct']:.2f}%)",
        ])
    return _markdown_table(
        ["Policy", "Conditional miss rate", "Gross authority-exposure proxy", "Combined non-autonomous intervention"],
        rows,
    )


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
    validated = readme_path.read_text(encoding="utf-8")
    if f"{README_RESULTS_START}\n{generated}\n{README_RESULTS_END}" not in validated:
        raise ValueError("README primary results do not match policy_comparison.csv")


def results_summary_text(
    decisions_path: Path, comparison_path: Path, sensitivity_path: Path, confusion_path: Path,
) -> str:
    """Render public result values from generated CSV artifacts."""

    decisions = pd.read_csv(decisions_path)
    metrics = pd.read_csv(comparison_path).set_index("policy")
    sensitivity = pd.read_csv(sensitivity_path)
    confusion = pd.read_csv(confusion_path)
    primary_rows: list[list[str]] = []
    secondary_rows: list[list[str]] = []
    for policy, label in (("fixed", "Fixed threshold"), ("mcab", "MCAB")):
        row = metrics.loc[policy]
        primary_rows.append([
            label,
            f"{int(row['overall_failure_numerator'])}/{int(row['overall_failure_denominator'])} ({row['overall_failure_incidence_pct']:.2f}%)",
            f"{int(row['conditional_miss_numerator'])}/{int(row['conditional_miss_denominator'])} ({row['conditional_miss_rate_pct']:.2f}%)",
            f"A${row['unauthorised_economic_exposure']:,.0f}",
            f"{int(row['independent_review_n'])}/{int(row['independent_review_denominator'])} ({row['independent_review_pct']:.2f}%)",
            f"{int(row['block_n'])}/{int(row['block_denominator'])} ({row['block_pct']:.2f}%)",
            f"{int(row['non_autonomous_intervention_n'])}/{int(row['non_autonomous_intervention_denominator'])} ({row['non_autonomous_intervention_pct']:.2f}%)",
        ])
        secondary_rows.append([
            label,
            f"{int(row['false_escalations_n'])}/{int(row['false_escalation_denominator'])} ({row['false_escalation_rate_pct']:.2f}%)",
            str(int(row["aggregation_failures_n"])),
            f"{int(row['qualitative_correctly_escalated_n'])}/{int(row['qualitative_override_cases_n'])} ({row['qualitative_correctly_escalated_pct']:.2f}%)",
        ])

    matched = sensitivity[(sensitivity["analysis"] == "matched_budget")]
    matched_rows = [[
        f"A${row.mcab_initial_budget:,.0f}", "Fixed threshold" if row.policy == "fixed" else "MCAB",
        str(int(row.consequential_failures_n)), f"A${row.unauthorised_economic_exposure:,.0f}",
        str(int(row.non_autonomous_intervention_n)), str(int(row.false_escalations_n)),
    ] for row in matched.itertuples(index=False)]

    confusion_rows: list[list[str]] = []
    for policy, label in (("fixed", "Fixed threshold"), ("mcab", "MCAB")):
        subset = confusion[confusion["policy"] == policy]
        for oracle_action in [action.value for action in Action]:
            by_action = subset[subset["oracle_action"] == oracle_action].set_index("policy_action")["count"]
            confusion_rows.append([
                label, oracle_action,
                str(int(by_action.get(Action.AUTO_EXECUTE.value, 0))),
                str(int(by_action.get(Action.INDEPENDENT_REVIEW.value, 0))),
                str(int(by_action.get(Action.BLOCK.value, 0))),
            ])

    qualitative_scenarios = int(decisions["scenario_type"].eq("qualitative_risk").sum())
    confirmed_error_flags = int((decisions["scenario_type"].eq("confirmed_error_signal") & decisions["qualitative_flag"].ne("none")).sum())
    interval_support = int(((decisions["amount"] > 25_000) & (decisions["amount"] <= 50_000)).sum())
    original_aggregation = decisions[decisions["scenario_type"].eq("aggregation_pressure")]
    residual_misses = int((
        original_aggregation["oracle_required_action"].ne(Action.AUTO_EXECUTE.value)
        & original_aggregation["mcab_action"].eq(Action.AUTO_EXECUTE.value)
    ).sum())

    sections = [
        "# Generated results summary",
        "",
        "> Generated by `python -m mcab_prototype.run_demo` from the current CSV outputs. Do not edit numerical values manually.",
        "",
        "## Primary matched A$50,000 comparison",
        "",
        _markdown_table(
            ["Policy", "Overall failure incidence", "Conditional miss rate", "Gross authority-exposure proxy", "Review", "Block", "Combined intervention"],
            primary_rows,
        ),
        "",
        "The exposure measure is gross transaction amount associated with missed escalations. It is an authority-exposure proxy, not realised financial loss.",
        "",
        "## Secondary outcomes",
        "",
        _markdown_table(["Policy", "False escalations", "Aggregation failures", "Qualitative cases correctly escalated"], secondary_rows),
        "",
        f"The qualitative denominator comprises {qualitative_scenarios} transactions in the qualitative-risk scenario family plus {confirmed_error_flags} confirmed-error signal carrying a management-override flag.",
        "",
        "## Action confusion counts",
        "",
        _markdown_table(["Policy", "Oracle action", "Policy AUTO_EXECUTE", "Policy INDEPENDENT_REVIEW", "Policy BLOCK"], confusion_rows),
        "",
        "For the consequential-failure metrics, `INDEPENDENT_REVIEW` is an adequate escalation when the oracle requires either review or blocking because autonomous authority is removed and a human reviewer can subsequently block execution. Review and block remain separate above so severity differences are visible.",
        "",
        "## Matched-budget sensitivity",
        "",
        _markdown_table(["Initial matched budget", "Policy", "Failures", "Exposure proxy", "Combined interventions", "False escalations"], matched_rows),
        "",
        f"There are {interval_support} authored transaction amounts above A$25,000 and at or below A$50,000. This sparse interval support explains why the fixed policy has identical A$25,000 and A$50,000 results; it is a limitation of this dataset, not evidence of threshold invariance.",
        "",
        "## Residual default-MCAB misses",
        "",
        f"The independently specified oracle begins requiring escalation one transaction before the default MCAB budget is exceeded in each original aggregation sequence. This rule is fixed before policy execution, and oracle labels do not change with treatment parameters. The {residual_misses} residual MCAB misses arise from the difference between the oracle's conservative escalation schedule and MCAB's budget-exhaustion rule.",
        "",
        "The tables are simulated evidence from an authored deterministic demonstration. They do not validate MCAB or establish professional thresholds.",
        "",
    ]
    return "\n".join(sections)


def write_and_validate_results_summary(
    decisions_path: Path, comparison_path: Path, sensitivity_path: Path,
    confusion_path: Path, summary_path: Path,
) -> None:
    """Write the generated Markdown and verify exact agreement with its CSVs."""

    expected = results_summary_text(decisions_path, comparison_path, sensitivity_path, confusion_path)
    summary_path.write_text(expected, encoding="utf-8", newline="\n")
    if summary_path.read_text(encoding="utf-8") != expected:
        raise ValueError("Generated result summary does not match the current CSV outputs")


def sensitivity_analysis(transactions: pd.DataFrame) -> pd.DataFrame:
    """Run primary, MCAB-design, and matched-budget comparisons."""

    rows: list[dict[str, object]] = []

    def add_condition(analysis: str, condition: str, fixed_threshold: float, safety: float, multiplier: float) -> None:
        decisions = apply_policies(
            transactions, FixedPolicyConfig(fixed_threshold),
            MCABConfig(safety_factor=safety, post_error_multiplier=multiplier),
        )
        for metrics in (summarise_policy(decisions, "fixed"), summarise_policy(decisions, "mcab")):
            rows.append({
                "analysis": analysis, "condition": condition,
                "fixed_threshold": fixed_threshold, "mcab_safety_factor": safety,
                "mcab_initial_budget": 500_000.0 * safety,
                "post_error_multiplier": multiplier,
                "post_error_condition": (
                    "no_tightening_aggregation_only" if multiplier == 1.0 else "prospective_tightening"
                ),
                **metrics,
            })

    add_condition("primary_matched_50000", "safety_0.10_multiplier_0.50", 50_000.0, 0.10, 0.50)
    for safety in (0.05, 0.10, 0.15):
        for multiplier in (0.25, 0.50, 0.75, 1.00):
            add_condition(
                "mcab_only_design", f"safety_{safety:.2f}_multiplier_{multiplier:.2f}",
                50_000.0, safety, multiplier,
            )
    for safety in (0.05, 0.10, 0.15):
        budget = 500_000.0 * safety
        add_condition(
            "matched_budget", f"matched_{budget:.0f}", budget, safety, 0.50,
        )
    return pd.DataFrame(rows)


def save_comparison_chart(metrics: pd.DataFrame, path: Path) -> None:
    """Save a three-panel chart without mixing incompatible units."""

    labels = ["Fixed threshold", "MCAB"]
    colours = ["#667085", "#2F6B5F"]
    panels = [
        ("overall_failure_incidence_pct", "Failure incidence", "Percent"),
        ("unauthorised_economic_exposure", "Authority-exposure proxy", "A$ gross amount"),
        ("non_autonomous_intervention_pct", "Intervention burden", "Percent"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.8))
    for axis, (column, title, ylabel) in zip(axes, panels, strict=True):
        values = metrics.set_index("policy").loc[["fixed", "mcab"], column]
        bars = axis.bar(labels, values, color=colours, width=0.62)
        axis.set_title(title, fontsize=10)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.tick_params(axis="x", labelrotation=12, labelsize=8)
        axis.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, values, strict=True):
            label = f"{value:,.1f}" if column == "unauthorised_economic_exposure" else f"{value:.1f}%"
            axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=8)
        axis.margins(y=0.18)
    fig.suptitle("Synthetic policy comparison (primary matched A$50,000 design)", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", metadata={"Software": "MCAB prototype"})
    plt.close(fig)
