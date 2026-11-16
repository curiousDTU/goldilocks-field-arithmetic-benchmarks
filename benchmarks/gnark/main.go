package main

import (
	"encoding/csv"
	"fmt"
	"math/big"
	"os"
	"runtime"
	"strconv"
	"time"

	"github.com/consensys/gnark-crypto/field/goldilocks"
)

const (
	operations   = 1_000_000
	warmupRounds = 10
	samples      = 30
	exponent     = uint64(65537)
	seed         = uint64(42)
)

type XorShift64 struct {
	state uint64
}

func (r *XorShift64) next() uint64 {
	x := r.state
	x ^= x << 13
	x ^= x >> 7
	x ^= x << 17
	r.state = x
	return x
}

func generateInputs() ([]goldilocks.Element, []goldilocks.Element) {
	rng := XorShift64{state: seed}
	modulus := goldilocks.Modulus().Uint64()

	a := make([]goldilocks.Element, operations)
	b := make([]goldilocks.Element, operations)

	for i := 0; i < operations; i++ {
		a[i] = goldilocks.NewElement(1 + rng.next()%(modulus-1))
	}
	for i := 0; i < operations; i++ {
		b[i] = goldilocks.NewElement(1 + rng.next()%(modulus-1))
	}

	return a, b
}

func validateArithmetic(
	a, b []goldilocks.Element,
	exponentBig *big.Int,
) {
	var result, inverse, expected, squared goldilocks.Element
	two := big.NewInt(2)

	for i := 0; i < 1000; i++ {
		result.Add(&a[i], &b[i])
		result.Sub(&result, &b[i])
		if !result.Equal(&a[i]) {
			panic("addition correctness check failed")
		}

		result.Sub(&a[i], &b[i])
		result.Add(&result, &b[i])
		if !result.Equal(&a[i]) {
			panic("subtraction correctness check failed")
		}

		result.Mul(&a[i], &b[i])
		inverse.Inverse(&b[i])
		result.Mul(&result, &inverse)
		if !result.Equal(&a[i]) {
			panic("multiplication/inversion correctness check failed")
		}

		inverse.Inverse(&a[i])
		result.Mul(&a[i], &inverse)
		if !result.IsOne() {
			panic("inversion correctness check failed")
		}

		expected.Exp(a[i], two)
		squared.Mul(&a[i], &a[i])
		if !expected.Equal(&squared) {
			panic("exponentiation correctness check failed")
		}

		_ = exponentBig
	}

	fmt.Println("Arithmetic correctness checks passed.")
}

type operationFunc func(int, *goldilocks.Element)

func measureAddition(
	a, b, output []goldilocks.Element,
) int64 {
	start := time.Now()

	for i := 0; i < operations; i++ {
		output[i].Add(&a[i], &b[i])
	}

	elapsed := time.Since(start)
	runtime.KeepAlive(a)
	runtime.KeepAlive(b)
	runtime.KeepAlive(output)

	return elapsed.Nanoseconds()
}

func measureSubtraction(
	a, b, output []goldilocks.Element,
) int64 {
	start := time.Now()

	for i := 0; i < operations; i++ {
		output[i].Sub(&a[i], &b[i])
	}

	elapsed := time.Since(start)
	runtime.KeepAlive(a)
	runtime.KeepAlive(b)
	runtime.KeepAlive(output)

	return elapsed.Nanoseconds()
}

func measureMultiplication(
	a, b, output []goldilocks.Element,
) int64 {
	start := time.Now()

	for i := 0; i < operations; i++ {
		output[i].Mul(&a[i], &b[i])
	}

	elapsed := time.Since(start)
	runtime.KeepAlive(a)
	runtime.KeepAlive(b)
	runtime.KeepAlive(output)

	return elapsed.Nanoseconds()
}

func measureExponentiation(
	a, output []goldilocks.Element, exponentBig *big.Int,
) int64 {
	start := time.Now()

	for i := 0; i < operations; i++ {
		output[i].Exp(a[i], exponentBig)
	}

	elapsed := time.Since(start)
	runtime.KeepAlive(a)
	runtime.KeepAlive(output)

	return elapsed.Nanoseconds()
}

func measureInversion(
	a, output []goldilocks.Element,
) int64 {
	start := time.Now()

	for i := 0; i < operations; i++ {
		output[i].Inverse(&a[i])
	}

	elapsed := time.Since(start)
	runtime.KeepAlive(a)
	runtime.KeepAlive(output)

	return elapsed.Nanoseconds()
}

func benchmarkOperation(
	writer *csv.Writer,
	name string,
	measure func() int64,
	runID string,
) error {
	fmt.Printf("Benchmarking %s...\n", name)

	for i := 0; i < warmupRounds; i++ {
		measure()
	}

	for sample := 1; sample <= samples; sample++ {
		elapsed := measure()

		timePerOperation := float64(elapsed) / float64(operations)
		throughput := float64(operations) * 1_000_000_000 / float64(elapsed)

		record := []string{
			strconv.FormatInt(time.Now().Unix(), 10),
			"gnark-crypto",
			"0.20.1",
			"Goldilocks",
			goldilocks.Modulus().String(),
			name,
			strconv.Itoa(sample),
			strconv.Itoa(operations),
			strconv.FormatInt(elapsed, 10),
			strconv.FormatFloat(timePerOperation, 'f', 6, 64),
			strconv.FormatFloat(throughput, 'f', 6, 64),
			strconv.Itoa(warmupRounds),
			strconv.FormatUint(exponent, 10),
			strconv.FormatUint(seed, 10),
			"release",
		}

		if err := writer.Write(record); err != nil {
			return err
		}

		if sample%10 == 0 {
			fmt.Printf("  %s: %d/%d samples completed\n",
				name, sample, samples)
		}
	}

	writer.Flush()
	if err := writer.Error(); err != nil {
		return err
	}

	fmt.Printf("Completed %s for %s.\n", name, runID)
	return nil
}
func main() {
	runID := "RECON_RUN1"
	if len(os.Args) > 1 {
		runID = os.Args[1]
	}

	filename := fmt.Sprintf(
		"../../data/reconstructed/gnark_crypto_goldilocks_math_operations_%s.csv",
		runID,
	)

	fmt.Println("gnark-crypto Goldilocks arithmetic benchmark")
	fmt.Println("Run ID:", runID)
	fmt.Println("Operations per sample:", operations)
	fmt.Println("Warmup rounds:", warmupRounds)
	fmt.Println("Samples per operation:", samples)
	fmt.Println("Goldilocks modulus:", goldilocks.Modulus())

	a, b := generateInputs()
	output := make([]goldilocks.Element, operations)

	exponentBig := new(big.Int).SetUint64(exponent)
	validateArithmetic(a, b, exponentBig)

	if err := os.MkdirAll("../../data/reconstructed", 0755); err != nil {
		panic(err)
	}

	file, err := os.Create(filename)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)

	header := []string{
		"timestamp_unix",
		"library",
		"library_version",
		"field",
		"field_modulus",
		"operation",
		"sample",
		"operations",
		"total_time_ns",
		"time_per_operation_ns",
		"throughput_operations_per_second",
		"warmup_rounds",
		"exponent",
		"seed",
		"build_mode",
	}

	if err := writer.Write(header); err != nil {
		panic(err)
	}

	benchmarks := []struct {
		name    string
		measure func() int64
	}{
		{
			"addition",
			func() int64 {
				return measureAddition(a, b, output)
			},
		},
		{
			"subtraction",
			func() int64 {
				return measureSubtraction(a, b, output)
			},
		},
		{
			"multiplication",
			func() int64 {
				return measureMultiplication(a, b, output)
			},
		},
		{
			"exponentiation",
			func() int64 {
				return measureExponentiation(a, output, exponentBig)
			},
		},
		{
			"inversion",
			func() int64 {
				return measureInversion(a, output)
			},
		},
	}

	for _, benchmark := range benchmarks {
		if err := benchmarkOperation(
			writer,
			benchmark.name,
			benchmark.measure,
			runID,
		); err != nil {
			panic(err)
		}
	}

	writer.Flush()
	if err := writer.Error(); err != nil {
		panic(err)
	}

	fmt.Println("\nBenchmark completed.")
	fmt.Println("CSV saved to:", filename)
}
