from pathlib import Path
import re
import subprocess

root = Path(__file__).parent
old = Path('D:/compete/.codex-deploy/profiling/source/ggml-cpu.c').read_text(encoding='utf-8')
new = (root / 'ggml-cpu-node-stats.c').read_text(encoding='utf-8')
# Every inserted block must disappear when the diagnostic macro is absent.
stripped = re.sub(r'#if defined\(GGML_CPU_NODE_STATS\).*?\n#endif\n', '', new, flags=re.S)
stripped = re.sub(r'#ifdef GGML_CPU_NODE_STATS_ENABLED\n.*?\n#endif\n', '', stripped, flags=re.S)
assert stripped.split() == old.split(), 'Non-diagnostic token stream changed'
assert new.count('ggml_barrier(state->threadpool);') == old.count('ggml_barrier(state->threadpool);')
assert new.count('#pragma omp barrier') == old.count('#pragma omp barrier')
assert all(ord(c) < 128 for c in (root / 'node-stats.patch').read_text(encoding='utf-8'))

structs = new.split('#define GGML_CPU_NODE_STATS_ENABLED\n', 1)[1].split('\n#endif', 1)[0]
helpers = new.split('#ifdef GGML_CPU_NODE_STATS_ENABLED\nstatic int ggml_cpu_node_stats_int', 1)[1].split('\n#endif', 1)[0]
helpers = 'static int ggml_cpu_node_stats_int' + helpers
stub = r'''
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include <assert.h>
#define GGML_CACHE_LINE 64
#define GGML_MAX_N_THREADS 512
#define GGML_MAX_DIMS 4
#define GGML_MAX_SRC 3
#define GGML_LOG_WARN(...) fprintf(stderr, __VA_ARGS__)
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
struct ggml_tensor { int64_t ne[4]; struct ggml_tensor * src[3]; int op; };
struct ggml_cgraph { int n_nodes; struct ggml_tensor ** nodes; };
static void * ggml_aligned_malloc(size_t size) { return malloc(size); }
static void ggml_aligned_free(void * p, size_t size) { (void) size; free(p); }
static int64_t ggml_time_us(void) { return 100; }
static int ggml_get_n_tasks(struct ggml_tensor * n, int nth) { (void) n; return nth; }
static const char * ggml_op_name(int op) { (void) op; return "DUP"; }
'''
test = r'''
int main(void) {
    assert(sizeof(struct ggml_cpu_node_sample) == 64);
    assert(ggml_cpu_node_stats_prefix("/tmp/diag/pp"));
    assert(!ggml_cpu_node_stats_prefix("relative"));
    assert(!ggml_cpu_node_stats_prefix("/tmp/../etc/out"));
    assert(!ggml_cpu_node_stats_prefix("/tmp/space name"));
    assert(!ggml_cpu_node_stats_prefix("/tmp/"));
    assert(!ggml_cpu_node_stats_prefix(NULL));
    putenv("NODE_STATS_TEST=64");
    assert(ggml_cpu_node_stats_int("NODE_STATS_TEST", 0, 64) == 64);
    putenv("NODE_STATS_TEST=65");
    assert(ggml_cpu_node_stats_int("NODE_STATS_TEST", 0, 64) == -1);
    putenv("NODE_STATS_TEST=-1");
    assert(ggml_cpu_node_stats_int("NODE_STATS_TEST", 0, 64) == -1);
    putenv("NODE_STATS_TEST=999999999999999999999999");
    assert(ggml_cpu_node_stats_int("NODE_STATS_TEST", 0, 64) == -1);
    putenv("NODE_STATS_TEST=");
    assert(ggml_cpu_node_stats_int("NODE_STATS_TEST", 0, 64) == 0);
    struct ggml_tensor tensor = { .ne = {4, 2, 1, 1} };
    struct ggml_tensor * nodes[] = { &tensor, &tensor };
    struct ggml_cgraph graph = {2, nodes};
    struct ggml_cpu_node_stats stats;
    putenv("GGML_NODE_STATS_PREFIX=");
    ggml_cpu_node_stats_begin(&stats, &graph, 2);
    assert(stats.samples == NULL);
    FILE * out = fopen("node-stats-test.csv", "w");
    assert(out != NULL);
    stats.samples = calloc(4, sizeof(*stats.samples));
    assert(stats.samples != NULL);
    stats.file = out;
    stats.n_threads = 2;
    stats.size = 4*sizeof(*stats.samples);
    stats.graph = 0;
    stats.base = 100;
    for (int i = 0; i < 4; ++i) {
        stats.samples[i].start = 110 + i;
        stats.samples[i].end = 120 + i;
        stats.samples[i].enter = 121 + i;
        stats.samples[i].exit = 125 + i;
        stats.samples[i].nth = 2;
    }
    ggml_cpu_node_stats_end(&stats, &graph);
    assert(stats.samples == NULL);
    puts("node stats helper checks passed");
    return 0;
}
'''
(root / 'node-stats-check.c').write_text(stub + structs + helpers + test, encoding='ascii')
subprocess.run(['D:/mingw64/bin/gcc.exe', '-std=c11', '-Wall', '-Wextra', '-Werror',
    '-Wno-unknown-pragmas', 'node-stats-check.c', '-o', 'node-stats-check.exe'], cwd=root, check=True)
subprocess.run([str(root / 'node-stats-check.exe')], cwd=root, check=True)
import csv
with (root / 'node-stats-test.csv').open() as handle:
    rows = list(csv.DictReader(handle))
assert len(rows) == 2
assert rows[0]['compute_sum_us'] == '20'
assert rows[0]['boundary_wait_sum_us'] == '8'
assert rows[0]['arrival_spread_us'] == '1'
assert rows[0]['start_us'] == '10;11'
assert rows[0]['has_boundary_barrier'] == '1'
assert rows[1]['has_boundary_barrier'] == '0'
print('No diagnostic macro: identical token stream; existing barriers preserved; CSV checks passed')
