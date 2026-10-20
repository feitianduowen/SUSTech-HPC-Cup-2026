import json
import statistics
import subprocess
import sys
from pathlib import Path

r=Path(sys.argv[1]);names=['baseline','mask','unroll','candidate'];rounds=12
checks={name:json.loads((r/('dot-'+name+'-check.json')).read_text()) for name in names}
assert all(x['status']=='PASS' and x['failures']==0 and x['cases']==262432 for x in checks.values())
base=(r/'dot-baseline.bin').read_bytes();assert len(base)==262432*4
exact={}
for name in names[1:]:
    candidate=(r/('dot-'+name+'.bin')).read_bytes();assert len(candidate)==len(base)
    mismatches=sum(base[i:i+4]!=candidate[i:i+4] for i in range(0,len(base),4))
    exact[name]={'status':'PASS' if not mismatches else 'FAIL','cases':262432,'bit_mismatches':mismatches,'repetitions':3}
(r/'dot-correctness.json').write_text(json.dumps(exact,indent=2));assert all(x['status']=='PASS' for x in exact.values())
samples=[]
for repeat in range(rounds):
    offset=repeat%4;order=names[offset:]+names[:offset]
    for name in order:
        p=subprocess.run(['numactl','--physcpubind=0','--membind=0',str(r/('dot-'+name)),'--bench'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=120)
        (r/('dot-'+name+'-bench-'+str(repeat)+'.log')).write_text(p.stderr)
        assert p.returncode==0,p.stderr
        samples.append({'round':repeat,'name':name,'order':order,'data':json.loads(p.stdout)})
        (r/'dot-raw-samples.json').write_text(json.dumps(samples,indent=2))
results=[]
for n in [256,1024,2560,6144,16384]:
    groups={name:[next(x['ns_per_call'] for x in row['data'] if x['n']==n) for row in samples if row['name']==name] for name in names}
    med={name:statistics.median(x) for name,x in groups.items()}
    comparisons={name:{'reference_ns_median':med[name],'speedup':med[name]/med['candidate'],'paired_wins':sum(a>b for a,b in zip(groups[name],groups['candidate'])),'samples_ns':groups[name]} for name in ['mask','unroll']}
    results.append({'n':n,'baseline_ns_median':med['baseline'],'candidate_ns_median':med['candidate'],'speedup':med['baseline']/med['candidate'],'samples':{'baseline':groups['baseline'],'candidate':groups['candidate']},'comparators':comparisons,'speedup_vs_best_single':min(med['mask'],med['unroll'])/med['candidate']})
advance=all(x['speedup_vs_best_single']>=0.95 for x in results) and any(x['n'] in [2560,6144] and x['speedup_vs_best_single']>=1.02 and all(v['paired_wins']>=9 for v in x['comparators'].values()) for x in results)
summary={'dot_checks':checks,'dot_correctness':exact,'microbench_rounds':rounds,'microbench':results,'advance_to_model':advance,'assembly_statistics':json.loads((r/'dot-assembly-stats.json').read_text()),'interpretation':'Four actual-library variants match original bitwise for262432 direct-dot cases each.12 cyclic-order rounds; each variant occupies each position3times,CPU0/membind0 resident inputs. Incremental gate uses best single-change kernel:>=2% at2560or6144 with>=9/12wins against each single change, no size below0.95x best single. Kernel results are not model scores. '+('Incremental gate passed; independent fixed PPL and full original/combined/original model tests pending.' if advance else 'Incremental gate failed; no model PPL/PP/TG run, do not promote.')}
(r/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
