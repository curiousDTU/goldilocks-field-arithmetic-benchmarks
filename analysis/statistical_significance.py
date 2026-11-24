from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"

df = pd.read_csv(TABLE_DIR / "per_run_medians.csv")

OPERATIONS = [
    "addition",
    "subtraction",
    "multiplication"
]

ALPHA = 0.05
results = []


def holm_correction(p_values):
    p_values = np.asarray(p_values, dtype=float)
    n = len(p_values)

    order = np.argsort(p_values)
    adjusted = np.empty(n)
    previous = 0.0

    for rank, idx in enumerate(order):
        value = (n - rank) * p_values[idx]
        previous = max(previous, value)
        adjusted[idx] = min(previous, 1.0)

    return adjusted


for operation in OPERATIONS:

    subset = df[
        (df["operation"] == operation)
        & df["library_label"].isin(["Plonky2", "Plonky3"])
    ]

    paired = subset.pivot(
        index="run",
        columns="library_label",
        values="run_median_ns"
    ).loc[["RUN5", "RUN6", "RUN7"]]

    p2 = paired["Plonky2"].to_numpy()
    p3 = paired["Plonky3"].to_numpy()

    assert len(p2) == len(p3) == 3
    assert np.isfinite(paired.to_numpy()).all()

    differences = p3 - p2

    t_stat, t_p = ttest_rel(
        p3, p2, alternative="two-sided"
    )

    w_stat, w_p = wilcoxon(
        differences,
        alternative="two-sided",
        method="exact"
    )

    percentage = (
        (np.mean(p3) - np.mean(p2))
        / np.mean(p2)
    ) * 100

    results.append({
        "operation": operation,
        "n_pairs": len(p2),
        "plonky2_mean_ns": np.mean(p2),
        "plonky3_mean_ns": np.mean(p3),
        "mean_difference_ns": np.mean(differences),
        "percentage_difference": percentage,
        "t_statistic": t_stat,
        "t_p_value": t_p,
        "wilcoxon_statistic": w_stat,
        "wilcoxon_p_value": w_p
    })

results = pd.DataFrame(results)

results["t_p_holm"] = holm_correction(
    results["t_p_value"]
)

results["wilcoxon_p_holm"] = holm_correction(
    results["wilcoxon_p_value"]
)

results["t_significant"] = (
    results["t_p_holm"] < ALPHA
)

results["wilcoxon_significant"] = (
    results["wilcoxon_p_holm"] < ALPHA
)

output = TABLE_DIR / "statistical_significance.csv"

results.to_csv(
    output,
    index=False,
    float_format="%.8f"
)

print("\nStatistical Significance Analysis\n")
print(results.to_string(index=False))
print(f"\nResults saved to: {output}")
