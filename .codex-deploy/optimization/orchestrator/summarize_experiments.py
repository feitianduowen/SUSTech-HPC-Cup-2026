import json, math, sys
from pathlib import Path

root = Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
paths = [Path('/work/apac2602/qwen38-cpu/llama_bench_results_'+jid) for jid in ['4335768','4335769']]+sorted((root/'results').iterdir())
rows = []
for d in paths:
    if not d.is_dir():
        continue
    if not any((d/f).exists() for f in ['perplexity_result.json','pp2048.json','tg128_d2048.json']):
        continue
    row = {'name': d.name, 'path': str(d), 'ppl_status': 'pending', 'ppl': None, 'pp': None, 'tg': None, 'score': None}
    if (d/'perplexity_result.json').exists():
        p = json.loads((d/'perplexity_result.json').read_text())
        row['ppl_status'] = p.get('status')
        row['ppl'] = p.get('ppl',p.get('optimized_ppl'))
    for key, filename, workload in [('pp','pp2048.json',(2048,0,0)),('tg','tg128_d2048.json',(0,128,2048))]:
        try:
            data = json.loads((d/filename).read_text())
        except (FileNotFoundError,ValueError):
            continue
        assert len(data)==1
        b = data[0]
        assert (b['n_prompt'],b['n_gen'],b['n_depth'])==workload
        assert (b['n_threads'],b['n_batch'],b['n_ubatch'],b['n_gpu_layers'],b['type_k'],b['type_v'])==(38,2048,512,0,'f16','f16')
        assert len(b['samples_ns'])==10 and len(b['samples_ts'])==10
        row[key] = b['avg_ts']
        row[key+'_std'] = b['stddev_ts']
        row[key+'_cv'] = b['stddev_ts']/b['avg_ts']*100
        row[key+'_samples'] = b['samples_ts']
        row[key+'_data'] = b
    if row['ppl_status']=='PASS' and row['pp'] and row['tg'] and not row['name'].startswith('diagnostic_'):
        row['score'] = 100*math.sqrt(row['pp']/46.929024*row['tg']/3.295524)
    rows.append(row)
(root/'results/experiment_summary.json').write_text(json.dumps(rows,indent=2))
if '--json' in sys.argv:
    print(json.dumps(rows,indent=2))
else:
    for r in rows:
        print('%-34s PPL=%s/%s PP=%s TG=%s Score=%s' % (r['name'],r['ppl_status'],r['ppl'],r['pp'],r['tg'],round(r['score'],3) if r['score'] else '-'))
