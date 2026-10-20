import json
import statistics
import subprocess
import sys
from pathlib import Path
out=Path(sys.argv[1])
checks={name:json.loads((out/('dot-'+name+'-check.json')).read_text()) for name in ['baseline','candidate']}
assert all(x['status']=='PASS' and x['failures']==0 and x['cases']==8672 for x in checks.values())
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
for n in [256,1024,2560,4096,16384]:
    groups={name:[next(d['ns_per_call'] for d in row['data'] if d['n']==n) for row in samples if row['name']==name] for name in ['baseline','candidate']}
    results.append({'n':n,'baseline_ns_median':statistics.median(groups['baseline']),'candidate_ns_median':statistics.median(groups['candidate']),'speedup':statistics.median(groups['baseline'])/statistics.median(groups['candidate']),'samples':groups})
summary={'dot_checks':checks,'microbench':results,'interpretation':'F32 actual-library direct-dot high-precision checks passed. Single-core CPU0/membind0 resident inputs; 10 alternating AB/BA rounds, all samples retained. These are kernel diagnostics, not model PP/TG or official scores; independent fixed PPL and full workload still required.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
