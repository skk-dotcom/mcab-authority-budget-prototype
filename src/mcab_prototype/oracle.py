"""Procedurally isolated pattern oracle for authored synthetic scenarios.

The oracle contains no policy monetary parameters. It remains an authored
research-design component rather than expert-validated ground truth.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import pandas as pd

from .domain import Action, RISK_CELL_COLUMNS, QualitativeFlag


# Frozen separately from the treatment-side mapping.
ORACLE_FLAG_ACTIONS: Mapping[str, Action] = MappingProxyType({
    QualitativeFlag.RELATED_PARTY.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.BANK_CHANGE.value: Action.BLOCK,
    QualitativeFlag.NON_STANDARD_JOURNAL.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.MANAGEMENT_OVERRIDE.value: Action.BLOCK,
    QualitativeFlag.PERIOD_END.value: Action.INDEPENDENT_REVIEW,
})


@dataclass(frozen=True)
class OraclePatternConfig:
    """Non-monetary recurrence rules frozen before revised execution."""

    pre_error_review_from_occurrence: int = 6
    post_error_review_from_occurrence: int = 3

    def __post_init__(self) -> None:
        if self.pre_error_review_from_occurrence < 2:
            raise ValueError("Pre-error recurrence rule must allow at least one initial occurrence")
        if self.post_error_review_from_occurrence < 2:
            raise ValueError("Post-error recurrence rule must allow at least one initial occurrence")


RECURRENCE_SCENARIOS = {"aggregation_pressure", "post_error_accumulation"}
ISOLATED_SIGNIFICANCE_SCENARIO = "isolated_significance"


def adjudicate_oracle(
    transactions: pd.DataFrame,
    config: OraclePatternConfig = OraclePatternConfig(),
) -> pd.Series:
    """Assign expected actions from qualitative and recurrence patterns."""

    required = {
        "sequence_number",
        "workflow",
        "entity",
        "reporting_period",
        "account",
        "counterparty",
        "qualitative_flag",
        "confirmed_control_error",
        "scenario_type",
    }
    missing = required.difference(transactions.columns)
    if missing:
        raise ValueError(f"Oracle input missing columns: {sorted(missing)}")
    forbidden = {
        column for column in transactions.columns
        if column.endswith("_action") and column != "oracle_required_action"
    }
    if forbidden:
        raise ValueError(f"Oracle input exposes policy decisions: {sorted(forbidden)}")
    if transactions["sequence_number"].duplicated().any() or not transactions["sequence_number"].is_monotonic_increasing:
        raise ValueError("Oracle input must have unique, increasing sequence numbers")

    occurrences: dict[tuple[str, ...], int] = {}
    confirmed_error_scopes: set[tuple[str, str]] = set()
    actions: list[str] = []

    for record in transactions.itertuples(index=False):
        row = record._asdict()
        scenario_type = str(row["scenario_type"])
        scope = (str(row["entity"]), str(row["workflow"]))
        flag_action = ORACLE_FLAG_ACTIONS.get(str(row["qualitative_flag"]))

        if flag_action is not None:
            action = flag_action
        elif scenario_type == ISOLATED_SIGNIFICANCE_SCENARIO:
            action = Action.INDEPENDENT_REVIEW
        elif scenario_type in RECURRENCE_SCENARIOS:
            cell = tuple(str(row[column]) for column in RISK_CELL_COLUMNS)
            occurrence = occurrences.get(cell, 0) + 1
            occurrences[cell] = occurrence
            review_from = (
                config.post_error_review_from_occurrence
                if scope in confirmed_error_scopes
                else config.pre_error_review_from_occurrence
            )
            action = Action.INDEPENDENT_REVIEW if occurrence >= review_from else Action.AUTO_EXECUTE
        else:
            action = Action.AUTO_EXECUTE

        actions.append(action.value)
        if bool(row["confirmed_control_error"]):
            confirmed_error_scopes.add(scope)

    return pd.Series(actions, index=transactions.index, name="oracle_required_action")
