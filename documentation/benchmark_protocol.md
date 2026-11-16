# Goldilocks Field Arithmetic Benchmark Protocol

## 1. Objective and scope

This project compares native Goldilocks field arithmetic in three
zero-knowledge proof ecosystem libraries:

- Plonky2
- Plonky3
- gnark-crypto

The evaluated operations are addition, subtraction, multiplication,
exponentiation, and inversion.

This is a primitive field-arithmetic microbenchmark. It is not a
benchmark of complete zero-knowledge proof systems.

## 2. Field

The benchmark uses the Goldilocks prime field:

p = 2^64 - 2^32 + 1

Decimal modulus:

18446744069414584321

Hexadecimal modulus:

0xffffffff00000001

## 3. Historical experiment and recovered data

The historical experiment description records the following settings:

| Parameter | Historical description |
|---|---|
| Plonky2 | 1.1.0 |
| Plonky3 | 0.7.0 |
| gnark-crypto | 0.20.1 |
| Rust | nightly 1.99.0 |
| Go | 1.27.1 |
| CPU | Intel Core i5-8250U |
| Architecture | x86_64 |
| Kernel | 6.12.0-160000.35-default |
| Reported workload sizes | 1,000; 10,000; 100,000; 1,000,000 |
| Warmup rounds | 10 |
| Samples per run | 30 |
| Exponent | 65537 |
| Random seed | 42 |
| CPU affinity | Logical CPU 2 |

The recovered original CSV files contain measurements for the
1,000,000-operation workload. The other workload sizes are part of
the historical description but are not present in the recovered CSV
files. They must not be represented as independently verified
measurements.

The recovered original CSV files are preserved without modification
in `data/original/`. They contain:

- Plonky2: RUN3 and RUN4
- Plonky3: RUN3 and RUN4
- gnark-crypto: RUN1 and RUN2

These historical datasets are kept separate from the reconstructed
measurements.

## 4. Reconstructed benchmark environment

The controlled reconstructed runs were collected in the following
environment:

| Parameter | Configuration |
|---|---|
| Operating system | openSUSE Leap 16.0 |
| Kernel | 6.12.0-160000.35-default |
| Architecture | x86_64 |
| CPU | Intel Core i5-8250U @ 1.60 GHz |
| Logical CPUs | 8 |
| Rust compiler | 1.102.0-nightly (5f4effd57, 2026-11-13) |
| Cargo | 1.102.0-nightly (ede6cefea, 2026-11-11) |
| Go | 1.27.3 linux/amd64 |
| Plonky2 | 1.1.0 |
| Plonky3 | 0.7.0 |
| gnark-crypto | 0.20.1 |
| CPU affinity | Logical CPU 2 |
| CPU governor | performance |
| Workload | 1,000,000 operations per sample |
| Warmup | 10 rounds per operation |
| Measured samples | 30 per operation per process run |
| Exponent | 65537 |
| Random seed | 42 |

Build configurations:

- Plonky2: `release-native`
- Plonky3: `release`
- gnark-crypto: `release`

The build configurations are recorded as implemented; they are not
assumed to produce identical compiler flags or machine code across
languages and libraries.

The `performance` governor does not lock the processor to a fixed
frequency. CPU affinity controls the logical CPU on which the process
runs, but does not eliminate frequency scaling, turbo behaviour,
thermal effects, or operating-system activity.

## 5. Benchmark harness and measurement

The reconstructed harnesses use preallocated output buffers outside
the timed region. Each measured operation writes its result to the
output buffer.

For Rust implementations, the output buffer is passed to
`black_box` after the elapsed-time measurement. For Go, the
`runtime.KeepAlive` operation is performed after the timed interval.

The Go implementation uses dedicated operation loops rather than
indirect function calls inside the timed loop.

The measured interval includes arithmetic, loop and indexing
overhead, and result storage. It does not represent isolated
instruction latency.

The primary metric is:

time_per_operation_ns = total_time_ns / operations

Throughput is:

throughput_operations_per_second =
    operations / (total_time_ns / 1,000,000,000)

Each operation is measured in a separate sequence. The operation
order within each library is fixed:

1. Addition
2. Subtraction
3. Multiplication
4. Exponentiation
5. Inversion

This fixed ordering is a potential source of order-related effects
and is considered when interpreting the results.

## 6. Reconstructed run groups

Reconstructed measurements are stored separately in
`data/reconstructed/`.

The runs have different methodological status:

| Runs | Status | Treatment |
|---|---|---|
| RUN1-RUN2 | Earlier reconstructed runs with known harness limitations | Excluded from primary comparisons |
| RUN3-RUN4 | Corrected harness, but without the controlled CPU affinity and governor protocol | Supplementary only |
| RUN5-RUN7 | Corrected harness and controlled CPU affinity/governor protocol | Primary dataset |

RUN5-RUN7 use CPU 2 affinity and the performance governor. The
execution order of libraries was varied between process runs:

| Run | Library execution order |
|---|---|
| RUN5 | Plonky2, Plonky3, gnark-crypto |
| RUN6 | gnark-crypto, Plonky3, Plonky2 |
| RUN7 | Plonky2, Plonky3, gnark-crypto |

Each primary process run contains 30 measured samples for each of
five operations for each library.

The primary dataset therefore contains:

- 3 libraries
- 3 independent process runs per library
- 5 operations
- 30 samples per operation per process run
- 1,350 raw timing observations in total

There are 90 raw observations per library and operation, but only
three independent process-level replicates. The 90 observations
must not be treated as 90 independent process runs.

## 7. Statistical analysis

The primary analysis reports:

- Median and interquartile range (IQR) of the 90 observations per
  library and operation, as descriptive sample-level statistics.
- The median for each individual process run.
- Mean, standard deviation, range, and coefficient of variation
  (CV) across the three process-run medians.

Between-run variability is calculated from the three process-level
medians. It is a descriptive measure based on n = 3 independent
process runs.

Potential outliers are screened using the Tukey 1.5 × IQR rule,
applied separately within each library, operation, and process run.
Flagged observations are retained in the primary analysis. Outlier
flags alone do not establish that a measurement is erroneous.

The small number of independent process runs does not support
strong inferential claims. Descriptive differences must not be
presented as statistically significant or as proof of equivalence.

## 8. Reproducibility and data integrity

Raw CSV measurements must remain unchanged after collection.
Analysis scripts should read the raw files and generate derived
tables and figures separately.

Each result must retain its library and process-run identity.
Historical, uncontrolled reconstructed, and controlled primary
datasets must not be pooled without an explicit methodological
justification.

The repository should preserve source code, toolchain information,
benchmark configuration, raw data, and analysis procedures so that
the reported results can be independently inspected.

## 9. Limitations

The benchmark measures selected native field arithmetic operations.
It does not directly measure:

- Complete proof generation or verification
- FFT or polynomial commitment performance
- SIMD or batch inversion performance
- Hashing performance
- Memory consumption
- End-to-end blockchain performance

Results are specific to the tested hardware, operating system,
compiler and runtime versions, library versions, build
configurations, and benchmark harness.

Cross-library comparisons are affected by implementation and
language differences. The measurements do not isolate the
mathematical algorithms from their implementation details.

The fixed operation order, three independent process runs, and
possibility of CPU frequency and thermal variation are additional
limitations. Further experiments with counterbalanced operation
orders and more independent process runs would strengthen the
reproducibility assessment.
