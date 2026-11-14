use plonky2::field::goldilocks_field::GoldilocksField;
use plonky2::field::types::{Field, Field64};

use std::fs::File;
use std::hint::black_box;
use std::io::{BufWriter, Write};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

const MODULUS: u64 = 18_446_744_069_414_584_321;
const OPERATIONS: usize = 1_000_000;
const WARMUP_ROUNDS: usize = 10;
const SAMPLES: usize = 30;
const EXPONENT: u64 = 65_537;
const SEED: u64 = 42;

type F = GoldilocksField;

// Deterministic XorShift64 input generator.
// This is a reconstruction, not a claim of the original PRNG implementation.
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

    fn next_field(&mut self) -> F {
        // Generate a nonzero canonical field element.
        F::from_canonical_u64(1 + self.next() % (F::ORDER - 1))
    }
}

fn measure<Op>(
    operation: &str,
    exponent: u64,
    run_id: &str,
    writer: &mut BufWriter<File>,
    op: Op,
) -> std::io::Result<()>
where
    Op: Fn(usize) -> F,
{
    for _ in 0..WARMUP_ROUNDS {
        for i in 0..OPERATIONS {
            black_box(op(i));
        }
    }

    for sample in 1..=SAMPLES {
        let start = Instant::now();

        for i in 0..OPERATIONS {
            black_box(op(i));
        }

        let elapsed_ns = start.elapsed().as_nanos() as u64;
        let time_per_operation = elapsed_ns as f64 / OPERATIONS as f64;
        let throughput = OPERATIONS as f64 * 1_000_000_000.0 / elapsed_ns as f64;

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        writeln!(
            writer,
            "{},{},1.1.0,Goldilocks,{},{},{},{},{},{:.6},{:.3},{},{},{},release-native",
            timestamp,
            "plonky2",
            MODULUS,
            operation,
            sample,
            OPERATIONS,
            elapsed_ns,
            time_per_operation,
            throughput,
            WARMUP_ROUNDS,
            exponent,
            SEED
        )?;
    }

    println!("Completed: {} ({})", operation, run_id);
    Ok(())
}

fn main() -> std::io::Result<()> {
    let run_id = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "RECON_RUN1".to_string());

    std::fs::create_dir_all("../../data/reconstructed")?;

    let output_path = format!(
        "../../data/reconstructed/plonky2_goldilocks_math_operations_{}.csv",
        run_id
    );

    let file = File::create(&output_path)?;
    let mut writer = BufWriter::new(file);

    writeln!(
        writer,
        "timestamp_unix,library,library_version,field,field_modulus,operation,sample,operations,total_time_ns,time_per_operation_ns,throughput_operations_per_second,warmup_rounds,exponent,seed,build_mode"
    )?;

    println!("Generating {} deterministic field elements...", OPERATIONS);

    let mut rng = XorShift64::new(SEED);

    let a: Vec<F> = (0..OPERATIONS).map(|_| rng.next_field()).collect();

    let b: Vec<F> = (0..OPERATIONS).map(|_| rng.next_field()).collect();

    println!("Running Plonky2 Goldilocks benchmark");
    println!("Run: {}", run_id);
    println!("Operations per sample: {}", OPERATIONS);
    println!("Warmups: {}", WARMUP_ROUNDS);
    println!("Measured samples: {}", SAMPLES);

    // Correctness checks before timing.
    for i in 0..100 {
        assert_eq!((a[i] + b[i]) - b[i], a[i]);
        assert_eq!((a[i] * b[i]) / b[i], a[i]);
        assert_eq!(a[i].try_inverse().unwrap() * a[i], F::ONE);
    }

    println!("Correctness checks passed.");

    measure("addition", 0, &run_id, &mut writer, |i| a[i] + b[i])?;

    measure("subtraction", 0, &run_id, &mut writer, |i| a[i] - b[i])?;

    measure("multiplication", 0, &run_id, &mut writer, |i| a[i] * b[i])?;

    measure("exponentiation", EXPONENT, &run_id, &mut writer, |i| {
        a[i].exp_u64(EXPONENT)
    })?;

    measure("inversion", 0, &run_id, &mut writer, |i| {
        a[i].try_inverse().expect("Input must be nonzero")
    })?;

    writer.flush()?;

    println!("\nBenchmark completed.");
    println!("CSV saved to: {}", output_path);

    Ok(())
}
