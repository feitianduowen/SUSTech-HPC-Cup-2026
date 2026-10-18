#!/usr/bin/env python3
import json, sys, time
from pathlib import Path
root = Path(sys.argv[1])
for name in ['pp2048', 'tg128_d2048']:
    d = root / name
    if not d.exists():
        continue
    events = [json.loads(x) for x in (d / 'events.jsonl').read_text().splitlines()] if (d/'events.jsonl').exists() else []
    rows = [json.loads(x) for x in (d / 'system.jsonl').read_text().splitlines()] if (d/'system.jsonl').exists() else []
    info = {'case': name, 'latest_event': events[-1] if events else None}
    if (d/'resume.json').exists():
        resume = json.loads((d/'resume.json').read_text())
        roi = [r for r in rows if r['time'] >= resume['completed']]
        if len(roi)>1:
            info['roi_cpu_cores']=(roi[-1]['cpu_seconds']-roi[0]['cpu_seconds'])/(roi[-1]['time']-roi[0]['time'])
            info['roi_elapsed_seconds']=roi[-1]['time']-roi[0]['time']
    if rows:
        info['sample_age_seconds'] = time.time()-rows[-1]['time']
        info['rss_gib'] = int(rows[-1]['status']['VmRSS'].split()[0])/1024/1024
        info['numa_gib']={k:v/1024/1024 for k,v in rows[-1]['numa_kb'].items()}
    for filename in ['target.exit','collector.exit']:
        if (d/filename).exists():
            info[filename]=(d/filename).read_text().strip()
    print(json.dumps(info))
