"""Deterministic synthetic transaction generator."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from .domain import POLICY_VISIBLE_COLUMNS, SCENARIO_ONLY_COLUMNS, QualitativeFlag
from .oracle import adjudicate_oracle

DEFAULT_SEED = 20260818
ROW_COUNT = 240


def generate_transactions(seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Create the ordered, synthetic MCAB demonstration dataset."""

    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []

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

    def add_ordinary(count: int) -> None:
        for _ in range(count):
            workflow = str(rng.choice(["procure_to_pay", "journal_entry_month_end_close"]))
            sequence = len(rows) + 1
            add(
                workflow=workflow,
                entity=str(rng.choice(["ENTITY_A", "ENTITY_B"])),
                account=str(rng.choice(["operating_expense", "cash_clearing", "accrued_liability"])),
                transaction_type=("invoice" if workflow == "procure_to_pay" else "standard_accrual"),
                counterparty=(f"SYNTH_VENDOR_{int(rng.integers(1, 13)):02d}" if workflow == "procure_to_pay" else "INTERNAL"),
                reporting_period=str(rng.choice(["2026-06", "2026-07"])),
                amount=float(rng.integers(500, 4_201)),
                reversible=bool(rng.random() > 0.12),
                scenario_id=f"ORD_{sequence:04d}",
                scenario_type="ordinary_low_risk",
            )

    def add_sequence(
        amounts: Iterable[float], *, scenario_id: str, scenario_type: str, workflow: str,
        entity: str, period: str, account: str, transaction_type: str, counterparty: str,
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

    add_ordinary(90)
    add_sequence(
        [7_800, 8_200, 7_600, 8_400, 7_900, 8_100, 8_300, 7_700, 8_250, 7_950],
        scenario_id="AGG_P2P", scenario_type="aggregation_pressure",
        workflow="procure_to_pay", entity="ENTITY_A", period="2026-06",
        account="aggregation_test", transaction_type="invoice", counterparty="SYNTH_VENDOR_AGG",
    )
    add_ordinary(45)
    add_sequence(
        [9_200, 8_800, 9_100, 8_900, 9_000, 9_300, 8_700, 9_150, 8_850, 9_050],
        scenario_id="AGG_JE", scenario_type="aggregation_pressure",
        workflow="journal_entry_month_end_close", entity="ENTITY_A", period="2026-07",
        account="aggregation_test", transaction_type="standard_accrual", counterparty="INTERNAL",
    )

    flags = [
        QualitativeFlag.RELATED_PARTY, QualitativeFlag.BANK_CHANGE,
        QualitativeFlag.NON_STANDARD_JOURNAL, QualitativeFlag.MANAGEMENT_OVERRIDE,
        QualitativeFlag.PERIOD_END,
    ]
    for index in range(12):
        flag = flags[index % len(flags)]
        p2p = flag in {QualitativeFlag.RELATED_PARTY, QualitativeFlag.BANK_CHANGE}
        add(
            workflow="procure_to_pay" if p2p else "journal_entry_month_end_close",
            entity="ENTITY_B",
            account="qualitative_risk",
            transaction_type="payment" if p2p else "manual_adjustment",
            counterparty="SYNTH_VENDOR_FLAG" if p2p else "INTERNAL",
            reporting_period="2026-07",
            amount=float(1_000 + 275 * index),
            qualitative_flag=flag.value,
            reversible=flag not in {QualitativeFlag.BANK_CHANGE, QualitativeFlag.MANAGEMENT_OVERRIDE},
            scenario_id=f"QUAL_{index + 1:02d}",
            scenario_type="qualitative_risk",
        )

    for index, amount in enumerate([55_000, 62_500, 71_000, 83_000, 95_000, 58_500, 76_000, 88_000], start=1):
        p2p = index % 2 == 1
        add(
            workflow="procure_to_pay" if p2p else "journal_entry_month_end_close",
            entity="ENTITY_A" if index <= 4 else "ENTITY_B",
            account="large_value_account",
            transaction_type="invoice" if p2p else "standard_accrual",
            counterparty=f"SYNTH_VENDOR_L{index}" if p2p else "INTERNAL",
            reporting_period="2026-07",
            amount=float(amount),
            scenario_id=f"LARGE_{index:02d}",
            scenario_type="isolated_large",
        )

    add(
        workflow="journal_entry_month_end_close", entity="ENTITY_B",
        account="post_error_adjustments", transaction_type="manual_adjustment",
        counterparty="INTERNAL", reporting_period="2026-07", amount=4_500.0,
        qualitative_flag=QualitativeFlag.MANAGEMENT_OVERRIDE.value, reversible=False,
        confirmed_control_error=True, scenario_id="ERROR_SIGNAL",
        scenario_type="confirmed_error_signal",
    )
    add_sequence(
        [6_500, 7_000, 6_200, 6_800, 6_400, 7_100, 6_300, 6_900, 6_600, 7_200, 6_100, 6_750, 6_350, 7_050],
        scenario_id="POST_ERROR", scenario_type="post_error_accumulation",
        workflow="journal_entry_month_end_close", entity="ENTITY_B", period="2026-07",
        account="post_error_adjustments", transaction_type="manual_adjustment", counterparty="INTERNAL",
    )
    add_ordinary(50)

    frame = pd.DataFrame(rows)
    frame["oracle_required_action"] = adjudicate_oracle(frame)
    frame = frame.loc[:, [*POLICY_VISIBLE_COLUMNS, *SCENARIO_ONLY_COLUMNS]]
    _validate_generated_data(frame)
    return frame


def _validate_generated_data(frame: pd.DataFrame) -> None:
    """Fail fast if the authored dataset loses its required invariants."""

    if len(frame) != ROW_COUNT or not frame["transaction_id"].is_unique:
        raise ValueError("Synthetic dataset must contain 240 uniquely identified rows")
    if frame["sequence_number"].tolist() != list(range(1, ROW_COUNT + 1)):
        raise ValueError("Synthetic dataset order is invalid")
    if set(frame["workflow"]) != {"procure_to_pay", "journal_entry_month_end_close"}:
        raise ValueError("Both workflow families are required")
    if (frame["amount"] <= 0).any() or frame.isna().any().any():
        raise ValueError("Synthetic data require positive amounts and no missing values")
