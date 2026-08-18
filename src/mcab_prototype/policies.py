"""Transparent fixed, cumulative-cap, and MCAB policy conditions."""

from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping

import pandas as pd

from .domain import (
    Action,
    DECISION_COLUMNS,
    POLICY_VISIBLE_COLUMNS,
    RISK_CELL_COLUMNS,
    SCENARIO_ONLY_COLUMNS,
    QualitativeFlag,
)


# Frozen treatment-side mappings shared by every policy condition.
POLICY_FLAG_ACTIONS: Mapping[str, Action] = MappingProxyType({
    QualitativeFlag.RELATED_PARTY.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.BANK_CHANGE.value: Action.BLOCK,
    QualitativeFlag.NON_STANDARD_JOURNAL.value: Action.INDEPENDENT_REVIEW,
    QualitativeFlag.MANAGEMENT_OVERRIDE.value: Action.BLOCK,
    QualitativeFlag.PERIOD_END.value: Action.INDEPENDENT_REVIEW,
})

DEFAULT_ENTITY_ANCHORS: tuple[tuple[str, float], ...] = (
    ("ENTITY_SMALL", 250_000.0),
    ("ENTITY_REFERENCE", 500_000.0),
    ("ENTITY_LARGE", 1_000_000.0),
)


def _positive_finite(value: float, label: str) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be finite and positive")


@dataclass(frozen=True)
class FixedPolicyConfig:
    """Illustrative stateless comparator settings."""

    threshold: float = 50_000.0

    def __post_init__(self) -> None:
        _positive_finite(self.threshold, "Fixed threshold")


@dataclass(frozen=True)
class CumulativeCapConfig:
    """Uniform cumulative-cap settings with no materiality calibration."""

    cap: float = 50_000.0

    def __post_init__(self) -> None:
        _positive_finite(self.cap, "Uniform cumulative cap")


@dataclass(frozen=True)
class MCABConfig:
    """Illustrative entity-relative MCAB parameters, not prescribed values."""

    entity_anchors: tuple[tuple[str, float], ...] = DEFAULT_ENTITY_ANCHORS
    safety_factor: float = 0.10
    post_error_multiplier: float = 0.50

    def __post_init__(self) -> None:
        _positive_finite(self.safety_factor, "MCAB safety factor")
        _positive_finite(self.post_error_multiplier, "Post-error multiplier")
        if self.post_error_multiplier > 1:
            raise ValueError("Post-error multiplier cannot exceed 1.00")
        anchors = dict(self.entity_anchors)
        if len(anchors) != len(self.entity_anchors) or not anchors:
            raise ValueError("MCAB entity anchors must be unique and non-empty")
        for entity, anchor in anchors.items():
            if not entity:
                raise ValueError("MCAB entity identifiers cannot be empty")
            _positive_finite(float(anchor), f"MCAB anchor for {entity}")

    @property
    def anchor_map(self) -> dict[str, float]:
        """Return a defensive entity-to-anchor mapping."""

        return dict(self.entity_anchors)

    def initial_budget_for(self, entity: str) -> float:
        """Return the initial authority ceiling for one synthetic entity."""

        try:
            anchor = self.anchor_map[entity]
        except KeyError as exc:
            raise ValueError(f"No MCAB materiality anchor configured for entity {entity!r}") from exc
        return anchor * self.safety_factor


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
    """Return the frozen treatment-side qualitative override."""

    return POLICY_FLAG_ACTIONS.get(flag)


def _risk_cell(row: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(str(row[column]) for column in RISK_CELL_COLUMNS)


class FixedThresholdPolicy:
    """Transparent comparator with no cumulative exposure state."""

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
                "transaction_id": row["transaction_id"],
                "action": action.value,
                "route": route,
                "risk_cell": "",
                "initial_budget": self.config.threshold,
                "effective_budget": self.config.threshold,
                "projected_utilisation": amount,
                "utilisation_before": pd.NA,
                "utilisation_after": pd.NA,
                "tightening_active_before": False,
                "tightening_triggered_after": False,
            })
        return pd.DataFrame(decisions, columns=DECISION_COLUMNS)


def _run_cumulative_policy(
    transactions: pd.DataFrame,
    initial_budget_for: Callable[[str], float],
    *,
    post_error_multiplier: float = 1.0,
    enable_tightening: bool = False,
) -> pd.DataFrame:
    """Apply the shared cumulative accounting rules transparently."""

    _validate_policy_input(transactions)
    utilisation: dict[tuple[str, ...], float] = {}
    tightened_scopes: set[tuple[str, str]] = set()
    decisions: list[dict[str, object]] = []

    for record in transactions.itertuples(index=False):
        row = record._asdict()
        entity = str(row["entity"])
        cell = _risk_cell(row)
        scope = (entity, str(row["workflow"]))
        tightening_active = enable_tightening and scope in tightened_scopes
        initial_budget = initial_budget_for(entity)
        effective_budget = initial_budget * (post_error_multiplier if tightening_active else 1.0)
        before = utilisation.get(cell, 0.0)
        amount = float(row["amount"])
        projected = before + amount
        override = _qualitative_override(str(row["qualitative_flag"]))

        if override is not None:
            action, route, after = override, f"qualitative_override:{row['qualitative_flag']}", before
        elif projected > effective_budget:
            action, route, after = Action.INDEPENDENT_REVIEW, "projected_usage_above_budget", before
        else:
            action, route, after = Action.AUTO_EXECUTE, "within_cumulative_budget", projected
            utilisation[cell] = after

        trigger = (
            enable_tightening
            and bool(row["confirmed_control_error"])
            and post_error_multiplier < 1.0
        )
        if trigger:
            tightened_scopes.add(scope)
        decisions.append({
            "transaction_id": row["transaction_id"],
            "action": action.value,
            "route": route,
            "risk_cell": "|".join(cell),
            "initial_budget": initial_budget,
            "effective_budget": effective_budget,
            "projected_utilisation": projected,
            "utilisation_before": before,
            "utilisation_after": after,
            "tightening_active_before": tightening_active,
            "tightening_triggered_after": trigger,
        })

    return pd.DataFrame(decisions, columns=DECISION_COLUMNS)


class CumulativeCapPolicy:
    """Stateful uniform cap without entity calibration or error tightening."""

    def __init__(self, config: CumulativeCapConfig = CumulativeCapConfig()) -> None:
        self.config = config

    def run(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """Apply one cumulative cap to every entity and risk cell."""

        return _run_cumulative_policy(transactions, lambda _entity: self.config.cap)


class MCABPolicy:
    """Entity-calibrated cumulative budget with configurable tightening."""

    def __init__(self, config: MCABConfig = MCABConfig()) -> None:
        self.config = config

    def run(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """Apply MCAB sequentially; a new run always starts with empty state."""

        return _run_cumulative_policy(
            transactions,
            self.config.initial_budget_for,
            post_error_multiplier=self.config.post_error_multiplier,
            enable_tightening=self.config.post_error_multiplier < 1.0,
        )
