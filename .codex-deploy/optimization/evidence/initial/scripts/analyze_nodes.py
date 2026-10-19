import csv, json, sys
from pathlib import Path
from collections import defaultdict

root = Path(sys.argv[1])
result = {}
for phase in ['pp','tg']:
    ops = defaultdict(lambda:dict(nodes=0,compute_critical_us=0,boundary_wait_cpu_us=0,arrival_spread_us=0,compute_cpu_us=0,nominal_serial_nodes=0))
    graphs=[]
    for path in sorted(root.glob(phase+'_nodes.g*.csv')):
        rows=list(csv.DictReader(path.open()))
        graphs.append({'file':path.name,'rows':len(rows),'first_shapes':[{'op':r['op'],'dst':r['dst_shape']} for r in rows[:5]]})
        for r in rows:
            assert int(r['recorded_threads'])==int(r['pool_threads'])==38
            a=ops[r['op']]
            a['nodes']+=1
            a['compute_critical_us']+=int(r['compute_max_us'])
            a['boundary_wait_cpu_us']+=int(r['boundary_wait_sum_us'])
            a['arrival_spread_us']+=int(r['arrival_spread_us'])
            a['compute_cpu_us']+=int(r['compute_sum_us'])
            a['nominal_serial_nodes']+=int(r['n_tasks_nominal'])==1
    critical=sorted([{'op':op,**a} for op,a in ops.items()],key=lambda a:a['compute_critical_us'],reverse=True)
    waiting=sorted([{'op':op,**a} for op,a in ops.items()],key=lambda a:a['boundary_wait_cpu_us'],reverse=True)
    shapes=[]
    path=root/(phase+'_shapes.csv')
    if path.exists():
        shapes=list(csv.DictReader(path.open()))
        shapes.sort(key=lambda x:int(x['total_tiles'])*int(x['k_blocks']),reverse=True)
    result[phase]={'graphs':graphs,'operators_by_critical_compute':critical,'operators_by_boundary_wait':waiting,'tinyblas_shapes_by_tiles_times_k':shapes}
(root/'node_analysis.json').write_text(json.dumps(result,indent=2))
for phase, data in result.items():
    print(phase,'graphs',len(data['graphs']))
    print('critical:',data['operators_by_critical_compute'][:6])
    print('waiting:',data['operators_by_boundary_wait'][:6])
    print('shapes:',data['tinyblas_shapes_by_tiles_times_k'][:4])
