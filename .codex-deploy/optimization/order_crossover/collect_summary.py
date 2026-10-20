import json
import re
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261020-order-crossover')
def fields(text):
    result={}
    for line in (text or '').splitlines():
        parts=line.replace(':','').split()
        if len(parts)>=2:
            try: result[parts[0]]=int(parts[1])
            except ValueError: result[parts[0]]=parts[1]
    return result

out={}
for jid in ['4339778','4339779']:
    run=root/'results'/jid
    sha=(run/'hash-check.txt').read_text()
    assert all(x.endswith(': OK') for x in sha.splitlines())
    ppl=json.loads((run/'ppl/perplexity_result.json').read_text())
    assert ppl['status']=='PASS' and ppl['ppl']==2.7767
    cases=[]
    for case in sorted(run.glob('[0-9][0-9]_*')):
        meta=json.loads((case/'result.json').read_text())
        phase=meta['workload']
        x=json.loads((case/(phase+'.json')).read_text())[0]
        result=json.loads((case/(phase+'.result.json')).read_text())
        assert result['returncode']==0 and not result['timed_out']
        assert len(x['samples_ts'])==len(x['samples_ns'])==10
        rows=[json.loads(s) for s in (case/(phase+'.observations.jsonl')).read_text().splitlines()]
        compute=[r for r in rows if len(r.get('threads',[]))==38]
        sched=[]
        affinity=[]
        wchan={}
        for row in compute:
            aff={}
            for t in row['threads']:
                f=fields(t.get('status')); key=f.get('Cpus_allowed_list','unknown')
                aff[key]=aff.get(key,0)+1
                w=(t.get('wchan') or '').strip();wchan[w]=wchan.get(w,0)+1
                try: sched.append([int(v) for v in t['schedstat_raw'].split()])
                except (TypeError,ValueError): pass
            if aff not in affinity: affinity.append(aff)
        deltas={'runtime_ns':0,'runnable_wait_ns':0,'timeslices':0,'voluntary_context_switches':0,'involuntary_context_switches':0}
        first_seen={};last_seen={}
        for row in compute:
            for t in row['threads']:
                key=(t['tid'],t['start_ticks']);first_seen.setdefault(key,t);last_seen[key]=t
        for key,a in first_seen.items():
            b=last_seen[key]
            try:
                v1=list(map(int,a['schedstat_raw'].split()));v2=list(map(int,b['schedstat_raw'].split()))
                if len(v1)==len(v2)==3:
                    for i,name in enumerate(['runtime_ns','runnable_wait_ns','timeslices']): deltas[name]+=max(0,v2[i]-v1[i])
            except (TypeError,ValueError): pass
            fa,fb=fields(a['status']),fields(b['status'])
            for name,stat in [('voluntary_context_switches','voluntary_ctxt_switches'),('involuntary_context_switches','nonvoluntary_ctxt_switches')]:
                deltas[name]+=max(0,fb.get(stat,0)-fa.get(stat,0))
        stderr=(case/(phase+'.stderr.log')).read_text(errors='replace')
        loads=re.findall(r'load time\s*=\s*([0-9.]+) ms',stderr)
        vm0=fields(rows[0].get('host_vmstat'));vm1=fields(rows[-1].get('host_vmstat'))
        c={'directory':case.name,'meta':meta,'avg_ts':x['avg_ts'],'cv_percent':100*x['stddev_ts']/x['avg_ts'],'samples_ts':x['samples_ts'],
           'process_result':result,'sampling_count':len(rows),'sampling_cost_seconds':sum(r.get('sampling_seconds',0) for r in rows),
           'sched_schedstats_values':sorted(set(str(r.get('host_sched_schedstats')).strip() for r in rows)),
           'schedstat_any_nonzero':any(any(v) for v in sched),'thread_affinity_snapshots_unique':affinity,
           'wchan_snapshot_counts':wchan,'thread_deltas_over_observed_lifetimes':deltas,
           'first_compute_model_kb':compute[0].get('numa',{}).get('model_kb') if compute else None,
           'last_compute_model_kb':compute[-1].get('numa',{}).get('model_kb') if compute else None,
           'last_io':fields(rows[-1].get('io')),'reported_load_ms':float(loads[-1]) if loads else None,
           'host_numa_pages_migrated_delta':vm1.get('numa_pages_migrated',0)-vm0.get('numa_pages_migrated',0)}
        cases.append(c)
    assert len(cases)==12
    blocks=[]
    for n in range(1,5):
        group={c['meta']['role']:c for c in cases if c['meta']['block']==n}
        a,b=group['anchor'],group['probe']
        blocks.append({'block':n,'order':a['meta']['order'],'anchor_pp':a['avg_ts'],'probe_pp':b['avg_ts'],
                       'probe_change_percent':100*(b['avg_ts']/a['avg_ts']-1),'anchor_cv_percent':a['cv_percent'],'probe_cv_percent':b['cv_percent']})
    out[jid]={'status':(run/'job.status').read_text(),'ppl':ppl,'blocks':blocks,'cases':cases,'sha_all_ok':True}
    print(json.dumps({'job_id':jid,'blocks':blocks,'schedstat_any_nonzero':any(c['schedstat_any_nonzero'] for c in cases)}))
(root/'completed_summary.json').write_text(json.dumps(out,indent=2))
