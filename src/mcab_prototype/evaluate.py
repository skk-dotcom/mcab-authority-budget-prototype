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
PRIMARY_CHART_POLICIES = POLICY_ORDER
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


def corrective_comparison_text(
    decisions: pd.DataFrame,
    metrics: pd.DataFrame,
    supplementary: pd.DataFrame,
    exposure_decomposition: pd.DataFrame,
    oracle_sensitivity: pd.DataFrame,
    heading_level: int = 3,
) -> str:
    """Render corrected population, mixed-result, and factorial interpretation."""

    from .supplementary import exact_exposure, format_ratio, observed_interpretations

    heading = "#" * heading_level
    interpretations = observed_interpretations(decisions, oracle_sensitivity)
    repository = interpretations["exact_repository_exposure"]
    entity_ratio_rows = [
        [
            POLICY_LABELS[policy],
            *[
                format_ratio(repository[policy].entity_ratios[entity])
                for entity in ENTITY_ORDER
            ],
        ]
        for policy in POLICY_ORDER
    ]
    uniform_ratio_text = (
        f"{format_ratio(repository['uniform_cap'].entity_ratios['ENTITY_SMALL'])}, "
        f"{format_ratio(repository['uniform_cap'].entity_ratios['ENTITY_REFERENCE'])} and "
        f"{format_ratio(repository['uniform_cap'].entity_ratios['ENTITY_LARGE'])}"
    )

    small = decisions[decisions["entity"].eq("ENTITY_SMALL")]

    def small_failure_evidence(policy: str) -> pd.DataFrame:
        failure = (
            small[f"{policy}_action"].eq(Action.AUTO_EXECUTE.value)
            & small["oracle_required_action"].ne(Action.AUTO_EXECUTE.value)
        )
        evidence = small.loc[
            failure,
            ["transaction_id", "amount", "oracle_required_action", f"{policy}_action"],
        ].copy()
        return evidence.rename(columns={f"{policy}_action": "policy_action"}).reset_index(drop=True)

    fixed_small = small_failure_evidence("fixed")
    uniform_small = small_failure_evidence("uniform_cap")
    if fixed_small.equals(uniform_small):
        small_explanation = (
            f"For SMALL, the Fixed and Uniform conditions have the same {len(fixed_small)} "
            f"consequential-failure transaction IDs and the same A${fixed_small['amount'].sum():,.0f} "
            "failed exposure; the oracle requires `INDEPENDENT_REVIEW` and both policies choose "
            "`AUTO_EXECUTE` on those failed rows. The A$50,000 uniform cumulative cap therefore did "
            "not reduce SMALL consequential-failure exposure relative to the fixed policy in this "
            "authored dataset. This does not imply identical behaviour elsewhere or across all actions."
        )
    elif (
        repository["fixed"].entity_ratios["ENTITY_SMALL"]
        == repository["uniform_cap"].entity_ratios["ENTITY_SMALL"]
    ):
        small_explanation = (
            "For SMALL, the Fixed and Uniform conditions have equal aggregate entity-exposure ratios "
            "but different consequential-failure rows or actions. The equal displayed ratios are an "
            "aggregate coincidence and do not imply identical decisions."
        )
    else:
        small_explanation = (
            "For SMALL, the Fixed and Uniform conditions differ in both their consequential-failure "
            "evidence and entity-exposure ratios."
        )
    aggregation = decisions[decisions["scenario_type"].eq("aggregation_pressure")]
    post_error = decisions[decisions["scenario_type"].eq("post_error_accumulation")]
    isolated = decisions[decisions["scenario_type"].eq("isolated_significance")]
    uniform_aggregation = exact_exposure(aggregation, "uniform_cap")
    no_tightening_aggregation = exact_exposure(aggregation, "mcab_no_tightening")
    no_tightening_post_error = exact_exposure(post_error, "mcab_no_tightening")
    full_post_error = exact_exposure(post_error, "mcab_full")
    uniform_isolated = exact_exposure(isolated, "uniform_cap")
    no_tightening_isolated = exact_exposure(isolated, "mcab_no_tightening")
    full_isolated = exact_exposure(isolated, "mcab_full")

    calibration_rows: list[list[str]] = []
    for measure, metric_column, scale_column, formatter, direction in (
        ("Absolute-dollar exposure", "unauthorised_economic_exposure", None, lambda value: f"A${value:,.0f}", "Higher under no tightening"),
        ("Summed anchor-normalised exposure", None, "anchor_normalised_exposure", lambda value: f"{value:.4f}", "Higher under no tightening"),
        ("Maximum entity-anchor ratio", None, "maximum_entity_anchor_ratio", lambda value: f"{value:.4f}", "Higher under no tightening"),
        ("Conditional misses", "conditional", None, str, "Lower under no tightening"),
    ):
        if metric_column == "conditional":
            values = [
                f"{int(metrics.loc[policy, 'conditional_miss_numerator'])}/{int(metrics.loc[policy, 'conditional_miss_denominator'])} ({metrics.loc[policy, 'conditional_miss_rate_pct']:.2f}%)"
                for policy in ("uniform_cap", "mcab_no_tightening")
            ]
        elif metric_column is not None:
            values = [formatter(metrics.loc[policy, metric_column]) for policy in ("uniform_cap", "mcab_no_tightening")]
        else:
            values = [formatter(supplementary.loc[policy, scale_column]) for policy in ("uniform_cap", "mcab_no_tightening")]
        calibration_rows.append([measure, *values, direction])

    mixed_rows = [
        [
            "Consequential failures",
            f"{int(metrics.loc['uniform_cap', 'overall_failure_numerator'])}/{int(metrics.loc['uniform_cap', 'overall_failure_denominator'])}",
            f"{int(metrics.loc['mcab_full', 'overall_failure_numerator'])}/{int(metrics.loc['mcab_full', 'overall_failure_denominator'])}",
            "Full MCAB",
        ],
        [
            "Summed anchor-normalised exposure",
            f"{supplementary.loc['uniform_cap', 'anchor_normalised_exposure']:.4f}",
            f"{supplementary.loc['mcab_full', 'anchor_normalised_exposure']:.4f}",
            "Full MCAB",
        ],
        [
            "Absolute-dollar exposure",
            f"A${metrics.loc['uniform_cap', 'unauthorised_economic_exposure']:,.0f}",
            f"A${metrics.loc['mcab_full', 'unauthorised_economic_exposure']:,.0f}",
            "Uniform cap",
        ],
        [
            "Maximum entity-anchor ratio",
            f"{supplementary.loc['uniform_cap', 'maximum_entity_anchor_ratio']:.4f}",
            f"{supplementary.loc['mcab_full', 'maximum_entity_anchor_ratio']:.4f}",
            "Uniform cap",
        ],
        [
            "Combined intervention",
            f"{int(metrics.loc['uniform_cap', 'non_autonomous_intervention_n'])}/{int(metrics.loc['uniform_cap', 'non_autonomous_intervention_denominator'])} ({metrics.loc['uniform_cap', 'non_autonomous_intervention_pct']:.2f}%)",
            f"{int(metrics.loc['mcab_full', 'non_autonomous_intervention_n'])}/{int(metrics.loc['mcab_full', 'non_autonomous_intervention_denominator'])} ({metrics.loc['mcab_full', 'non_autonomous_intervention_pct']:.2f}%)",
            "Uniform cap",
        ],
    ]

    ratio_difference = (
        repository["uniform_cap"].summed_anchor_equivalents
        - repository["mcab_full"].summed_anchor_equivalents
    )
    ratio_difference_text = format_ratio(ratio_difference)
    relative_difference = (
        float(ratio_difference / repository["uniform_cap"].summed_anchor_equivalents) * 100
    )

    scenario_rows = exposure_decomposition[
        exposure_decomposition["dimension"].eq("scenario_type")
    ].set_index("group")
    aggregation_difference = abs(float(scenario_rows.loc["aggregation_pressure", "exposure_difference_full_minus_uniform"]))
    post_error_difference = abs(float(scenario_rows.loc["post_error_accumulation", "exposure_difference_full_minus_uniform"]))
    eight_three = oracle_sensitivity[oracle_sensitivity["configuration"].eq("8/3")].set_index("policy")
    sensitivity_order_rows = [
        [configuration, order]
        for configuration, order in interpretations["sensitivity_orders"].items()
    ]

    sections = [
        f"{heading} Repository-level calibration contrast",
        "",
        _markdown_table(
            ["Repository-level measure", "Uniform cap", "MCAB no tightening", "Observed direction"],
            calibration_rows,
        ),
        "",
        f"Calibration Branch {interpretations['calibration_branch']}: {interpretations['calibration_text']}",
        "",
        f"On matched pre-error aggregation rows, summed anchor-normalised exposure is {format_ratio(uniform_aggregation.summed_anchor_equivalents)} under the uniform cap and {format_ratio(no_tightening_aggregation.summed_anchor_equivalents)} under MCAB no tightening. These prespecified mechanism-subset values are reported separately and are not inputs to the repository-level branch label.",
        "",
        "In this authored dataset, entity-relative calibration improves the matched aggregation subset while weakening control over the isolated-significance vignettes. Its repository-level result therefore depends on the authored mixture of cumulative-risk and isolated-transaction scenarios.",
        "",
        "Calibration alone slightly reduces conditional misses but increases absolute-dollar exposure, summed anchor-normalised exposure, and the maximum entity-anchor ratio at repository level. It performs substantially better on the matched aggregation subset; the repository-level exposure result is worse because that subset excludes isolated-significance cases.",
        "",
        f"{heading} Entity-level distribution behind the aggregate",
        "",
        "Each cell is entity consequential-failure exposure divided by that entity's authored anchor.",
        "",
        _markdown_table(
            ["Policy", "SMALL", "REFERENCE", "LARGE"],
            entity_ratio_rows,
        ),
        "",
        f"In this authored construction, the uniform cap’s entity-level exposure ratio falls from SMALL to LARGE: {uniform_ratio_text}. Relative to the uniform cap, MCAB without tightening lowers the SMALL ratio, leaves REFERENCE unchanged and raises LARGE; Full MCAB lowers SMALL and REFERENCE but raises LARGE.",
        "",
        "The summed MCAB indices are therefore heavily influenced by LARGE isolated-significance exposure and conceal this cross-entity redistribution. These patterns reflect the authored scenarios, anchors and risk composition; they are not evidence of monotonic behaviour across real organisations.",
        "",
        small_explanation,
        "",
        "This distribution motivates future research on layered per-transaction, cumulative risk-cell, and cross-entity or group-level authority limits. It does not establish or professionally prescribe such a hierarchy.",
        "",
        f"{heading} Uniform cap and Full MCAB: mixed repository-level measures",
        "",
        _markdown_table(
            ["Measure", "Uniform cap", "Full MCAB", "Lower observed value"],
            mixed_rows,
        ),
        "",
        "“Lower observed value” is descriptive and is not a policy-winner designation. These measures are not equally weighted and do not form a composite score.",
        "",
        f"The summed-ratio difference is {ratio_difference_text}, approximately {relative_difference:.1f}% below the uniform-cap value. Full MCAB exchanges fewer misses and slightly lower summed relative exposure for higher gross-dollar exposure, a higher worst-entity ratio, and more intervention. Overall Branch A reflects the combined Full MCAB design and must not be attributed to calibration alone.",
        "",
        f"Overall Branch {interpretations['overall_branch']}: {interpretations['overall_text']}",
        "",
        f"{heading} Mechanism-subset and isolated-significance context",
        "",
        f"Four isolated-significance vignettes in `ENTITY_LARGE` contribute A${no_tightening_isolated.gross_cents / 100:,.0f} under MCAB no tightening and A${full_isolated.gross_cents / 100:,.0f} under Full MCAB, compared with A${uniform_isolated.gross_cents / 100:,.0f} under the uniform cap. They sit outside the prespecified mechanism-identification subsets.",
        "",
        f"Aggregation-pressure exposure is A${aggregation_difference:,.0f} lower under Full MCAB, and post-error-accumulation exposure is A${post_error_difference:,.0f} lower. Mechanism claims should therefore be read from decomposition and ablation contrasts rather than inferred from the headline table alone.",
        "",
        f"Within the entity-calibrated post-error subset, summed anchor-normalised exposure is {format_ratio(no_tightening_post_error.summed_anchor_equivalents)} without tightening and {format_ratio(full_post_error.summed_anchor_equivalents)} under Full MCAB. Tightening Branch {interpretations['tightening_branch']}: {interpretations['tightening_text']}",
        "",
        f"{heading} Oracle-recurrence ordering",
        "",
        _markdown_table(["Configuration", "Exact conditional-miss ordering (lowest to highest)"], sensitivity_order_rows),
        "",
        f"Sensitivity Branch {interpretations['sensitivity_branch']}: {interpretations['sensitivity_text']}",
        "",
        "Full MCAB has the lowest conditional-miss fraction in all five authored configurations, but the complete weak ordering changes under `4/3` because the relation between the uniform cap and MCAB no tightening reverses. The Full-MCAB–no-tightening ordering persists across this narrow recurrence grid. This is local sensitivity within one authored dataset, not independent confirmation, robustness, or external validation.",
        "",
        f"Under `8/3`, false escalations are {int(eight_three.loc['uniform_cap', 'false_escalation_numerator'])}/{int(eight_three.loc['uniform_cap', 'false_escalation_denominator'])} for the uniform cap, {int(eight_three.loc['mcab_no_tightening', 'false_escalation_numerator'])}/{int(eight_three.loc['mcab_no_tightening', 'false_escalation_denominator'])} for MCAB no tightening, and {int(eight_three.loc['mcab_full', 'false_escalation_numerator'])}/{int(eight_three.loc['mcab_full', 'false_escalation_denominator'])} for Full MCAB. The higher false-escalation counts under `8/3` arise from relabelling fixed policy interventions against a more permissive oracle configuration, not from any change in policy behaviour.",
        "",
        "The identical `0.2777` Fixed-threshold entity ratios are a product of proportional scenario scaling and proportional entity anchors, not evidence of empirical invariance across differently sized organisations. This matched construction makes the cross-entity comparison cleaner than would ordinarily be expected in operational data.",
        "",
        f"{heading} Incomplete factorial and future question",
        "",
        _markdown_table(
            ["Calibration", "No tightening", "Tightening"],
            [
                ["No entity calibration", "Uniform cap", "Not implemented"],
                ["Entity calibration", "MCAB no tightening", "Full MCAB"],
            ],
        ),
        "",
        "The policy ladder is not a complete 2×2 factorial because it contains no uniform-cap-with-tightening condition. The no-tightening–Full-MCAB contrast therefore measures prospective tightening only within entity-calibrated conditions and cannot determine whether the observed tightening result requires, interacts with or generalises beyond entity calibration.",
        "",
        "The entity-calibration step does not improve repository-level absolute exposure, summed anchor-normalised exposure, or maximum entity-anchor exposure in this authored dataset; it slightly improves conditional misses and substantially improves the matched aggregation subset. Adding prospective tightening within the entity-calibrated conditions reduces repository-level summed exposure and failures relative to MCAB no tightening. Because uniform-cap-with-tightening is absent, the design cannot determine whether this result depends on calibration or would also occur under a uniform cap. The mechanism decomposition sharpens a future question rather than resolving it.",
        "",
        "The mixed results motivate a sharper future question: under what risk compositions does entity-relative authority improve control, and what hierarchy of per-transaction, cumulative risk-cell and cross-entity constraints is required to prevent gains in aggregation control from weakening isolated-transaction control?",
        "",
        interpretations["maximum_ratio_statement"],
    ]
    return "\n".join(sections)


def readme_primary_results_text(
    decisions_path: Path,
    comparison_path: Path,
    supplementary_path: Path,
    exposure_decomposition_path: Path,
    oracle_sensitivity_path: Path,
) -> str:
    """Render the four-policy public comparison from generated metrics."""

    decisions = pd.read_csv(decisions_path)
    metrics = pd.read_csv(comparison_path).set_index("policy")
    supplementary = pd.read_csv(supplementary_path).set_index("policy")
    exposure_decomposition = pd.read_csv(exposure_decomposition_path)
    oracle_sensitivity = pd.read_csv(oracle_sensitivity_path)
    rows = []
    for policy in PRIMARY_CHART_POLICIES:
        row = metrics.loc[policy]
        scale = supplementary.loc[policy]
        rows.append([
            POLICY_LABELS[policy],
            f"{int(row['overall_failure_numerator'])}/{int(row['overall_failure_denominator'])} ({row['overall_failure_incidence_pct']:.2f}%)",
            f"{int(row['conditional_miss_numerator'])}/{int(row['conditional_miss_denominator'])} ({row['conditional_miss_rate_pct']:.2f}%)",
            f"A${row['unauthorised_economic_exposure']:,.0f}",
            f"{scale['anchor_normalised_exposure']:.4f}",
            f"{scale['maximum_entity_anchor_ratio']:.4f}",
            f"{int(row['non_autonomous_intervention_n'])}/{int(row['non_autonomous_intervention_denominator'])} ({row['non_autonomous_intervention_pct']:.2f}%)",
        ])
    table = _markdown_table(
        [
            "Policy",
            "Failure incidence",
            "Conditional miss rate",
            "A$ exposure proxy",
            "Summed anchor equivalents",
            "Maximum entity ratio",
            "Combined intervention",
        ],
        rows,
    )
    interpretation = (
        "Absolute-dollar exposure remains the primary exposure outcome. Summed anchor equivalents and the "
        "maximum entity ratio are supplementary scale-relative descriptions and do not define a universal ranking."
    )
    corrective = corrective_comparison_text(
        decisions,
        metrics,
        supplementary,
        exposure_decomposition,
        oracle_sensitivity,
    )
    return f"{table}\n\n{interpretation}\n\n{corrective}"


def write_and_validate_readme_results(
    readme_path: Path,
    decisions_path: Path,
    comparison_path: Path,
    supplementary_path: Path,
    exposure_decomposition_path: Path,
    oracle_sensitivity_path: Path,
) -> None:
    """Replace the delimited README table and verify it against the CSV."""

    readme = readme_path.read_text(encoding="utf-8")
    if readme.count(README_RESULTS_START) != 1 or readme.count(README_RESULTS_END) != 1:
        raise ValueError("README must contain exactly one generated-results block")
    before, remainder = readme.split(README_RESULTS_START, maxsplit=1)
    _, after = remainder.split(README_RESULTS_END, maxsplit=1)
    generated = readme_primary_results_text(
        decisions_path,
        comparison_path,
        supplementary_path,
        exposure_decomposition_path,
        oracle_sensitivity_path,
    )
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
    supplementary_path: Path,
    exposure_decomposition_path: Path,
    oracle_sensitivity_path: Path,
) -> str:
    """Render public result values from generated summary CSV artifacts."""

    decisions = pd.read_csv(decisions_path)
    metrics = pd.read_csv(comparison_path).set_index("policy")
    entities = pd.read_csv(entity_path)
    mechanisms = pd.read_csv(mechanism_path)
    confusion = pd.read_csv(confusion_path)
    supplementary = pd.read_csv(supplementary_path).set_index("policy")
    exposure_decomposition = pd.read_csv(exposure_decomposition_path)
    oracle_sensitivity = pd.read_csv(oracle_sensitivity_path)
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

    supplementary_rows: list[list[str]] = []
    for policy in POLICY_ORDER:
        row = supplementary.loc[policy]
        supplementary_rows.append([
            POLICY_LABELS[policy],
            f"{row.anchor_normalised_exposure:.4f}",
            f"{row.entity_small_anchor_ratio:.4f}",
            f"{row.entity_reference_anchor_ratio:.4f}",
            f"{row.entity_large_anchor_ratio:.4f}",
            f"{row.maximum_entity_anchor_ratio:.4f}",
        ])

    exposure_decomposition_rows: list[list[str]] = []
    for row in exposure_decomposition.itertuples(index=False):
        difference = float(row.exposure_difference_full_minus_uniform)
        signed_difference = f"{'+' if difference >= 0 else '−'}A${abs(difference):,.0f}"
        exposure_decomposition_rows.append([
            row.dimension,
            row.group,
            str(int(row.uniform_failure_count)),
            f"A${row.uniform_absolute_dollar_exposure:,.0f}",
            str(int(row.full_mcab_failure_count)),
            f"A${row.full_mcab_absolute_dollar_exposure:,.0f}",
            signed_difference,
        ])

    oracle_sensitivity_rows: list[list[str]] = []
    for row in oracle_sensitivity.itertuples(index=False):
        oracle_sensitivity_rows.append([
            row.configuration,
            POLICY_LABELS[row.policy],
            f"{int(row.oracle_escalation_numerator)}/{int(row.oracle_escalation_denominator)}",
            f"{int(row.conditional_miss_numerator)}/{int(row.conditional_miss_denominator)} ({row.conditional_miss_rate_pct:.2f}%)",
            f"{int(row.false_escalation_numerator)}/{int(row.false_escalation_denominator)} ({row.false_escalation_rate_pct:.2f}%)",
            f"A${row.absolute_dollar_exposure:,.0f}",
            f"{row.anchor_normalised_exposure:.4f}",
            f"{row.maximum_entity_anchor_ratio:.4f}",
            f"{int(row.independent_review_n)}/{int(row.block_n)}/{int(row.combined_intervention_n)}",
        ])
    corrective = corrective_comparison_text(
        decisions,
        metrics,
        supplementary,
        exposure_decomposition,
        oracle_sensitivity,
        heading_level=2,
    )

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
        "## Supplementary scale-relative exposure",
        "",
        _markdown_table(
            ["Policy", "Summed anchor equivalents", "SMALL ratio", "REFERENCE ratio", "LARGE ratio", "Maximum ratio"],
            supplementary_rows,
        ),
        "",
        "Summed anchor equivalents are dimensionless and may exceed 1.0. They reflect both failure incidence and relative failure size, while the maximum is the largest fraction of a single entity's authored anchor. Neither is realised loss, audit materiality, or a validated loss metric.",
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
        "## Uniform-cap versus Full-MCAB absolute-dollar decomposition",
        "",
        _markdown_table(
            ["Dimension", "Group", "Uniform failures", "Uniform exposure", "Full failures", "Full exposure", "Full − Uniform exposure"],
            exposure_decomposition_rows,
        ),
        "",
        "Each dimension is a separate partition and reconciles to the same repository-level totals. Rows are existing absolute-dollar measures, not anchor-normalised results.",
        "",
        "## Oracle-recurrence sensitivity",
        "",
        _markdown_table(
            ["Configuration", "Policy", "Oracle escalations", "Conditional misses", "False escalations", "A$ exposure", "Anchor equivalents", "Maximum ratio", "Review/Block/Combined"],
            oracle_sensitivity_rows,
        ),
        "",
        "Oracle configurations are written as pre-error/post-error review recurrences. Denominators change when oracle labels change, so rate levels are not directly comparable across configurations; ordering and trade-offs are assessed within each authored configuration.",
        "",
        corrective,
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
    supplementary_path: Path,
    exposure_decomposition_path: Path,
    oracle_sensitivity_path: Path,
    summary_path: Path,
) -> None:
    """Write generated Markdown and verify exact agreement with CSV inputs."""

    expected = results_summary_text(
        decisions_path,
        comparison_path,
        entity_path,
        mechanism_path,
        confusion_path,
        supplementary_path,
        exposure_decomposition_path,
        oracle_sensitivity_path,
    )
    summary_path.write_text(expected, encoding="utf-8", newline="\n")
    if summary_path.read_text(encoding="utf-8") != expected:
        raise ValueError("Generated result summary does not match current CSV outputs")


def chart_source_values(metrics: pd.DataFrame, supplementary: pd.DataFrame) -> pd.DataFrame:
    """Return the exact portable values and labels used by the chart."""

    indexed = metrics.set_index("policy")
    scale = supplementary.set_index("policy")
    rows = []
    for policy in PRIMARY_CHART_POLICIES:
        rows.append({
            "policy": policy,
            "label": POLICY_LABELS[policy],
            "overall_failure_incidence_pct": indexed.loc[policy, "overall_failure_incidence_pct"],
            "unauthorised_economic_exposure": indexed.loc[policy, "unauthorised_economic_exposure"],
            "anchor_normalised_exposure": scale.loc[policy, "anchor_normalised_exposure"],
            "non_autonomous_intervention_pct": indexed.loc[policy, "non_autonomous_intervention_pct"],
        })
    return pd.DataFrame(rows)


def save_comparison_chart(metrics: pd.DataFrame, supplementary: pd.DataFrame, path: Path) -> None:
    """Save a descriptive four-policy, four-panel comparison chart."""

    source = chart_source_values(metrics, supplementary)
    colours = ["#667085", "#8A6F3D", "#567B8A", "#2F6B5F"]
    panels = [
        ("overall_failure_incidence_pct", "Failure incidence", "Percent"),
        ("unauthorised_economic_exposure", "Authority-exposure proxy", "A$ gross amount"),
        ("anchor_normalised_exposure", "Summed anchor equivalents", "Dimensionless equivalents"),
        ("non_autonomous_intervention_pct", "Intervention burden", "Percent"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(16.0, 4.2))
    for axis, (column, title, ylabel) in zip(axes, panels, strict=True):
        values = source[column]
        bars = axis.bar(source["label"], values, color=colours, width=0.62)
        axis.set_title(title, fontsize=10)
        axis.set_ylabel(ylabel, fontsize=9)
        axis.tick_params(axis="x", labelrotation=15, labelsize=8)
        axis.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, values, strict=True):
            if column == "unauthorised_economic_exposure":
                label = f"{value:,.0f}"
            elif column == "anchor_normalised_exposure":
                label = f"{value:.4f}"
            else:
                label = f"{value:.1f}%"
            axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=8)
        axis.margins(y=0.18)
    fig.suptitle("Illustrative comparison under authored scenarios", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", metadata={"Software": "MCAB prototype"})
    plt.close(fig)
