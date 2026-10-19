import difflib
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
reference = root/'reference/quants.c'
original = reference.read_text(encoding='utf-8')
begin = original.index('void ggml_vec_dot_q8_0_q8_0(')
end = original.index('\nvoid ggml_vec_dot_tq1_0_q8_K(',begin)
function = original[begin:end]
anchor = '    // Main loop\n'
assert function.count(anchor) == 1
pair_loop = '''#if defined(__AVX512F__) && defined(__AVX512BW__) && !defined(__AVX512VNNI__) && !defined(__AVXVNNI__) && !defined(__AVXVNNIINT8__)
    const __m512i zero = _mm512_setzero_si512();
    const __m512i ones = _mm512_set1_epi16(1);

    for (; ib + 1 < nb; ib += 2) {
        __m512i qx = _mm512_castsi256_si512(_mm256_loadu_si256((const __m256i *) x[ib].qs));
        __m512i qy = _mm512_castsi256_si512(_mm256_loadu_si256((const __m256i *) y[ib].qs));
        qx = _mm512_inserti64x4(qx, _mm256_loadu_si256((const __m256i *) x[ib + 1].qs), 1);
        qy = _mm512_inserti64x4(qy, _mm256_loadu_si256((const __m256i *) y[ib + 1].qs), 1);

        const __m512i ax = _mm512_abs_epi8(qx);
        // Zero x lanes have zero products, so only negative x lanes need a sign change.
        const __m512i sy = _mm512_mask_sub_epi8(qy, _mm512_movepi8_mask(qx), zero, qy);
        const __m512i pairs = _mm512_maddubs_epi16(ax, sy);
        const __m512i sums = _mm512_madd_epi16(pairs, ones);
        const __m256 q0 = _mm256_cvtepi32_ps(_mm512_castsi512_si256(sums));
        const __m256 q1 = _mm256_cvtepi32_ps(_mm512_extracti64x4_epi64(sums, 1));
        const __m256 d0 = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[ib].d) * GGML_CPU_FP16_TO_FP32(y[ib].d));
        const __m256 d1 = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[ib + 1].d) * GGML_CPU_FP16_TO_FP32(y[ib + 1].d));

        // Keep the AVX2 block order and eight-lane floating-point accumulator.
        acc = _mm256_fmadd_ps(d0, q0, acc);
        acc = _mm256_fmadd_ps(d1, q1, acc);
    }
#endif

'''
modified_function = function.replace(anchor,pair_loop+anchor)
modified = original[:begin]+modified_function+original[end:]
relative = 'ggml/src/ggml-cpu/arch/x86/quants.c'
patch = ''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
(root/'q8-avx512-ordered.patch').write_bytes(patch.encode())
(root/'quants.modified.c').write_bytes(modified.encode())

# Compile the exact candidate function with the existing microbenchmark infrastructure.
helpers = ''
for name in ['hsum_float_8','sum_i16_pairs_float','mul_sum_us8_pairs_float','mul_sum_i8_pairs_float']:
    position = original.index(name+'(')
    left = original.rfind('static inline ',0,position)
    right = original.index('{',position)
    depth = 1
    right += 1
    while depth:
        depth += (original[right]=='{')-(original[right]=='}')
        right += 1
    helpers += original[left:right]+'\n'
prefix = '''#include <immintrin.h>
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#define QK8_0 32
#define GGML_RESTRICT restrict
#define UNUSED(x) ((void) (x))
#define GGML_CPU_FP16_TO_FP32(x) _cvtsh_ss(x)
typedef struct { uint16_t d; int8_t qs[QK8_0]; } block_q8_0;
_Static_assert(sizeof(block_q8_0) == 34, "Q8_0 block layout");
'''
baseline = function.replace('void ggml_vec_dot_q8_0_q8_0(', '__attribute__((noinline)) void q8_reference(')
candidate = modified_function.replace('void ggml_vec_dot_q8_0_q8_0(', '__attribute__((noinline)) void q8_candidate(')
(root/'q8-candidate-kernels.c').write_bytes((prefix+helpers+baseline+'\n'+candidate).encode())
(root/'patch_manifest.json').write_bytes(json.dumps({'base_commit':'d81235049384534c167caea52b85a694f6103d14','file':relative,'original_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'modified_sha256':hashlib.sha256(modified.encode()).hexdigest(),'patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),'scope':'Q8_0 two-block AVX-512BW integer path, ordered eight-lane AVX2 floating accumulation; odd block and non-AVX512/VNNI paths retained'},indent=2).encode())
print(root/'q8-avx512-ordered.patch')
