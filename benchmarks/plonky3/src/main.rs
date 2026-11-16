use p3_field::{Field, PrimeCharacteristicRing, PrimeField64};
use p3_goldilocks::Goldilocks;

use std::env;
use std::fs::{self, File};
use std::hint::black_box;
use std::io::{BufWriter, Write};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

const OPERATIONS: usize = 1_000_000;
const WARMUP_ROUNDS: usize = 10;
const SAMPLES: usize = 30;
const EXPONENT: u64 = 65537;
const SEED: u64 = 42;

struct XorShift64 {
    state: u64,
}

impl XorShift64 {
    fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    fn next(&mut self) -> u64 {
        let mut x = self.state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.state = x;
        x
    }
}

fn generate_inputs() -> (Vec<Goldilocks>, Vec<Goldilocks>) {
    let mut rng = XorShift64::new(SEED);
    let modulus = <Goldilocks as PrimeField64>::ORDER_U64;

    let a: Vec<Goldilocks> = (0..OPERATIONS)
        .map(|_| Goldilocks::new(1 + rng.next() % (modulus - 1)))
        .collect();

    let b: Vec<Goldilocks> = (0..OPERATIONS)
        .map(|_| Goldilocks::new(1 + rng.next() % (modulus - 1)))
        .collect();

    (a, b)
}

fn validate_arithmetic(a: &[Goldilocks], b: &[Goldilocks]) {
    for i in 0..1000 {
        assert_eq!(a[i] + b[i] - b[i], a[i]);
        assert_eq!(a[i] - b[i] + b[i], a[i]);

        let inverse_b = b[i].try_inverse().expect("b must be nonzero");
        assert_eq!((a[i] * b[i]) * inverse_b, a[i]);

        let inverse_a = a[i].try_inverse().expect("a must be nonzero");
        assert_eq!(a[i] * inverse_a, Goldilocks::ONE);
    }

    println!("Arithmetic correctness checks passed.");
}

fn measure<F>(operation: &F, output: &mut [Goldilocks]) -> u128
where
    F: Fn(usize) -> Goldilocks,
{
    let start = Instant::now();

    for i in 0..OPERATIONS {
        output[i] = operation(i);
    }

    let elapsed_ns = start.elapsed().as_nanos();
    black_box(&output[..]);

    elapsed_ns
}

fn timestamp_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("System clock is before UNIX epoch")
        .as_secs()
}

fn benchmark_operation<F>(
    writer: &mut BufWriter<File>,
    operation_name: &str,
    operation: F,
    output: &mut [Goldilocks],
    run_id: &str,
) -> std::io::Result<()>
where
    F: Fn(usize) -> Goldilocks,
{
    println!("Benchmarking {operation_name}...");

    for _ in 0..WARMUP_ROUNDS {
        measure(&operation, output);
    }

    for sample in 1..=SAMPLES {
        let elapsed_ns = measure(&operation, output);
        let time_per_operation = elapsed_ns as f64 / OPERATIONS as f64;
        let throughput = OPERATIONS as f64 * 1_000_000_000.0 / elapsed_ns as f64;

        writeln!(
            writer,
            "{},{},{},{},{},{},{},{},{},{:.6},{:.6},{},{},{},release",
            timestamp_unix(),
            "Plonky3",
            "0.7.0",
            "Goldilocks",
            <Goldilocks as PrimeField64>::ORDER_U64,
            operation_name,
            sample,
            OPERATIONS,
            elapsed_ns,
            time_per_operation,
            throughput,
            WARMUP_ROUNDS,
            EXPONENT,
            SEED
        )?;

        if sample % 10 == 0 {
            println!("  {operation_name}: {sample}/{SAMPLES} samples completed");
        }
    }

    println!("Completed {operation_name} for {run_id}.");
    Ok(())
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = env::args().collect();

    let run_id = args.get(1).map(String::as_str).unwrap_or("RECON_RUN1");

    let filename =
        format!("../../data/reconstructed/plonky3_goldilocks_math_operations_{run_id}.csv");

    println!("Plonky3 Goldilocks arithmetic benchmark");
    println!("Run ID: {run_id}");
    println!("Operations per sample: {OPERATIONS}");
    println!("Warmup rounds: {WARMUP_ROUNDS}");
    println!("Samples per operation: {SAMPLES}");
    println!(
        "Goldilocks modulus: {}",
        <Goldilocks as PrimeField64>::ORDER_U64
    );

    let (a, b) = generate_inputs();
    validate_arithmetic(&a, &b);
    let mut output = vec![Goldilocks::ZERO; OPERATIONS];

    fs::create_dir_all("../../data/reconstructed")?;

    let file = File::create(&filename)?;
    let mut writer = BufWriter::new(file);

    writeln!(
        writer,
        "timestamp_unix,library,library_version,field,field_modulus,operation,sample,operations,total_time_ns,time_per_operation_ns,throughput_operations_per_second,warmup_rounds,exponent,seed,build_mode"
    )?;

    benchmark_operation(
        &mut writer,
        "addition",
        |i| a[i] + b[i],
        &mut output,
        run_id,
    )?;

    benchmark_operation(
        &mut writer,
        "subtraction",
        |i| a[i] - b[i],
        &mut output,
        run_id,
    )?;

    benchmark_operation(
        &mut writer,
        "multiplication",
        |i| a[i] * b[i],
        &mut output,
        run_id,
    )?;

    benchmark_operation(
        &mut writer,
        "exponentiation",
        |i| a[i].exp_u64(EXPONENT),
        &mut output,
        run_id,
    )?;

    benchmark_operation(
        &mut writer,
        "inversion",
        |i| a[i].try_inverse().expect("Input must be nonzero"),
        &mut output,
        run_id,
    )?;

    writer.flush()?;

    println!("\nBenchmark completed.");
    println!("CSV saved to: {filename}");

    Ok(())
}
