import csv
import json
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1])
checks = {}
for name in ['correctness.json','fallback-correctness.json','library-correctness.json']:
    if (root/name).is_file():
        checks[name]=json.loads((root/name).read_text())
        if checks[name]['status']!='PASS' or checks[name]['bit_mismatches']:
            raise ValueError('Numerical check failed: '+name)
times = []
path = root/'kernel-times.csv'
if path.exists():
    rows = list(csv.DictReader(path.open()))
    for shape in [80,192]:
        for mode in ['resident','stream']:
            selected=[r for r in rows if int(r['shape_blocks'])==shape and r['mode']==mode]
            pairs=[]
            for trial in range(10):
                group={r['kernel']:float(r['ns_per_dot']) for r in selected if int(r['round'])==trial}
                if len(group)!=2: raise ValueError('Missing paired sample')
                pairs.append(group['baseline']/group['avx512-ordered']-1)
            result={'blocks':shape,'mode':mode,'paired_samples':10,'paired_median_speedup':statistics.median(pairs),'all_paired_speedups':pairs}
            for kernel in ['baseline','avx512-ordered']:
                samples=[float(r['ns_per_dot']) for r in selected if r['kernel']==kernel]
                result[kernel]={'ns_median':statistics.median(samples),'ns_mean':statistics.mean(samples),'cv':statistics.stdev(samples)/statistics.mean(samples),'all_ns':samples}
            times.append(result)
summary={'checks':checks,'kernel_times':times,'scope':'Single-core resident/256MiB stream diagnostics, alternating AB/BA; kernel excerpt or actual-library path is recorded in stderr. Not official PP/TG and no model Score.'}
(root/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
