# Benchmarking Goldilocks Field Arithmetic Across ZK Libraries

Reproducible benchmark reconstruction for:

- Plonky2
- Plonky3
- gnark-crypto

## Experimental environment

- OS: openSUSE Leap 16.0
- Architecture: x86_64
- CPU: Intel Core i5-8250U
- Rust: 1.100.0
- Go: 1.27.3
- Python: isolated virtual environment

## Project structure

- benchmarks/: benchmark implementations
- data/original/: recovered original experimental data
- data/reconstructed/: new experimental measurements
- analysis/: statistical analysis scripts
- results/: tables and figures
- documentation/: experimental protocols and environment details

Original and reconstructed datasets must remain separate.
