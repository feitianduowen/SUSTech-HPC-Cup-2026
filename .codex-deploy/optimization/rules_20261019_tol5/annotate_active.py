import hashlib
import json
import re
import subprocess
from datetime import datetime,timezone,timedelta
from pathlib import Path

deploy=Path('/work/apac2602/qwen38-cpu')
root=deploy/'optimization/20261019-compiler-pgo'
gate=root/'ppl_gate.lsf'
text=gate.read_text()
assert 'PPL_MAX_REL_DIFF_PERCENT=5.0' in text
assert '2.63112 <= ppl <= 2.90808' in text
active=subprocess.run(['bjobs','-w'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,timeout=15).stdout
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
ids=[]
for line in active.splitlines():
    if not re.match(r'^\d+\s',line):continue
    jid=line.split()[0]
    out=root/'results'/jid
    if not out.is_dir():continue
    status=out/'job.status'
    startup=out/'ppl_gate.lsf'
    event={'policy_id':'20261019-ppl-tolerance-5pct','applied_at_hkt':stamp,'baseline_ppl':2.7696,'tolerance_percent':5.0,'accepted_interval_inclusive':[2.63112,2.90808],'runtime_gate':str(gate),'runtime_gate_sha256':hashlib.sha256(gate.read_bytes()).hexdigest(),'startup_gate_sha256':hashlib.sha256(startup.read_bytes()).hexdigest() if startup.exists() else None,'stage_at_update':status.read_text() if status.exists() else None,'scope':'The future PPL stage reads the updated root gate. Startup snapshot and prior PPL JSON remain original. No model, training, compiler, PPL parameters/590s limit or fixed speed workload changes.'}
    snapshot=out/'ppl_gate.tol5.lsf'
    if not snapshot.exists():snapshot.write_bytes(gate.read_bytes())
    destination=out/'ppl_rule_update_20261019.json'
    if not destination.exists():destination.write_text(json.dumps(event,ensure_ascii=False,indent=2))
    ids.append(jid)
audit=deploy/'optimization/20261019-ppl-policy5'
audit.mkdir(exist_ok=True)
(audit/'active-job-policy-notices.json').write_text(json.dumps({'applied_at_hkt':stamp,'jobs':ids,'scheduler_snapshot':active},ensure_ascii=False,indent=2))
print(json.dumps({'annotated_jobs':ids,'gate_sha256':hashlib.sha256(gate.read_bytes()).hexdigest()}))
