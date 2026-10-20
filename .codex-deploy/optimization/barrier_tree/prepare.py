import json
from pathlib import Path

here=Path(__file__).resolve().parent
prior=here.parent/'kmp_infinite'
remote='/work/apac2602/qwen38-cpu/optimization/20261020-barrier-tree'
(here/'runtime_probe.c').write_bytes((prior/'runtime_probe.c').read_bytes())
gate=(prior/'evaluate.lsf').read_text(encoding='utf-8')
gate=gate.replace('unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET','unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET KMP_PLAIN_BARRIER_PATTERN KMP_FORKJOIN_BARRIER_PATTERN')
gate=gate.replace('A) export KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE;;','A) export KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE KMP_PLAIN_BARRIER_PATTERN=hyper,hyper KMP_FORKJOIN_BARRIER_PATTERN=hyper,hyper;;')
gate=gate.replace('B) export KMP_BLOCKTIME=infinite OMP_WAIT_POLICY=ACTIVE;;','B) export KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE KMP_PLAIN_BARRIER_PATTERN=tree,tree KMP_FORKJOIN_BARRIER_PATTERN=hyper,hyper;;')
(here/'evaluate.lsf').write_bytes(gate.encode('utf-8'))
script=(prior/'runtime_pair.lsf').read_text(encoding='utf-8')
script=script.replace('20261020-kmp-infinite','20261020-barrier-tree').replace('qwen38_kmp_infinite','qwen38_barrier_tree').replace('%J.kmp_infinite.','%J.barrier_tree.')
script=script.replace('PROF_DIR KMP_SETTINGS','PROF_DIR KMP_SETTINGS KMP_PLAIN_BARRIER_PATTERN KMP_FORKJOIN_BARRIER_PATTERN')
start=script.index('for value in 200 infinite; do')
end=script.index('\nna=0; nb=0',start)
replacement='''for value in hyper tree; do
    KMP_PLAIN_BARRIER_PATTERN="$value,$value" KMP_FORKJOIN_BARRIER_PATTERN=hyper,hyper KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE KMP_SETTINGS=TRUE "$OUT/runtime-probe" > "$OUT/runtime-$value.log" 2>&1
done
python3 - "$OUT" <<'PY'
import json,re,sys
from pathlib import Path
d=Path(sys.argv[1]); result={}
for mode in ['hyper','tree']:
    text=(d/('runtime-'+mode+'.log')).read_text()
    assert 'THREADS=38' in text
    def setting(name):
        values=re.findall(name+r'\\s*=\\s*([^\\n]+)',text)
        assert values,name
        return values[-1].strip().strip(chr(39)+chr(34))
    assert setting('KMP_PLAIN_BARRIER_PATTERN')==mode+','+mode
    assert setting('KMP_FORKJOIN_BARRIER_PATTERN')=='hyper,hyper'
    assert setting('KMP_BLOCKTIME')=='200'
    result[mode]={'plain_pattern':setting('KMP_PLAIN_BARRIER_PATTERN'),'forkjoin_pattern':setting('KMP_FORKJOIN_BARRIER_PATTERN'),'KMP_BLOCKTIME':200,'OMP_WAIT_POLICY':'ACTIVE','threads':38}
(d/'runtime-validation.json').write_text(json.dumps(result,indent=2))
PY
'''
script=script[:start]+replacement+script[end:]
(here/'runtime_pair.lsf').write_bytes(script.encode('utf-8'))
for order in ['ABBA','BAAB']:
    spec=json.loads((prior/(order+'.json')).read_text(encoding='utf-8'))
    old=spec['case_prefix']; prefix='confirm-barrier-tree-'+order.lower()
    mapping={k.replace(old,prefix):(v.replace(old,prefix) if v else None) for k,v in spec['measurement_baselines'].items()}
    spec.update(script=remote+'/runtime_pair.lsf',purpose='针对约30% barrier自旋CPU时间：普通barrier hyper/tree单变量无采样对照，顺序'+order,
                config='同一SHA核验Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model原版，OpenMP/tinyBLAS ON、BLAS/GPU OFF；hg_6148单节点40slots/Gold6148，38线程close/cores。唯一测速变量：KMP_PLAIN_BARRIER_PATTERN A=hyper,hyper，B=tree,tree；两者KMP_FORKJOIN_BARRIER_PATTERN=hyper,hyper，KMP_BLOCKTIME200、OMP_WAIT_POLICY ACTIVE、OMP_DYNAMIC FALSE。Intel编译的小程序先验证两种plain模式真实生效并确认forkjoin和blocktime不变。四轮'+order+'，每轮独立固定默认环境PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup timeout590s，±5%；通过后测速PP2048及TG128d2048各r10 t38 b2048ub512 f16KV ngl0 NUMA distribute。无VTune/OS采样。',
                baseline='本作业hyper普通barrier A1/A2；tree B1对应A1，B2对应A2，同节点配对；不与同时运行的infinite实验混用',
                case_prefix=prefix,baseline_case=prefix+'-A1_{job_id}',measurement_baselines=mapping,
                lsf_args=['-J','qwen38_barrier_tree_'+order],
                note='独立检验普通barrier算法，等待时长固定200ms，forkjoin算法固定hyper，不组合infinite干预。上一轮VTune自旋比例前后接近30%，并非首次慢速唯一原因；此次面向潜在稳定开销。保留所有四轮和低速样本，不挑最快轮。首次状态/顺序/跨节点/时段混杂仍需逐项分析。正式采用运行时参数前按赛题申报；开发自测非正式成绩。源码、模型和生产环境不改。')
    (here/(order+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared plain-barrier hyper/tree ABBA and BAAB; waits fixed at 200ms')
