import json
import sys
from pathlib import Path

root = Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo')
for parent in sys.argv[1:]:
    run = root/'results'/parent
    assert (run/'job.status').read_text().startswith('READY_FOR_PAIRED_BENCH')
    manifest = json.loads((run/'manifest.json').read_text())
    assert all(x['ppl']['status']=='PASS' for x in manifest['builds'].values())
    level = manifest['opt_level']
    for order in ['control-first','pgo-first']:
        spec = {'script':str(root/'paired_bench.lsf'),'kind':'同节点完整对照',
            'purpose':'Intel Classic O'+level+' PGO完整对照，顺序='+order+'，产物来自'+parent,
            'config':'Gold6148单节点40 slots；推理38线程；官方源码d812350；Intel Classic2021.9，O'+level+'，precise/no-ftz/CORE-AVX512/qsimd-honor-fp-model，OpenMP=ON,BLAS=OFF，未启用-ipo；同节点先后各自固定PPL t/tb38,c512,chunks2,b512,ub256,f16KV,ngl0,NUMA=distribute,no-warmup,timeout590s；PASS后PP p2048/n0及TG p0/n128/d2048，各r10，t38,b2048,ub512,f16KV,ngl0,NUMA=distribute，close/cores；无VTune/OS采样；顺序='+order,
            'baseline':'作业内同一O级无PGO control（同节点顺序对照）','baseline_case':'compiler-control_{job_id}','case_prefix':'compiler',
            'environment':{'PGO_PARENT_JOB':parent,'PGO_ORDER':order},'lsf_args':['-J','qwen38_O'+level+'_'+order],
            'note':'每个构建独立PPL门槛，无共享PPL。PGO训练未使用WikiText输入，不计入测速；先核对全部产物哈希。正反顺序分属不同节点，保留节点/缓存/顺序局限；只算开发自测分数。分析前须检查PGO反馈日志，确认热点函数有匹配的训练计数。'}
        path = root/('paired_'+parent+'_'+order+'.json')
        path.write_text(json.dumps(spec,ensure_ascii=False,indent=2))
        print(path)
