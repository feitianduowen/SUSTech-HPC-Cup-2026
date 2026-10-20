import json
import statistics
import subprocess
import sys
from pathlib import Path
out=Path(sys.argv[1])
checks={name:json.loads((out/('dot-'+name+'-check.json')).read_text()) for name in ['baseline','candidate']}
assert all(x['status']=='PASS' and x['failures']==0 and x['cases']==262432 for x in checks.values())
a=(out/'dot-baseline.bin').read_bytes();b=(out/'dot-candidate.bin').read_bytes()
assert len(a)==len(b)==262432*4
bit=sum(a[i:i+4]!=b[i:i+4] for i in range(0,len(a),4))
exact={'status':'PASS' if bit==0 else 'FAIL','cases':262432,'bit_mismatches':bit,'repetitions':3}
(out/'dot-correctness.json').write_text(json.dumps(exact,indent=2))
assert not bit,exact
samples=[]
for repeat in range(10):
    order=['baseline','candidate'] if repeat%2==0 else ['candidate','baseline']
    for name in order:
        p=subprocess.run(['numactl','--physcpubind=0','--membind=0',str(out/('dot-'+name)),'--bench'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120)
        (out/('dot-'+name+'-bench-'+str(repeat)+'.log')).write_text(p.stderr)
        assert p.returncode==0,p.stderr
        data=json.loads(p.stdout)
        samples.append({'round':repeat,'name':name,'order':order,'data':data})
        (out/'dot-raw-samples.json').write_text(json.dumps(samples,indent=2))
results=[]
for n in [256,1024,2560,6144,16384]:
    groups={name:[next(d['ns_per_call'] for d in row['data'] if d['n']==n) for row in samples if row['name']==name] for name in ['baseline','candidate']}
    results.append({'n':n,'baseline_ns_median':statistics.median(groups['baseline']),'candidate_ns_median':statistics.median(groups['candidate']),'speedup':statistics.median(groups['baseline'])/statistics.median(groups['candidate']),'paired_wins':sum(a>b for a,b in zip(groups['baseline'],groups['candidate'])),'samples':groups})
advance=all(x['speedup']>=0.95 for x in results) and any(x['n'] in [2560,6144] and x['speedup']>=1.03 and x['paired_wins']>=7 for x in results)
summary={'dot_checks':checks,'dot_correctness':exact,'microbench':results,'advance_to_model':advance,'interpretation':'Q5 paired-FP16-conversion actual-library direct-dot bit comparison passed for 262432 cases. Single-core CPU0/membind0 resident inputs; 10 alternating AB/BA rounds, all samples retained. This kernel screen does not certify model PPL or speed. Advance threshold: >=3% speedup at 2560 or 6144 with >=7/10 paired wins, and no size slower by >5% in throughput. '+('Model phase eligible; fixed PPL and full bracketing tests pending.' if advance else 'No model phase: kernel gain threshold not met; do not promote.')}
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
