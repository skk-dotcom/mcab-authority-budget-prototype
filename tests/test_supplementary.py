"""Supplementary exact-exposure and recurrence-sensitivity tests."""

import csv
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest

from mcab_prototype.domain import Action
from mcab_prototype.evaluate import apply_policies, compare_policies
from mcab_prototype.generate_data import generate_transactions
from mcab_prototype.oracle import OraclePatternConfig, adjudicate_oracle
from mcab_prototype.supplementary import (
    CALIBRATION_BRANCHES,
    MAXIMUM_RATIO_TEMPLATE,
    ORACLE_CONFIGURATIONS,
    OVERALL_BRANCHES,
    POLICY_ORDER,
    SENSITIVITY_BRANCH_A,
    SENSITIVITY_BRANCH_B_TEMPLATE,
    TIGHTENING_BRANCHES,
    exact_exposure,
    exposure_difference_decomposition,
    observed_interpretations,
    oracle_sensitivity_analysis,
    supplementary_policy_metrics,
)


FROZEN_BASE_HASHES = {
    "data/synthetic_transactions.csv": "e11ed1e2714d899ad12a51ada6968655608e706fbb1814be6a512fbc7f3b9f28",
    "outputs/policy_decisions.csv": "694c3e8d08d066a1a4292f5d1ddf98ff18f9166ae4994bc7d7e6f761efb883c5",
    "outputs/policy_comparison.csv": "a9c51cb783fb1860c1ffe844f929b93622b7505652c5acb0527044f12fee22bb",
    "outputs/policy_entity_comparison.csv": "23bdbd12e0edb5c640861e1d3f562d05e0a7a686fcd4358cb125ab5101e83701",
    "outputs/mechanism_decomposition.csv": "c45a3bf22fee4d462fcb8a80361c1ecffcdbd0fd5bb52374c0a32be58eea0b64",
    "outputs/sensitivity_analysis.csv": "4b1c61994db559ebf6761e4108dcf094725947396301e22bf3100792463c1c4c",
    "outputs/action_confusion.csv": "4d00e2e036b041f23bb906d0e5df9790b66a576785527821cf57fa5e92931231",
}
PUBLIC_PREDECLARATION_BYTES = 19_593
PUBLIC_PREDECLARATION_SHA256 = "d92822718eb382f7284dbaede870e6c600c3309723f6af3ed4ecab50489e4402"
CANONICAL_TEXTS_SHA256 = "3431f65b15a5d48840f18d2177f46189d20cd9b15fc315eb9acfbbdba58b36d4"


def test_exact_exposure_is_hand_checkable_and_filters_non_failures() -> None:
    decisions = pd.DataFrame({
        "entity": ["ENTITY_SMALL", "ENTITY_REFERENCE", "ENTITY_LARGE", "ENTITY_SMALL"],
        "amount": [1_000, 5_000, 10_000, 2_000],
        "oracle_required_action": [
            Action.INDEPENDENT_REVIEW.value,
            Action.BLOCK.value,
            Action.INDEPENDENT_REVIEW.value,
            Action.AUTO_EXECUTE.value,
        ],
        "fixed_action": [
            Action.AUTO_EXECUTE.value,
            Action.AUTO_EXECUTE.value,
            Action.INDEPENDENT_REVIEW.value,
            Action.AUTO_EXECUTE.value,
        ],
    })

    exposure = exact_exposure(decisions, "fixed")

    assert exposure.failure_count == 2
    assert exposure.gross_cents == 600_000
    assert exposure.entity_ratios == {
        "ENTITY_SMALL": Fraction(1_000, 250_000),
        "ENTITY_REFERENCE": Fraction(5_000, 500_000),
        "ENTITY_LARGE": Fraction(0),
    }
    assert exposure.summed_anchor_equivalents == Fraction(7, 500)
    assert exposure.maximum_entity_ratio == Fraction(1, 100)


def test_exact_exposure_zero_failure_case_is_zero() -> None:
    decisions = pd.DataFrame({
        "entity": ["ENTITY_SMALL"],
        "amount": [1_000],
        "oracle_required_action": [Action.INDEPENDENT_REVIEW.value],
        "fixed_action": [Action.INDEPENDENT_REVIEW.value],
    })
    exposure = exact_exposure(decisions, "fixed")
    assert exposure.failure_count == 0
    assert exposure.gross_cents == 0
    assert exposure.summed_anchor_equivalents == 0
    assert exposure.maximum_entity_ratio == 0


def test_supplementary_base_values_reconcile_to_primary_metrics() -> None:
    decisions = apply_policies(generate_transactions())
    primary = compare_policies(decisions).set_index("policy")
    supplementary = supplementary_policy_metrics(decisions).set_index("policy")

    for policy in POLICY_ORDER:
        exact = exact_exposure(decisions, policy)
        row = supplementary.loc[policy]
        assert row["consequential_failure_numerator"] == primary.loc[policy, "consequential_failures_n"]
        assert row["absolute_dollar_exposure"] == primary.loc[policy, "unauthorised_economic_exposure"]
        assert row["combined_intervention_n"] == primary.loc[policy, "non_autonomous_intervention_n"]
        assert row["maximum_entity_anchor_ratio"] == round(float(exact.maximum_entity_ratio), 4)
        assert row["anchor_normalised_exposure"] == round(float(exact.summed_anchor_equivalents), 4)


def test_oracle_sensitivity_preserves_base_labels_policy_decisions_and_interventions() -> None:
    transactions = generate_transactions()
    decisions = apply_policies(transactions)
    original = decisions.copy(deep=True)
    sensitivity = oracle_sensitivity_analysis(transactions, decisions)

    pd.testing.assert_frame_equal(decisions, original)
    base_oracle = adjudicate_oracle(
        transactions.drop(columns="oracle_required_action"),
        OraclePatternConfig(6, 3),
    )
    pd.testing.assert_series_equal(
        base_oracle,
        transactions["oracle_required_action"],
        check_names=False,
    )
    for policy in POLICY_ORDER:
        policy_rows = sensitivity[sensitivity["policy"].eq(policy)]
        assert policy_rows["independent_review_n"].nunique() == 1
        assert policy_rows["block_n"].nunique() == 1
        assert policy_rows["combined_intervention_n"].nunique() == 1


def test_oracle_sensitivity_rates_and_denominators_reconcile() -> None:
    transactions = generate_transactions()
    decisions = apply_policies(transactions)
    sensitivity = oracle_sensitivity_analysis(transactions, decisions).set_index(
        ["configuration", "policy"]
    )
    oracle_input = transactions.drop(columns="oracle_required_action")

    for pre_error, post_error in ORACLE_CONFIGURATIONS:
        configuration = f"{pre_error}/{post_error}"
        oracle = adjudicate_oracle(oracle_input, OraclePatternConfig(pre_error, post_error))
        required = oracle.ne(Action.AUTO_EXECUTE.value)
        for policy in POLICY_ORDER:
            row = sensitivity.loc[(configuration, policy)]
            action = decisions[f"{policy}_action"]
            missed = action.eq(Action.AUTO_EXECUTE.value) & required
            false_escalation = action.ne(Action.AUTO_EXECUTE.value) & ~required
            assert row["oracle_escalation_numerator"] == int(required.sum())
            assert row["oracle_escalation_denominator"] == len(decisions)
            assert row["conditional_miss_numerator"] == int(missed.sum())
            assert row["conditional_miss_denominator"] == int(required.sum())
            assert row["false_escalation_numerator"] == int(false_escalation.sum())
            assert row["false_escalation_denominator"] == int((~required).sum())
            assert row["absolute_dollar_exposure"] == decisions.loc[missed, "amount"].sum()


def test_oracle_sensitivity_is_deterministic() -> None:
    transactions = generate_transactions()
    decisions = apply_policies(transactions)
    pd.testing.assert_frame_equal(
        oracle_sensitivity_analysis(transactions, decisions),
        oracle_sensitivity_analysis(transactions, decisions),
    )


def test_oracle_sensitivity_rejects_misaligned_decisions() -> None:
    transactions = generate_transactions()
    decisions = apply_policies(transactions).iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="identical ordered identifiers"):
        oracle_sensitivity_analysis(transactions, decisions)


def test_exposure_decomposition_reconciles_each_partition() -> None:
    decisions = apply_policies(generate_transactions())
    decomposition = exposure_difference_decomposition(decisions)
    primary = compare_policies(decisions).set_index("policy")
    totals = decomposition[decomposition["group"].eq("TOTAL")]

    assert set(totals["dimension"]) == {"entity", "scenario_type", "error_status", "workflow"}
    assert (totals["uniform_failure_count"] == primary.loc["uniform_cap", "consequential_failures_n"]).all()
    assert (
        totals["uniform_absolute_dollar_exposure"]
        == primary.loc["uniform_cap", "unauthorised_economic_exposure"]
    ).all()
    assert (totals["full_mcab_failure_count"] == primary.loc["mcab_full", "consequential_failures_n"]).all()
    assert (
        totals["full_mcab_absolute_dollar_exposure"]
        == primary.loc["mcab_full", "unauthorised_economic_exposure"]
    ).all()
    assert (totals["exposure_difference_full_minus_uniform"] == 194_825).all()


def test_exact_predeclared_branches_and_maximum_template_are_applied() -> None:
    transactions = generate_transactions()
    decisions = apply_policies(transactions)
    sensitivity = oracle_sensitivity_analysis(transactions, decisions)
    observed = observed_interpretations(decisions, sensitivity)

    assert observed["overall_branch"] == "A"
    assert observed["calibration_branch"] == "B"
    assert observed["tightening_branch"] == "A"
    assert observed["sensitivity_branch"] == "B"
    assert observed["changed_sensitivity_configurations"] == ["4/3"]
    assert observed["sensitivity_orders"]["4/3"] == (
        "Full MCAB < Uniform cumulative cap < MCAB no tightening < Fixed threshold"
    )
    assert observed["sensitivity_orders"]["6/3"] == (
        "Full MCAB < MCAB no tightening < Uniform cumulative cap < Fixed threshold"
    )
    assert "0.3493 (34.9300%)" in observed["maximum_ratio_statement"]
    assert "MCAB no tightening–ENTITY_LARGE" in observed["maximum_ratio_statement"]
    assert "[computed" not in observed["maximum_ratio_statement"]

    repository = observed["exact_repository_exposure"]
    assert repository["uniform_cap"].summed_anchor_equivalents == Fraction(3719, 10_000)
    assert repository["mcab_no_tightening"].summed_anchor_equivalents == Fraction(5129, 10_000)
    assert repository["mcab_full"].summed_anchor_equivalents == Fraction(3533, 10_000)
    mechanism_calibration = observed["exact_mechanism_calibration_exposure"]
    assert mechanism_calibration["uniform_cap"].summed_anchor_equivalents == Fraction(1869, 10_000)
    assert mechanism_calibration["mcab_no_tightening"].summed_anchor_equivalents == Fraction(243, 5_000)
    mechanism_tightening = observed["exact_mechanism_tightening_exposure"]
    assert mechanism_tightening["mcab_no_tightening"].summed_anchor_equivalents == Fraction(123, 625)
    assert mechanism_tightening["mcab_full"].summed_anchor_equivalents == Fraction(93, 2_500)
    assert (
        mechanism_calibration["mcab_no_tightening"].summed_anchor_equivalents
        < mechanism_calibration["uniform_cap"].summed_anchor_equivalents
    )
    assert observed["calibration_branch"] == "B"

    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    for key in ("overall_text", "calibration_text", "tightening_text", "sensitivity_text"):
        assert observed[key] in readme
    assert observed["maximum_ratio_statement"] in readme


def test_exact_repository_values_control_branch_when_display_values_tie() -> None:
    decisions = pd.DataFrame({
        "entity": ["ENTITY_SMALL", "ENTITY_SMALL"],
        "amount": [0.01, 0.01],
        "oracle_required_action": [Action.INDEPENDENT_REVIEW.value] * 2,
        "scenario_type": ["aggregation_pressure"] * 2,
        "fixed_action": [Action.INDEPENDENT_REVIEW.value] * 2,
        "uniform_cap_action": [Action.AUTO_EXECUTE.value, Action.INDEPENDENT_REVIEW.value],
        "mcab_no_tightening_action": [Action.AUTO_EXECUTE.value] * 2,
        "mcab_full_action": [Action.AUTO_EXECUTE.value, Action.INDEPENDENT_REVIEW.value],
    })
    sensitivity = pd.DataFrame([
        {
            "configuration": configuration,
            "policy": policy,
            "conditional_miss_numerator": numerator,
            "conditional_miss_denominator": 100,
        }
        for configuration in ("4/3", "6/3", "8/3", "6/2", "6/4")
        for policy, numerator in zip(POLICY_ORDER, (4, 3, 2, 1), strict=True)
    ])
    observed = observed_interpretations(decisions, sensitivity)
    repository = observed["exact_repository_exposure"]
    uniform = repository["uniform_cap"].summed_anchor_equivalents
    no_tightening = repository["mcab_no_tightening"].summed_anchor_equivalents
    assert round(float(uniform), 4) == round(float(no_tightening), 4) == 0.0
    assert no_tightening > uniform
    assert observed["calibration_branch"] == "B"


def test_public_predeclaration_prefix_and_canonical_texts_are_unchanged() -> None:
    root = Path(__file__).resolve().parents[1]
    decisions = (root / "DECISIONS.md").read_bytes().replace(b"\r\n", b"\n")
    assert sha256(decisions[:PUBLIC_PREDECLARATION_BYTES]).hexdigest() == PUBLIC_PREDECLARATION_SHA256
    canonical = "\n".join([
        *OVERALL_BRANCHES.values(),
        *CALIBRATION_BRANCHES.values(),
        *TIGHTENING_BRANCHES.values(),
        SENSITIVITY_BRANCH_A,
        SENSITIVITY_BRANCH_B_TEMPLATE,
        MAXIMUM_RATIO_TEMPLATE,
    ]).encode("utf-8")
    assert sha256(canonical).hexdigest() == CANONICAL_TEXTS_SHA256


def test_isolated_significance_failures_affect_both_mcab_conditions() -> None:
    decisions = apply_policies(generate_transactions())
    isolated = decisions[decisions["scenario_type"].eq("isolated_significance")]
    for policy in ("mcab_no_tightening", "mcab_full"):
        exposure = exact_exposure(isolated, policy)
        assert exposure.failure_count == 4
        assert exposure.gross_cents == 26_750_000
    assert exact_exposure(isolated, "uniform_cap").failure_count == 0


def test_eight_three_false_escalations_are_oracle_relabelling() -> None:
    transactions = generate_transactions()
    decisions = apply_policies(transactions)
    oracle_input = transactions.drop(columns="oracle_required_action")
    oracle_six = adjudicate_oracle(oracle_input, OraclePatternConfig(6, 3))
    oracle_eight = adjudicate_oracle(oracle_input, OraclePatternConfig(8, 3))
    expected = {
        "uniform_cap": (5, 12, 7),
        "mcab_no_tightening": (0, 9, 9),
        "mcab_full": (0, 9, 9),
    }
    for policy, (base_false, eight_false, newly_relabelled) in expected.items():
        action = decisions[f"{policy}_action"]
        assert int((action.ne(Action.AUTO_EXECUTE.value) & oracle_six.eq(Action.AUTO_EXECUTE.value)).sum()) == base_false
        assert int((action.ne(Action.AUTO_EXECUTE.value) & oracle_eight.eq(Action.AUTO_EXECUTE.value)).sum()) == eight_false
        relabelled = (
            action.ne(Action.AUTO_EXECUTE.value)
            & oracle_six.ne(Action.AUTO_EXECUTE.value)
            & oracle_eight.eq(Action.AUTO_EXECUTE.value)
        )
        assert int(relabelled.sum()) == newly_relabelled
        assert set(decisions.loc[relabelled, "scenario_step"]) <= {6, 7}


def test_fixed_entity_ratios_follow_proportional_failure_contributions() -> None:
    decisions = apply_policies(generate_transactions())
    anchors = {
        "ENTITY_SMALL": 250_000,
        "ENTITY_REFERENCE": 500_000,
        "ENTITY_LARGE": 1_000_000,
    }
    scales = {"ENTITY_SMALL": 0.5, "ENTITY_REFERENCE": 1.0, "ENTITY_LARGE": 2.0}
    normalised_sequences: dict[str, list[float]] = {}
    for entity in anchors:
        failed = decisions[
            decisions["entity"].eq(entity)
            & decisions["fixed_action"].eq(Action.AUTO_EXECUTE.value)
            & decisions["oracle_required_action"].ne(Action.AUTO_EXECUTE.value)
        ].sort_values(["scenario_type", "workflow", "scenario_step"])
        assert len(failed) == 18
        assert Fraction(int(failed["amount"].sum()), anchors[entity]) == Fraction(2777, 10_000)
        normalised_sequences[entity] = (failed["amount"] / scales[entity]).tolist()
    assert normalised_sequences["ENTITY_SMALL"] == normalised_sequences["ENTITY_REFERENCE"]
    assert normalised_sequences["ENTITY_LARGE"] == normalised_sequences["ENTITY_REFERENCE"]


def test_public_docs_show_corrective_tables_sensitivity_and_factorial_limit() -> None:
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    summary = (root / "outputs" / "results_summary.md").read_text(encoding="utf-8")
    limitation = (
        "The policy ladder is not a complete 2×2 factorial because it contains no "
        "uniform-cap-with-tightening condition."
    )
    for text in (readme, summary):
        assert "Repository-level calibration contrast" in text
        assert "Uniform cap and Full MCAB: mixed repository-level measures" in text
        assert "Calibration Branch B" in text
        assert "Sensitivity Branch B" in text
        assert "Full MCAB < Uniform cumulative cap < MCAB no tightening < Fixed threshold" in text
        assert limitation in text
        assert "No entity calibration | Uniform cap | Not implemented" in text
        assert "12/198" in text and text.count("9/198") >= 2
    assert "uniform_cap_with_tightening" not in " ".join(POLICY_ORDER)


def test_frozen_base_artifact_hashes_are_unchanged() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative, expected in FROZEN_BASE_HASHES.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == expected


def test_tracked_supplementary_ratios_use_four_decimal_places() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "outputs/supplementary_policy_metrics.csv",
        "outputs/oracle_sensitivity_analysis.csv",
    ):
        with (root / relative).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            for column in (
                "anchor_normalised_exposure",
                "entity_small_anchor_ratio",
                "entity_reference_anchor_ratio",
                "entity_large_anchor_ratio",
                "maximum_entity_anchor_ratio",
            ):
                whole, decimal = row[column].split(".")
                assert whole.isdigit() and len(decimal) == 4 and decimal.isdigit()
