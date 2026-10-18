from pathlib import Path
import subprocess
import sys

root = Path(__file__).parent
out = root / 'package'
out.mkdir(exist_ok=True)
remote = '/work/apac2602/qwen38-cpu'

def write(name, text):
    (out / name).write_text(text, encoding='utf-8', newline='\n')

for source, name in [('install.reference.lsf', 'build.sh'), ('eval.reference.lsf', 'benchmark.lsf')]:
    text = (root / source).read_text(encoding='utf-8')
    text = text.replace('/work/ssc-202621/llama.cpp', remote + '/llama.cpp')
    text = text.replace('#BSUB -e %J.err', '#BSUB -e ' + remote + '/logs/%J.err')
    text = text.replace('#BSUB -o %J.out', '#BSUB -o ' + remote + '/logs/%J.out')
    text = text.replace('#BSUB -q ssc-cpu', '#BSUB -q ssc-cpu\n#BSUB -m hg_6148\n#BSUB -W 04:00')
    if name == 'build.sh':
        text = text.replace('CLEAN_BUILD=1', 'CLEAN_BUILD=0')
        text = text.replace('    -DGGML_BLAS=OFF \\\n', '    -DGGML_BLAS=OFF \\\n    -DGGML_CUDA=OFF -DGGML_HIP=OFF -DGGML_VULKAN=OFF \\\n    -DGGML_SYCL=OFF -DGGML_OPENCL=OFF -DGGML_RPC=OFF \\\n    -DGGML_METAL=OFF -DGGML_MUSA=OFF \\\n')
        text = text.replace('set -euo pipefail', 'set -euo pipefail\n[[ "${LSB_DJOB_NUMPROC:-0}" -eq 40 ]] || { echo "Submit with bsub on a 40-slot CPU node" >&2; exit 1; }')
    write(name, text)

write('env.sh', '''#!/bin/bash
export QWEN_DEPLOY=/work/apac2602/qwen38-cpu
export LLAMA_CPP_DIR="$QWEN_DEPLOY/llama.cpp"
export MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
export PPL_DATA=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/wikitext-2-raw/wiki.test.raw
export PPL_BASELINE_JSON=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/perplexity_result.json
module load cmake/3.28.1 gcc/12.2.0
export PATH="$LLAMA_CPP_DIR/build/bin:$PATH"
export OMP_NUM_THREADS=38
export OMP_DYNAMIC=FALSE
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OPENBLAS_NUM_THREADS=38
export MKL_NUM_THREADS=38
export BLIS_NUM_THREADS=38
''')

write('bootstrap.lsf', '''#!/bin/bash
#BSUB -J qwen38_deploy
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 02:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.err
set -euo pipefail
cd /work/apac2602/qwen38-cpu
trap 'code=$?; if (( code != 0 )); then echo "FAILED exit=$code job=$LSB_JOBID" > deployment.status; fi' EXIT
echo "BUILDING job=$LSB_JOBID host=$(hostname)" > deployment.status
source scripts/env.sh
python3 scripts/check_assets.py > logs/assets.json
bash scripts/build.sh
echo "VALIDATING_PPL job=$LSB_JOBID host=$(hostname)" > deployment.status
RUN_BENCH=0 bash scripts/benchmark.lsf
echo "VALIDATING_SERVER job=$LSB_JOBID host=$(hostname)" > deployment.status
python3 scripts/server_smoke.py
echo "READY job=$LSB_JOBID host=$(hostname)" > deployment.status
date -Is >> deployment.status
''')

write('check_assets.py', '''import hashlib
import json
import os
import struct
from pathlib import Path

ref = json.loads(Path(os.environ['PPL_BASELINE_JSON']).read_text())
assert ref['schema'] == 'llama_cpp_ppl_regression_v1'
assert ref['status'] == 'REFERENCE_RECORDED'
assert ref['ppl'] == 2.7696 and ref['tolerance_percent'] == 0.5
records = []
for name, size in ref['conditions']['model_files_path_and_size']:
    path = Path(name)
    assert path.stat().st_size == size, name
    with path.open('rb') as stream:
        magic, version = struct.unpack('<4sI', stream.read(8))
    assert magic == b'GGUF' and version in (2, 3), name
    records.append({'path': name, 'size': size, 'gguf_version': version})
assert len(records) == 4
digest = hashlib.sha256(Path(os.environ['PPL_DATA']).read_bytes()).hexdigest()
assert digest == '173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08'
assert digest == ref['conditions']['data_sha256']
print(json.dumps({'model_shards': records, 'data_sha256': digest, 'baseline_ppl': ref['ppl']}, indent=2))
''')

write('server.lsf', '''#!/bin/bash
#BSUB -J qwen38_server
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.server.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.server.err
set -euo pipefail
cd /work/apac2602/qwen38-cpu
source scripts/env.sh
python3 scripts/check_assets.py > "logs/assets_server_${LSB_JOBID}.json"
echo "Node: $(hostname); loopback endpoint: http://127.0.0.1:18080"
echo "Job: $LSB_JOBID; stop with: bkill $LSB_JOBID"
exec "$LLAMA_CPP_DIR/build/bin/llama-server" \\
  -m "$MODEL" -t 38 -tb 38 -ngl 0 --numa distribute \\
  -c 2048 -b 512 -ub 256 -ctk f16 -ctv f16 -np 1 \\
  --host 127.0.0.1 --port 18080 --no-webui --no-warmup
''')

write('server_smoke.py', '''import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import Request, urlopen

root = Path(os.environ['QWEN_DEPLOY'])
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
base = 'http://127.0.0.1:' + str(port)
args = [str(root / 'llama.cpp/build/bin/llama-server'), '-m', os.environ['MODEL'],
        '-t', '38', '-tb', '38', '-ngl', '0', '--numa', 'distribute',
        '-c', '2048', '-b', '512', '-ub', '256', '-ctk', 'f16', '-ctv', 'f16',
        '-np', '1', '--host', '127.0.0.1', '--port', str(port), '--no-webui', '--no-warmup']
started = time.monotonic()
with (root / 'logs/server_smoke.log').open('w') as log:
    proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 360
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError('Server exited early: ' + str(proc.returncode))
            try:
                with urlopen(base + '/health', timeout=3) as response:
                    health = json.load(response)
                if health.get('status') == 'ok':
                    break
            except Exception:
                pass
            time.sleep(2)
        else:
            raise RuntimeError('Server readiness timed out')
        with urlopen(base + '/v1/models', timeout=10) as response:
            models = json.load(response)
        request = Request(base + '/completion',
                          data=json.dumps({'prompt': 'The capital of France is', 'n_predict': 12,
                                           'temperature': 0, 'seed': 1}).encode(),
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=240) as response:
            completion = json.load(response)
        assert completion.get('content') and completion.get('tokens_predicted', 0) > 0
        result = {'status': 'PASS', 'health': health, 'models': models,
                  'completion': completion, 'seconds': time.monotonic() - started,
                  'host': socket.gethostname(), 'job_id': os.environ.get('LSB_JOBID')}
        (root / 'logs/server_smoke_result.json').write_text(json.dumps(result, indent=2) + '\\n')
        print('Server smoke PASS: ' + completion['content'], flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
''')

write('cli.lsf', '''#!/bin/bash
#BSUB -J qwen38_cli
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 00:30
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.cli.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.cli.err
set -euo pipefail
cd /work/apac2602/qwen38-cpu
source scripts/env.sh
exec llama-cli -m "$MODEL" -t 38 -tb 38 -ngl 0 --numa distribute \\
  -c 2048 -b 512 -ub 256 -ctk f16 -ctv f16 \\
  -p "${PROMPT:-Explain what a CPU is in two sentences.}" -n 128 --single-turn
''')

subprocess.run([sys.executable, str(root / 'switch_to_intel.py')], check=True)
