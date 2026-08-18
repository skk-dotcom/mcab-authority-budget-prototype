"""Evaluation, decomposition, chart, and generated-output tests."""

from pathlib import Path
from shutil import copyfile

import pandas as pd
from matplotlib import image as mpimg

from mcab_prototype.domain import POLICY_VISIBLE_COLUMNS
from mcab_prototype.evaluate import (
    POLICY_ORDER,
    action_confusion,
    apply_policies,
    chart_source_values,
    compare_policies,
    compare_policies_by_entity,
    mechanism_decomposition,
    readme_primary_results_text,
    results_summary_text,
    save_comparison_chart,
    sensitivity_analysis,
)
from mcab_prototype.generate_data import generate_transactions
from mcab_prototype.run_demo import run_demo


def test_policy_interface_excludes_oracle_and_scenario_metadata() -> None:
    data = generate_transactions()
    visible = data.loc[:, POLICY_VISIBLE_COLUMNS]
    assert "oracle_required_action" not in visible
    assert not {"scenario_id", "scenario_type", "scenario_step"}.intersection(visible.columns)
    assert len(apply_policies(data)) == len(data)


def test_all_policy_metrics_reconcile_to_decision_rows() -> None:
    decisions = apply_policies(generate_transactions())
    metrics = compare_policies(decisions).set_index("policy")
    assert set(metrics.index) == set(POLICY_ORDER)
    for policy in POLICY_ORDER:
        row = metrics.loc[policy]
        false_negative = (
            decisions[f"{policy}_action"].eq("AUTO_EXECUTE")
            & decisions["oracle_required_action"].ne("AUTO_EXECUTE")
        )
        assert row["overall_failure_numerator"] == false_negative.sum()
        assert row["overall_failure_denominator"] == len(decisions)
        assert row["conditional_miss_numerator"] == false_negative.sum()
        assert row["conditional_miss_denominator"] == decisions["oracle_required_action"].ne("AUTO_EXECUTE").sum()
        assert row["unauthorised_economic_exposure"] == decisions.loc[false_negative, "amount"].sum()
        assert row["non_autonomous_intervention_n"] == row["independent_review_n"] + row["block_n"]


def test_reference_uniform_cap_and_no_tightening_decisions_are_identical() -> None:
    decisions = apply_policies(generate_transactions())
    reference = decisions[decisions["entity"].eq("ENTITY_REFERENCE")]
    columns = ("action", "route", "initial_budget", "effective_budget", "utilisation_before", "utilisation_after")
    for column in columns:
        pd.testing.assert_series_equal(
            reference[f"uniform_cap_{column}"].reset_index(drop=True),
            reference[f"mcab_no_tightening_{column}"].reset_index(drop=True),
            check_names=False,
        )


def test_no_tightening_and_full_mcab_are_identical_through_each_signal() -> None:
    decisions = apply_policies(generate_transactions())
    for entity in decisions["entity"].unique():
        signal_sequence = int(
            decisions.loc[decisions["entity"].eq(entity) & decisions["confirmed_control_error"], "sequence_number"].item()
        )
        before_and_signal = decisions[decisions["entity"].eq(entity) & decisions["sequence_number"].le(signal_sequence)]
        for column in ("action", "route", "effective_budget", "utilisation_before", "utilisation_after"):
            pd.testing.assert_series_equal(
                before_and_signal[f"mcab_no_tightening_{column}"].reset_index(drop=True),
                before_and_signal[f"mcab_full_{column}"].reset_index(drop=True),
                check_names=False,
            )


def test_mechanism_decomposition_uses_only_prespecified_subsets() -> None:
    decomposition = mechanism_decomposition(apply_policies(generate_transactions()))
    assert len(decomposition) == 5
    statefulness = decomposition[decomposition["mechanism"].eq("statefulness")].iloc[0]
    assert statefulness["subset"] == "matched_pre_error_aggregation"
    assert statefulness["transactions_n"] == 60
    assert (statefulness["baseline_policy"], statefulness["comparison_policy"]) == ("fixed", "uniform_cap")
    calibration = decomposition[decomposition["mechanism"].eq("entity_relative_calibration")]
    assert set(calibration["entity"]) == {"ENTITY_SMALL", "ENTITY_REFERENCE", "ENTITY_LARGE"}
    assert set(calibration["transactions_n"]) == {20}
    assert set(calibration["baseline_policy"]) == {"uniform_cap"}
    assert set(calibration["comparison_policy"]) == {"mcab_no_tightening"}
    reference = calibration[calibration["entity"].eq("ENTITY_REFERENCE")].iloc[0]
    assert reference["decision_disagreements_n"] == 0
    tightening = decomposition[decomposition["mechanism"].eq("prospective_error_tightening")].iloc[0]
    assert tightening["subset"] == "post_error_rows_only"
    assert tightening["transactions_n"] == 30
    assert (tightening["baseline_policy"], tightening["comparison_policy"]) == ("mcab_no_tightening", "mcab_full")


def test_entity_comparison_has_every_policy_and_entity() -> None:
    comparison = compare_policies_by_entity(apply_policies(generate_transactions()))
    assert len(comparison) == 12
    assert set(comparison["policy"]) == set(POLICY_ORDER)
    assert comparison.groupby("entity")["policy"].nunique().eq(4).all()


def test_sensitivity_uses_only_predeclared_grids() -> None:
    sensitivity = sensitivity_analysis(generate_transactions())
    assert set(sensitivity["analysis"]) == {
        "primary_frozen",
        "fixed_threshold_grid",
        "uniform_cap_grid",
        "mcab_safety_grid",
        "tightening_grid",
        "matched_reference_grid",
    }
    assert set(sensitivity["policy"]) == set(POLICY_ORDER)
    assert set(sensitivity.loc[sensitivity["analysis"].eq("fixed_threshold_grid"), "fixed_threshold"]) == {25_000, 50_000, 100_000}
    assert set(sensitivity.loc[sensitivity["analysis"].eq("uniform_cap_grid"), "uniform_cap"]) == {25_000, 50_000, 100_000}
    assert set(sensitivity.loc[sensitivity["analysis"].eq("mcab_safety_grid"), "mcab_safety_factor"]) == {0.05, 0.10, 0.15}
    assert set(sensitivity.loc[sensitivity["analysis"].eq("tightening_grid"), "full_post_error_multiplier"]) == {0.25, 0.50, 0.75, 1.00}
    matched = sensitivity[sensitivity["analysis"].eq("matched_reference_grid")]
    assert (matched["uniform_cap"] == matched["reference_mcab_budget"]).all()


def test_action_confusion_preserves_three_action_severity_for_four_policies() -> None:
    decisions = apply_policies(generate_transactions())
    confusion = action_confusion(decisions)
    assert len(confusion) == 36
    assert (confusion.groupby("policy")["count"].sum() == len(decisions)).all()


def test_chart_uses_validated_source_values_and_renders_portably(tmp_path: Path) -> None:
    metrics = compare_policies(apply_policies(generate_transactions()))
    source = chart_source_values(metrics)
    assert source["policy"].tolist() == ["fixed", "uniform_cap", "mcab_full"]
    assert source["label"].tolist() == ["Fixed threshold", "Uniform cumulative cap", "Full MCAB"]
    for column in ("overall_failure_incidence_pct", "unauthorised_economic_exposure", "non_autonomous_intervention_pct"):
        expected = metrics.set_index("policy").loc[source["policy"], column].reset_index(drop=True)
        pd.testing.assert_series_equal(source[column], expected, check_names=False)
    chart = tmp_path / "comparison.png"
    save_comparison_chart(metrics, chart)
    image = mpimg.imread(chart)
    assert chart.stat().st_size > 10_000
    assert image.shape[0] >= 500 and image.shape[1] >= 1_500
    assert float(image.std()) > 0.01


def test_demo_writes_complete_reconciled_outputs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    copyfile(root / "README.md", tmp_path / "README.md")
    metrics_path, chart_path = run_demo(tmp_path)
    expected_files = {
        tmp_path / "data" / "synthetic_transactions.csv",
        tmp_path / "outputs" / "policy_decisions.csv",
        tmp_path / "outputs" / "policy_comparison.csv",
        tmp_path / "outputs" / "policy_entity_comparison.csv",
        tmp_path / "outputs" / "mechanism_decomposition.csv",
        tmp_path / "outputs" / "sensitivity_analysis.csv",
        tmp_path / "outputs" / "action_confusion.csv",
        tmp_path / "outputs" / "results_summary.md",
    }
    assert metrics_path.is_file() and chart_path.is_file()
    assert all(path.is_file() for path in expected_files)
    expected_summary = results_summary_text(
        tmp_path / "outputs" / "policy_decisions.csv",
        metrics_path,
        tmp_path / "outputs" / "policy_entity_comparison.csv",
        tmp_path / "outputs" / "mechanism_decomposition.csv",
        tmp_path / "outputs" / "action_confusion.csv",
    )
    assert (tmp_path / "outputs" / "results_summary.md").read_text(encoding="utf-8") == expected_summary
    assert readme_primary_results_text(metrics_path) in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_checked_in_public_results_match_current_csv_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = results_summary_text(
        root / "outputs" / "policy_decisions.csv",
        root / "outputs" / "policy_comparison.csv",
        root / "outputs" / "policy_entity_comparison.csv",
        root / "outputs" / "mechanism_decomposition.csv",
        root / "outputs" / "action_confusion.csv",
    )
    assert (root / "outputs" / "results_summary.md").read_text(encoding="utf-8") == expected
    assert readme_primary_results_text(root / "outputs" / "policy_comparison.csv") in (
        root / "README.md"
    ).read_text(encoding="utf-8")


def test_deterministic_csv_and_markdown_reruns(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    copyfile(root / "README.md", first / "README.md")
    copyfile(root / "README.md", second / "README.md")
    run_demo(first)
    run_demo(second)
    relative_paths = [
        "data/synthetic_transactions.csv",
        "outputs/policy_decisions.csv",
        "outputs/policy_comparison.csv",
        "outputs/policy_entity_comparison.csv",
        "outputs/mechanism_decomposition.csv",
        "outputs/sensitivity_analysis.csv",
        "outputs/action_confusion.csv",
        "outputs/results_summary.md",
        "README.md",
    ]
    for relative in relative_paths:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_github_actions_workflow_is_minimal_and_read_only() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "contents: read" in workflow
    assert "pull_request:" in workflow and "push:" in workflow
    assert 'python-version: "3.11"' in workflow
    assert "python -m pip install -r requirements.txt" in workflow
    assert "python -m pip install -e ." in workflow
    assert "python -m pytest" in workflow
    assert not any(term in workflow.lower() for term in ("secrets.", "deploy", "publish"))
