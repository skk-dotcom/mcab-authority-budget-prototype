"""Independent synthetic adjudication oracle.

The oracle encodes expected control actions for authored vignettes. It is a
demonstration ground truth, not a validated professional judgement protocol.
"""

from typing import Mapping

import pandas as pd

from .domain import Action, QualitativeFlag


# Deliberately separate from the treatment-side override table.
ORACLE_FLAG_ACTIONS: Mapping[str, Action] = {
    QualitativeFlag.RELATED_PARTY.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.BANK_CHANGE.value: Action.BLOCK,
    QualitativeFlag.NON_STANDARD_JOURNAL.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.MANAGEMENT_OVERRIDE.value: Action.BLOCK,
    QualitativeFlag.PERIOD_END.value: Action.INDEPENDENT_REVIEW,
}

AGGREGATION_REVIEW_FROM_STEP = {"AGG_P2P": 6, "AGG_JE": 5, "POST_ERROR": 4}


def adjudicate_oracle(transactions: pd.DataFrame) -> pd.Series:
    """Assign expected actions without consulting either treatment policy."""

    required = {"qualitative_flag", "scenario_id", "scenario_type", "scenario_step"}
    missing = required.difference(transactions.columns)
    if missing:
        raise ValueError(f"Oracle input missing columns: {sorted(missing)}")

    def adjudicate(row: pd.Series) -> str:
        flag_action = ORACLE_FLAG_ACTIONS.get(str(row["qualitative_flag"]))
        if flag_action is not None:
            return flag_action.value
        scenario_type = str(row["scenario_type"])
        if scenario_type == "isolated_large":
            return Action.INDEPENDENT_REVIEW.value
        if scenario_type in {"aggregation_pressure", "post_error_accumulation"}:
            review_step = AGGREGATION_REVIEW_FROM_STEP[str(row["scenario_id"])]
            if int(row["scenario_step"]) >= review_step:
                return Action.INDEPENDENT_REVIEW.value
        return Action.AUTO_EXECUTE.value

    return transactions.apply(adjudicate, axis=1).rename("oracle_required_action")
