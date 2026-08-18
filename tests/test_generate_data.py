"""Tests for the frozen deterministic matched-scale dataset."""

import pandas as pd

from mcab_prototype.domain import RISK_CELL_COLUMNS
from mcab_prototype.generate_data import (
    ENTITY_SCALE_FACTORS,
    ISOLATED_SIGNIFICANCE_AMOUNTS,
    JOURNAL_AGGREGATION_BASE,
    P2P_AGGREGATION_BASE,
    POST_ERROR_BASE,
    ROW_COUNT,
    generate_transactions,
)


def test_identical_seed_produces_identical_data() -> None:
    pd.testing.assert_frame_equal(generate_transactions(20260818), generate_transactions(20260818))


def test_different_seed_changes_only_seeded_ordinary_values() -> None:
    first = generate_transactions(1)
    second = generate_transactions(2)
    ordinary = first["scenario_type"].eq("ordinary_low_risk")
    assert not first.loc[ordinary, "amount"].equals(second.loc[ordinary, "amount"])
    pd.testing.assert_series_equal(first.loc[~ordinary, "amount"], second.loc[~ordinary, "amount"])


def test_dataset_shape_entities_and_scenarios() -> None:
    data = generate_transactions()
    assert len(data) == ROW_COUNT == 270
    assert data["transaction_id"].is_unique
    assert data["entity"].value_counts().to_dict() == {entity: 90 for entity in ENTITY_SCALE_FACTORS}
    assert data["scenario_type"].value_counts().to_dict() == {
        "ordinary_low_risk": 150,
        "aggregation_pressure": 60,
        "post_error_accumulation": 30,
        "qualitative_risk": 15,
        "isolated_significance": 12,
        "confirmed_error_signal": 3,
    }
    assert set(data["workflow"]) == {"procure_to_pay", "journal_entry_month_end_close"}
    assert (data["amount"] > 0).all() and not data.isna().any().any()


def test_matched_sequences_scale_exactly_by_entity() -> None:
    data = generate_transactions()
    templates = {
        "AGG_P2P": P2P_AGGREGATION_BASE,
        "AGG_JOURNAL": JOURNAL_AGGREGATION_BASE,
        "POST_ERROR": POST_ERROR_BASE,
    }
    for prefix, template in templates.items():
        for entity, scale in ENTITY_SCALE_FACTORS.items():
            scenario = data[data["scenario_id"].eq(f"{prefix}_{entity}")]
            assert scenario["scenario_step"].tolist() == list(range(1, len(template) + 1))
            assert scenario["amount"].tolist() == [amount * scale for amount in template]


def test_qualitative_mappings_and_isolated_amounts_are_frozen() -> None:
    data = generate_transactions()
    qualitative = data[data["scenario_type"].eq("qualitative_risk")]
    assert qualitative.groupby("entity")["qualitative_flag"].nunique().eq(5).all()
    isolated = data[data["scenario_type"].eq("isolated_significance")]
    assert tuple(isolated["amount"].astype(int)) == ISOLATED_SIGNIFICANCE_AMOUNTS


def test_fixed_threshold_grid_has_disclosed_sparse_interval_support() -> None:
    data = generate_transactions()
    assert int(((data["amount"] > 25_000) & (data["amount"] <= 50_000)).sum()) == 0


def test_aggregation_scenarios_have_distinct_risk_cells() -> None:
    data = generate_transactions()
    aggregation = data[data["scenario_type"].eq("aggregation_pressure")].copy()
    aggregation["risk_cell"] = aggregation.loc[:, RISK_CELL_COLUMNS].astype(str).agg("|".join, axis=1)
    by_scenario = aggregation.groupby("scenario_id")["risk_cell"]
    assert by_scenario.nunique().eq(1).all()
    assert not by_scenario.first().duplicated().any()


def test_non_aggregation_cases_do_not_share_aggregation_risk_cells() -> None:
    data = generate_transactions().copy()
    data["risk_cell"] = data.loc[:, RISK_CELL_COLUMNS].astype(str).agg("|".join, axis=1)
    aggregation_cells = set(data.loc[data["scenario_type"].eq("aggregation_pressure"), "risk_cell"])
    excluded = data[data["scenario_type"].isin(["ordinary_low_risk", "qualitative_risk", "isolated_significance"])]
    assert not aggregation_cells.intersection(excluded["risk_cell"])


def test_confirmed_error_signal_precedes_fresh_post_error_cell() -> None:
    data = generate_transactions().copy()
    data["risk_cell"] = data.loc[:, RISK_CELL_COLUMNS].astype(str).agg("|".join, axis=1)
    for entity in ENTITY_SCALE_FACTORS:
        signal = data[(data["entity"].eq(entity)) & data["confirmed_control_error"]].iloc[0]
        post = data[data["scenario_id"].eq(f"POST_ERROR_{entity}")]
        assert post["sequence_number"].min() == signal["sequence_number"] + 1
        assert post["scenario_step"].tolist() == list(range(1, 11))
        assert post["risk_cell"].nunique() == 1
        assert signal["risk_cell"] != post["risk_cell"].iloc[0]
