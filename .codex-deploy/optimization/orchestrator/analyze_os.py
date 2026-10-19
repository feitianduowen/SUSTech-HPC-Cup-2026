import json
import statistics
from pathlib import Path

root = Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1/results')
all_results = {}
for path in sorted(root.glob('*/os.jsonl')):
    phases = {}
    previous = {}
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        cmd = row['command']
        workload = 'tg' if cmd[cmd.index('-n')+1] == '128' else 'pp'
        parts=cmd[0].split('/')
        variant=parts[parts.index('sources')+1] if 'sources' in parts else 'baseline'
        phase=variant+'/'+workload
        data = phases.setdefault(phase, dict(intervals=0, active_cores=[], minor_faults=0, major_faults=0))
        old = previous.get(row['pid'])
        if old:
            elapsed = row['time']-old['time']
            if elapsed > 0:
                data['active_cores'].append((row['cpu_seconds']-old['cpu_seconds'])/elapsed)
                data['intervals'] += 1
                for field in ['minor_faults','major_faults']:
                    data[field] += row[field]-old[field]
        previous[row['pid']] = row
        data['last_rss_kb'] = int(row['status']['VmRSS'].split()[0])
        data['last_numa_kb'] = row['numa_kb']
        if data['last_rss_kb'] > data.get('peak_rss_kb',0):
            data['peak_rss_kb'] = data['last_rss_kb']
            data['numa_at_peak_rss_kb'] = row['numa_kb']
        data['thread_count'] = int(row['status']['Threads'])
    for phase, data in phases.items():
        values = data.pop('active_cores')
        data['median_active_cores_including_spin'] = statistics.median(values) if values else None
        data['mean_active_cores_including_spin'] = statistics.mean(values) if values else None
    all_results[path.parent.name] = phases
(root/'os_summary.json').write_text(json.dumps(all_results,indent=2))
print(json.dumps(all_results,indent=2))
