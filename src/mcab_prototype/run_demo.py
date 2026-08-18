"""One-command deterministic MCAB demonstration."""

from pathlib import Path

import pandas as pd

from .evaluate import (
    action_confusion,
    apply_policies,
    compare_policies_by_entity,
    compare_policies,
    mechanism_decomposition,
    save_comparison_chart,
    sensitivity_analysis,
    write_and_validate_results_summary,
    write_and_validate_readme_results,
)
from .generate_data import DEFAULT_SEED, generate_transactions
from .supplementary import (
    exposure_difference_decomposition,
    oracle_sensitivity_analysis,
    supplementary_policy_metrics,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SUPPLEMENTARY_RATIO_COLUMNS = (
    "anchor_normalised_exposure",
    "entity_small_anchor_ratio",
    "entity_reference_anchor_ratio",
    "entity_large_anchor_ratio",
    "maximum_entity_anchor_ratio",
)


def _write_supplementary_csv(
    frame: pd.DataFrame,
    path: Path,
    csv_options: dict[str, object],
) -> None:
    """Write displayed scale-relative measures to exactly four decimal places."""

    output = frame.copy()
    for column in SUPPLEMENTARY_RATIO_COLUMNS:
        output[column] = output[column].map(lambda value: f"{value:.4f}")
    output.to_csv(path, **csv_options)


def run_demo(root: Path = REPOSITORY_ROOT) -> tuple[Path, Path]:
    """Generate data, decisions, metrics, sensitivities, and the chart."""

    data_dir, output_dir = root / "data", root / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    transactions = generate_transactions(DEFAULT_SEED)
    decisions = apply_policies(transactions)
    metrics = compare_policies(decisions)
    entity_metrics = compare_policies_by_entity(decisions)
    decomposition = mechanism_decomposition(decisions)
    sensitivity = sensitivity_analysis(transactions)
    confusion = action_confusion(decisions)
    supplementary = supplementary_policy_metrics(decisions)
    exposure_decomposition = exposure_difference_decomposition(decisions)
    oracle_sensitivity = oracle_sensitivity_analysis(transactions, decisions)
    csv_options = {"index": False, "float_format": "%.6f", "lineterminator": "\n"}
    transactions.to_csv(data_dir / "synthetic_transactions.csv", **csv_options)
    decisions.to_csv(output_dir / "policy_decisions.csv", **csv_options)
    metrics.to_csv(output_dir / "policy_comparison.csv", **csv_options)
    entity_metrics.to_csv(output_dir / "policy_entity_comparison.csv", **csv_options)
    decomposition.to_csv(output_dir / "mechanism_decomposition.csv", **csv_options)
    sensitivity.to_csv(output_dir / "sensitivity_analysis.csv", **csv_options)
    confusion_path = output_dir / "action_confusion.csv"
    confusion.to_csv(confusion_path, **csv_options)
    supplementary_path = output_dir / "supplementary_policy_metrics.csv"
    exposure_decomposition_path = output_dir / "exposure_difference_decomposition.csv"
    oracle_sensitivity_path = output_dir / "oracle_sensitivity_analysis.csv"
    _write_supplementary_csv(supplementary, supplementary_path, csv_options)
    exposure_decomposition.to_csv(exposure_decomposition_path, **csv_options)
    _write_supplementary_csv(oracle_sensitivity, oracle_sensitivity_path, csv_options)
    chart_path = output_dir / "policy_comparison.png"
    save_comparison_chart(metrics, supplementary, chart_path)
    write_and_validate_results_summary(
        output_dir / "policy_decisions.csv",
        output_dir / "policy_comparison.csv",
        output_dir / "policy_entity_comparison.csv",
        output_dir / "mechanism_decomposition.csv",
        confusion_path,
        supplementary_path,
        exposure_decomposition_path,
        oracle_sensitivity_path,
        output_dir / "results_summary.md",
    )
    write_and_validate_readme_results(
        root / "README.md",
        output_dir / "policy_decisions.csv",
        output_dir / "policy_comparison.csv",
        supplementary_path,
        exposure_decomposition_path,
        oracle_sensitivity_path,
    )
    return output_dir / "policy_comparison.csv", chart_path


def main() -> None:
    """Run the demonstration and print computed primary metrics."""

    metrics_path, chart_path = run_demo()
    print(f"Wrote metrics: {metrics_path.relative_to(REPOSITORY_ROOT)}")
    print(f"Wrote chart: {chart_path.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
