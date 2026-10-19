import json
from pathlib import Path

local=Path(__file__).resolve().parent
root='/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx512'
old=(local.parent/'orchestrator/build_variant.lsf').read_text(encoding='utf-8')
start=old.index('cmake -S "$SRC"')
end=old.index('echo BUILD_READY',start)
body=old[start:end]
header='''#!/bin/bash
#BSUB -J qwen38_q8_avx512_build_ppl
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 02:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.q8_avx512_build.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.q8_avx512_build.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx512
SRC="$ROOT/source-v2"
BUILD="$SRC/build"
OUT="$ROOT/results/$LSB_JOBID"
PARENT=${Q8_UNIT_JOB:?set successful unit test job}
mkdir -p "$OUT"
phase=COPY_SOURCE
trap 'rc=$?; echo "FAILED phase=$phase exit=$rc" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; echo "$phase time=$(date -Is)" > "$OUT/job.status"; }
[[ "$PARENT" =~ ^[0-9]+$ ]]
[[ "${LSB_DJOB_NUMPROC:?missing allocated slots}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
grep -q UNIT_PASS "$ROOT/results/$PARENT/job.status"
sha256sum -c "$ROOT/results/$PARENT/sha256.txt" > "$OUT/unit-input-verification.txt"
stage COPY_SOURCE
if test ! -f "$ROOT/compute-source.ready"; then python3 -u "$ROOT/scripts/copy_source_parallel.py" --compute > "$OUT/copy-source.log" 2>&1; fi
if test ! -f "$ROOT/source-modification.json"; then python3 "$ROOT/scripts/apply_source_patch.py" > "$OUT/apply-patch.log" 2>&1; fi
stage VERIFY_SOURCE
python3 "$ROOT/scripts/verify_candidate_source.py" > "$OUT/source-verification.json"
unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY
flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
omp=ON
blas=OFF
extra=()
{ date -Is; hostname; lscpu; icc --version; icpc --version; module list; } > "$OUT/environment.txt" 2>&1
stage BUILDING
'''
tail='''stage LIBRARY_DIFFERENTIAL
cp "$ROOT/results/$PARENT/test-q8-avx512" "$OUT/test-q8-avx512"
BASE=/work/apac2602/qwen38-cpu/llama.cpp/build/bin/libggml-cpu.so
CANDIDATE="$BUILD/bin/libggml-cpu.so"
"$OUT/test-q8-avx512" "$BASE" "$CANDIDATE" --check > "$OUT/library-correctness.json" 2> "$OUT/library-correctness.log"
objdump -d "$CANDIDATE" > "$OUT/library-assembly.txt"
awk '/<ggml_vec_dot_q8_0_q8_0>:/ {inside=1; print; next} inside && /^[[:xdigit:]]+ <[^>]+>:/ {exit} inside {print}' "$OUT/library-assembly.txt" > "$OUT/avx512-assembly.txt"
grep -Eq 'vpmaddubsw.*%zmm' "$OUT/avx512-assembly.txt"
stage LIBRARY_MICROBENCH
numactl --physcpubind=0 --membind=0 "$OUT/test-q8-avx512" "$BASE" "$CANDIDATE" --bench > "$OUT/kernel-times.csv" 2> "$OUT/kernel-times.log"
python3 "$ROOT/scripts/analyze_kernel.py" "$OUT" > "$OUT/kernel-summary.log"
stage PPL_CANDIDATE
COMPILER_BUILD_ROOT="$SRC" RUN_BENCH=0 EXPERIMENT_OUTPUT_DIR="$OUT/01_candidate" bash "$ROOT/ppl_gate.lsf" > "$OUT/ppl-gate.log" 2>&1
sha256sum "$BUILD/bin/llama-bench" "$BUILD/bin/llama-perplexity" "$CANDIDATE" >> "$OUT/sha256.txt"
stage BUILD_PPL_PASS
'''
(local/'build_ppl.lsf').write_bytes((header+body+tail).encode())
(local/'ppl_gate.lsf').write_bytes((local.parent/'compiler_pgo/ppl_gate.lsf').read_bytes())
verify='''import hashlib
import json
from pathlib import Path
root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx512')
identity=json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json').read_text())
change=json.loads((root/'source-modification.json').read_text())
bad=[]
for name,sha in identity['files'].items():
    expected=change['modified_sha256'] if name==change['file'] else sha
    file=root/'source-v2'/name
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=expected:bad.append(name)
if bad:raise ValueError('Unexpected source changes: '+str(bad))
old=Path(change['original_preserved_at'])
assert hashlib.sha256(old.read_bytes()).hexdigest()==change['original_sha256']
print(json.dumps({'base_commit':identity['revision'],'files_verified':len(identity['files']),'changed_files':[change['file']],'previous_source_unchanged':True,'all_match':True}))
'''
(local/'verify_candidate_source.py').write_bytes(verify.encode())
print(local/'build_ppl.lsf')
