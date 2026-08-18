"""Deterministic matched-scale synthetic transaction generator."""

from collections.abc import Iterable
from types import MappingProxyType
from typing import Mapping

import numpy as np
import pandas as pd

from .domain import POLICY_VISIBLE_COLUMNS, RISK_CELL_COLUMNS, SCENARIO_ONLY_COLUMNS, QualitativeFlag
from .oracle import adjudicate_oracle


DEFAULT_SEED = 20260818
ROW_COUNT = 270

ENTITY_SCALE_FACTORS: Mapping[str, float] = MappingProxyType({
    "ENTITY_SMALL": 0.5,
    "ENTITY_REFERENCE": 1.0,
    "ENTITY_LARGE": 2.0,
})

P2P_AGGREGATION_BASE = (7_800, 8_200, 7_600, 8_400, 7_900, 8_100, 8_300, 7_700, 8_250, 7_950)
JOURNAL_AGGREGATION_BASE = (9_200, 8_800, 9_100, 8_900, 9_000, 9_300, 8_700, 9_150, 8_850, 9_050)
POST_ERROR_BASE = (6_500, 7_000, 6_200, 6_800, 6_400, 7_100, 6_300, 6_900, 6_600, 7_200)
QUALITATIVE_BASE_AMOUNTS = (1_000, 1_275, 1_550, 1_825, 2_100)

# Frozen before the first revised run. Every value comes from the original
# eight isolated-large vignettes; the first four repeat to give four cases per
# revised entity. These cases are excluded from mechanism decomposition.
ISOLATED_SIGNIFICANCE_AMOUNTS = (
    55_000, 62_500, 71_000, 83_000, 95_000, 58_500,
    76_000, 88_000, 55_000, 62_500, 71_000, 83_000,
)

QUALITATIVE_FLAGS = (
    QualitativeFlag.RELATED_PARTY,
    QualitativeFlag.BANK_CHANGE,
    QualitativeFlag.NON_STANDARD_JOURNAL,
    QualitativeFlag.MANAGEMENT_OVERRIDE,
    QualitativeFlag.PERIOD_END,
)


def generate_transactions(seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Create 270 ordered transactions across three synthetic entity scales."""

    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    ordinary_counts = {entity: 0 for entity in ENTITY_SCALE_FACTORS}

    def add(**values: object) -> None:
        sequence = len(rows) + 1
        base: dict[str, object] = {
            "transaction_id": f"TXN{sequence:04d}",
            "sequence_number": sequence,
            "qualitative_flag": QualitativeFlag.NONE.value,
            "reversible": True,
            "confirmed_control_error": False,
            "scenario_step": 1,
        }
        base.update(values)
        rows.append(base)

    def add_ordinary(entity: str, count: int) -> None:
        scale = ENTITY_SCALE_FACTORS[entity]
        for _ in range(count):
            ordinary_counts[entity] += 1
            index = ordinary_counts[entity]
            workflow = str(rng.choice(["procure_to_pay", "journal_entry_month_end_close"]))
            add(
                workflow=workflow,
                entity=entity,
                account=f"ordinary_{entity.lower()}_{index:03d}",
                transaction_type="invoice" if workflow == "procure_to_pay" else "standard_accrual",
                counterparty=f"SYNTH_ORDINARY_{entity}_{index:03d}",
                reporting_period=str(rng.choice(["2026-06", "2026-07"])),
                amount=float(int(rng.integers(1_000, 4_001)) * scale),
                reversible=bool(rng.random() > 0.12),
                scenario_id=f"ORD_{entity}_{index:03d}",
                scenario_type="ordinary_low_risk",
            )

    def add_sequence(
        amounts: Iterable[float], *, scenario_id: str, scenario_type: str,
        workflow: str, entity: str, period: str, account: str,
        transaction_type: str, counterparty: str,
    ) -> None:
        for step, amount in enumerate(amounts, start=1):
            add(
                workflow=workflow,
                entity=entity,
                account=account,
                transaction_type=transaction_type,
                counterparty=counterparty,
                reporting_period=period,
                amount=float(amount),
                scenario_id=scenario_id,
                scenario_type=scenario_type,
                scenario_step=step,
            )

    entities = tuple(ENTITY_SCALE_FACTORS)
    for entity in entities:
        add_ordinary(entity, 25)

    for entity, scale in ENTITY_SCALE_FACTORS.items():
        add_sequence(
            (amount * scale for amount in P2P_AGGREGATION_BASE),
            scenario_id=f"AGG_P2P_{entity}", scenario_type="aggregation_pressure",
            workflow="procure_to_pay", entity=entity, period="2026-06",
            account="aggregation_p2p", transaction_type="invoice",
            counterparty=f"SYNTH_AGG_P2P_{entity}",
        )

    for entity in entities:
        add_ordinary(entity, 25)

    for entity, scale in ENTITY_SCALE_FACTORS.items():
        add_sequence(
            (amount * scale for amount in JOURNAL_AGGREGATION_BASE),
            scenario_id=f"AGG_JOURNAL_{entity}", scenario_type="aggregation_pressure",
            workflow="journal_entry_month_end_close", entity=entity, period="2026-07",
            account="aggregation_journal", transaction_type="standard_accrual",
            counterparty=f"INTERNAL_AGG_{entity}",
        )

    for entity, scale in ENTITY_SCALE_FACTORS.items():
        for index, (flag, base_amount) in enumerate(zip(QUALITATIVE_FLAGS, QUALITATIVE_BASE_AMOUNTS, strict=True), start=1):
            p2p = flag in {QualitativeFlag.RELATED_PARTY, QualitativeFlag.BANK_CHANGE}
            add(
                workflow="procure_to_pay" if p2p else "journal_entry_month_end_close",
                entity=entity,
                account=f"qualitative_{entity.lower()}_{index}",
                transaction_type="payment" if p2p else "manual_adjustment",
                counterparty=f"SYNTH_QUALITATIVE_{entity}_{index}",
                reporting_period="2026-07",
                amount=float(base_amount * scale),
                qualitative_flag=flag.value,
                reversible=flag not in {QualitativeFlag.BANK_CHANGE, QualitativeFlag.MANAGEMENT_OVERRIDE},
                scenario_id=f"QUAL_{entity}_{index}",
                scenario_type="qualitative_risk",
            )

    entity_cycle = entities * 4
    for index, (entity, amount) in enumerate(zip(entity_cycle, ISOLATED_SIGNIFICANCE_AMOUNTS, strict=True), start=1):
        p2p = index % 2 == 1
        add(
            workflow="procure_to_pay" if p2p else "journal_entry_month_end_close",
            entity=entity,
            account=f"isolated_significance_{index:02d}",
            transaction_type="isolated_significance_vignette",
            counterparty=f"SYNTH_ISOLATED_{index:02d}",
            reporting_period="2026-07",
            amount=float(amount),
            scenario_id=f"ISOLATED_{index:02d}",
            scenario_type="isolated_significance",
        )

    for entity, scale in ENTITY_SCALE_FACTORS.items():
        add(
            workflow="journal_entry_month_end_close",
            entity=entity,
            account="confirmed_error_signal",
            transaction_type="control_error_confirmation",
            counterparty=f"INTERNAL_SIGNAL_{entity}",
            reporting_period="2026-07",
            amount=float(4_500 * scale),
            qualitative_flag=QualitativeFlag.MANAGEMENT_OVERRIDE.value,
            reversible=False,
            confirmed_control_error=True,
            scenario_id=f"ERROR_SIGNAL_{entity}",
            scenario_type="confirmed_error_signal",
        )
        add_sequence(
            (amount * scale for amount in POST_ERROR_BASE),
            scenario_id=f"POST_ERROR_{entity}", scenario_type="post_error_accumulation",
            workflow="journal_entry_month_end_close", entity=entity, period="2026-07",
            account="post_error_repeated_cell", transaction_type="manual_adjustment",
            counterparty=f"INTERNAL_POST_ERROR_{entity}",
        )

    frame = pd.DataFrame(rows)
    frame["oracle_required_action"] = adjudicate_oracle(frame)
    frame = frame.loc[:, [*POLICY_VISIBLE_COLUMNS, *SCENARIO_ONLY_COLUMNS]]
    _validate_generated_data(frame)
    return frame


def _risk_cells(frame: pd.DataFrame) -> pd.Series:
    return frame.loc[:, RISK_CELL_COLUMNS].astype(str).agg("|".join, axis=1)


def _validate_generated_data(frame: pd.DataFrame) -> None:
    """Fail fast if the frozen matched design loses an invariant."""

    if len(frame) != ROW_COUNT or not frame["transaction_id"].is_unique:
        raise ValueError(f"Synthetic dataset must contain {ROW_COUNT} uniquely identified rows")
    if frame["sequence_number"].tolist() != list(range(1, ROW_COUNT + 1)):
        raise ValueError("Synthetic dataset order is invalid")
    if set(frame["workflow"]) != {"procure_to_pay", "journal_entry_month_end_close"}:
        raise ValueError("Both workflow families are required")
    if set(frame["entity"]) != set(ENTITY_SCALE_FACTORS):
        raise ValueError("All three synthetic entity scales are required")
    if (frame["amount"] <= 0).any() or frame.isna().any().any():
        raise ValueError("Synthetic data require positive amounts and no missing values")

    expected_counts = {
        "ordinary_low_risk": 150,
        "aggregation_pressure": 60,
        "qualitative_risk": 15,
        "isolated_significance": 12,
        "confirmed_error_signal": 3,
        "post_error_accumulation": 30,
    }
    if frame["scenario_type"].value_counts().to_dict() != expected_counts:
        raise ValueError("Synthetic scenario counts changed from the frozen design")
    if frame["entity"].value_counts().to_dict() != {entity: 90 for entity in ENTITY_SCALE_FACTORS}:
        raise ValueError("Synthetic entities must each contain 90 rows")

    aggregation = frame[frame["scenario_type"].eq("aggregation_pressure")].copy()
    aggregation["risk_cell"] = _risk_cells(aggregation)
    cells_per_scenario = aggregation.groupby("scenario_id")["risk_cell"].nunique()
    if not cells_per_scenario.eq(1).all() or aggregation.groupby("scenario_id")["risk_cell"].first().duplicated().any():
        raise ValueError("Aggregation scenarios must use distinct single risk cells")

    signals = frame[frame["confirmed_control_error"]].copy()
    post_error = frame[frame["scenario_type"].eq("post_error_accumulation")].copy()
    signals["risk_cell"] = _risk_cells(signals)
    post_error["risk_cell"] = _risk_cells(post_error)
    if set(signals["risk_cell"]).intersection(post_error["risk_cell"]):
        raise ValueError("Confirmed-error signals cannot share post-error recurrence cells")
    if not post_error.groupby("scenario_id")["scenario_step"].min().eq(1).all():
        raise ValueError("Each post-error repeated cell must begin at occurrence one")

    isolated = frame[frame["scenario_type"].eq("isolated_significance")]
    if tuple(isolated["amount"].astype(int)) != ISOLATED_SIGNIFICANCE_AMOUNTS:
        raise ValueError("Isolated-significance amounts changed from the frozen design")
