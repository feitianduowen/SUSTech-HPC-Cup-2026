import hashlib
import json
import re
import subprocess
from datetime import datetime,timezone,timedelta
from pathlib import Path
from rule_patch import POLICY,patch_gate,patch_bounds

deploy=Path('/work/apac2602/qwen38-cpu')
here=deploy/'optimization/20261019-ppl-tol5'
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
gates=['optimization/20261019-compiler-pgo/ppl_gate.lsf','optimization/20261019-q8-avx512/ppl_gate.lsf','optimization/20261019-q8-avx2-v2/ppl_gate.lsf']+['optimization/20261018-v1/scripts/benchmark_'+x+'.lsf' for x in ['variant','runtime','load_mode','diagnostic']]
bounds=['optimization/20261019-q8-avx2-v2/scripts/verify_pair.py','optimization/20261019-q8-avx2-v2/scripts/verify_reverse.py','optimization/20261019-compiler-pgo/pipeline_ggml_pgo_v3.lsf','optimization/20261019-compiler-pgo/pipeline_ggml_pgo_v4.lsf','optimization/20261019-compiler-pgo/pipeline_driver_no_as_needed.lsf','optimization/20261019-compiler-pgo/pipeline_driver_long_train.lsf']
manifest=[]
for name in gates+bounds:
    file=deploy/name
    if not file.is_file():continue
    old=file.read_bytes()
    text=old.decode('utf-8')
    updated=(patch_gate(text) if name in gates else patch_bounds(text)).encode()
    backup=here/'before_remote'/name
    if updated!=old:
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():backup.write_bytes(old)
        temporary=file.with_name(file.name+'.tol5.tmp')
        temporary.write_bytes(updated)
        temporary.replace(file)
    if name in gates:
        subprocess.check_call(['bash','-n',str(file)])
    manifest.append({'path':str(file),'backup':str(backup) if backup.exists() else None,'original_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(updated).hexdigest()})

# Active pipelines read the root gate when their future PPL stage begins. Keep
# their startup snapshot intact and append the actual rule change separately.
active=subprocess.run(['bjobs','-w'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,timeout=15).stdout
notified=[]
root=deploy/'optimization/20261019-compiler-pgo'
for line in active.splitlines():
    if not re.match(r'^\d+\s',line):continue
    jid=line.split()[0]
    out=root/'results'/jid
    if not out.is_dir():continue
    gate=root/'ppl_gate.lsf'
    status=out/'job.status'
    record={'applied_at':stamp,'policy':POLICY,'stage_at_update':status.read_text() if status.exists() else None,'runtime_gate':str(gate),'runtime_gate_sha256':hashlib.sha256(gate.read_bytes()).hexdigest(),'scope':'Future PPL gate uses updated root script. Startup snapshots and prior PPL results retained; no training, model, compiler, workload or process-limit changes.'}
    snapshot=out/'ppl_gate.tol5.lsf'
    if not snapshot.exists():snapshot.write_bytes(gate.read_bytes())
    (out/'ppl_rule_update_20261019.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
    notified.append(jid)
(here/'policy.json').write_text(json.dumps(POLICY,ensure_ascii=False,indent=2))
(here/'remote-patch-manifest.json').write_text(json.dumps({'applied_at':stamp,'files':manifest,'active_jobs_annotated':notified,'scheduler_snapshot':active},ensure_ascii=False,indent=2))
print(json.dumps({'files':len(manifest),'active_jobs_annotated':notified,'rule':POLICY['version']}))
