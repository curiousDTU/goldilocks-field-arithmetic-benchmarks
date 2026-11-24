from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "reconstructed"
TABLE_DIR = ROOT / "results" / "tables"
FIGURE_DIR = ROOT / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

OPERATIONS = [
    "addition",
    "subtraction",
    "multiplication",
    "exponentiation",
    "inversion",
]

LIBRARIES = ["Plonky2", "Plonky3", "gnark-crypto"]

RUNS = [5, 6, 7]

METRIC = "time_per_operation_ns"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 12,
    "legend.fontsize": 10,
    "figure.dpi": 300,
})


# -------------------------------------------------
# 1. Load raw benchmark data
# -------------------------------------------------

frames = []

for run in RUNS:
    files = sorted(DATA_DIR.glob(f"*RECON_RUN{run}.csv"))

    if len(files) != 3:
        raise ValueError(
            f"Expected 3 CSV files for RUN{run}, "
            f"found {len(files)}"
        )

    for file in files:
        df = pd.read_csv(file)
        df["run"] = f"RUN{run}"
        frames.append(df)

data = pd.concat(frames, ignore_index=True)

data["library"] = (
    data["library"]
    .str.lower()
    .replace({
        "plonky2": "Plonky2",
        "plonky3": "Plonky3",
        "gnark_crypto": "gnark-crypto",
    })
)

data = data[data["operations"] == 1_000_000].copy()

assert len(data) == 1350, "Unexpected sample count"

counts = data.groupby(
    ["library", "operation", "run"]
).size()

assert len(counts) == 45
assert counts.eq(30).all()
assert data[METRIC].notna().all()

print(f"Total observations: {len(data)}")


# -------------------------------------------------
# 2. IQR-based outlier analysis
# -------------------------------------------------

summary = []
outlier_records = []

for library in LIBRARIES:
    for operation in OPERATIONS:

        group = data[
            (data["library"] == library)
            & (data["operation"] == operation)
        ].copy()

        values = group[METRIC]

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        upper_mask = values > upper_bound
        lower_mask = values < lower_bound

        outlier_mask = upper_mask | lower_mask

        outliers = group[outlier_mask].copy()
        filtered = values[~outlier_mask]

        outliers["lower_bound"] = lower_bound
        outliers["upper_bound"] = upper_bound

        outliers["outlier_type"] = np.where(
            outliers[METRIC] > upper_bound,
            "upper",
            "lower",
        )

        outlier_records.append(outliers)

        original_mean = values.mean()
        original_median = values.median()

        filtered_mean = filtered.mean()
        filtered_median = filtered.median()

        mean_change = (
            abs(original_mean - filtered_mean)
            / original_mean * 100
        )

        median_change = (
            abs(original_median - filtered_median)
            / original_median * 100
        )

        summary.append({
            "library": library,
            "operation": operation,
            "samples": len(values),
            "q1_ns": q1,
            "q3_ns": q3,
            "iqr_ns": iqr,
            "lower_bound_ns": lower_bound,
            "upper_bound_ns": upper_bound,
            "minimum_ns": values.min(),
            "maximum_ns": values.max(),
            "std_ns": values.std(),
            "upper_outliers": int(upper_mask.sum()),
            "lower_outliers": int(lower_mask.sum()),
            "total_outliers": int(outlier_mask.sum()),
            "outlier_percent":
                outlier_mask.mean() * 100,
            "original_mean_ns": original_mean,
            "filtered_mean_ns": filtered_mean,
            "original_median_ns": original_median,
            "filtered_median_ns": filtered_median,
            "mean_change_percent": mean_change,
            "median_change_percent": median_change,
        })

summary_df = pd.DataFrame(summary)

outliers_df = pd.concat(
    outlier_records,
    ignore_index=True,
)

summary_df.to_csv(
    TABLE_DIR / "outlier_analysis_summary.csv",
    index=False,
    float_format="%.6f",
)

outliers_df.to_csv(
    TABLE_DIR / "outlier_sample_details.csv",
    index=False,
)


# -------------------------------------------------
# Helper: Save figures in PNG and PDF formats
# -------------------------------------------------

def save_figure(fig, name):
    fig.tight_layout()

    for extension in ["png", "pdf"]:
        fig.savefig(
            FIGURE_DIR / f"{name}.{extension}",
            dpi=300,
            bbox_inches="tight",
        )

    plt.close(fig)


# -------------------------------------------------
# 3. Updated Fig. 2: Latency distributions
# -------------------------------------------------

fig, axes = plt.subplots(
    2, 3,
    figsize=(12, 7),
)

axes = axes.flatten()

for ax, operation in zip(axes, OPERATIONS):

    distributions = [
        data.loc[
            (data["library"] == library)
            & (data["operation"] == operation),
            METRIC,
        ].values
        for library in LIBRARIES
    ]

    ax.boxplot(
        distributions,
        tick_labels=LIBRARIES,
        widths=0.5,
        showfliers=True,
        whis=1.5,
        showmeans=True,
        flierprops={
            "marker": "o",
            "markersize": 4,
            "markerfacecolor": "none",
        },
        meanprops={
            "marker": "D",
            "markersize": 4,
        },
    )

    ax.set_title(operation.capitalize())
    ax.set_ylabel("Latency (ns/op)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.tick_params(axis="x", labelsize=9)

axes[5].axis("off")

save_figure(
    fig,
    "latency_distribution_updated",
)


# -------------------------------------------------
# 4. Outlier percentage comparison
# -------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5.5))

x = np.arange(len(OPERATIONS))
width = 0.24

for index, library in enumerate(LIBRARIES):

    subset = (
        summary_df[summary_df["library"] == library]
        .set_index("operation")
        .loc[OPERATIONS]
    )

    bars = ax.bar(
        x + (index - 1) * width,
        subset["outlier_percent"],
        width,
        label=library,
    )

    ax.bar_label(
        bars,
        fmt="%.1f",
        fontsize=8,
        padding=3,
    )

ax.set_xticks(x)
ax.set_xticklabels(
    [op.capitalize() for op in OPERATIONS]
)

ax.set_ylabel("Outlier percentage (%)")
ax.set_xlabel("Goldilocks field operation")
ax.set_ylim(
    0,
    summary_df["outlier_percent"].max() * 1.25,
)

ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

save_figure(fig, "outlier_percentage")


# -------------------------------------------------
# 5. Sensitivity of mean and median to outliers
# -------------------------------------------------

fig, axes = plt.subplots(
    3, 1,
    figsize=(10, 9),
    sharex=True,
)

for ax, library in zip(axes, LIBRARIES):

    subset = (
        summary_df[summary_df["library"] == library]
        .set_index("operation")
        .loc[OPERATIONS]
    )

    ax.bar(
        x - 0.18,
        subset["mean_change_percent"],
        0.36,
        label="Mean",
    )

    ax.bar(
        x + 0.18,
        subset["median_change_percent"],
        0.36,
        label="Median",
    )

    ax.set_title(library)
    ax.set_ylabel("Change (%)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend()

    ax.set_ylim(
        0,
        max(
            summary_df["mean_change_percent"].max(),
            summary_df["median_change_percent"].max(),
        ) * 1.15,
    )

axes[-1].set_xticks(x)

axes[-1].set_xticklabels(
    [op.capitalize() for op in OPERATIONS]
)

axes[-1].set_xlabel("Goldilocks field operation")

save_figure(fig, "outlier_sensitivity")


# -------------------------------------------------
# 6. Print final statistical summary
# -------------------------------------------------

print("\nOUTLIER ANALYSIS SUMMARY\n")

print(
    summary_df[
        [
            "library",
            "operation",
            "total_outliers",
            "outlier_percent",
            "mean_change_percent",
            "median_change_percent",
        ]
    ].round(4).to_string(index=False)
)

total_outliers = summary_df["total_outliers"].sum()

print("\nTotal observations:", len(data))
print("Total outliers:", total_outliers)

print(
    "Overall outlier percentage:",
    round(total_outliers / len(data) * 100, 4),
)

print(
    "Maximum mean change (%):",
    round(summary_df["mean_change_percent"].max(), 4),
)

print(
    "Maximum median change (%):",
    round(summary_df["median_change_percent"].max(), 4),
)

print("\nFigures saved to:", FIGURE_DIR)
print("Tables saved to:", TABLE_DIR)
print("\nOutlier analysis completed successfully.")
