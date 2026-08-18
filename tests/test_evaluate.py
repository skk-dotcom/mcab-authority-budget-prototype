"""Evaluation and end-to-end output tests."""

from pathlib import Path
from shutil import copyfile

import pandas as pd

from mcab_prototype.domain import POLICY_VISIBLE_COLUMNS
from mcab_prototype.evaluate import (
    action_confusion,
    apply_policies,
    compare_policies,
    readme_primary_results_text,
    results_summary_text,
    sensitivity_analysis,
)
from mcab_prototype.generate_data import generate_transactions
from mcab_prototype.run_demo import run_demo


def test_policy_interface_excludes_oracle_and_scenario_metadata() -> None:
    data = generate_transactions()
    visible = data.loc[:, POLICY_VISIBLE_COLUMNS]
    assert "oracle_required_action" not in visible
    assert not {"scenario_id", "scenario_type", "scenario_step"}.intersection(visible.columns)
    decisions = apply_policies(data)
    assert len(decisions) == len(data)


def test_metrics_reconcile_to_decision_rows() -> None:
    decisions = apply_policies(generate_transactions())
    metrics = compare_policies(decisions).set_index("policy")
    for policy in ("fixed", "mcab"):
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


def test_policies_differ_on_aggregation_and_show_tradeoff() -> None:
    metrics = compare_policies(apply_policies(generate_transactions())).set_index("policy")
    assert metrics.loc["mcab", "aggregation_failures_n"] < metrics.loc["fixed", "aggregation_failures_n"]
    assert metrics.loc["mcab", "unauthorised_economic_exposure"] < metrics.loc["fixed", "unauthorised_economic_exposure"]
    assert metrics.loc["mcab", "non_autonomous_intervention_n"] > metrics.loc["fixed", "non_autonomous_intervention_n"]


def test_sensitivity_has_three_separate_designs() -> None:
    sensitivity = sensitivity_analysis(generate_transactions())
    assert set(sensitivity["analysis"]) == {"primary_matched_50000", "mcab_only_design", "matched_budget"}
    primary = sensitivity[sensitivity["analysis"] == "primary_matched_50000"]
    assert set(primary["fixed_threshold"]) == {50_000.0}
    assert set(primary["mcab_initial_budget"]) == {50_000.0}
    mcab_design = sensitivity[sensitivity["analysis"] == "mcab_only_design"]
    assert set(mcab_design["fixed_threshold"]) == {50_000.0}
    assert 1.0 in set(mcab_design["post_error_multiplier"])
    no_tightening = mcab_design[mcab_design["post_error_multiplier"] == 1.0]
    assert set(no_tightening["post_error_condition"]) == {"no_tightening_aggregation_only"}
    matched = sensitivity[sensitivity["analysis"] == "matched_budget"]
    assert (matched["fixed_threshold"] == matched["mcab_initial_budget"]).all()


def test_action_confusion_preserves_review_and_block_severity() -> None:
    decisions = apply_policies(generate_transactions())
    confusion = action_confusion(decisions)
    assert len(confusion) == 18
    assert set(confusion["oracle_action"]) == {"AUTO_EXECUTE", "INDEPENDENT_REVIEW", "BLOCK"}
    assert set(confusion["policy_action"]) == {"AUTO_EXECUTE", "INDEPENDENT_REVIEW", "BLOCK"}
    assert (confusion.groupby("policy")["count"].sum() == len(decisions)).all()


def test_demo_writes_complete_outputs(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    copyfile(root / "README.md", tmp_path / "README.md")
    metrics_path, chart_path = run_demo(tmp_path)
    assert metrics_path.is_file() and chart_path.is_file()
    assert chart_path.stat().st_size > 10_000
    assert (tmp_path / "data" / "synthetic_transactions.csv").is_file()
    assert (tmp_path / "outputs" / "policy_decisions.csv").is_file()
    assert (tmp_path / "outputs" / "sensitivity_analysis.csv").is_file()
    assert (tmp_path / "outputs" / "action_confusion.csv").is_file()
    assert (tmp_path / "outputs" / "results_summary.md").is_file()
    metrics = pd.read_csv(metrics_path)
    assert set(metrics["policy"]) == {"fixed", "mcab"}
    expected = results_summary_text(
        tmp_path / "outputs" / "policy_decisions.csv",
        tmp_path / "outputs" / "policy_comparison.csv",
        tmp_path / "outputs" / "sensitivity_analysis.csv",
        tmp_path / "outputs" / "action_confusion.csv",
    )
    assert (tmp_path / "outputs" / "results_summary.md").read_text(encoding="utf-8") == expected
    assert readme_primary_results_text(metrics_path) in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_checked_in_results_summary_matches_current_csv_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = results_summary_text(
        root / "outputs" / "policy_decisions.csv",
        root / "outputs" / "policy_comparison.csv",
        root / "outputs" / "sensitivity_analysis.csv",
        root / "outputs" / "action_confusion.csv",
    )
    assert (root / "outputs" / "results_summary.md").read_text(encoding="utf-8") == expected
    assert readme_primary_results_text(root / "outputs" / "policy_comparison.csv") in (
        root / "README.md"
    ).read_text(encoding="utf-8")
