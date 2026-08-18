"""Fixed-threshold comparator and stateful MCAB treatment."""

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import pandas as pd

from .domain import Action, DECISION_COLUMNS, POLICY_VISIBLE_COLUMNS, SCENARIO_ONLY_COLUMNS, QualitativeFlag


POLICY_FLAG_ACTIONS: Mapping[str, Action] = {
    QualitativeFlag.RELATED_PARTY.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.BANK_CHANGE.value: Action.BLOCK,
    QualitativeFlag.NON_STANDARD_JOURNAL.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.MANAGEMENT_OVERRIDE.value: Action.BLOCK,
    QualitativeFlag.PERIOD_END.value: Action.INDEPENDENT_REVIEW,
}


@dataclass(frozen=True)
class FixedPolicyConfig:
    """Illustrative fixed comparator settings."""

    threshold: float = 50_000.0

    def __post_init__(self) -> None:
        if not isfinite(self.threshold) or self.threshold <= 0:
            raise ValueError("Fixed threshold must be finite and positive")


@dataclass(frozen=True)
class MCABConfig:
    """Illustrative MCAB research parameters, not prescribed values."""

    materiality_anchor: float = 500_000.0
    safety_factor: float = 0.10
    post_error_multiplier: float = 0.50

    def __post_init__(self) -> None:
        values = (self.materiality_anchor, self.safety_factor, self.post_error_multiplier)
        if not all(isfinite(value) and value > 0 for value in values):
            raise ValueError("MCAB parameters must be finite and positive")
        if self.post_error_multiplier > 1:
            raise ValueError("Post-error multiplier cannot exceed 1.00")

    @property
    def initial_budget(self) -> float:
        """Return the initial authority ceiling for each risk cell."""

        return self.materiality_anchor * self.safety_factor


def _validate_policy_input(transactions: pd.DataFrame) -> None:
    if transactions.empty:
        return
    forbidden = set(SCENARIO_ONLY_COLUMNS).intersection(transactions.columns)
    if forbidden:
        raise ValueError(f"Policy input exposes scenario-only columns: {sorted(forbidden)}")
    missing = set(POLICY_VISIBLE_COLUMNS).difference(transactions.columns)
    if missing:
        raise ValueError(f"Policy input missing columns: {sorted(missing)}")
    if transactions["sequence_number"].duplicated().any() or not transactions["sequence_number"].is_monotonic_increasing:
        raise ValueError("Policy input must have unique, increasing sequence numbers")
    amounts = pd.to_numeric(transactions["amount"], errors="coerce")
    if amounts.isna().any() or (~amounts.map(isfinite)).any() or (amounts <= 0).any():
        raise ValueError("Policy amounts must be finite and positive")
    allowed_flags = {flag.value for flag in QualitativeFlag}
    if not set(transactions["qualitative_flag"]).issubset(allowed_flags):
        raise ValueError("Policy input contains an unknown qualitative flag")


def _qualitative_override(flag: str) -> Action | None:
    """Return the common treatment-side qualitative override."""

    return POLICY_FLAG_ACTIONS.get(flag)


class FixedThresholdPolicy:
    """Transparent comparator with no exposure state."""

    def __init__(self, config: FixedPolicyConfig = FixedPolicyConfig()) -> None:
        self.config = config

    def run(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """Apply qualitative and per-transaction monetary rules in order."""

        _validate_policy_input(transactions)
        decisions: list[dict[str, object]] = []
        for record in transactions.itertuples(index=False):
            row = record._asdict()
            amount = float(row["amount"])
            override = _qualitative_override(str(row["qualitative_flag"]))
            if override is not None:
                action, route = override, f"qualitative_override:{row['qualitative_flag']}"
            elif amount > self.config.threshold:
                action, route = Action.INDEPENDENT_REVIEW, "amount_above_fixed_threshold"
            else:
                action, route = Action.AUTO_EXECUTE, "within_fixed_threshold"
            decisions.append({
                "transaction_id": row["transaction_id"], "action": action.value, "route": route,
                "risk_cell": "", "initial_budget": self.config.threshold,
                "effective_budget": self.config.threshold, "projected_utilisation": amount,
                "utilisation_before": pd.NA, "utilisation_after": pd.NA,
                "tightening_active_before": False, "tightening_triggered_after": False,
            })
        return pd.DataFrame(decisions, columns=DECISION_COLUMNS)


class MCABPolicy:
    """Stateful authority budget with prospective confirmed-error tightening."""

    def __init__(self, config: MCABConfig = MCABConfig()) -> None:
        self.config = config

    def run(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """Apply MCAB sequentially; a new run always starts with empty state."""

        _validate_policy_input(transactions)
        utilisation: dict[tuple[str, str, str, str], float] = {}
        tightened_scopes: set[tuple[str, str]] = set()
        decisions: list[dict[str, object]] = []

        for record in transactions.itertuples(index=False):
            row = record._asdict()
            cell = (str(row["entity"]), str(row["reporting_period"]), str(row["workflow"]), str(row["account"]))
            scope = (str(row["entity"]), str(row["workflow"]))
            tightening_active = scope in tightened_scopes
            multiplier = self.config.post_error_multiplier if tightening_active else 1.0
            budget = self.config.initial_budget * multiplier
            before = utilisation.get(cell, 0.0)
            amount = float(row["amount"])
            projected = before + amount
            override = _qualitative_override(str(row["qualitative_flag"]))

            if override is not None:
                action, route, after = override, f"qualitative_override:{row['qualitative_flag']}", before
            elif projected > budget:
                action, route, after = Action.INDEPENDENT_REVIEW, "projected_usage_above_budget", before
            else:
                action, route, after = Action.AUTO_EXECUTE, "within_cumulative_budget", projected
                utilisation[cell] = after

            trigger = bool(row["confirmed_control_error"]) and self.config.post_error_multiplier < 1.0
            if trigger:
                tightened_scopes.add(scope)
            decisions.append({
                "transaction_id": row["transaction_id"], "action": action.value, "route": route,
                "risk_cell": "|".join(cell), "initial_budget": self.config.initial_budget,
                "effective_budget": budget, "projected_utilisation": projected,
                "utilisation_before": before, "utilisation_after": after,
                "tightening_active_before": tightening_active,
                "tightening_triggered_after": trigger,
            })

        return pd.DataFrame(decisions, columns=DECISION_COLUMNS)
