# GGML PGO V2

Job 4336889 failed at the final instrumented llama-bench link, before training.
Its control PPL passed at 2.7767. The linker reported undefined
`__start___pgoseg_addr` and a missing DSO dependency from libipgo.a.

The previous CMake target-name list missed static helper targets, including
llama-common-base and cpp-httplib. It also only changed compilation, leaving
global PGO driver options enabled for non-GGML links.

New files preserve the old experiment:

- ggml_pgo_targets_v2.cmake recursively visits actual CMake targets. All non-GGML
  compiled targets receive the disabling flag; dynamic targets and executables
  also receive it at link time. GGML remains instrumented/profile-optimized.
- check_pgo_scope_v2.py checks every translation unit and generated link command,
  before building and after building. The plain stage already validates 28 GGML
  and 276 other translation units.
- pipeline_ggml_pgo_v2.lsf uses the new hook and checker in an independent build
  directory. Intel Classic and precise/no-ftz flags, original source, model,
  fixed PPL and future fixed PP/TG remain unchanged.

Retry job 4337216 started on r13n10 at 2026-10-19 15:26 Hong Kong time. Its plain
control build passed and fixed control PPL is running. The repaired gen-stage
link and profile generation are not yet verified. Do not claim PGO success until
training exits normally, counters merge, feedback compilation succeeds, and its
independent fixed PPL passes.

Account job 4337222 is a separately submitted driver-PGO experiment. It was
discovered while monitoring and is retained in the shared ledger; this V2 retry
does not modify its files or cancel it. Preserve both distinct configurations.

Old failed jobs, partial diagnostic profiles and all slow measurements remain.
The shared Excel records each accepted job, its actual configuration and result.
