import json
import statistics
import subprocess
import sys
from pathlib import Path

r=Path(sys.argv[1]);names=['baseline','mask','unroll','combined'];samples=[];reference_hashes={}
paths={
 'baseline':'/work/apac2602/qwen38-cpu/llama.cpp/build/bin',
 'mask':'/work/apac2602/qwen38-cpu/optimization/20261019-q5-mask/sources/q5-mask-4338563/build/bin',
 'unroll':'/work/apac2602/qwen38-cpu/optimization/20261020-q5-unroll/sources/q5-unroll4-4340602/build/bin',
 'combined':'/work/apac2602/qwen38-cpu/optimization/20261020-q5-combined/sources/q5-mask-unroll4-4340624/build/bin'}
def key(c):return (c['n'],c['threads'],c['mode'])
for repeat in range(12):
    offset=repeat%4;order=names[offset:]+names[:offset]
    for name in order:
        p=subprocess.run([str(r/('stream-'+name)),paths[name]],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=600)
        (r/('raw-'+str(repeat)+'-'+name+'.json')).write_text(p.stdout)
        (r/('raw-'+str(repeat)+'-'+name+'.log')).write_text(p.stderr)
        assert p.returncode==0,(name,p.returncode,p.stderr)
        x=json.loads(p.stdout);assert len(x['cases'])==12
        for c in x['cases']:
            k=key(c);assert c['ns_per_dot']>0 and len(c['cpu_ids'])==c['threads']
            h=c['checked_output_hashes'];assert len(h)==c['threads']
            if k not in reference_hashes:
                assert name=='baseline';reference_hashes[k]=h
            assert h==reference_hashes[k],(name,k,'output hash mismatch')
        samples.append({'round':repeat,'name':name,'order':order,'result':x})
        (r/'stream-raw-samples.json').write_text(json.dumps(samples,indent=2))
results=[]
for n in [2560,6144]:
    for threads in [1,19,38]:
        for mode in ['resident4rows','stream512MiB']:
            k=(n,threads,mode);groups={}
            for name in names:
                cases=[next(c for c in row['result']['cases'] if key(c)==k) for row in samples if row['name']==name]
                ns=[c['ns_per_dot'] for c in cases]
                groups[name]={'median_ns_per_dot':statistics.median(ns),'all_ns':ns,'all_effective_weight_GBps':[c['effective_weight_GBps'] for c in cases],'weight_bytes':cases[0]['weight_bytes'],'cpu_ids':cases[0]['cpu_ids']}
            original=groups['baseline']['median_ns_per_dot']
            change={name:original/groups[name]['median_ns_per_dot']-1 for name in names[1:]}
            results.append({'n':n,'threads':threads,'mode':mode,'variants':groups,'throughput_change_vs_original':change})
s={'streaming_microbench':results,'rounds':12,'variants':names,'checks':'All variants and all repetitions match original full-row output hashes for every generated row, per worker; prior262432-case bitwise tests remain the primary kernel correctness evidence.','interpretation':'Q5 actual-library resident versus512MiB streaming diagnostic,1/19/38OpenMP threads,12cyclic four-variant rounds. Each worker first-touches its own weights and Q8 inputs. Timings include one OpenMP fork/join per calibrated measurement, target~200ms, with all samples retained. effective_weight_GBps is derived logical Q5 bytes/time, not measured DRAM bandwidth. OMP close/cores is explicit; synthetic access and scheduling differ from full GGML graph. No model loaded, no model PPL/PP/TG or Score; results only diagnose compute/memory/scaling sensitivity.'}
(r/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s))
