
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
struct ggml_cpu_node_sample {
    int64_t start;
    int64_t end;
    int64_t enter;
    int64_t exit;
    int n_fused;
    int nth;
    char padding[GGML_CACHE_LINE - 4*sizeof(int64_t) - 2*sizeof(int)];
};

struct ggml_cpu_node_stats {
    struct ggml_cpu_node_sample * samples;
    FILE * file;
    size_t size;
    int n_threads;
    int graph;
    int64_t base;
};static int ggml_cpu_node_stats_int(const char * name, int fallback, int maximum) {
    const char * value = getenv(name);
    if (value == NULL) {
        return fallback;
    }
    if (*value == '\0') {
        return -1;
    }
    int result = 0;
    for (const char * p = value; *p; ++p) {
        if (*p < '0' || *p > '9' || result > (maximum - (*p - '0'))/10) {
            return -1;
        }
        result = result*10 + (*p - '0');
    }
    return result <= maximum ? result : -1;
}

static bool ggml_cpu_node_stats_prefix(const char * prefix) {
    if (prefix == NULL || prefix[0] != '/' || strlen(prefix) > 3000) {
        return false;
    }
    // Restrict this diagnostic output to an explicit absolute, traversal-free prefix.
    for (const char * p = prefix; *p; ++p) {
        const char c = *p;
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '/' || c == '_' || c == '-' || c == '.')) {
            return false;
        }
        if ((p == prefix || p[-1] == '/') && c == '.' && p[1] == '.' &&
                (p[2] == '/' || p[2] == '\0')) {
            return false;
        }
    }
    return prefix[strlen(prefix) - 1] != '/';
}

static void ggml_cpu_node_stats_begin(struct ggml_cpu_node_stats * stats,
                                    const struct ggml_cgraph * graph, int n_threads) {
    memset(stats, 0, sizeof(*stats));
    const char * prefix = getenv("GGML_NODE_STATS_PREFIX");
    if (prefix == NULL) {
        return;
    }
    const int skip = ggml_cpu_node_stats_int("GGML_NODE_STATS_SKIP", 0, 1000000);
    const int count = ggml_cpu_node_stats_int("GGML_NODE_STATS_GRAPHS", 4, 64);
    if (!ggml_cpu_node_stats_prefix(prefix) || skip < 0 || count < 0) {
        GGML_LOG_WARN("node stats: invalid output prefix or sample limits\n");
        return;
    }
    static int next_graph = 0;
    int graph_id;
    #pragma omp critical (ggml_cpu_node_stats_sequence)
    {
        graph_id = next_graph;
        if (next_graph < INT_MAX) {
            ++next_graph;
        }
    }
    if (graph_id < skip || graph_id - skip >= count) {
        return;
    }
    if (graph->n_nodes <= 0 || n_threads <= 0 || n_threads > GGML_MAX_N_THREADS ||
            (size_t) graph->n_nodes > SIZE_MAX/(size_t) n_threads/sizeof(*stats->samples)) {
        GGML_LOG_WARN("node stats: invalid graph allocation dimensions\n");
        return;
    }
    const size_t size = (size_t) graph->n_nodes*(size_t) n_threads*sizeof(*stats->samples);
    if (size > 128U*1024U*1024U) {
        GGML_LOG_WARN("node stats: graph sample exceeds 128 MiB limit\n");
        return;
    }
    char path[3072];
    const int length = snprintf(path, sizeof(path), "%s.g%06d.csv", prefix, graph_id);
    if (length < 0 || (size_t) length >= sizeof(path)) {
        return;
    }
    // Exclusive creation avoids overwriting an existing result or following its symlink.
    FILE * file = fopen(path, "wx");
    if (file == NULL) {
        GGML_LOG_WARN("node stats: cannot create %s: %s\n", path, strerror(errno));
        return;
    }
    struct ggml_cpu_node_sample * samples = ggml_aligned_malloc(size);
    if (samples == NULL) {
        fclose(file);
        GGML_LOG_WARN("node stats: sample allocation failed\n");
        return;
    }
    memset(samples, 0, size);
    stats->samples = samples;
    stats->file = file;
    stats->size = size;
    stats->n_threads = n_threads;
    stats->graph = graph_id;
    stats->base = ggml_time_us();
}

static void ggml_cpu_node_stats_shape(FILE * file, const struct ggml_tensor * tensor) {
    for (int dim = 0; dim < GGML_MAX_DIMS; ++dim) {
        fprintf(file, "%s%" PRId64, dim ? "x" : "", tensor->ne[dim]);
    }
}

static void ggml_cpu_node_stats_end(struct ggml_cpu_node_stats * stats, const struct ggml_cgraph * graph) {
    if (stats->samples == NULL) {
        return;
    }
    FILE * file = stats->file;
    fprintf(file, "graph,node,node_end,op,n_tasks_nominal,pool_threads,recorded_threads,dst_shape,src_shapes,compute_min_us,compute_max_us,compute_sum_us,boundary_wait_sum_us,arrival_spread_us,has_boundary_barrier,start_us,end_us,barrier_enter_us,barrier_exit_us\n");
    for (int node_n = 0; node_n < graph->n_nodes; ++node_n) {
        const struct ggml_cpu_node_sample * row = stats->samples + (size_t) node_n*stats->n_threads;
        int n_recorded = 0;
        int nth = 0;
        int n_fused = 0;
        int64_t min_compute = INT64_MAX, max_compute = 0, sum_compute = 0, sum_wait = 0;
        int64_t min_enter = INT64_MAX, max_enter = 0;
        for (int ith = 0; ith < stats->n_threads; ++ith) {
            if (row[ith].start == 0) {
                continue;
            }
            ++n_recorded;
            nth = row[ith].nth;
            n_fused = row[ith].n_fused;
            const int64_t compute = row[ith].end - row[ith].start;
            min_compute = MIN(min_compute, compute);
            max_compute = MAX(max_compute, compute);
            sum_compute += compute;
            sum_wait += row[ith].exit - row[ith].enter;
            min_enter = MIN(min_enter, row[ith].enter);
            max_enter = MAX(max_enter, row[ith].enter);
        }
        if (n_recorded == 0) {
            continue;
        }
        const struct ggml_tensor * node = graph->nodes[node_n];
        fprintf(file, "%d,%d,%d,%s,%d,%d,%d,\"", stats->graph, node_n, node_n + n_fused,
                ggml_op_name(node->op), ggml_get_n_tasks(graph->nodes[node_n], nth), nth, n_recorded);
        ggml_cpu_node_stats_shape(file, node);
        fprintf(file, "\",\"");
        for (int src = 0; src < GGML_MAX_SRC; ++src) {
            if (node->src[src] != NULL) {
                fprintf(file, "%d:", src);
                ggml_cpu_node_stats_shape(file, node->src[src]);
                fprintf(file, ";");
            }
        }
        fprintf(file, "\",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%d",
                min_compute, max_compute, sum_compute, sum_wait, max_enter - min_enter,
                node_n + n_fused + 1 < graph->n_nodes);
        for (int metric = 0; metric < 4; ++metric) {
            fprintf(file, ",\"");
            for (int ith = 0; ith < stats->n_threads; ++ith) {
                int64_t value = 0;
                if (row[ith].start != 0) {
                    switch (metric) {
                        case 0: value = row[ith].start; break;
                        case 1: value = row[ith].end; break;
                        case 2: value = row[ith].enter; break;
                        case 3: value = row[ith].exit; break;
                    }
                    value -= stats->base;
                }
                fprintf(file, "%s%" PRId64, ith ? ";" : "", value);
            }
            fprintf(file, "\"");
        }
        fprintf(file, "\n");
    }
    if (ferror(file)) {
        GGML_LOG_WARN("node stats: output write failed\n");
    }
    if (fclose(file) != 0) {
        GGML_LOG_WARN("node stats: output close failed\n");
    }
    ggml_aligned_free(stats->samples, stats->size);
    stats->samples = NULL;
}
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
