# Microbenchmarking Goldilocks Field Arithmetic in Plonky2, Plonky3, and gnark-crypto

This repository provides benchmark implementations,
experimental datasets, statistical analysis scripts,
and reproducibility materials for a comparative
performance evaluation of Goldilocks field arithmetic.

## Evaluated libraries

- Plonky2 (v1.1.0)
- Plonky3 (p3-goldilocks v0.7.0)
- gnark-crypto (v0.20.1)

## Evaluated operations

- Addition
- Subtraction
- Multiplication
- Exponentiation (exponent = 65537)
- Inversion

## Experimental environment

- OS: openSUSE Leap 16.0
- Architecture: x86_64
- CPU: Intel Core i5-8250U
- Physical cores: 4
- Logical CPUs: 8
- CPU affinity: logical CPU 2
- CPU frequency governor: performance
- Rust: nightly toolchain
- Go: 1.27.3
- Python: isolated virtual environment

## Experimental methodology

- Goldilocks prime: 18446744069414584321
- Random number generator: XorShift64
- Shift parameters: 13, 7, 17
- Random seed: 42
- Warm-up rounds: 10
- Operations per sample: 1,000,000
- Samples per operation per run: 30
- Primary experimental runs: RECON_RUN5 to RECON_RUN7
- Total primary experimental observations: 1350

The primary performance metric is the arithmetic mean
of the three independent process-run medians.

## Statistical analysis

The analysis includes:

- Descriptive statistics
- Effective per-operation latency
- Derived computational throughput
- Between-run reproducibility
- Standard deviation and coefficient of variation
- Paired t-test
- Exact Wilcoxon signed-rank test
- Holm multiple-comparison correction
- Tukey IQR-based outlier detection
- Outlier sensitivity analysis

Statistical significance testing compares Plonky2
and Plonky3 for addition, subtraction, and
multiplication using three matched experimental runs.

Given the limited number of independent runs,
inferential results are interpreted as exploratory.

Outlier detection uses the 1.5 x IQR criterion.
All primary observations are retained in the main
performance analysis.

## Reproducing the additional analysis

From the repository root, activate a Python
environment containing NumPy, pandas, SciPy,
and Matplotlib.

Run:

    python analysis/statistical_significance.py
    python analysis/plot_outlier_analysis.py

## Generated statistical tables

- results/tables/statistical_significance.csv
- results/tables/outlier_analysis_summary.csv
- results/tables/outlier_sample_details.csv

## Generated figures

- latency_distribution_updated.pdf/png
- outlier_percentage.pdf/png
- outlier_sensitivity.pdf/png

All generated figures are available in results/figures/.

## Project structure

- benchmarks/: benchmark implementations
- data/original/: recovered original experimental data
- data/reconstructed/: new experimental measurements
- analysis/: statistical analysis scripts
- results/: tables and figures
- documentation/: experimental protocols and environment details

## Experimental limitations

The experiments evaluate native field arithmetic on
a single hardware platform using a fixed workload.

The results should not be interpreted as universal
performance rankings or end-to-end zero-knowledge
proof generation performance.

Future work includes multi-platform evaluation,
additional workload sizes, more independent runs,
and hardware-level performance profiling.

## Data integrity and reproducibility

Original and reconstructed datasets remain separate.

The primary analysis uses RECON_RUN5 to RECON_RUN7
for each evaluated library.

Benchmark implementations, dependency lock files,
experimental measurements, and analysis scripts
are provided to support reproducibility.
