from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "reconstructed"
TABLE_DIR = ROOT / "results" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

LIBRARIES = {
    "plonky2": "Plonky2",
    "plonky3": "Plonky3",
    "gnark_crypto": "gnark-crypto",
}
RUNS = ["RUN5", "RUN6", "RUN7"]
OPERATIONS = [
    "addition",
    "subtraction",
    "multiplication",
    "exponentiation",
    "inversion",
]
EXPECTED_SAMPLES = 30
EXPECTED_OPERATIONS = 1_000_000


def load_primary_data():
    frames = []

    for library_key, library_name in LIBRARIES.items():
        for run in RUNS:
            path = DATA_DIR / (
                f"{library_key}_goldilocks_math_operations_RECON_{run}.csv"
            )
            if not path.is_file():
                raise FileNotFoundError(path)

            frame = pd.read_csv(path)
            required = {
                "library",
                "library_version",
                "field",
                "field_modulus",
                "operation",
                "sample",
                "operations",
                "time_per_operation_ns",
                "warmup_rounds",
                "exponent",
                "seed",
                "build_mode",
            }
            missing = required.difference(frame.columns)
            if missing:
                raise ValueError(f"{path}: missing columns {sorted(missing)}")

            if len(frame) != len(OPERATIONS) * EXPECTED_SAMPLES:
                raise ValueError(f"{path}: unexpected row count {len(frame)}")

            if set(frame["operation"]) != set(OPERATIONS):
                raise ValueError(f"{path}: unexpected operation set")

            counts = frame.groupby("operation").size()
            if not (counts == EXPECTED_SAMPLES).all():
                raise ValueError(f"{path}: unexpected samples per operation")

            if not (frame["operations"] == EXPECTED_OPERATIONS).all():
                raise ValueError(f"{path}: unexpected workload size")

            if not (frame["warmup_rounds"] == 10).all():
                raise ValueError(f"{path}: unexpected warmup count")

            if library_key == "plonky2":
                expected_exponents = frame["operation"].map(
                    lambda op: 65537 if op == "exponentiation" else 0
                )
            else:
                expected_exponents = pd.Series(
                    65537, index=frame.index
                )

            if not (frame["exponent"] == expected_exponents).all():
                raise ValueError(f"{path}: unexpected exponent metadata")

            if not (frame["seed"] == 42).all():
                raise ValueError(f"{path}: unexpected seed")

            if not np.isfinite(frame["time_per_operation_ns"]).all():
                raise ValueError(f"{path}: non-finite timing")

            if (frame["time_per_operation_ns"] <= 0).any():
                raise ValueError(f"{path}: non-positive timing")

            frame["library_key"] = library_key
            frame["library_label"] = library_name
            frame["run"] = run
            frames.append(frame)

    data = pd.concat(frames, ignore_index=True)

    if len(data) != 1350:
        raise ValueError(f"Expected 1350 observations, got {len(data)}")

    return data


def descriptive_statistics(data):
    rows = []

    for (library, operation), group in data.groupby(
        ["library_label", "operation"], sort=False
    ):
        values = group["time_per_operation_ns"]
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        rows.append({
            "library": library,
            "operation": operation,
            "n_samples": len(values),
            "median_ns": values.median(),
            "mean_ns": values.mean(),
            "std_ns": values.std(ddof=1),
            "q1_ns": q1,
            "q3_ns": q3,
            "iqr_ns": q3 - q1,
            "min_ns": values.min(),
            "max_ns": values.max(),
        })

    return pd.DataFrame(rows)


def run_level_statistics(data):
    run_medians = (
        data.groupby(
            ["library_label", "operation", "run"], sort=False
        )["time_per_operation_ns"]
        .median()
        .rename("run_median_ns")
        .reset_index()
    )

    rows = []

    for (library, operation), group in run_medians.groupby(
        ["library_label", "operation"], sort=False
    ):
        values = group["run_median_ns"]
        mean = values.mean()
        sd = values.std(ddof=1)

        rows.append({
            "library": library,
            "operation": operation,
            "independent_runs": len(values),
            "mean_run_median_ns": mean,
            "sd_between_runs_ns": sd,
            "min_run_median_ns": values.min(),
            "max_run_median_ns": values.max(),
            "range_ns": values.max() - values.min(),
            "cv_percent": (sd / mean * 100) if mean else np.nan,
        })

    return run_medians, pd.DataFrame(rows)


def relative_performance(run_summary):
    pivot = run_summary.pivot(
        index="operation",
        columns="library",
        values="mean_run_median_ns",
    )

    ratio = pivot.div(pivot["Plonky2"], axis=0)
    percent = (ratio - 1.0) * 100.0

    return pivot, ratio, percent


def outlier_analysis(data):
    rows = []

    for (library, operation, run), group in data.groupby(
        ["library_label", "operation", "run"], sort=False
    ):
        values = group["time_per_operation_ns"]
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        flags = (values < lower) | (values > upper)

        rows.append({
            "library": library,
            "operation": operation,
            "run": run,
            "n_samples": len(values),
            "outlier_count": int(flags.sum()),
            "outlier_percent": flags.mean() * 100,
            "lower_fence_ns": lower,
            "upper_fence_ns": upper,
            "minimum_ns": values.min(),
            "maximum_ns": values.max(),
        })

    return pd.DataFrame(rows)


def save_table(frame, filename):
    frame.to_csv(TABLE_DIR / filename, index=False, float_format="%.8f")


def main():
    data = load_primary_data()

    descriptive = descriptive_statistics(data)
    run_medians, run_summary = run_level_statistics(data)
    mean_pivot, ratio, percent = relative_performance(run_summary)
    outliers = outlier_analysis(data)

    save_table(descriptive, "pooled_descriptive_statistics.csv")
    save_table(run_medians, "per_run_medians.csv")
    save_table(run_summary, "between_run_reproducibility.csv")
    save_table(mean_pivot.reset_index(), "mean_run_medians_comparison.csv")
    save_table(ratio.reset_index(), "relative_timing_vs_plonky2.csv")
    save_table(percent.reset_index(), "percentage_difference_vs_plonky2.csv")
    save_table(outliers, "tukey_outlier_analysis.csv")

    print(f"Validated observations: {len(data)}")
    print("\nMean of process-run medians (ns/op):")
    print(mean_pivot.round(4).to_string())

    print("\nRelative timing compared with Plonky2:")
    print(ratio.round(3).to_string())

    print("\nBetween-run reproducibility:")
    print(
        run_summary.pivot(
            index="operation",
            columns="library",
            values="cv_percent",
        ).round(3).to_string()
    )

    print("\nTukey outlier totals (observations retained):")
    print(
        outliers.groupby("library")["outlier_count"]
        .sum()
        .to_string()
    )

    print(f"\nCSV tables written to: {TABLE_DIR}")


if __name__ == "__main__":
    main()
