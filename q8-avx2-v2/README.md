# Q8_0 AVX2 V2 source experiments

Base commit: d81235049384534c167caea52b85a694f6103d14. Intel Classic 2021.9, precise/no-ftz, CORE-AVX512. Old source and AVX512 V1 are preserved.

## Layout

- `source/`: independent unmodified official source, all 3687 files SHA256 verified.
- `variants/`: six modified full quants.c files, patches, and the unchanged control.
- `source-schedule4/`, `source-schedule4_prefetch16/`: independent full candidate trees.
- `evidence/`: immutable raw test summaries; main experiment ledger is ../Qwen38_CPU_????.xlsx.

Only ggml/src/ggml-cpu/arch/x86/quants.c changes. The ordered eight-lane FMA accumulator, tail, ABI and other architecture paths are preserved. Prefetch targets stay inside the input.

## Screening job 4336888

Gold6148 r13n19, 40 allocated slots. Configurations run sequentially. Each configuration passed 204154 bitwise cases against the production library, including 66 guard-page cases, all 65536 int8 pairs under three scale patterns, and 760 concurrent cases with 38 threads. Each shape/mode has ten alternating AB/BA pairs pinned to CPU0, memory node0, with a resident row or 256MiB weight stream.

The excerpt uses the actual production FP16 table. The unchanged control nevertheless differs substantially in resident timing, so all excerpt speedups are screening evidence only. Full library paired tests are required. These are not fixed model PP/TG measurements and have no PPL or Score.

| Variant | nb80 resident | nb80 stream | nb192 resident | nb192 stream |
|---|---:|---:|---:|---:|
| control | +25.85% | +1.44% | +31.50% | +1.55% |
| prefetch16 | +16.88% | +15.49% | +16.66% | +18.17% |
| prefetch32 | -1.78% | -3.00% | -11.52% | -0.10% |
| prefetch8 | -9.83% | -2.30% | -13.46% | -4.10% |
| schedule4 | +36.09% | +11.64% | +37.91% | +10.59% |
| schedule4_prefetch16 | +31.71% | +18.27% | +33.90% | +23.76% |
| schedule4_prefetch16_t1 | +12.32% | +14.17% | +7.81% | +14.52% |

Full-library build/differential/PPL jobs: schedule4 4336892; schedule4_prefetch16 4336891. Do not promote based on the screening numbers.

## Full library checks

| Variant | Job / host | nb80 resident | nb80 stream | nb192 resident | nb192 stream |
|---|---|---:|---:|---:|---:|
| schedule4 | 4336892 / r13n33 | +33.60% | +12.49% | +37.94% | +11.05% |
| schedule4_prefetch16 | 4336891 / r13n22 | +32.33% | +18.28% | +35.52% | +23.38% |

Both actual libraries passed 204154 bitwise cases and the full quantization unit test. All four targets and dependencies built successfully with Intel. Library microbench CVs are below 0.7%. Gains are relative to the original library on each job host; candidate absolute times across hosts are not compared. Fixed model PPL completed: both 2.7767 PASS versus official 2.7696 (+0.2563547083%), with identical conditions; elapsed 316s for schedule4 and 318s for schedule4_prefetch16. Full model PP/TG remains unconfirmed.

## Full model paired jobs

4337011: schedule4 versus production on r13n33. 4337012: schedule4_prefetch16 versus production on r13n38. Both started at 2026-10-19 14:34 Hong Kong time. Order: baseline PP, candidate PP, candidate TG, baseline TG. All workloads retain fixed ten repetitions and original parameters. Each binary reuses its independent fixed PPL pass, verified by fingerprints; no PPL rerun in these performance jobs. Results pending; no model gain or score claimed.

## Forward model results and decision

Both jobs completed with all ten samples per workload. For schedule4 (4337011), baseline PP/TG = 28.023191/2.866171 and candidate = 50.748614/2.796380 tokens/s. For schedule4_prefetch16 (4337012), baseline = 27.472820/3.037347 and candidate = 53.802074/3.044166. The baseline PP CVs are about 9.0% and 10.1%; schedule4 candidate TG CV is 19.4%, including late slow samples which are retained. Development scores are in the ledger and are not official results.

The large PP difference cannot yet be attributed to source changes, because baseline PP executes first and is unusually slow. TG changes are -2.43% and +0.22%, providing no stable TG gain. Preserve both candidates without replacing production. Reverse order jobs 4337219 (schedule4, r13n38) and 4337220 (schedule4_prefetch16, r13n06) run candidate PP, baseline PP, baseline TG, candidate TG; each remains a fixed ten-sample workload with verified reused per-binary PPL. Across-job node/cache differences remain a limitation. Raw forward data are in evidence/forward-evidence.tar.gz and evidence/forward-analysis.json.
