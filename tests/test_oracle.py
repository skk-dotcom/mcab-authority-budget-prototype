"""Tests for pattern boundaries and oracle isolation."""

import ast
from pathlib import Path

import pandas as pd
import pytest

import mcab_prototype.oracle as oracle_module
from mcab_prototype.domain import POLICY_VISIBLE_COLUMNS
from mcab_prototype.generate_data import ENTITY_SCALE_FACTORS, generate_transactions
from mcab_prototype.oracle import OraclePatternConfig, adjudicate_oracle
from mcab_prototype.policies import (
    CumulativeCapConfig,
    CumulativeCapPolicy,
    FixedPolicyConfig,
    FixedThresholdPolicy,
    MCABConfig,
    MCABPolicy,
)


def test_pre_error_pattern_boundary_is_sixth_occurrence() -> None:
    data = generate_transactions()
    aggregation = data[data["scenario_type"].eq("aggregation_pressure")]
    for _, scenario in aggregation.groupby("scenario_id"):
        ordered = scenario.sort_values("scenario_step")
        assert ordered.iloc[:5]["oracle_required_action"].eq("AUTO_EXECUTE").all()
        assert ordered.iloc[5:]["oracle_required_action"].eq("INDEPENDENT_REVIEW").all()


def test_post_error_pattern_boundary_is_third_fresh_occurrence() -> None:
    data = generate_transactions()
    post_error = data[data["scenario_type"].eq("post_error_accumulation")]
    for _, scenario in post_error.groupby("scenario_id"):
        ordered = scenario.sort_values("scenario_step")
        assert ordered.iloc[:2]["oracle_required_action"].eq("AUTO_EXECUTE").all()
        assert ordered.iloc[2:]["oracle_required_action"].eq("INDEPENDENT_REVIEW").all()


def test_qualitative_and_isolated_oracle_actions_remain_separate() -> None:
    data = generate_transactions()
    assert set(data.loc[data["qualitative_flag"].eq("management_override_indicator"), "oracle_required_action"]) == {"BLOCK"}
    assert set(data.loc[data["scenario_type"].eq("isolated_significance"), "oracle_required_action"]) == {"INDEPENDENT_REVIEW"}


def test_policy_parameter_changes_do_not_change_oracle_labels() -> None:
    data = generate_transactions()
    policy_input = data.loc[:, POLICY_VISIBLE_COLUMNS]
    expected = data["oracle_required_action"].copy()
    anchors = tuple((entity, anchor * 3) for entity, anchor in zip(ENTITY_SCALE_FACTORS, (250_000, 500_000, 1_000_000), strict=True))
    policy_runs = (
        FixedThresholdPolicy(FixedPolicyConfig(25_000)).run(policy_input),
        FixedThresholdPolicy(FixedPolicyConfig(100_000)).run(policy_input),
        CumulativeCapPolicy(CumulativeCapConfig(25_000)).run(policy_input),
        CumulativeCapPolicy(CumulativeCapConfig(100_000)).run(policy_input),
        MCABPolicy(MCABConfig(safety_factor=0.05, post_error_multiplier=1.0)).run(policy_input),
        MCABPolicy(MCABConfig(entity_anchors=anchors, safety_factor=0.15, post_error_multiplier=0.25)).run(policy_input),
    )
    assert len({tuple(run["action"]) for run in policy_runs}) > 1
    pd.testing.assert_series_equal(adjudicate_oracle(data), expected)


def test_oracle_module_imports_no_policy_code_or_configuration() -> None:
    source = Path(oracle_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: list[str] = []
    accessed_columns: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            accessed_columns.add(node.slice.value)
    assert not any(name.endswith("policies") or ".policies" in name for name in imported)
    assert accessed_columns.isdisjoint({
        "amount", "threshold", "cap", "materiality_anchor", "safety_factor",
        "post_error_multiplier", "scenario_step", "oracle_required_action",
    })


def test_non_recurrence_cases_do_not_contaminate_occurrence_count() -> None:
    rows = []
    cases = [
        ("ordinary_low_risk", "none"),
        ("qualitative_risk", "related_party_activity"),
        ("isolated_significance", "none"),
        ("ordinary_low_risk", "none"),
        ("aggregation_pressure", "none"),
    ]
    for index, (scenario_type, flag) in enumerate(cases, start=1):
        rows.append({
            "sequence_number": index,
            "workflow": "procure_to_pay",
            "entity": "ENTITY_REFERENCE",
            "reporting_period": "2026-07",
            "account": "shared_cell",
            "counterparty": "SYNTH_SHARED",
            "qualitative_flag": flag,
            "confirmed_control_error": False,
            "scenario_type": scenario_type,
        })
    actions = adjudicate_oracle(pd.DataFrame(rows))
    assert actions.iloc[-1] == "AUTO_EXECUTE"


def test_signal_is_not_post_error_occurrence() -> None:
    rows = [{
        "sequence_number": 1,
        "workflow": "journal_entry_month_end_close",
        "entity": "ENTITY_REFERENCE",
        "reporting_period": "2026-07",
        "account": "same_cell",
        "counterparty": "INTERNAL",
        "qualitative_flag": "management_override_indicator",
        "confirmed_control_error": True,
        "scenario_type": "confirmed_error_signal",
    }]
    for sequence in range(2, 5):
        rows.append({
            **rows[0],
            "sequence_number": sequence,
            "qualitative_flag": "none",
            "confirmed_control_error": False,
            "scenario_type": "post_error_accumulation",
        })
    assert adjudicate_oracle(pd.DataFrame(rows)).tolist() == [
        "BLOCK", "AUTO_EXECUTE", "AUTO_EXECUTE", "INDEPENDENT_REVIEW",
    ]


def test_oracle_rejects_policy_decisions_and_missing_metadata() -> None:
    data = generate_transactions()
    contaminated = data.assign(fixed_action="AUTO_EXECUTE")
    with pytest.raises(ValueError, match="policy decisions"):
        adjudicate_oracle(contaminated)
    with pytest.raises(ValueError, match="missing columns"):
        adjudicate_oracle(pd.DataFrame({"qualitative_flag": ["none"]}))
    with pytest.raises(ValueError, match="at least one"):
        OraclePatternConfig(pre_error_review_from_occurrence=1)
