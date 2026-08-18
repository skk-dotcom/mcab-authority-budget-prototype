"""Unit tests for the four policy conditions and shared boundaries."""

import pandas as pd
import pytest

from conftest import policy_frame
from mcab_prototype.domain import Action, QualitativeFlag
from mcab_prototype.generate_data import generate_transactions
from mcab_prototype.policies import (
    CumulativeCapConfig,
    CumulativeCapPolicy,
    FixedPolicyConfig,
    FixedThresholdPolicy,
    MCABConfig,
    MCABPolicy,
)


def test_fixed_threshold_boundary_and_above_threshold() -> None:
    decisions = FixedThresholdPolicy().run(policy_frame([49_999, 50_000, 50_001]))
    assert decisions["action"].tolist() == [
        Action.AUTO_EXECUTE.value,
        Action.AUTO_EXECUTE.value,
        Action.INDEPENDENT_REVIEW.value,
    ]


def test_fixed_policy_remains_stateless_for_repeated_small_transactions() -> None:
    decisions = FixedThresholdPolicy().run(policy_frame([20_000, 20_000, 20_000]))
    assert set(decisions["action"]) == {Action.AUTO_EXECUTE.value}
    assert decisions["utilisation_before"].isna().all()


def test_uniform_cap_escalates_only_above_cumulative_cap() -> None:
    decisions = CumulativeCapPolicy().run(policy_frame([20_000, 20_000, 10_000, 1]))
    assert decisions["action"].tolist() == [
        Action.AUTO_EXECUTE.value,
        Action.AUTO_EXECUTE.value,
        Action.AUTO_EXECUTE.value,
        Action.INDEPENDENT_REVIEW.value,
    ]
    assert decisions.loc[2, "utilisation_after"] == 50_000


def test_uniform_cap_is_equal_across_entities() -> None:
    frame = policy_frame(
        [30_000, 30_000, 21_000, 21_000],
        entities=["ENTITY_SMALL", "ENTITY_LARGE", "ENTITY_SMALL", "ENTITY_LARGE"],
    )
    decisions = CumulativeCapPolicy().run(frame)
    assert set(decisions["initial_budget"]) == {50_000.0}
    assert decisions["action"].tolist() == [
        Action.AUTO_EXECUTE.value,
        Action.AUTO_EXECUTE.value,
        Action.INDEPENDENT_REVIEW.value,
        Action.INDEPENDENT_REVIEW.value,
    ]


@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        (QualitativeFlag.RELATED_PARTY.value, Action.INDEPENDENT_REVIEW.value),
        (QualitativeFlag.BANK_CHANGE.value, Action.BLOCK.value),
        (QualitativeFlag.NON_STANDARD_JOURNAL.value, Action.INDEPENDENT_REVIEW.value),
        (QualitativeFlag.MANAGEMENT_OVERRIDE.value, Action.BLOCK.value),
        (QualitativeFlag.PERIOD_END.value, Action.INDEPENDENT_REVIEW.value),
    ],
)
def test_frozen_qualitative_overrides_apply_to_all_policies(flag: str, expected: str) -> None:
    frame = policy_frame([100], flags=[flag])
    policies = (
        FixedThresholdPolicy(),
        CumulativeCapPolicy(),
        MCABPolicy(MCABConfig(post_error_multiplier=1.0)),
        MCABPolicy(),
    )
    assert {policy.run(frame).loc[0, "action"] for policy in policies} == {expected}


@pytest.mark.parametrize(
    "policy",
    [
        CumulativeCapPolicy(),
        MCABPolicy(MCABConfig(post_error_multiplier=1.0)),
        MCABPolicy(),
    ],
)
def test_reviewed_or_blocked_amounts_do_not_consume_cumulative_authority(policy: object) -> None:
    frame = policy_frame(
        [40_000, 30_000, 20_000, 1],
        flags=[
            QualitativeFlag.RELATED_PARTY.value,
            QualitativeFlag.NONE.value,
            QualitativeFlag.NONE.value,
            QualitativeFlag.NONE.value,
        ],
    )
    decisions = policy.run(frame)  # type: ignore[union-attr]
    assert decisions.loc[0, "utilisation_after"] == 0
    assert decisions.loc[2, "utilisation_after"] == 50_000
    assert decisions.loc[3, "action"] == Action.INDEPENDENT_REVIEW.value


def test_mcab_uses_entity_specific_budgets() -> None:
    frame = policy_frame(
        [20_000, 40_000, 80_000],
        entities=["ENTITY_SMALL", "ENTITY_REFERENCE", "ENTITY_LARGE"],
    )
    decisions = MCABPolicy(MCABConfig(post_error_multiplier=1.0)).run(frame)
    assert decisions["initial_budget"].tolist() == [25_000.0, 50_000.0, 100_000.0]
    assert set(decisions["action"]) == {Action.AUTO_EXECUTE.value}


def test_uniform_cap_matches_no_tightening_mcab_for_reference_entity() -> None:
    reference = generate_transactions().query("entity == 'ENTITY_REFERENCE'")
    visible = reference.drop(columns=["scenario_id", "scenario_type", "scenario_step", "oracle_required_action"])
    uniform = CumulativeCapPolicy().run(visible)
    no_tightening = MCABPolicy(MCABConfig(post_error_multiplier=1.0)).run(visible)
    pd.testing.assert_series_equal(uniform["action"], no_tightening["action"])
    pd.testing.assert_series_equal(uniform["utilisation_after"], no_tightening["utilisation_after"])


def test_multiplier_one_is_no_tightening_ablation() -> None:
    frame = policy_frame(
        [20_000, 1_000, 20_000],
        flags=[QualitativeFlag.NONE.value, QualitativeFlag.MANAGEMENT_OVERRIDE.value, QualitativeFlag.NONE.value],
        errors=[False, True, False],
    )
    decisions = MCABPolicy(MCABConfig(post_error_multiplier=1.0)).run(frame)
    assert not decisions["tightening_triggered_after"].any()
    assert decisions.loc[2, "effective_budget"] == 50_000
    assert decisions.loc[2, "action"] == Action.AUTO_EXECUTE.value


def test_full_mcab_tightens_later_budget_and_retains_utilisation() -> None:
    frame = policy_frame(
        [20_000, 1_000, 5_000, 1],
        flags=[
            QualitativeFlag.NONE.value,
            QualitativeFlag.MANAGEMENT_OVERRIDE.value,
            QualitativeFlag.NONE.value,
            QualitativeFlag.NONE.value,
        ],
        errors=[False, True, False, False],
    )
    decisions = MCABPolicy().run(frame)
    assert decisions.loc[1, "effective_budget"] == 50_000
    assert decisions.loc[1, "tightening_triggered_after"]
    assert decisions.loc[2, "effective_budget"] == 25_000
    assert decisions.loc[2, "utilisation_before"] == 20_000
    assert decisions.loc[3, "action"] == Action.INDEPENDENT_REVIEW.value


def test_tightening_scope_is_entity_and_workflow() -> None:
    frame = policy_frame(
        [1_000, 1_000, 1_000, 1_000],
        flags=[QualitativeFlag.MANAGEMENT_OVERRIDE.value] + [QualitativeFlag.NONE.value] * 3,
        errors=[True, False, False, False],
        entities=["ENTITY_REFERENCE", "ENTITY_REFERENCE", "ENTITY_LARGE", "ENTITY_REFERENCE"],
        workflows=["procure_to_pay", "procure_to_pay", "procure_to_pay", "journal_entry_month_end_close"],
        accounts=["a", "b", "b", "b"],
    )
    decisions = MCABPolicy().run(frame)
    assert decisions.loc[1, "effective_budget"] == 25_000
    assert decisions.loc[2, "effective_budget"] == 100_000
    assert decisions.loc[3, "effective_budget"] == 50_000


def test_cumulative_risk_cell_includes_counterparty() -> None:
    frame = policy_frame(
        [30_000, 30_000],
        counterparties=["SYNTH_A", "SYNTH_B"],
    )
    decisions = CumulativeCapPolicy().run(frame)
    assert set(decisions["action"]) == {Action.AUTO_EXECUTE.value}
    assert decisions["risk_cell"].nunique() == 2


def test_empty_input_returns_all_empty_decision_tables() -> None:
    assert FixedThresholdPolicy().run(pd.DataFrame()).empty
    assert CumulativeCapPolicy().run(pd.DataFrame()).empty
    assert MCABPolicy().run(pd.DataFrame()).empty


def test_invalid_and_oracle_bearing_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        FixedThresholdPolicy().run(policy_frame([-1]))
    with pytest.raises(ValueError, match="scenario-only"):
        CumulativeCapPolicy().run(generate_transactions())
    with pytest.raises(ValueError, match="positive"):
        FixedPolicyConfig(0)
    with pytest.raises(ValueError, match="positive"):
        CumulativeCapConfig(0)
    with pytest.raises(ValueError, match="exceed"):
        MCABConfig(post_error_multiplier=1.1)
    with pytest.raises(ValueError, match="No MCAB"):
        MCABPolicy().run(policy_frame([1], entities=["UNKNOWN_ENTITY"]))
