import difflib
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
old = root.parent/'source_v2'
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2'
original = (old/'reference/quants.c').read_text(encoding='utf-8')
begin = original.index('void ggml_vec_dot_q8_0_q8_0(')
end = original.index('\nvoid ggml_vec_dot_tq1_0_q8_K(', begin)
function = original[begin:end]
anchor = '    // Main loop\n'
loop_end = function.index('\n    sumf = hsum_float_8(acc);')
loop_start = function.index(anchor)
original_loop = function[loop_start:loop_end]

def scheduled(distance=0, hint='_MM_HINT_T0'):
    lines = ['    // Schedule four blocks ahead while preserving the original FMA order.',
             '    for (; ib + 3 < nb; ib += 4) {']
    if distance:
        lines += ['        if (ib + %d < nb) {' % distance,
                  '            _mm_prefetch((const char *) &x[ib + %d], %s);' % (distance,hint),
                  '        }']
    for i in range(4):
        lines += ['        const __m256i x%d = _mm256_loadu_si256((const __m256i *) x[ib + %d].qs);' % (i,i),
                  '        const __m256i y%d = _mm256_loadu_si256((const __m256i *) y[ib + %d].qs);' % (i,i)]
    for i in range(4):
        lines += ['        const __m256 q%d = mul_sum_i8_pairs_float(x%d, y%d);' % (i,i,i),
                  '        const __m256 d%d = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[ib + %d].d) * GGML_CPU_FP16_TO_FP32(y[ib + %d].d));' % (i,i,i)]
    for i in range(4):
        lines += ['        acc = _mm256_fmadd_ps(d%d, q%d, acc);' % (i,i)]
    lines += ['    }', '', original_loop]
    return '\n'.join(lines)

variants = {'control': original_loop, 'schedule4': scheduled()}
for distance in [8,16,32]:
    variants['prefetch%d' % distance] = original_loop.replace('        // Compute combined scale for the block',
        '        if (ib + %d < nb) {\n            _mm_prefetch((const char *) &x[ib + %d], _MM_HINT_T0);\n        }\n        // Compute combined scale for the block' % (distance,distance))
variants['schedule4_prefetch16'] = scheduled(16)
variants['schedule4_prefetch16_t1'] = scheduled(16,'_MM_HINT_T1')

helpers = ''
for name in ['hsum_float_8','sum_i16_pairs_float','mul_sum_us8_pairs_float','mul_sum_i8_pairs_float']:
    position = original.index(name+'(')
    left = original.rfind('static inline ',0,position)
    right = original.index('{',position)+1
    depth = 1
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
static float * q8_table;
#define GGML_CPU_FP16_TO_FP32(x) q8_table[(uint16_t) (x)]
typedef struct { uint16_t d; int8_t qs[QK8_0]; } block_q8_0;
_Static_assert(sizeof(block_q8_0) == 34, "Q8_0 block layout");
'''
kernels = prefix+helpers+function.replace('void ggml_vec_dot_q8_0_q8_0(', '__attribute__((noinline)) void q8_reference(')+'\n'
manifest = {'base_commit':'d81235049384534c167caea52b85a694f6103d14','original_sha256':hashlib.sha256(original.encode()).hexdigest(),'variants':{}}
for name, loop in variants.items():
    modified_function = function[:loop_start]+loop+function[loop_end:]
    full = original[:begin]+modified_function+original[end:]
    target = root/'variants'/name
    target.mkdir(parents=True, exist_ok=True)
    (target/'quants.c').write_bytes(full.encode())
    patch = ''.join(difflib.unified_diff(original.splitlines(True),full.splitlines(True),fromfile='a/ggml/src/ggml-cpu/arch/x86/quants.c',tofile='b/ggml/src/ggml-cpu/arch/x86/quants.c'))
    (target/'change.patch').write_bytes(patch.encode())
    manifest['variants'][name] = {'sha256':hashlib.sha256(full.encode()).hexdigest(),'patch_sha256':hashlib.sha256(patch.encode()).hexdigest()}
    kernels += modified_function.replace('void ggml_vec_dot_q8_0_q8_0(', '__attribute__((noinline)) void q8_'+name+'(')+'\n'
(root/'q8-candidate-kernels.c').write_bytes(kernels.encode())
(root/'manifest.json').write_bytes(json.dumps(manifest,indent=2).encode())
test = (old/'test-q8-avx512.c').read_text()
test = test.replace('static void * load_library', 'static const char * candidate_name;\nstatic const char * candidate_names[] = {'+','.join('"'+name+'"' for name in variants)+'};\nstatic dot_fn candidates[] = {'+','.join('q8_'+name for name in variants)+'};\n\nstatic void * load_library')
test = test.replace('    init();','    init();\n    if (!q8_table) {\n        q8_table = (float *) dlsym(lib,"ggml_table_f32_f16");\n        if (!q8_table) { fprintf(stderr,"Missing production FP16 lookup table\\n"); exit(2); }\n    }')
test = test.replace('const char * names[] = {"baseline","avx512-ordered"};','const char * names[] = {"baseline",candidate_name};')
test = test.replace('puts("shape_blocks,mode,round,order,kernel,seconds,calls,ns_per_dot,weight_GB_s");','puts("shape_blocks,mode,round,order,kernel,seconds,calls,ns_per_dot,weight_GB_s");')
test = test.replace('int main(int argc, char ** argv) {', 'int main(int argc, char ** argv) {')
test = test.replace('if (argc!=4 ||','if (argc!=5 ||')
test = test.replace('CANDIDATE_LIB_OR_- --check|--bench','CANDIDATE_LIB_OR_- --check|--bench VARIANT')
test = test.replace('dot_fn baseline, candidate = q8_candidate;', '''dot_fn baseline, candidate = NULL;
    for (size_t i = 0; i < sizeof(candidates)/sizeof(candidates[0]); ++i) {
        if (!strcmp(argv[4],candidate_names[i])) { candidate = candidates[i]; candidate_name = candidate_names[i]; }
    }
    if (!candidate) return 2;''')
(root/'test-q8.c').write_bytes(test.encode())
lsf = (old/'kernel_test.lsf').read_text().split('stage COMPILE\n',1)[0]
lsf = lsf.replace('20261019-q8-avx512','20261019-q8-avx2-v2').replace('q8_avx512_unit','q8_avx2_screen').replace('qwen38_q8_avx512_unit','qwen38_q8_avx2_screen')
lsf += '''stage COMPILE
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
icc "${flags[@]}" -xCORE-AVX512 "$ROOT/scripts/test-q8.c" -ldl -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed -o "$OUT/test-q8" > "$OUT/compile.log" 2>&1
objdump -d "$OUT/test-q8" > "$OUT/full-assembly.txt"
sha256sum "$BASE" "$ROOT/scripts/test-q8.c" "$ROOT/scripts/q8-candidate-kernels.c" "$ROOT/scripts/manifest.json" > "$OUT/sha256.txt"
'''
for name in variants:
    lsf += '''stage CHECK_%s
mkdir -p "$OUT/%s"
"$OUT/test-q8" "$BASE" - --check %s > "$OUT/%s/correctness.json" 2> "$OUT/%s/correctness.log"
''' % (name,name,name,name,name)
lsf += '''stage MICROBENCH
'''
for name in variants:
    lsf += '''numactl --physcpubind=0 --membind=0 "$OUT/test-q8" "$BASE" - --bench %s > "$OUT/%s/kernel-times.csv" 2> "$OUT/%s/kernel-times.log"
''' % (name,name,name)
lsf += '''python3 "$ROOT/scripts/analyze.py" "$OUT"
stage UNIT_PASS
'''
(root/'screen.lsf').write_bytes(lsf.encode())
spec={'script':remote+'/screen.lsf','kind':'Q8源码修改/同节点候选筛选','purpose':'独立V2：测试AVX2四块加载调度、X侧8/16/32块T0预取及四块调度+16块T0/T1预取；保留浮点累加次序和所有旧版本','config':'Intel Classic 2021.9, O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；hg_6148单节点40slots；7配置依次运行（含原函数control）；每配置204154例逐位差分、38线程并发；使用生产FP16查表；CPU0/membind0单核nb80/192 resident及256MiB stream各10轮AB/BA；不加载模型','baseline':'同节点同进程生产Intel libggml-cpu.so；control为原函数重新编译；没有完整模型PP/TG baseline','note':'所有配置分别记录，不删低速样本；非固定PP/TG，不计算Score；先筛选后决定完整库构建及固定PPL'}
(root/'screen_submission.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print('Generated',len(variants),'independent source modifications at',root)
