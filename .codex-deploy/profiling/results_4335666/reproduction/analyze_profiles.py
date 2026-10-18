#!/usr/bin/env python3
"""Validate fixed workloads and summarize independently collected OS samples."""
import hashlib, json, statistics, sys
from pathlib import Path

root = Path(sys.argv[1])
result = {}
for name in ['pp2048', 'tg128_d2048']:
    d = root / name
    bench = json.loads((d / 'bench.json').read_text())
    assert len(bench) == 1, bench
    b = bench[0]
    assert b['n_threads'] == 38 and b['n_batch'] == 2048 and b['n_ubatch'] == 512
    assert b['n_gpu_layers'] == 0
    assert b['type_k'] == 'f16' and b['type_v'] == 'f16'
    assert len(b['samples_ns']) == 10
    assert b['n_prompt'] == (2048 if name == 'pp2048' else 0)
    assert b['n_gen'] == (0 if name == 'pp2048' else 128)
    assert b.get('n_depth', 0) == (0 if name == 'pp2048' else 2048)
    resume = json.loads((d / 'resume.json').read_text())
    assert resume['returncode'] == 0
    assert (d / 'target.exit').read_text().strip() == '0'
    assert (d / 'collector.exit').read_text().strip() == '0'
    events = [json.loads(x) for x in (d / 'events.jsonl').read_text().splitlines()]
    marker = 'prompt run 1/10' if name == 'pp2048' else 'generation run 1/10'
    first = next(e for e in events if marker in e['text'])
    rows = [json.loads(x) for x in (d / 'system.jsonl').read_text().splitlines()]
    prefix = 'prompt run ' if name == 'pp2048' else 'generation run '
    measured = [e for e in events if prefix in e['text'] and 'warmup' not in e['text']]
    bench_end = measured[-1]['time'] + b['samples_ns'][-1] / 1e9
    roi = [r for r in rows if resume['completed'] <= r['time'] <= bench_end]
    active = [(v['cpu_seconds']-u['cpu_seconds'])/(v['time']-u['time']) for u,v in zip(roi,roi[1:])]
    rss = [int(r['status']['VmRSS'].split()[0])/1024/1024 for r in roi]
    weighted = ((roi[-1]['cpu_seconds']-roi[0]['cpu_seconds'])/(roi[-1]['time']-roi[0]['time'])) if len(roi)>1 else None
    result[name] = {
        'workload_valid': True, 'bench': b,
        'roi_marker_time': first['time'],
        'estimated_measurement_end_time': bench_end,
        'resume_delay_seconds': resume['completed']-first['time'],
        'roi_os_samples': len(roi),
        'os_average_active_cpu_cores': weighted,
        'os_max_active_cpu_cores': max(active) if active else None,
        'rss_gib_min': min(rss) if rss else None,
        'rss_gib_max': max(rss) if rss else None,
        'last_numa_gib': {k:v/1024/1024 for k,v in roi[-1]['numa_kb'].items()} if roi else {},
        'roi_minor_faults': roi[-1]['minor_faults']-roi[0]['minor_faults'] if len(roi)>1 else None,
        'roi_major_faults': roi[-1]['major_faults']-roi[0]['major_faults'] if len(roi)>1 else None,
        'max_observed_threads': max(int(r['status']['Threads']) for r in rows),
        'profiled_measurement_not_official_score': True,
    }
(root / 'analysis.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
