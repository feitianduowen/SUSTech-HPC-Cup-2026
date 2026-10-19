import json
from pathlib import Path

local = Path('D:/compete/.codex-deploy/optimization/compiler_pgo')
local.mkdir(exist_ok=True)
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
template = (local.parent/'orchestrator/benchmark_variant.lsf').read_text(encoding='utf-8')
start = template.index('EXPERIMENT_VARIANT=${EXPERIMENT_VARIANT:?')
end = template.index('LLAMA_BENCH=', start)
gate = template[:start] + 'EXPERIMENT_VARIANT=${EXPERIMENT_VARIANT:-compiler}\nLLAMA_CPP_DIR=${COMPILER_BUILD_ROOT:?set COMPILER_BUILD_ROOT}\n\n' + template[end:]
(local/'ppl_gate.lsf').write_bytes(gate.encode())

pipeline = r'''#!/bin/bash
#BSUB -J qwen38_compiler_pgo
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.compiler_pgo.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.compiler_pgo.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo
SRC=/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native
LEVEL=${PGO_OPT_LEVEL:?set PGO_OPT_LEVEL}
[[ "$LEVEL" == 2 || "$LEVEL" == 3 ]]
OUT="$ROOT/results/$LSB_JOBID"
BUILDS="$ROOT/builds/$LSB_JOBID"
PROFILE="$OUT/profiles"
mkdir -p "$OUT" "$BUILDS" "$PROFILE"
phase=INIT
trap 'rc=$?; printf "FAILED phase=%s exit=%s time=%s\n" "$phase" "$rc" "$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; printf '%s time=%s\n' "$phase" "$(date -Is)" | tee "$OUT/job.status"; }
unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export GIT_OPTIONAL_LOCKS=0
[[ "${LSB_DJOB_NUMPROC:?missing LSF allocated slots}" == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
python3 "$ROOT/verify_source.py" "$SRC" "$ROOT/source_identity.json" > "$OUT/source-verification.json"
{
    date -Is; hostname; lscpu; module list; icc --version; icpc --version
    printf 'SOURCE=%s\nOPT_LEVEL=%s\n' "$SRC" "$LEVEL"
} > "$OUT/environment.txt" 2>&1
cp "$ROOT/pipeline.lsf" "$OUT/pipeline.lsf"
cp "$ROOT/ppl_gate.lsf" "$OUT/ppl_gate.lsf"
flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
link='-Wl,--no-as-needed,/lib64/libm.so.6,--as-needed'
build_stage() {
    local name=$1 mode=$2
    local dest="$BUILDS/$name/build" logs="$OUT/$name-build" pgo=''
    mkdir -p "$logs"
    case "$mode" in
        gen) pgo="-prof-gen=threadsafe -prof-dir $PROFILE";;
        use) pgo="-prof-use=nomerge -prof-dir $PROFILE";;
    esac
    local targets=(llama-cli llama-server llama-bench llama-perplexity test-quantize-fns)
    [[ "$mode" != gen ]] || targets=(llama-bench)
    local command=(cmake -S "$SRC" -B "$dest"
        -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
        -DCMAKE_C_COMPILER=icc -DCMAKE_CXX_COMPILER=icpc
        "-DCMAKE_C_FLAGS=-gcc-name=/share/base/e5/gcc/11.2.0/bin/gcc $flags $pgo"
        "-DCMAKE_CXX_FLAGS=-gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ $flags $pgo"
        "-DCMAKE_C_FLAGS_RELEASE=-O$LEVEL -DNDEBUG"
        "-DCMAKE_CXX_FLAGS_RELEASE=-O$LEVEL -DNDEBUG"
        "-DCMAKE_EXE_LINKER_FLAGS=$link $pgo"
        "-DCMAKE_SHARED_LINKER_FLAGS=$link $pgo"
        -DGGML_NATIVE=ON -DGGML_OPENMP=ON -DGGML_OPENMP_FETCH=OFF
        -DGGML_BLAS=OFF -DGGML_CUDA=OFF -DGGML_HIP=OFF -DGGML_VULKAN=OFF
        -DGGML_SYCL=OFF -DGGML_OPENCL=OFF -DGGML_RPC=OFF -DGGML_METAL=OFF -DGGML_MUSA=OFF
        -DLLAMA_BUILD_TESTS=ON -DLLAMA_BUILD_EXAMPLES=ON -DLLAMA_BUILD_TOOLS=ON
        -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_UI=OFF
        -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_OPENSSL=OFF -DFETCHCONTENT_FULLY_DISCONNECTED=ON)
    printf '%q ' "${command[@]}" > "$logs/configure.command"; printf '\n' >> "$logs/configure.command"
    "${command[@]}" > "$logs/configure.log" 2>&1
    cmake --build "$dest" --target "${targets[@]}" -j 40 > "$logs/build.log" 2>&1
    cp "$dest/CMakeCache.txt" "$logs/CMakeCache.txt"
    sha256sum "$dest/bin/llama-bench" "$dest/bin/libggml-cpu.so" > "$logs/sha256.txt"
    if [[ "$mode" != gen ]]; then
        "$dest/bin/test-quantize-fns" > "$logs/quantize-tests.log" 2>&1
        for name in llama-cli llama-server llama-bench llama-perplexity; do
            test -x "$dest/bin/$name"
            ldd "$dest/bin/$name" >> "$logs/ldd.txt"
            sha256sum "$dest/bin/$name" >> "$logs/sha256.txt"
        done
        ! grep -q 'not found' "$logs/ldd.txt"
    fi
}
gate() {
    local name=$1 ordinal=$2
    COMPILER_BUILD_ROOT="$BUILDS/$name" EXPERIMENT_OUTPUT_DIR="$OUT/${ordinal}_$name" RUN_BENCH=0 bash "$ROOT/ppl_gate.lsf" > "$OUT/$name-ppl-gate.log" 2>&1
}
stage BUILD_CONTROL
build_stage control plain
stage PPL_CONTROL
gate control 01
stage BUILD_GEN
build_stage gen gen
mkdir -p "$OUT/nontraining-profiles"
shopt -s nullglob
probe_profiles=("$PROFILE"/*.dyn)
if (( ${#probe_profiles[@]} )); then mv -- "${probe_profiles[@]}" "$OUT/nontraining-profiles/"; fi
export PROF_DIR="$PROFILE"
common=(-m "$MODEL" -t 38 -b 2048 -ub 512 -ctk f16 -ctv f16 -ngl 0 --numa distribute -r 1 --no-warmup -o json)
training() {
    local phase_name=$1 limit=$2; shift 2
    local command=(timeout --signal=TERM --kill-after=10s "$limit" "$BUILDS/gen/build/bin/llama-bench" "${common[@]}" "$@")
    printf '%q ' "${command[@]}" > "$OUT/training-$phase_name.command"; printf '\n' >> "$OUT/training-$phase_name.command"
    "${command[@]}" > "$OUT/training-$phase_name.json" 2> "$OUT/training-$phase_name.log"
}
stage TRAIN_PP_UNSCORED
training pp 900 -p 1024 -n 0
stage TRAIN_TG_UNSCORED
training tg 600 -p 0 -n 32 -d 512
stage MERGE
profiles=("$PROFILE"/*.dyn)
(( ${#profiles[@]} > 0 ))
profmerge -prof_dir "$PROFILE" -thread_max 2 > "$OUT/profmerge.log" 2>&1
test -s "$PROFILE/pgopti.dpi"
sha256sum "${profiles[@]}" "$PROFILE/pgopti.dpi" > "$OUT/profile-sha256.txt"
stage BUILD_USE
build_stage pgo use
# Retain all feedback-use warnings to verify actual hot-source profile matching.
grep -Ei 'profile|profiling|warning|error' "$OUT/pgo-build/build.log" > "$OUT/pgo-build/profile-diagnostics.txt" || true
stage PPL_USE
gate pgo 02
python3 "$ROOT/write_manifest.py" "$LSB_JOBID" "$LEVEL"
stage READY_FOR_PAIRED_BENCH
'''
(local/'pipeline.lsf').write_bytes(pipeline.encode())

manifest = '''import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
root = Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo')
jid,level = sys.argv[1:]
out = root/'results'/jid
builds = root/'builds'/jid
data = {'job_id':jid,'opt_level':level,'compiler':'Intel Classic 2021.9','source':'d81235049384534c167caea52b85a694f6103d14','source_path':'/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native','builds':{},'training':'Synthetic PP1024 and TG32@D512; 38 threads; profile branch counters only; unscored; no WikiText training','profile_count':len(list((out/'profiles').glob('*.dyn'))),'updated_at':datetime.now(timezone(timedelta(hours=8))).isoformat()}
for ordinal,name in [('01','control'),('02','pgo')]:
    gate=json.loads((out/(ordinal+'_'+name)/'perplexity_result.json').read_text())
    if gate['status']!='PASS': raise ValueError('PPL gate failed: '+name)
    data['builds'][name]={'root':str(builds/name),'ppl':gate,'artifacts':{}}
    for file in sorted((builds/name/'build/bin').iterdir()):
        if file.is_file() and (file.name.startswith('lib') or file.name in ['llama-cli','llama-server','llama-bench','llama-perplexity']):
            data['builds'][name]['artifacts'][file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
data['dpi_sha256']=hashlib.sha256((out/'profiles/pgopti.dpi').read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps(data,ensure_ascii=False))
'''
(local/'write_manifest.py').write_bytes(manifest.encode())
verify_source = '''import hashlib
import json
import subprocess
import sys
from pathlib import Path
src,target=map(Path,sys.argv[1:3])
expected='d81235049384534c167caea52b85a694f6103d14'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if '--snapshot' in sys.argv:
    revision=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip()
    if revision!=expected: raise ValueError('Unexpected source revision')
    subprocess.check_call(['git','-C',str(src),'diff','--exit-code','--quiet'])
    names=subprocess.check_output(['git','-C',str(src),'ls-files','-z']).decode().split(chr(0))
    data={'revision':revision,'files':{name:digest(src/name) for name in names if name and (src/name).is_file()}}
    target.write_text(json.dumps(data,indent=2))
else:
    data=json.loads(target.read_text())
    if data['revision']!=expected: raise ValueError('Unexpected source revision')
    bad=[name for name,sha in data['files'].items() if not (src/name).is_file() or digest(src/name)!=sha]
    if bad: raise ValueError('Source mismatch: '+str(bad))
print(json.dumps({'revision':data['revision'],'verified_files':len(data['files']),'all_match':True}))
'''
(local/'verify_source.py').write_bytes(verify_source.encode())
for level in [3,2]:
    spec = {'script':remote+'/pipeline.lsf','kind':'Intel PGO构建/训练/PPL',
        'purpose':f'Intel Classic O{level}：无PGO对照构建、线程安全计数训练、反馈优化重编译及独立固定PPL门槛',
        'config':f'Gold6148单节点40 slots；Intel Classic2021.9 icc/icpc，Release -O{level} -DNDEBUG；precise/no-ftz/CORE-AVX512/qsimd-honor-fp-model；未启用-ipo；官方原始源码d812350；OpenMP=ON,BLAS=OFF,CPU-only；构建-j40，推理38线程close/cores；gen=-prof-gen=threadsafe；use=-prof-use=nomerge；训练仅合成PP1024/TG32@D512、r1、不计分；control及pgo分别固定PPL t/tb38,c512,chunks2,b512,ub256,f16KV,ngl0,NUMA=distribute,no-warmup,timeout590s；本作业无完整PP/TG测速',
        'baseline':f'同源码同Intel编译器同-O{level}的无PGO control；正确性官方PPL=2.7696',
        'case_prefix':'compiler','baseline_case':'compiler-control_{job_id}',
        'environment':{'PGO_OPT_LEVEL':str(level)},'lsf_args':['-J',f'qwen38_icc_O{level}_pgo'],
        'note':'本阶段只构建、采集编译器计数并校验正确性；训练指标不计入性能结果。成功后另交同节点正反序完整10次PP/TG对照；两个O级分属不同节点，不直接比较。规则7明确允许compiler flags及PGO。'}
    (local/f'submit_O{level}.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
    retry = dict(spec)
    retry['retry_of'] = '4336529' if level==3 else '4336530'
    retry['note'] += ' 重提修复：计算节点无git，改为登录节点验证官方commit并保存3687个源码文件SHA256，计算节点逐文件校验；前次失败作业'+retry['retry_of']+'保留。'
    (local/f'retry_O{level}.json').write_bytes(json.dumps(retry,ensure_ascii=False,indent=2).encode())
(local/'next_actions.json').write_bytes(json.dumps({'phase':'Intel Classic O3/O2 PGO','jobs':[], 'next':'Check pipeline job.status and manifest. READY plus both PPL PASS and usable hot-source profile feedback => submit paired control/PGO full PPL->PP10->TG10, forward and reverse on matching free r13n Gold6148 nodes. Failed => inspect precise stage and logs, fix and resubmit through submit_logged.py. Register every acquired job ID in Excel immediately. Preserve all old jobs and samples.'},indent=2).encode())
print(local)
