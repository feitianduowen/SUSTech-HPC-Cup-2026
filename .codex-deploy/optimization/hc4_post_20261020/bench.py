import json
import statistics
import subprocess
import sys
from pathlib import Path

out=Path(sys.argv[1])
checks={name:json.loads((out/(name+'-check.json')).read_text()) for name in ['baseline','candidate']}
assert checks['baseline']==checks['candidate']
assert checks['baseline']['status']=='PASS' and checks['baseline']['cases']==972
a=(out/'baseline.bin').read_bytes();b=(out/'candidate.bin').read_bytes()
assert len(a)==len(b)==4*checks['baseline']['values']
bit=sum(a[i:i+4]!=b[i:i+4] for i in range(0,len(a),4))
exact={'status':'PASS' if not bit else 'FAIL','cases':checks['baseline']['cases'],'values':len(a)//4,'bit_mismatches':bit,'repetitions':3}
(out/'library-correctness.json').write_text(json.dumps(exact,indent=2))
assert not bit,exact
samples=[]
for repeat in range(10):
    order=['baseline','candidate'] if repeat%2==0 else ['candidate','baseline']
    for name in order:
        p=subprocess.run([str(out/('check-'+name)),'--bench'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=180)
        (out/(name+'-bench-'+str(repeat)+'.log')).write_text(p.stderr)
        assert p.returncode==0,p.stderr
        samples.append({'round':repeat,'name':name,'order':order,'data':json.loads(p.stdout)})
        (out/'hc-raw-samples.json').write_text(json.dumps(samples,indent=2))
results=[]
for shape in [[2560,4,1],[2560,4,32],[2560,4,512],[10240,4,1]]:
    groups={name:[next(x['ns_per_graph'] for x in row['data'] if x['shape']==shape) for row in samples if row['name']==name] for name in ['baseline','candidate']}
    results.append({'shape':shape,'baseline_ns_median':statistics.median(groups['baseline']),'candidate_ns_median':statistics.median(groups['candidate']),'speedup':statistics.median(groups['baseline'])/statistics.median(groups['candidate']),'paired_wins':sum(a>b for a,b in zip(groups['baseline'],groups['candidate'])),'samples':groups})
summary={'hc_checks':checks,'library_correctness':exact,'hc_microbench':results,'interpretation':'Actual GGML HC-post graphs: 972 configurations, 3 repetitions, 1/3/38 threads, hc1/2/4/8, contiguous/padded/transposed, absent/identity/dense comb, double oracle and baseline bit identity. Operator timings include graph threadpool overhead, 10 alternating AB/BA rounds. These are not model scores. Independent PPL and full balanced model comparisons pending.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
