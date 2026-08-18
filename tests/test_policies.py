"""Unit tests for fixed and stateful MCAB decisions."""

import pandas as pd
import pytest

from conftest import policy_frame
from mcab_prototype.domain import Action, QualitativeFlag
from mcab_prototype.generate_data import generate_transactions
from mcab_prototype.policies import FixedPolicyConfig, FixedThresholdPolicy, MCABConfig, MCABPolicy


def test_fixed_threshold_boundary_and_above_threshold() -> None:
    decisions = FixedThresholdPolicy().run(policy_frame([49_999, 50_000, 50_001]))
    assert decisions["action"].tolist() == [
        Action.AUTO_EXECUTE.value, Action.AUTO_EXECUTE.value, Action.INDEPENDENT_REVIEW.value,
    ]


def test_fixed_policy_does_not_detect_repeated_small_transactions() -> None:
    decisions = FixedThresholdPolicy().run(policy_frame([20_000, 20_000, 20_000]))
    assert set(decisions["action"]) == {Action.AUTO_EXECUTE.value}


def test_mcab_escalates_only_above_cumulative_budget() -> None:
    decisions = MCABPolicy().run(policy_frame([20_000, 20_000, 10_000, 1]))
    assert decisions["action"].tolist() == [
        Action.AUTO_EXECUTE.value, Action.AUTO_EXECUTE.value,
        Action.AUTO_EXECUTE.value, Action.INDEPENDENT_REVIEW.value,
    ]
    assert decisions.loc[2, "utilisation_after"] == 50_000
    assert decisions.loc[3, "utilisation_after"] == 50_000


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
def test_same_qualitative_overrides_apply_to_both_policies(flag: str, expected: str) -> None:
    frame = policy_frame([100], flags=[flag])
    assert FixedThresholdPolicy().run(frame).loc[0, "action"] == expected
    assert MCABPolicy().run(frame).loc[0, "action"] == expected


def test_reviewed_or_blocked_amounts_do_not_consume_mcab_budget() -> None:
    frame = policy_frame(
        [40_000, 30_000, 20_000, 1],
        flags=[QualitativeFlag.RELATED_PARTY.value, QualitativeFlag.NONE.value, QualitativeFlag.NONE.value, QualitativeFlag.NONE.value],
    )
    decisions = MCABPolicy().run(frame)
    assert decisions["action"].tolist() == [
        Action.INDEPENDENT_REVIEW.value, Action.AUTO_EXECUTE.value,
        Action.AUTO_EXECUTE.value, Action.INDEPENDENT_REVIEW.value,
    ]
    assert decisions.loc[0, "utilisation_after"] == 0
    assert decisions.loc[2, "utilisation_after"] == 50_000


def test_confirmed_error_tightens_later_budget_and_retains_utilisation() -> None:
    frame = policy_frame(
        [20_000, 1_000, 5_000, 1],
        flags=[QualitativeFlag.NONE.value, QualitativeFlag.MANAGEMENT_OVERRIDE.value, QualitativeFlag.NONE.value, QualitativeFlag.NONE.value],
        errors=[False, True, False, False],
    )
    decisions = MCABPolicy().run(frame)
    assert decisions.loc[1, "effective_budget"] == 50_000
    assert decisions.loc[1, "tightening_triggered_after"]
    assert decisions.loc[2, "tightening_active_before"]
    assert decisions.loc[2, "effective_budget"] == 25_000
    assert decisions.loc[2, "utilisation_before"] == 20_000
    assert decisions.loc[2, "action"] == Action.AUTO_EXECUTE.value
    assert decisions.loc[3, "action"] == Action.INDEPENDENT_REVIEW.value


def test_multiplier_one_is_no_tightening_condition() -> None:
    frame = policy_frame(
        [20_000, 1_000, 20_000],
        flags=[QualitativeFlag.NONE.value, QualitativeFlag.MANAGEMENT_OVERRIDE.value, QualitativeFlag.NONE.value],
        errors=[False, True, False],
    )
    decisions = MCABPolicy(MCABConfig(post_error_multiplier=1.0)).run(frame)
    assert not decisions["tightening_triggered_after"].any()
    assert decisions.loc[2, "effective_budget"] == 50_000
    assert decisions.loc[2, "action"] == Action.AUTO_EXECUTE.value


def test_tightening_scope_is_entity_and_workflow_and_persists() -> None:
    frame = policy_frame(
        [1_000, 1_000, 1_000, 1_000],
        flags=[QualitativeFlag.MANAGEMENT_OVERRIDE.value] + [QualitativeFlag.NONE.value] * 3,
        errors=[True, False, False, False],
        entities=["ENTITY_A", "ENTITY_A", "ENTITY_B", "ENTITY_A"],
        workflows=["procure_to_pay", "procure_to_pay", "procure_to_pay", "journal_entry_month_end_close"],
        accounts=["a", "b", "b", "b"],
    )
    decisions = MCABPolicy().run(frame)
    assert decisions.loc[1, "effective_budget"] == 25_000
    assert decisions.loc[2, "effective_budget"] == 50_000
    assert decisions.loc[3, "effective_budget"] == 50_000


def test_mcab_risk_cell_includes_entity_period_workflow_and_account() -> None:
    frame = policy_frame(
        [30_000, 30_000, 30_000, 30_000],
        entities=["A", "B", "A", "A"],
        periods=["P1", "P1", "P2", "P1"],
        workflows=["W1", "W1", "W1", "W2"],
        accounts=["X", "X", "X", "X"],
    )
    decisions = MCABPolicy().run(frame)
    assert set(decisions["action"]) == {Action.AUTO_EXECUTE.value}
    assert decisions["risk_cell"].nunique() == 4


def test_unusually_large_transaction_is_escalated_by_mcab() -> None:
    assert MCABPolicy().run(policy_frame([500_000])).loc[0, "action"] == Action.INDEPENDENT_REVIEW.value


def test_empty_input_returns_empty_decision_tables() -> None:
    assert FixedThresholdPolicy().run(pd.DataFrame()).empty
    assert MCABPolicy().run(pd.DataFrame()).empty


def test_invalid_and_oracle_bearing_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        FixedThresholdPolicy().run(policy_frame([-1]))
    full_data = generate_transactions()
    with pytest.raises(ValueError, match="scenario-only"):
        MCABPolicy().run(full_data)
    with pytest.raises(ValueError, match="positive"):
        FixedPolicyConfig(0)
    with pytest.raises(ValueError, match="exceed"):
        MCABConfig(post_error_multiplier=1.1)
