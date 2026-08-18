"""One-command deterministic MCAB demonstration."""

from pathlib import Path

from .evaluate import (
    action_confusion,
    apply_policies,
    compare_policies,
    save_comparison_chart,
    sensitivity_analysis,
    write_and_validate_results_summary,
    write_and_validate_readme_results,
)
from .generate_data import DEFAULT_SEED, generate_transactions

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def run_demo(root: Path = REPOSITORY_ROOT) -> tuple[Path, Path]:
    """Generate data, decisions, metrics, sensitivities, and the chart."""

    data_dir, output_dir = root / "data", root / "outputs"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    transactions = generate_transactions(DEFAULT_SEED)
    decisions = apply_policies(transactions)
    metrics = compare_policies(decisions)
    sensitivity = sensitivity_analysis(transactions)
    confusion = action_confusion(decisions)
    csv_options = {"index": False, "float_format": "%.6f", "lineterminator": "\n"}
    transactions.to_csv(data_dir / "synthetic_transactions.csv", **csv_options)
    decisions.to_csv(output_dir / "policy_decisions.csv", **csv_options)
    metrics.to_csv(output_dir / "policy_comparison.csv", **csv_options)
    sensitivity.to_csv(output_dir / "sensitivity_analysis.csv", **csv_options)
    confusion_path = output_dir / "action_confusion.csv"
    confusion.to_csv(confusion_path, **csv_options)
    chart_path = output_dir / "policy_comparison.png"
    save_comparison_chart(metrics, chart_path)
    write_and_validate_results_summary(
        output_dir / "policy_decisions.csv", output_dir / "policy_comparison.csv",
        output_dir / "sensitivity_analysis.csv", confusion_path,
        output_dir / "results_summary.md",
    )
    write_and_validate_readme_results(root / "README.md", output_dir / "policy_comparison.csv")
    return output_dir / "policy_comparison.csv", chart_path


def main() -> None:
    """Run the demonstration and print computed primary metrics."""

    metrics_path, chart_path = run_demo()
    print(f"Wrote metrics: {metrics_path.relative_to(REPOSITORY_ROOT)}")
    print(f"Wrote chart: {chart_path.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
