import fcntl
import json
import subprocess
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-other-source')
registry=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1/results/submission_registry.jsonl')
with (root/'submit.lock').open('w') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    for variant in ['gemm-balanced','row-quant']:
        previous=[json.loads(s) for s in registry.read_text().splitlines()]
        matches=[x for x in previous if x.get('script')==str(root/'build_and_pair.lsf') and x.get('environment',{}).get('SOURCE_VARIANT')==variant and x.get('job_id')]
        if matches:
            print('ALREADY_SUBMITTED '+variant+' '+matches[-1]['job_id'],flush=True)
            continue
        code=subprocess.call(['python3','-u','/work/apac2602/qwen38-cpu/optimization/20261018-v1/scripts/submit_logged.py',str(root/(variant+'.json'))])
        print('SUBMIT_RETURN '+variant+' '+str(code),flush=True)
