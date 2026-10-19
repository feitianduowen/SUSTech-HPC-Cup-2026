import csv
import json
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1])
checks = {}
times = []
for directory in sorted(root.iterdir()):
    if not directory.is_dir() or not (directory/'correctness.json').exists():
        continue
    name = directory.name
    check = json.loads((directory/'correctness.json').read_text())
    checks[name] = check
    if check['status'] != 'PASS' or check['bit_mismatches']:
        raise ValueError('Failed correctness: '+name)
    rows = list(csv.DictReader((directory/'kernel-times.csv').open()))
    for shape in [80,192]:
        for mode in ['resident','stream']:
            selected = [r for r in rows if int(r['shape_blocks']) == shape and r['mode'] == mode]
            pairs = []
            for trial in range(10):
                group = {r['kernel']:float(r['ns_per_dot']) for r in selected if int(r['round']) == trial}
                if set(group) != {'baseline',name}:
                    raise ValueError('Missing paired sample: '+name)
                pairs.append(group['baseline']/group[name]-1)
            item = {'variant':name,'blocks':shape,'mode':mode,'paired_samples':10,'paired_median_speedup':statistics.median(pairs),'all_paired_speedups':pairs}
            for kernel in ['baseline',name]:
                samples = [float(r['ns_per_dot']) for r in selected if r['kernel'] == kernel]
                item[kernel] = {'ns_median':statistics.median(samples),'ns_mean':statistics.mean(samples),'cv':statistics.stdev(samples)/statistics.mean(samples),'all_ns':samples}
            times.append(item)
summary = {'checks':checks,'kernel_times':times,'scope':'Seven configurations sequential on one allocated Gold6148 host; each uses the production FP16 table and ten alternating AB/BA pairs against the actual production library on CPU0/membind0. Not fixed model PP/TG; no PPL or Score. Original function control measures source-excerpt compilation differences.'}
(root/'summary.json').write_text(json.dumps(summary,indent=2))
for item in times:
    print('%s nb%d %s %+.2f%%' % (item['variant'],item['blocks'],item['mode'],100*item['paired_median_speedup']))
