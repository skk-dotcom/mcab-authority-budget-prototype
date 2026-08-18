"""Reusable synthetic rows for policy unit tests."""

from collections.abc import Sequence

import pandas as pd

from mcab_prototype.domain import POLICY_VISIBLE_COLUMNS, QualitativeFlag


def policy_frame(
    amounts: Sequence[float],
    *,
    flags: Sequence[str] | None = None,
    errors: Sequence[bool] | None = None,
    entities: Sequence[str] | None = None,
    workflows: Sequence[str] | None = None,
    accounts: Sequence[str] | None = None,
    counterparties: Sequence[str] | None = None,
    periods: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Build the policy-visible interface with controlled state keys."""

    count = len(amounts)
    flags = flags or [QualitativeFlag.NONE.value] * count
    errors = errors or [False] * count
    entities = entities or ["ENTITY_REFERENCE"] * count
    workflows = workflows or ["procure_to_pay"] * count
    accounts = accounts or ["test_account"] * count
    counterparties = counterparties or ["SYNTH_TEST"] * count
    periods = periods or ["2026-07"] * count
    rows = []
    for index, amount in enumerate(amounts):
        rows.append({
            "transaction_id": f"TEST{index + 1:03d}",
            "sequence_number": index + 1,
            "workflow": workflows[index],
            "entity": entities[index],
            "account": accounts[index],
            "transaction_type": "test_transaction",
            "counterparty": counterparties[index],
            "reporting_period": periods[index],
            "amount": amount,
            "qualitative_flag": flags[index],
            "reversible": True,
            "confirmed_control_error": errors[index],
        })
    return pd.DataFrame(rows, columns=POLICY_VISIBLE_COLUMNS)
