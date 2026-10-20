import json
import statistics
from pathlib import Path

here=Path(__file__).resolve().parent
bundle=json.loads((here/'completed_telemetry.json').read_text(encoding='utf-8'))
def counters(text):
    result={}
    for line in (text or '').splitlines():
        p=line.replace(':','').split()
        if len(p)>=2:
            try: result[p[0]]=int(p[1])
            except ValueError: pass
    return result
summaries={}
for jid,files in bundle.items():
    assert all(s.endswith(': OK') for s in files['hash-check.txt'].splitlines())
    phases=[]
    for name,text in files.items():
        if not name.endswith('.observations.jsonl'): continue
        rows=[json.loads(line) for line in text.splitlines()]
        result=json.loads(files[name.replace('.observations.jsonl','.result.json')])
        assert result['returncode']==0 and not result['timed_out']
        peak_model_kb=max(sum(r.get('numa',{}).get('model_kb',{}).values()) for r in rows)
        loaded=[r for r in rows if peak_model_kb and sum(r.get('numa',{}).get('model_kb',{}).values())>=0.9*peak_model_kb]
        compute=[r for r in rows if counters(r.get('status')).get('Threads')==38]
        first,last=rows[0],rows[-1]
        node0=[]
        for row in loaded:
            n=row['numa']['model_kb']; total=sum(n.values())
            node0.append(100*n.get('N0',0)/total)
        vmfirst=counters(first.get('host_vmstat')); vmlast=counters(last.get('host_vmstat'))
        entry={'phase':name.split('.')[0], 'result':result,'samples':len(rows),
               'observation_cost_total_s':sum(r.get('sampling_seconds',0) for r in rows),
               'observation_cost_max_s':max(r.get('sampling_seconds',0) for r in rows),
               'last_io':counters(last.get('io')),'first_loaded_model_kb':loaded[0]['numa']['model_kb'] if loaded else None,
               'last_model_kb':last.get('numa',{}).get('model_kb'),
               'peak_model_kb':peak_model_kb,
               'compute_rss_kb_min_max': [min(counters(r.get('status')).get('VmRSS',0) for r in compute), max(counters(r.get('status')).get('VmRSS',0) for r in compute)] if compute else None,
               'compute_main_thread_voluntary_context_switches_delta': counters(compute[-1].get('status')).get('voluntary_ctxt_switches',0)-counters(compute[0].get('status')).get('voluntary_ctxt_switches',0) if compute else None,
               'model_node0_pct_min_max':[min(node0),max(node0)] if node0 else None,
               'host_counter_deltas':{k:vmlast[k]-vmfirst[k] for k in vmlast if k in vmfirst},
               'available_kb_min_max':[min(counters(r['host_meminfo']).get('MemAvailable',0) for r in rows),max(counters(r['host_meminfo']).get('MemAvailable',0) for r in rows)]}
        phases.append(entry)
    phases.sort(key=lambda p:p['result']['started_unix'])
    summaries[jid]=phases
    for p in phases:
        print(json.dumps({'job_id':jid,'phase':p['phase'],'seconds':round(p['result']['wall_seconds'],1),'majflt':p['result']['major_faults'],'read_GiB':p['last_io'].get('read_bytes',0)/1024**3,'model_start_GiB':{k:round(v/1024**2,2) for k,v in (p['first_loaded_model_kb'] or {}).items()},'model_end_GiB':{k:round(v/1024**2,2) for k,v in (p['last_model_kb'] or {}).items()},'node0_pct_range':p['model_node0_pct_min_max'],'host_migrated':p['host_counter_deltas'].get('numa_pages_migrated'),'min_available_GiB':round(p['available_kb_min_max'][0]/1024**2,2),'sampling_max_s':round(p['observation_cost_max_s'],3)}))
(here/'telemetry_summary.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
