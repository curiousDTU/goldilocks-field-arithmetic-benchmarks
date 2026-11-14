# Goldilocks Field Arithmetic Benchmark Protocol

## 1. Objective

Compare native Goldilocks field arithmetic in three zero-knowledge
proof ecosystem libraries:

- Plonky2
- Plonky3
- gnark-crypto

The benchmark covers addition, subtraction, multiplication,
exponentiation, and inversion.

## 2. Field

Goldilocks prime field:

p = 2^64 - 2^32 + 1

Decimal modulus:

18446744069414584321

## 3. Original experiment configuration

The recovered original dataset documents the following configuration:

| Parameter | Original configuration |
|---|---|
| Plonky2 | 1.1.0 |
| Plonky3 | 0.7.0 |
| gnark-crypto | 0.20.1 |
| Rust | nightly 1.99.0 |
| Go | 1.27.1 |
| CPU | Intel Core i5-8250U |
| Architecture | x86_64 |
| Kernel | 6.12.0-160000.35-default |
| Workload sizes | 1,000; 10,000; 100,000; 1,000,000 |
| Warmup rounds | 10 |
| Samples per run | 30 |
| Independent runs | 2 per implementation |
| Exponent | 65537 |
| Random seed | 42 |
| CPU affinity | Logical CPU 2 |

These are historical experiment settings, not the current
reconstruction environment.

## 4. Operations

1. Addition
2. Subtraction
3. Multiplication
4. Exponentiation
5. Inversion

The exponentiation workload uses exponent 65537.

## 5. Measurement

The primary per-operation metric is:

time_per_operation_ns = total_time_ns / operations

Throughput is:

throughput_operations_per_second =
    operations / (total_time_ns / 1,000,000,000)

The elapsed-time measurement includes the benchmark loop,
array access, result assignment, and anti-optimization overhead.
It must not be interpreted as isolated instruction latency.

## 6. Recovered original datasets

The original CSV files are preserved without modification in:

data/original/

They contain two runs per implementation:

- Plonky2: RUN3 and RUN4
- Plonky3: RUN3 and RUN4
- gnark-crypto: RUN1 and RUN2

There are 30 samples per operation in each run, giving
60 pooled observations per operation and implementation.

## 7. Reconstructed experiments

New benchmark source code and measurements must be identified
as reconstructed work.

New measurements must be stored separately in:

data/reconstructed/

The reconstruction must record actual compiler versions,
library versions, build flags, operating system, CPU details,
kernel, CPU affinity, workload sizes, seed, warmup, and sample
counts.

Do not describe reconstructed measurements as original results.

## 8. Statistical analysis

Report median and interquartile range (IQR) for each operation
and implementation.

Inspect distributions and potential outliers. Do not remove
observations solely because they are statistical outliers.

The original dataset has only two independent process runs.
Its 60 pooled observations per operation must not automatically
be treated as 60 independent experimental runs for inferential
significance testing.

Future reconstructed experiments should use multiple independent
process runs and preserve run identifiers in the raw data.

## 9. Scope and limitations

This benchmark measures selected native field arithmetic
operations. It does not directly measure:

- Complete proof generation or verification
- FFT or polynomial commitment performance
- SIMD or batch inversion performance
- Hashing performance
- Memory consumption
- End-to-end blockchain performance

Conclusions must remain limited to the tested libraries,
versions, hardware, and workloads.
