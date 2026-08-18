"""Shared data vocabulary without treatment or oracle logic."""

from enum import StrEnum


class Action(StrEnum):
    """Available control routes."""

    AUTO_EXECUTE = "AUTO_EXECUTE"
    INDEPENDENT_REVIEW = "INDEPENDENT_REVIEW"
    BLOCK = "BLOCK"


class QualitativeFlag(StrEnum):
    """Observable synthetic qualitative risk indicators."""

    NONE = "none"
    RELATED_PARTY = "related_party_activity"
    BANK_CHANGE = "vendor_bank_detail_change"
    NON_STANDARD_JOURNAL = "unusual_non_standard_journal"
    MANAGEMENT_OVERRIDE = "management_override_indicator"
    PERIOD_END = "period_end_adjustment"


POLICY_VISIBLE_COLUMNS = (
    "transaction_id",
    "sequence_number",
    "workflow",
    "entity",
    "account",
    "transaction_type",
    "counterparty",
    "reporting_period",
    "amount",
    "qualitative_flag",
    "reversible",
    "confirmed_control_error",
)

SCENARIO_ONLY_COLUMNS = (
    "scenario_id",
    "scenario_type",
    "scenario_step",
    "oracle_required_action",
)

DECISION_COLUMNS = (
    "transaction_id",
    "action",
    "route",
    "risk_cell",
    "initial_budget",
    "effective_budget",
    "projected_utilisation",
    "utilisation_before",
    "utilisation_after",
    "tightening_active_before",
    "tightening_triggered_after",
)
