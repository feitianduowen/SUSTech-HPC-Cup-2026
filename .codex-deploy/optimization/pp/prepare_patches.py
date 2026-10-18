from pathlib import Path
import difflib

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / "profiling" / "source" / "sgemm.cpp"
original = SOURCE.read_text(encoding="utf-8")

helper = r'''#if defined(GGML_CPU_SHAPE_STATS) && defined(__AVX2__) && defined(__F16C__)
struct tinyblas_shape_stats {
    std::mutex mutex;
    std::map<std::array<int64_t, 8>, uint64_t> calls;
    std::string path;

    tinyblas_shape_stats() {
        const char * value = std::getenv("GGML_TINYBLAS_DIAG");
        if (value != nullptr && value[0] != '\0' && std::strcmp(value, "0") != 0) {
            path = value;
        }
    }

    void record(const std::array<int64_t, 8> & key) {
        if (path.empty()) {
            return;
        }
        std::lock_guard<std::mutex> lock(mutex);
        ++calls[key];
    }

    ~tinyblas_shape_stats() {
        if (path.empty()) {
            return;
        }
        FILE * file = std::fopen(path.c_str(), "w");
        if (file == nullptr) {
            std::fprintf(stderr, "tinyBLAS: cannot write shape stats to %s\n", path.c_str());
            return;
        }
        const char * types[] = { "q8_0", "q4_0", "q5_0", "iq4_nl" };
        std::fprintf(file, "a_type,k_blocks,m0,m,n0,n,tile_m,tile_n,nth,calls,xtiles,ytiles,tiles_per_call,total_tiles,active_threads,idle_threads,min_active_tiles,max_active_tiles,idle_thread_calls\n");
        for (const auto & entry : calls) {
            const auto & key = entry.first;
            const int64_t xtiles = (key[5] - key[4]) / key[6];
            const int64_t ytiles = (key[3] - key[2]) / 4;
            const int64_t tiles = xtiles * ytiles;
            const int64_t duty = (tiles + key[7] - 1) / key[7];
            const int64_t active = duty == 0 ? 0 : (tiles + duty - 1) / duty;
            const int64_t minimum = active == 0 ? 0 : tiles - (active - 1) * duty;
            std::fprintf(file, "%s,%lld,%lld,%lld,%lld,%lld,4,%lld,%lld,%llu,%lld,%lld,%lld,%llu,%lld,%lld,%lld,%lld,%llu\n",
                types[key[0]], (long long) key[1], (long long) key[2], (long long) key[3],
                (long long) key[4], (long long) key[5], (long long) key[6], (long long) key[7],
                (unsigned long long) entry.second, (long long) xtiles, (long long) ytiles,
                (long long) tiles, (unsigned long long) (entry.second * tiles),
                (long long) active, (long long) (key[7] - active), (long long) minimum,
                (long long) duty, (unsigned long long) (entry.second * (key[7] - active)));
        }
        std::fclose(file);
    }
};

inline tinyblas_shape_stats & tinyblas_get_shape_stats() {
    static tinyblas_shape_stats stats;
    return stats;
}

template <typename TA>
void tinyblas_record_shape(int64_t k, int64_t m0, int64_t m, int64_t n0, int64_t n, int rn, int nth) {
    const int64_t type = std::is_same<TA, block_q8_0>::value ? 0 :
                         std::is_same<TA, block_q4_0>::value ? 1 :
                         std::is_same<TA, block_q5_0>::value ? 2 : 3;
    tinyblas_get_shape_stats().record({ type, k, m0, m, n0, n, rn, nth });
}
#endif
'''

diagnostic = original.replace("#include <type_traits>\n", "#include <type_traits>\n\n#if defined(GGML_CPU_SHAPE_STATS)\n#include <cstdio>\n#include <cstdlib>\n#include <cstring>\n#include <map>\n#include <mutex>\n#include <string>\n#endif\n", 1)
diagnostic = diagnostic.replace("inline float unhalf(ggml_fp16_t d) {", helper + "\ninline float unhalf(ggml_fp16_t d) {", 1)
signature = "    NOINLINE void gemm4xN(int64_t m0, int64_t m, int64_t n0, int64_t n) {\n"
diagnostic = diagnostic.replace(signature, signature + "#if defined(GGML_CPU_SHAPE_STATS)\n        if (ith == 0) {\n            tinyblas_record_shape<TA>(k, m0, m, n0, n, RN, nth);\n        }\n#endif\n", 1)

begin = original.index(signature)
end = original.index("    // Templated functions for gemm of dimensions Mx4", begin)
kernel = original[begin:end]
load_b = "load(B + ldb * (jj + j) + l)"
kernel_b = kernel.replace("                        __m128 db =", "                        const __m256i bvec = " + load_b + ";\n                        __m128 db =", 1)
# Keep the newly added load; replace only its four consumers.
position = kernel_b.index("                        __m128 db =")
kernel_b = kernel_b[:position] + kernel_b[position:].replace(load_b, "bvec")
assert kernel_b.count(load_b) == 1
assert kernel.count(load_b) == 4
reuse_b = original[:begin] + kernel_b + original[end:]

abs_lines = "".join(f"                const __m256i a_abs{i} = _mm256_sign_epi8(avec{i}, avec{i});\n" for i in range(4))
kernel_abs = kernel_b.replace("                for (int64_t j = 0; j < RN; ++j) {", abs_lines + "                for (int64_t j = 0; j < RN; ++j) {", 1)
for i in range(4):
    # Restrict replacement to accumulator expressions, preserving declarations.
    kernel_abs = kernel_abs.replace(f"updot(_mm256_sign_epi8(avec{i}, avec{i}),", f"updot(a_abs{i},")
reuse_abs = original[:begin] + kernel_abs + original[end:]

path = "ggml/src/ggml-cpu/llamafile/sgemm.cpp"
for name, updated in (("tinyblas-diagnostic", diagnostic), ("tinyblas-reuse-b", reuse_b), ("tinyblas-reuse-b-abs", reuse_abs)):
    (ROOT / (name + ".cpp")).write_text(updated, encoding="utf-8", newline="\n")
    patch = "".join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True), fromfile="a/" + path, tofile="b/" + path))
    (ROOT / (name + ".patch")).write_text(patch, encoding="utf-8", newline="\n")
    print(name, len(patch.splitlines()))
