import hashlib
import json
import sys
from pathlib import Path

out,variant,parent = Path(sys.argv[1]),sys.argv[2],sys.argv[3]
root = Path('/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2')
registry = json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1/results/job_registry.json').read_text())
baseline_job = next(j for j in registry['jobs'] if j['job_id']=='4335636')
assert baseline_job['measurements'][0]['ppl']['status']=='PASS'
deployment = json.loads((root/'scripts/deployment-baseline.json').read_text())
assert deployment['validation_job']=='4335636' and deployment['ppl_status']=='PASS'
for name,expected in deployment['artifact_sha256'].items():
    file = Path('/work/apac2602/qwen38-cpu/llama.cpp/build/bin')/name
    assert hashlib.sha256(file.read_bytes()).hexdigest()==expected, 'Baseline artifact changed: '+name
conditions = None
for case in ['01_baseline','02_candidate']:
    gate = json.loads((out/case/'perplexity_result.json').read_text())
    assert gate['status']=='PASS'
    assert 2.63112 <= gate['ppl'] <= 2.90808
    if conditions is None:
        conditions = gate['conditions']
    assert conditions == gate['conditions'], 'PPL conditions changed'
# Pin the parent files checked by the build and deployment records, preserving the
# raw fingerprints as evidence. Parent SHA checks execute in the shell beforehand.
fingerprints = {}
for name,base in [('baseline',Path('/work/apac2602/qwen38-cpu/llama.cpp/build/bin')),('candidate',root/'sources'/variant/'build/bin')]:
    for file in ['llama-bench','libggml-cpu.so','libggml.so','libggml-base.so']:
        fingerprints[name+'/'+file] = hashlib.sha256((base/file).read_bytes()).hexdigest()
plan={'variant':variant,'build_job':parent,'ppl_reused':{'baseline':'4335636','candidate':parent},'order':['baselinePP','candidatePP','candidateTG','baselineTG'],'scope':'Same host sequential comparison. Each binary reuses its independent fixed PPL result. No PPL rerun in this job. Development score only.','fingerprints':fingerprints}
model = '/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf'
common = ['-m',model,'-t','38','-ngl','0','-b','2048','-ub','512','-ctk','f16','-ctv','f16','--numa','distribute','-r','10']
for case,source in [('01_baseline',Path('/work/apac2602/qwen38-cpu/llama.cpp')),('02_candidate',root/'sources'/variant)]:
    exe = str(source/'build/bin/llama-bench')
    for phase,args in [('pp',['-p','2048','-n','0']),('tg',['-p','0','-n','128','-d','2048'])]:
        command = [exe]+common+args+['-o','json']
        (out/case/(phase+'.command.json')).write_text(json.dumps(command,indent=2))
(out/'plan.json').write_text(json.dumps(plan,indent=2))
print(json.dumps(plan,indent=2))
