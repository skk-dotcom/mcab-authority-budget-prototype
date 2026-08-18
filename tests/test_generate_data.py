"""Tests for deterministic, synthetic data generation."""

import pandas as pd

from mcab_prototype.generate_data import ROW_COUNT, generate_transactions


def test_identical_seed_produces_identical_data() -> None:
    pd.testing.assert_frame_equal(generate_transactions(20260818), generate_transactions(20260818))


def test_different_seed_changes_seeded_ordinary_rows() -> None:
    first = generate_transactions(1)
    second = generate_transactions(2)
    assert not first.loc[first["scenario_type"] == "ordinary_low_risk", "amount"].equals(
        second.loc[second["scenario_type"] == "ordinary_low_risk", "amount"]
    )


def test_dataset_shape_and_scenarios() -> None:
    data = generate_transactions()
    assert len(data) == ROW_COUNT
    assert data["transaction_id"].is_unique
    assert set(data["workflow"]) == {"procure_to_pay", "journal_entry_month_end_close"}
    assert {"ordinary_low_risk", "aggregation_pressure", "qualitative_risk", "post_error_accumulation"}.issubset(
        set(data["scenario_type"])
    )
    assert (data["amount"] > 0).all()
    assert not data.isna().any().any()


def test_confirmed_error_signal_precedes_post_error_sequence() -> None:
    data = generate_transactions()
    signal = int(data.loc[data["confirmed_control_error"], "sequence_number"].item())
    post_error = data.loc[data["scenario_type"] == "post_error_accumulation", "sequence_number"]
    assert len(data.loc[data["confirmed_control_error"]]) == 1
    assert (post_error > signal).all()
