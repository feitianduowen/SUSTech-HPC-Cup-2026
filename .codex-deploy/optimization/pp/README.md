# PP tinyBLAS experiment patches

Based on the original `ggml/src/ggml-cpu/llamafile/sgemm.cpp` supplied from the validated Intel Classic build. All three patches are independent and target that original file. They do not depend on each other. Do not apply both reuse variants together.

## 1. Shape diagnostics

`tinyblas-diagnostic.patch` adds diagnostics only to the AVX2/F16C `gemm4xN<RN>` path. It does not cover `gemmMx4`, generic `gemm`, Q5_1 dot, or repacked Q4_K kernels.

Enable the separate diagnostic build with both a compiler macro and an environment variable:

```sh
# Append to the existing validated Intel CXX flags; retain all original flags.
cmake -S "$DIAG_SOURCE" -B "$DIAG_BUILD" \
  -DCMAKE_CXX_FLAGS="$VALIDATED_CXX_FLAGS -DGGML_CPU_SHAPE_STATS" \
  <the remaining validated CMake arguments>
cmake --build "$DIAG_BUILD" --target llama-bench -j 38

GGML_TINYBLAS_DIAG="$OUT/pp-tinyblas-shapes.csv" \
  "$DIAG_BUILD/bin/llama-bench" -m "$MODEL" -t 38 -ngl 0 \
  -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute \
  -r 10 -p 2048 -n 0 -o json > "$OUT/pp-diagnostic.json"
```

The CMake snippet is illustrative: replace the angle-bracket placeholder with the original build arguments. Do not change the validated compiler, FP flags, ISA, workloads, or 38-thread setting. Use an absolute, writable, unique CSV path for each process. `GGML_TINYBLAS_DIAG=0`, an empty value, or an unset variable disables recording. A build without `GGML_CPU_SHAPE_STATS` contains no additional branch, static initialization, environment lookup, mutex, or collector object.

Only thread `ith == 0` records each kernel invocation. A single shared mutex protects a map aggregated across quantization types and caller threads. The key is `(a_type, k_blocks, m0, m, n0, n, tile_n, nth)`. The B type is Q8_0 for the existing callers. `k_blocks` counts 32-element quantization blocks. `m` and `n` are end bounds; matrix extents are `m-m0` and `n-n0`. Current tile height stays 4; tile width is the existing RN.

The existing deterministic contiguous tile schedule gives exact active/idle thread counts and min/max tiles per active thread without synchronizing all 38 workers. The CSV includes counts, not wall times. It includes warmup and all measured iterations executed by that process. It cannot by itself assign barrier time or prove an imbalance bottleneck. Prioritize shapes by `calls * tiles_per_call * k_blocks * 4 * tile_n` as a work proxy, then correlate with actual hotspot samples.

CSV output occurs at normal process exit. A killed or crashed process may not write it. Output failures are reported to stderr; benchmark stdout remains JSON. This is a diagnostic binary: its measurements must not be used as the official performance result.

## 2. Arithmetic-preserving reuse candidates

`tinyblas-reuse-b.patch` names the B quantized-vector load once per `(l,j)`, reusing the exact same vector for the four output accumulators. The existing code spells that same load four times. No address, loop, tile, dot-product operand, scale product, reduction, or accumulator order changes.

`tinyblas-reuse-b-abs.patch` also moves the four `_mm256_sign_epi8(avecI, avecI)` expressions outside the RN loop. Each is a pure integer operation on an unchanged A vector; the result is reused across j. The B sign operation still executes separately for every A row because it depends on that row's signs. The B scale (`db`) and combined A/B scale (`dvec`) were already calculated once per `(l,j)` and are unchanged. Signed-byte -128 behavior remains exactly the original intrinsic behavior.

Every accumulator still sees the same sequence of `madd(scale, updot(...), Cv[j][i])` operations for increasing l. No additional accumulators, reassociation, FP reduction changes, or multiply/FMA substitutions are introduced.

Intel Classic at O3 may already common-subexpression-eliminate all of this. Explicit reuse can therefore generate identical assembly and zero gain. Hoisting A absolutes also extends four vector live ranges; register pressure can offset a saved operation or create spills, particularly on a 16-register AVX2 target. The validated AVX512 target has 32 vector registers, but assembly and measured results still decide. Compare disassembly for the Q8_0 `gemm4xN<4>` specialization before spending full benchmark time on a variant with identical instructions.

Acceptance requires the same Intel compiler and flags, unchanged official workload parameters, the complete fixed PPL check, PP/TG 10-repeat results, and no diagnostic macro/environment instrumentation in the scored build. Keep a candidate only if the required correctness check passes and a measured gain survives the observed variation. No speedup is claimed by these source edits alone.

## 3. Deliberately deferred

`ggml_vec_dot_q5_1_q8_1` has one ordered FMA accumulator and a separate ordered scalar minimum-term sum. Splitting either into multiple accumulators changes the arithmetic order; this patch set does not do so. The AVX2 Q4_K repack functions are a different kernel family. No evidence here identifies a safe, useful change to those kernels, so no speculative patch is supplied.

## Self-review

- Scope: CPU-only, private experiment; one diagnostic patch and two alternative single-purpose reuse candidates. No public API, model format, or backend dispatch changes.
- Security: no input indexing or memory access additions in the reuse candidates; diagnostics access only a fixed-size key and fixed internal type IDs. The sole output filename is explicitly supplied by the process environment. Map/string own their storage.
- General/backend: added code/comments are ASCII; no third-party dependencies; ordinary builds compile diagnostics out; diagnostic code must not enter the scored build.
- Approach: deterministic scheduling statistics avoid per-worker atomics and timing calls. Shared state prevents type-specific destructors from overwriting the same output file.
- Validation still required remotely: Intel compilation, disassembly comparison, full fixed PPL, and the official fixed PP/TG workload. Local review is not an accuracy or speed certification.
