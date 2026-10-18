# GGML node diagnostics

This is an independent diagnostic patch for the validated private competition source. It changes only `ggml/src/ggml-cpu/ggml-cpu.c`; it does not change an operator, its task count, fusion choice, or an existing barrier. Do not include it in a performance submission build.

Apply from the llama.cpp source root:

```sh
git apply --check /path/to/node-stats.patch
git apply /path/to/node-stats.patch
```

Use a separate build directory with the same validated Intel Classic configuration and append `-DGGML_CPU_NODE_STATS` to **C flags**. No C++ flag is necessary. It is active only with all of `GGML_CPU_NODE_STATS`, `GGML_USE_OPENMP`, and `__linux__`. Without the diagnostic flag, every added declaration and runtime statement is preprocessed away. The non-OpenMP implementation is unchanged even if the flag is set.

Example environment (the parent output directory must already exist):

```sh
export GGML_NODE_STATS_PREFIX=/work/apac2602/qwen38-cpu/optimization/node_stats/pp
export GGML_NODE_STATS_SKIP=0
export GGML_NODE_STATS_GRAPHS=4
```

The prefix must be absolute, at most 3000 bytes, and contain only ASCII letters, digits, `/`, `_`, `-`, and `.`. A trailing slash or a `..` path component is rejected. Files use exclusive creation: `pp.g000000.csv`, etc. Existing files are not overwritten, including existing symlinks at the result filename. Parent directory symlinks are not resolved or rejected; use the account's controlled result directory.

`GGML_NODE_STATS_SKIP` defaults to 0, accepts 0..1000000. `GGML_NODE_STATS_GRAPHS` defaults to 4, accepts 0..64 (0 disables collection). Invalid values disable collection with a warning. Unset `GGML_NODE_STATS_PREFIX` causes no sample allocation, file output, or per-node clock reads. The diagnostic-only stack initialization and pointer checks still exist; use a build without the flag for timing/PPL evidence.

Graph selection counts **all calls to CPU `ggml_graph_compute` with a valid prefix**, including model initialization, warmup, prefill/depth, decode, and backend splits. There is one process-wide counter protected by an OpenMP critical section. File graph IDs and graph tensor shapes identify the actual phase. Do not assume the first four graphs are exactly four PP microbatches until checking shapes. For TG, first determine the warmup/depth count from a diagnostic run, then set `GGML_NODE_STATS_SKIP` to that count and `GGML_NODE_STATS_GRAPHS=1`. Do not change benchmark workload arguments to force a phase.

Allocation is outside the worker parallel region, with checked node/thread multiplication and a 128 MiB cap per graph. Each worker writes only its own cache-line-sized slot. There is no worker-side logging and no new barrier. CSV output and free happen after OpenMP workers join; the sample pointer is cleared before freeing. The original threadpool's restriction against simultaneous graph execution on the same pool remains. Different pools receive distinct graph IDs.

Each CSV row describes one executed graph node, including the fused operation group beginning at that node. `node_end` is the inclusive final fused node index. Skipped NOP/non-compute nodes and nodes consumed by a fusion have no separate row. Shapes are four-dimensional numeric strings such as `4096x512x1x1`; `src_shapes` lists each non-null source as `source_index:shape;`.

Columns:

| Column | Meaning |
| --- | --- |
| graph, node, node_end, op | Process graph ID, graph node range, leading GGML op |
| n_tasks_nominal | `ggml_get_n_tasks(leading_node, actual_pool_threads)`; planning result, **not** a changed runtime task count |
| pool_threads | Actual `params.nth` supplied to the operation, after OpenMP team-size adjustment |
| recorded_threads | Number of workers with a populated record; should equal pool_threads |
| dst_shape, src_shapes | Tensor dimensions; no tensor content or names are logged |
| compute_min_us, compute_max_us, compute_sum_us | Min/max/sum of worker end minus start |
| boundary_wait_sum_us | Sum of worker boundary-barrier exit minus entry |
| arrival_spread_us | Latest minus earliest arrival at the boundary barrier |
| has_boundary_barrier | Whether the original per-node boundary barrier exists; false for the final node |
| start_us, end_us, barrier_enter_us, barrier_exit_us | Quoted semicolon vectors, indexed by worker ID, relative to graph diagnostic start; zero for missing workers |

`compute` includes fused operators and any **internal operator barriers**, so it is not pure arithmetic time. Boundary wait measures only the existing barrier between graph nodes. The final graph-wide barrier is preserved but excluded from these rows; the final node has exit equal to entry and zero boundary wait. The thread-zero abort callback occurs between compute end and barrier entry. Arrival spread can expose imbalance but cannot distinguish arithmetic imbalance from OS preemption or internal synchronization. Microsecond timestamps perturb small nodes and have microsecond resolution. These logs diagnose scheduling; do not use their throughput as a formal score.

Local validation: `python check_node_stats.py` checks that removing all diagnostic blocks restores the original source token stream, existing barrier counts are unchanged, additions are ASCII, and a C11 helper harness compiles and passes path/limit/CSV aggregation checks. Full Intel source compilation and real-model execution are required on the cluster; the local helper harness is not a replacement for them.
