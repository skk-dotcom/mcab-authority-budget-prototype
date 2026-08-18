"""Exact supplementary exposure, decomposition, and oracle sensitivity."""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping, Sequence

import pandas as pd

from .domain import Action
from .oracle import OraclePatternConfig, adjudicate_oracle
from .policies import DEFAULT_ENTITY_ANCHORS


POLICY_ORDER = ("fixed", "uniform_cap", "mcab_no_tightening", "mcab_full")
ENTITY_ORDER = ("ENTITY_SMALL", "ENTITY_REFERENCE", "ENTITY_LARGE")
POLICY_LABELS = {
    "fixed": "Fixed threshold",
    "uniform_cap": "Uniform cumulative cap",
    "mcab_no_tightening": "MCAB no tightening",
    "mcab_full": "Full MCAB",
}
ORACLE_CONFIGURATIONS = ((4, 3), (6, 3), (8, 3), (6, 2), (6, 4))
ENTITY_ANCHOR_CENTS: Mapping[str, int] = MappingProxyType({
    entity: int(Decimal(str(anchor)) * 100)
    for entity, anchor in DEFAULT_ENTITY_ANCHORS
})
RATIO_QUANTUM = Decimal("0.0001")


OVERALL_BRANCHES = {
    "A": "Full MCAB has lower summed anchor-normalised exposure than the uniform cap while retaining higher absolute-dollar exposure. The measures diverge because one reports gross dollars and the other scales each consequential failure to its entity’s authored anchor. This divergence is consistent with the intended operation of entity-relative calibration, but it is not evidence that MCAB is effective or generally superior.",
    "B": "Full MCAB reduces consequential-failure incidence relative to the uniform cap but does not reduce summed anchor-normalised exposure. The supplementary scale-relative measure therefore does not favour Full MCAB, and the result is retained as a policy trade-off rather than explained away or used to retune the design.",
}
CALIBRATION_BRANCHES = {
    "A": "MCAB without tightening has lower summed anchor-normalised exposure than the uniform cap. In this authored design, changing from a common cumulative cap to entity-relative budgets changes the allocation of intervention and scale-relative exposure. This descriptive result does not establish the effectiveness or general superiority of entity calibration.",
    "B": "MCAB without tightening does not reduce summed anchor-normalised exposure relative to the uniform cap. The calibration step therefore does not favour MCAB on this supplementary measure, and the observed result is retained without changing entity anchors, scenario amounts or policy parameters.",
}
TIGHTENING_BRANCHES = {
    "A": "Full MCAB has lower summed anchor-normalised exposure than MCAB without tightening. Within the authored post-error sequences, prospective tightening is associated descriptively with lower scale-relative exposure and a different intervention burden. This is not causal evidence that tightening is effective outside the constructed scenarios.",
    "B": "Full MCAB does not reduce summed anchor-normalised exposure relative to MCAB without tightening. Prospective tightening therefore does not favour Full MCAB on this supplementary measure. The result is reported as an observed trade-off, is not treated as a design defect, and does not trigger retuning.",
}
SENSITIVITY_BRANCH_A = (
    "The conditional-miss-rate policy ordering, including ties, is unchanged across the five authored recurrence "
    "configurations examined. This is local sensitivity to the selected recurrence points within one authored "
    "dataset, not evidence of robustness."
)
SENSITIVITY_BRANCH_B_TEMPLATE = (
    "The conditional-miss-rate policy ordering changes under [computed configuration or configurations]. The "
    "base-case ordering is therefore conditional on the authored 6/3 recurrence points. This dependence is "
    "retained as a limitation and is not resolved by selecting a preferred configuration or adjusting the "
    "recurrence grid."
)
MAXIMUM_RATIO_TEMPLATE = (
    "Under the maximum entity-anchor exposure ratio, the ranking across the four conditions from lowest to "
    "highest is [computed ranking, including ties]. The highest single-entity figure is [computed value] for "
    "[computed policy–entity combination or combinations], meaning that this fraction of that entity’s authored "
    "anchor was exposed without independent review."
)


@dataclass(frozen=True)
class ExactExposure:
    """Exact supplementary exposure components for one policy and subset."""

    failure_count: int
    gross_cents: int
    summed_anchor_equivalents: Fraction
    entity_ratios: Mapping[str, Fraction]

    @property
    def maximum_entity_ratio(self) -> Fraction:
        """Return the largest entity-specific exposure ratio."""

        return max(self.entity_ratios.values(), default=Fraction(0))


def _amount_cents(value: object) -> int:
    decimal = Decimal(str(value)) * 100
    if decimal != decimal.to_integral_value():
        raise ValueError(f"Amount cannot be represented as integer cents: {value!r}")
    return int(decimal)


def _ratio_decimal(value: Fraction) -> Decimal:
    return (Decimal(value.numerator) / Decimal(value.denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def format_ratio(value: Fraction) -> str:
    """Format an exact ratio to the frozen four-decimal display precision."""

    return f"{_ratio_decimal(value):.4f}"


def _percentage(numerator: int, denominator: int) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def exact_exposure(
    decisions: pd.DataFrame,
    policy: str,
    oracle_actions: Sequence[str] | pd.Series | None = None,
) -> ExactExposure:
    """Calculate exact exposure for autonomous actions missed by an oracle."""

    if policy not in POLICY_ORDER:
        raise ValueError(f"Unknown policy: {policy}")
    oracle = list(decisions["oracle_required_action"] if oracle_actions is None else oracle_actions)
    if len(oracle) != len(decisions):
        raise ValueError("Oracle action count must match decision rows")

    entity_cents = {entity: 0 for entity in ENTITY_ORDER}
    failures = 0
    for position, row in enumerate(decisions.itertuples(index=False)):
        action = str(getattr(row, f"{policy}_action"))
        if action != Action.AUTO_EXECUTE.value or oracle[position] == Action.AUTO_EXECUTE.value:
            continue
        entity = str(row.entity)
        if entity not in ENTITY_ANCHOR_CENTS:
            raise ValueError(f"No authored anchor for entity {entity!r}")
        entity_cents[entity] += abs(_amount_cents(row.amount))
        failures += 1

    ratios = {
        entity: Fraction(entity_cents[entity], ENTITY_ANCHOR_CENTS[entity])
        for entity in ENTITY_ORDER
    }
    return ExactExposure(
        failure_count=failures,
        gross_cents=sum(entity_cents.values()),
        summed_anchor_equivalents=sum(ratios.values(), Fraction(0)),
        entity_ratios=MappingProxyType(ratios),
    )


def _policy_summary(
    decisions: pd.DataFrame,
    policy: str,
    oracle_actions: Sequence[str] | pd.Series,
) -> dict[str, object]:
    oracle = pd.Series(list(oracle_actions), index=decisions.index, dtype="string")
    action = decisions[f"{policy}_action"].astype("string")
    oracle_escalation = oracle.ne(Action.AUTO_EXECUTE.value)
    oracle_auto = ~oracle_escalation
    failure = action.eq(Action.AUTO_EXECUTE.value) & oracle_escalation
    intervention = action.ne(Action.AUTO_EXECUTE.value)
    exposure = exact_exposure(decisions, policy, oracle)
    total = len(decisions)
    escalation_n = int(oracle_escalation.sum())
    oracle_auto_n = int(oracle_auto.sum())
    failure_n = int(failure.sum())
    false_escalation_n = int((intervention & oracle_auto).sum())
    review_n = int(action.eq(Action.INDEPENDENT_REVIEW.value).sum())
    block_n = int(action.eq(Action.BLOCK.value).sum())

    return {
        "policy": policy,
        "transactions_n": total,
        "oracle_escalation_numerator": escalation_n,
        "oracle_escalation_denominator": total,
        "oracle_escalation_pct": _percentage(escalation_n, total),
        "consequential_failure_numerator": failure_n,
        "consequential_failure_denominator": total,
        "overall_failure_incidence_pct": _percentage(failure_n, total),
        "conditional_miss_numerator": failure_n,
        "conditional_miss_denominator": escalation_n,
        "conditional_miss_rate_pct": _percentage(failure_n, escalation_n),
        "false_escalation_numerator": false_escalation_n,
        "false_escalation_denominator": oracle_auto_n,
        "false_escalation_rate_pct": _percentage(false_escalation_n, oracle_auto_n),
        "absolute_dollar_exposure": exposure.gross_cents / 100,
        "anchor_normalised_exposure": float(_ratio_decimal(exposure.summed_anchor_equivalents)),
        "entity_small_anchor_ratio": float(_ratio_decimal(exposure.entity_ratios["ENTITY_SMALL"])),
        "entity_reference_anchor_ratio": float(_ratio_decimal(exposure.entity_ratios["ENTITY_REFERENCE"])),
        "entity_large_anchor_ratio": float(_ratio_decimal(exposure.entity_ratios["ENTITY_LARGE"])),
        "maximum_entity_anchor_ratio": float(_ratio_decimal(exposure.maximum_entity_ratio)),
        "independent_review_n": review_n,
        "block_n": block_n,
        "combined_intervention_n": review_n + block_n,
        "combined_intervention_denominator": total,
        "combined_intervention_pct": _percentage(review_n + block_n, total),
    }


def supplementary_policy_metrics(decisions: pd.DataFrame) -> pd.DataFrame:
    """Return four-policy base-case metrics with supplementary exposure."""

    oracle = decisions["oracle_required_action"]
    return pd.DataFrame([_policy_summary(decisions, policy, oracle) for policy in POLICY_ORDER])


def oracle_sensitivity_analysis(
    transactions: pd.DataFrame,
    decisions: pd.DataFrame,
) -> pd.DataFrame:
    """Re-adjudicate five recurrence settings while keeping policy actions fixed."""

    if len(transactions) != len(decisions) or not transactions["transaction_id"].reset_index(
        drop=True
    ).equals(decisions["transaction_id"].reset_index(drop=True)):
        raise ValueError("Transactions and fixed policy decisions must have identical ordered identifiers")
    oracle_input = transactions.drop(columns=["oracle_required_action"], errors="ignore")
    rows: list[dict[str, object]] = []
    for pre_error, post_error in ORACLE_CONFIGURATIONS:
        oracle = adjudicate_oracle(
            oracle_input,
            OraclePatternConfig(
                pre_error_review_from_occurrence=pre_error,
                post_error_review_from_occurrence=post_error,
            ),
        )
        if (pre_error, post_error) == (6, 3) and not oracle.equals(transactions["oracle_required_action"]):
            raise ValueError("Frozen 6/3 oracle labels changed")
        for policy in POLICY_ORDER:
            rows.append({
                "configuration": f"{pre_error}/{post_error}",
                "pre_error_review_from_occurrence": pre_error,
                "post_error_review_from_occurrence": post_error,
                "is_base_configuration": (pre_error, post_error) == (6, 3),
                **_policy_summary(decisions, policy, oracle),
            })
    return pd.DataFrame(rows)


def exposure_difference_decomposition(decisions: pd.DataFrame) -> pd.DataFrame:
    """Partition the Uniform-minus-Full dollar reversal using base decisions."""

    signals = {
        (str(row.entity), str(row.workflow)): int(row.sequence_number)
        for row in decisions.itertuples(index=False)
        if bool(row.confirmed_control_error)
    }

    def error_status(row: object) -> str:
        signal = signals.get((str(row.entity), str(row.workflow)))
        return "post_error" if signal is not None and int(row.sequence_number) > signal else "pre_or_unaffected"

    dimensions = {
        "entity": lambda row: str(row.entity),
        "scenario_type": lambda row: str(row.scenario_type),
        "error_status": error_status,
        "workflow": lambda row: str(row.workflow),
    }
    output: list[dict[str, object]] = []
    for dimension, key_function in dimensions.items():
        groups: dict[str, dict[str, int]] = defaultdict(
            lambda: {
                "uniform_failure_count": 0,
                "uniform_exposure_cents": 0,
                "full_failure_count": 0,
                "full_exposure_cents": 0,
            }
        )
        for row in decisions.itertuples(index=False):
            group = key_function(row)
            amount_cents = abs(_amount_cents(row.amount))
            oracle_escalation = str(row.oracle_required_action) != Action.AUTO_EXECUTE.value
            if oracle_escalation and str(row.uniform_cap_action) == Action.AUTO_EXECUTE.value:
                groups[group]["uniform_failure_count"] += 1
                groups[group]["uniform_exposure_cents"] += amount_cents
            if oracle_escalation and str(row.mcab_full_action) == Action.AUTO_EXECUTE.value:
                groups[group]["full_failure_count"] += 1
                groups[group]["full_exposure_cents"] += amount_cents

        contributing = {
            group: values
            for group, values in groups.items()
            if values["uniform_failure_count"] or values["full_failure_count"]
        }
        totals = {
            key: sum(values[key] for values in contributing.values())
            for key in next(iter(contributing.values()))
        }
        for group, values in [*sorted(contributing.items()), ("TOTAL", totals)]:
            uniform_exposure = values["uniform_exposure_cents"] / 100
            full_exposure = values["full_exposure_cents"] / 100
            output.append({
                "dimension": dimension,
                "group": group,
                "uniform_failure_count": values["uniform_failure_count"],
                "uniform_absolute_dollar_exposure": uniform_exposure,
                "full_mcab_failure_count": values["full_failure_count"],
                "full_mcab_absolute_dollar_exposure": full_exposure,
                "failure_count_difference_full_minus_uniform": (
                    values["full_failure_count"] - values["uniform_failure_count"]
                ),
                "exposure_difference_full_minus_uniform": full_exposure - uniform_exposure,
            })
    return pd.DataFrame(output)


def _weak_order(items: Mapping[str, Fraction]) -> tuple[tuple[str, ...], ...]:
    grouped: dict[Fraction, list[str]] = defaultdict(list)
    for policy, value in items.items():
        grouped[value].append(policy)
    return tuple(
        tuple(policy for policy in POLICY_ORDER if policy in grouped[value])
        for value in sorted(grouped)
    )


def _order_text(order: tuple[tuple[str, ...], ...]) -> str:
    return " < ".join(" = ".join(POLICY_LABELS[policy] for policy in group) for group in order)


def observed_interpretations(
    decisions: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> dict[str, object]:
    """Select policy-level branches and retain mechanism subsets separately."""

    repository = {policy: exact_exposure(decisions, policy) for policy in POLICY_ORDER}
    aggregation = decisions[decisions["scenario_type"].eq("aggregation_pressure")]
    post_error = decisions[decisions["scenario_type"].eq("post_error_accumulation")]
    mechanism_calibration = {
        policy: exact_exposure(aggregation, policy)
        for policy in ("uniform_cap", "mcab_no_tightening")
    }
    mechanism_tightening = {
        policy: exact_exposure(post_error, policy)
        for policy in ("mcab_no_tightening", "mcab_full")
    }

    overall_branch = "A" if (
        repository["mcab_full"].summed_anchor_equivalents
        < repository["uniform_cap"].summed_anchor_equivalents
    ) else "B"
    calibration_branch = "A" if (
        repository["mcab_no_tightening"].summed_anchor_equivalents
        < repository["uniform_cap"].summed_anchor_equivalents
    ) else "B"
    tightening_branch = "A" if (
        repository["mcab_full"].summed_anchor_equivalents
        < repository["mcab_no_tightening"].summed_anchor_equivalents
    ) else "B"

    orders: dict[str, tuple[tuple[str, ...], ...]] = {}
    for configuration, group in sensitivity.groupby("configuration", sort=False):
        fractions = {
            str(row.policy): Fraction(
                int(row.conditional_miss_numerator),
                int(row.conditional_miss_denominator),
            )
            for row in group.itertuples(index=False)
        }
        orders[str(configuration)] = _weak_order(fractions)
    base_order = orders["6/3"]
    changed = [configuration for configuration, order in orders.items() if order != base_order]
    sensitivity_branch = "A" if not changed else "B"
    sensitivity_text = SENSITIVITY_BRANCH_A if not changed else SENSITIVITY_BRANCH_B_TEMPLATE.replace(
        "[computed configuration or configurations]",
        ", ".join(changed),
    )

    maximum_by_policy = {
        policy: exposure.maximum_entity_ratio
        for policy, exposure in repository.items()
    }
    maximum_order = _weak_order(maximum_by_policy)
    highest = max(maximum_by_policy.values())
    combinations = [
        (policy, entity)
        for policy in POLICY_ORDER
        for entity in ENTITY_ORDER
        if repository[policy].entity_ratios[entity] == highest
    ]
    percentage = _ratio_decimal(highest * 100)
    combination_text = " and ".join(
        f"{POLICY_LABELS[policy]}–{entity}"
        for policy, entity in combinations
    )
    maximum_statement = MAXIMUM_RATIO_TEMPLATE.replace(
        "[computed ranking, including ties]",
        _order_text(maximum_order),
    ).replace(
        "[computed value]",
        f"{format_ratio(highest)} ({percentage:.4f}%)",
    ).replace(
        "[computed policy–entity combination or combinations]",
        combination_text,
    )

    return {
        "overall_branch": overall_branch,
        "overall_text": OVERALL_BRANCHES[overall_branch],
        "calibration_branch": calibration_branch,
        "calibration_text": CALIBRATION_BRANCHES[calibration_branch],
        "tightening_branch": tightening_branch,
        "tightening_text": TIGHTENING_BRANCHES[tightening_branch],
        "sensitivity_branch": sensitivity_branch,
        "sensitivity_text": sensitivity_text,
        "changed_sensitivity_configurations": changed,
        "sensitivity_orders": {key: _order_text(value) for key, value in orders.items()},
        "maximum_ratio_statement": maximum_statement,
        "exact_repository_exposure": repository,
        "exact_mechanism_calibration_exposure": mechanism_calibration,
        "exact_mechanism_tightening_exposure": mechanism_tightening,
    }
