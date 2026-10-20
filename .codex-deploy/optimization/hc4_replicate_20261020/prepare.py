import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
prior=here.parent/'hc4_post_v2_20261020'
remote='/work/apac2602/qwen38-cpu/optimization/20261020-hc4-replicate'
verified=json.loads((prior/'completed_verification.json').read_text(encoding='utf-8'))
first=next(r for r in verified if r['job_id']=='4340916')
assert first['A1_A2_binaries_same'] and first['B1_B2_binaries_same'] and first['A_B_distinct']
candidate='/work/apac2602/qwen38-cpu/optimization/20261020-hc4-post-v2/sources/hc4-post-v2-4340916'
frozen={
    'compiler':'Intel Classic2021.9 icc/icpc O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model',
    'source_sha256':first['source_sha256'],
    'source_file':candidate+'/ggml/src/ggml-cpu/ops.cpp',
    'prior_actual_library_checks':{'job_id':'4340916','cases':972,'values':42341535,'repetitions':3,'threads':[1,3,38],'bit_mismatches':0,'reused_evidence_not_rerun':True},
    'builds':{
        'A':{'root':'/work/apac2602/qwen38-cpu/llama.cpp','files':dict((name,sha) for sha,name in first['baseline_sha256'])},
        'B':{'root':candidate,'files':dict((name,sha) for sha,name in first['candidate_sha256'])}}}
(here/'frozen_builds.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8',newline='\n')
(here/'ppl_gate.lsf').write_text((prior/'ppl_gate.lsf').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
for order in ['ABABA','BABAB']:
    prefix='confirm-hc4-rep-'+order.lower()
    names=['A1','B1','A2','B2','A3'] if order=='ABABA' else ['B1','A1','B2','A2','B3']
    mappings={prefix+'-'+n+'_{job_id}':None if n.startswith('A') else prefix+'-'+('A1' if n=='B1' else 'A2')+'_{job_id}' for n in names}
    spec={'script':remote+'/repeat.lsf','kind':'同节点完整对照',
          'purpose':'HC-post v2独立复现及漂移检查：'+order+'五轮交错，在排除原r13n08/r13n45的其他空闲Gold6148节点复用同一已验证Intel候选构建；后段'+('A2-B2-A3' if order=='ABABA' else 'B2-A2-B3')+'双侧对照，确认约5.5% PP与0.5%-1.8% TG收益是否复现。',
          'config':'Intel Classic2021.9 icc/icpc O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；OpenMP ON，BLAS OFF；每节点40物理核40slots，推理38线程close/cores。A=原版部署；B=4340916 HC-post v2构建，逐bit差分972组/42341535值已通过。冻结两构建eval二进制/动态库SHA及B源码SHA，每轮前复核并检查ldd。顺序'+order+'；每case独立PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup 590s ±5%；PP2048与TG128d2048各r10，t38 b2048ub512 f16KV ngl0 NUMA distribute。无采样；保留全部首轮/低速样本。',
          'baseline':'本作业同节点Intel原版A1/A2'+('/A3' if order=='ABABA' else '')+'；B1/A1，后段B2/A2'+('，补充B2/A3双侧分析' if order=='ABABA' else '，补充B3/A2双侧分析')+'；4340916/4340917为前期不同节点复测依据，不作直接速度除数',
          'environment':{'PAIR_ORDER':order},'lsf_args':['-J','qwen38_hc4_rep_'+order.lower()],
          'case_prefix':prefix,'measurement_baselines':mappings,'comparison_scope':'same-node',
          'ppl_scope':'每case独立重新执行固定PPL；算子正确性复用4340916既有证据，不声称重跑',
          'late_bracket':['A2','B2','A3'] if order=='ABABA' else ['B2','A2','B3'],
          'note':'此前ABBA/BAAB均完成8次PPL=2.7767和160测速样本，后段PP +5.595%/+5.432%，TG +1.784%/+0.504%，几何均值 +3.672%/+2.939%；首对PP +60.45%/-32.74%明显受顺序影响。当前为独立复现和漂移控制，不修改源码或部署；保留五轮全部样本，不把后段对照或算子收益称为正式成绩。'}
    (here/('submission_'+order.lower()+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'remote':remote,'frozen_files':{k:len(v['files']) for k,v in frozen['builds'].items()},'ppl_gate_sha256':hashlib.sha256((here/'ppl_gate.lsf').read_bytes()).hexdigest()}))
