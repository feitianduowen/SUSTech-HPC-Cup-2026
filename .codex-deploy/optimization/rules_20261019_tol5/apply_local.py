import hashlib
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from rule_patch import POLICY,patch_gate,patch_bounds

here=Path(__file__).resolve().parent
base=here.parent
gates=['compiler_pgo/ppl_gate.lsf','source_v2/ppl_gate.lsf','q8_avx2_v2/ppl_gate.lsf']+['orchestrator/benchmark_'+x+'.lsf' for x in ['variant','runtime','load_mode','diagnostic']]
bounds=['q8_avx2_v2/verify_pair.py','q8_avx2_v2/verify_reverse.py','compiler_pgo/prepare_ggml_v3.py','compiler_pgo/pipeline_ggml_pgo_v3.lsf','compiler_pgo/pipeline_ggml_pgo_v4.lsf','compiler_pgo/pipeline_driver_no_as_needed.lsf','compiler_pgo/pipeline_driver_long_train.lsf']
manifest=[]
for name in gates+bounds:
    file=base/name
    if not file.exists():continue
    old=file.read_bytes()
    text=old.decode('utf-8')
    updated=(patch_gate(text) if name in gates else patch_bounds(text)).encode()
    if updated==old:continue
    backup=here/'before_local'/name
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():backup.write_bytes(old)
    file.write_bytes(updated)
    manifest.append({'path':str(file),'backup':str(backup),'original_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(updated).hexdigest()})
(here/'policy.json').write_text(json.dumps(POLICY,ensure_ascii=False,indent=2),encoding='utf-8')
(here/'local-patch-manifest.json').write_text(json.dumps({'applied_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'files':manifest},indent=2),encoding='utf-8')
print('Updated operational gates/verifiers:',len(manifest))
