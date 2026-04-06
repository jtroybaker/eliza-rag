from __future__ import annotations

from pathlib import Path

from .eval_reporting import build_eval_report, discover_eval_artifacts


def generate_eval_plot(eval_dir: Path, *, output_path: Path, explicit_paths: list[Path] | None = None) -> Path:
    artifact_paths = discover_eval_artifacts(eval_dir, explicit_paths)
    report = build_eval_report(artifact_paths)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), constrained_layout=True)

    _render_accuracy_bars(axes[0], report)
    _render_query_heatmap(axes[1], report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _render_accuracy_bars(ax, report: dict[str, object]) -> None:
    runs = report["runs"]
    labels: list[str] = []
    pass_rates: list[float] = []
    non_fail_rates: list[float] = []

    for run in runs:
        summary = run["summary"]
        total = summary["pass"] + summary["partial_pass"] + summary["fail"]
        if total == 0:
            continue
        labels.append(run.get("plot_label", run["display_label"]))
        pass_rates.append(summary["pass"] / total)
        non_fail_rates.append((summary["pass"] + summary["partial_pass"]) / total)

    if not labels:
        ax.set_title("No scored eval artifacts available")
        ax.set_axis_off()
        return

    import seaborn as sns

    metrics = {
        "Run": labels + labels,
        "Metric": ["Pass rate"] * len(labels) + ["Non-fail rate"] * len(labels),
        "Rate": pass_rates + non_fail_rates,
    }
    sns.barplot(ax=ax, data=metrics, x="Rate", y="Run", hue="Metric", orient="h")
    ax.set_title("Provider Choice Accuracy Summary")
    ax.set_xlabel("Rate")
    ax.set_ylabel("")
    ax.set_xlim(0.0, 1.0)
    ax.legend(loc="lower right", title="")


def _render_query_heatmap(ax, report: dict[str, object]) -> None:
    query_rows = report["query_rows"]
    run_labels = [run.get("plot_label", run["display_label"]) for run in report["runs"]]
    scored_query_rows = [
        row
        for row in query_rows
        if any(cell["outcome"] != "not_scored" for cell in row["runs"])
    ]
    if not scored_query_rows:
        ax.set_title("No per-query scored data available")
        ax.set_axis_off()
        return

    matrix: list[list[int]] = []
    y_labels: list[str] = []
    for row in scored_query_rows:
        by_label = {cell.get("plot_label", cell["label"]): cell for cell in row["runs"]}
        matrix.append(
            [_encode_outcome(by_label.get(label, {"outcome": "not_scored"})["outcome"]) for label in run_labels]
        )
        y_labels.append(row["query_id"])

    import seaborn as sns

    sns.heatmap(
        matrix,
        ax=ax,
        cmap=sns.color_palette(["#d9d9d9", "#d73027", "#fdae61", "#1a9850"], as_cmap=True),
        cbar=False,
        linewidths=0.5,
        xticklabels=run_labels,
        yticklabels=y_labels,
        vmin=0,
        vmax=3,
    )
    ax.set_title("Per-Query Outcome Matrix")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)


def _encode_outcome(outcome: str) -> int:
    mapping = {
        "not_scored": 0,
        "fail": 1,
        "partial_pass": 2,
        "pass": 3,
    }
    return mapping.get(outcome, 0)
