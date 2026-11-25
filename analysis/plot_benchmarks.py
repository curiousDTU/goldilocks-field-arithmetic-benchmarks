from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
FIGURE_DIR = ROOT / "results" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OPERATIONS = [
    "addition", "subtraction", "multiplication",
    "exponentiation", "inversion",
]
LIBRARIES = ["Plonky2", "Plonky3", "gnark-crypto"]

COLORS = {
    "Plonky2": "tab:blue",
    "Plonky3": "tab:orange",
    "gnark-crypto": "tab:green",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
    "savefig.dpi": 600,
})


def performance_plot(operations, filename, title):
    data = pd.read_csv(
        TABLE_DIR / "mean_run_medians_comparison.csv"
    ).set_index("operation").loc[operations, LIBRARIES]

    x = np.arange(len(operations))
    width = 0.22

    fig, ax = plt.subplots(figsize=(7.2, 4.5))

    for i, library in enumerate(LIBRARIES):
        values = data[library].to_numpy()
        bars = ax.bar(
            x + (i - 1) * width,
            values,
            width,
            label=library,
            color=COLORS[library],
            edgecolor="black",
            linewidth=0.5,
        )

        for bar, value in zip(bars, values):
            ax.annotate(
                f"{value:.2f}",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_title(title, pad=14)
    ax.set_ylabel("Mean of process-run medians (ns/op)")
    ax.set_xlabel("Goldilocks field operation")
    ax.set_xticks(x)
    ax.set_xticklabels([op.capitalize() for op in operations])
    ax.set_ylim(0, max(data.max()) * 1.22)
    ax.grid(axis="y", linestyle=":", linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=False,
    )

    fig.text(
        0.99, 0.01,
        r"Workload: $10^6$ operations",
        ha="right",
        fontsize=8,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.94])

    fig.savefig(FIGURE_DIR / f"{filename}.png", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / f"{filename}.pdf", bbox_inches="tight")
    plt.close(fig)


def reproducibility_plot():
    data = pd.read_csv(
        TABLE_DIR / "between_run_reproducibility.csv"
    )

    pivot = data.pivot(
        index="operation",
        columns="library",
        values="cv_percent",
    ).loc[OPERATIONS, LIBRARIES]

    x = np.arange(len(OPERATIONS))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10, 5.8))

    for index, library in enumerate(LIBRARIES):
        positions = x + (index - 1) * width
        ax.bar(
            positions,
            pivot[library],
            width,
            label=library,
        )

    ax.set_ylabel("Between-run coefficient of variation (%)")
    ax.set_xlabel("Arithmetic operation")
    ax.set_title("Benchmark Reproducibility Across Three Process Runs")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [operation.capitalize() for operation in OPERATIONS]
    )
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.set_ylim(bottom=0)

    fig.tight_layout()
    fig.savefig(
        FIGURE_DIR / "between_run_reproducibility.png",
        dpi=300,
        bbox_inches="tight",
    )
    fig.savefig(
        FIGURE_DIR / "between_run_reproducibility.pdf",
        bbox_inches="tight",
    )
    plt.close(fig)


if __name__ == "__main__":
    performance_plot(
        ["addition", "subtraction", "multiplication"],
        "performance_basic_operations",
        "Mean of Run Medians: Basic Goldilocks Field Operations",
    )
    performance_plot(
        ["exponentiation", "inversion"],
        "performance_expensive_operations",
        "Mean of Run Medians: Expensive Goldilocks Field Operations",
    )
    reproducibility_plot()
    print(f"Figures saved in {FIGURE_DIR}")
