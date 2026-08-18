"""Tests for oracle behaviour and technical independence."""

import ast
from pathlib import Path

import pandas as pd

import mcab_prototype.oracle as oracle_module
from mcab_prototype.domain import POLICY_VISIBLE_COLUMNS
from mcab_prototype.generate_data import generate_transactions
from mcab_prototype.oracle import adjudicate_oracle
from mcab_prototype.policies import FixedPolicyConfig, FixedThresholdPolicy, MCABConfig, MCABPolicy


def test_oracle_assigns_authored_scenario_actions() -> None:
    data = generate_transactions()
    p2p = data[data["scenario_id"] == "AGG_P2P"].reset_index(drop=True)
    assert p2p.loc[4, "oracle_required_action"] == "AUTO_EXECUTE"
    assert p2p.loc[5, "oracle_required_action"] == "INDEPENDENT_REVIEW"
    assert set(data.loc[data["scenario_type"] == "isolated_large", "oracle_required_action"]) == {"INDEPENDENT_REVIEW"}
    assert set(data.loc[data["qualitative_flag"] == "management_override_indicator", "oracle_required_action"]) == {"BLOCK"}


def test_policy_configuration_changes_do_not_change_oracle_labels() -> None:
    data = generate_transactions()
    policy_input = data.loc[:, POLICY_VISIBLE_COLUMNS]
    expected = data["oracle_required_action"].copy()
    fixed_low = FixedThresholdPolicy(FixedPolicyConfig(25_000)).run(policy_input)
    fixed_high = FixedThresholdPolicy(FixedPolicyConfig(100_000)).run(policy_input)
    mcab_low = MCABPolicy(MCABConfig(safety_factor=0.05)).run(policy_input)
    mcab_high = MCABPolicy(MCABConfig(safety_factor=0.15, post_error_multiplier=1.0)).run(policy_input)
    assert not fixed_low["action"].equals(fixed_high["action"])
    assert not mcab_low["action"].equals(mcab_high["action"])
    pd.testing.assert_series_equal(adjudicate_oracle(data), expected)


def test_oracle_module_does_not_import_policy_code_or_configuration() -> None:
    source = Path(oracle_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(name.endswith("policies") or ".policies" in name for name in imported)


def test_oracle_rejects_missing_scenario_metadata() -> None:
    incomplete = pd.DataFrame({"qualitative_flag": ["none"]})
    try:
        adjudicate_oracle(incomplete)
    except ValueError as exc:
        assert "missing columns" in str(exc).lower()
    else:
        raise AssertionError("Expected missing oracle metadata to be rejected")
