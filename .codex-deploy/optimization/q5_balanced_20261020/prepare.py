import json
from pathlib import Path

r=Path(__file__).resolve().parent
q5=r.parent/'q5_mask_20261019'
root='/work/apac2602/qwen38-cpu/optimization/20261020-q5-balanced'
for name in ['ppl_gate.lsf','verify_existing.py']:
    (r/name).write_bytes((q5/name).read_bytes())
verification=(r/'verify_existing.py').read_text(encoding='utf-8').replace('Only objdump CLI compatibility repaired; existing immutable candidate source/build reused.','Balanced ABBA/BAAB model confirmation; existing immutable candidate source/build reused without recompilation.')
(r/'verify_existing.py').write_bytes(verification.encode())
for order in ['ABBA','BAAB']:
    baseline=candidate=0;cases=[]
    for ordinal,letter in enumerate(order,1):
        if letter=='A':
            baseline+=1;role='baseline'+str(baseline)
        else:
            candidate+=1;role='candidate'+str(candidate)
        cases.append({'ordinal':ordinal,'letter':letter,'role':role,'directory':'%02d_%s'%(ordinal,role)})
    plan={'order':order,'A':'original Intel build','B':'Q5 mask Intel build from4338563','preparation':'Same original build: separate fixed PPL then TG128d2048 r10; retained and excluded from comparative model statistics. All four later cases have their own fresh fixed PPL, PP10 and TG10.','cases':cases,'source_change':'none in this confirmation; reuse SHA-verified immutable candidate'}
    (r/(order+'-plan.json')).write_text(json.dumps(plan,indent=2),encoding='utf-8')
    spec={
      'script':root+'/balanced.lsf','kind':'Q5源码候选准备段后ABBA/BAAB平衡确认',
      'purpose':'Q5_1掩码解包稳定收益确认；顺序'+order+'（A原版/B候选），每节点先单独记录原版固定PPL→TG10准备段，然后四段独立固定PPL→PP10→TG10。针对既往首次PP慢、后续趋稳的顺序混杂。',
      'environment':{'Q5_ORDER':order},'lsf_args':['-J','qwen38_q5_balanced_'+order],
      'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model,OpenMP ON/BLAS OFF；hg_6148 40slots，推理38线程close/cores。复用4338563独立Q5源码与构建，不重新编译/改源码；源码3687文件SHA和原版/候选四工具及所有lib*.so* SHA前后核验。准备段原版固定PPL一次后TG128d2048 r10，独立目录保留且不参与收益。四个比较段顺序'+order+'，各固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup590s ±5%，通过后PP2048/TG128d2048各r10 b2048ub512。无VTune、无额外采样，无系统设置更改。',
      'baseline':'同作业baseline1和baseline2两次原版；明细相对baseline1，最终摘要用两个原版pass均值与两个候选pass均值比较。准备段不作为比较baseline。',
      'case_prefix':'confirm-q5-balanced-'+order.lower(),
      'baseline_case':'confirm-q5-balanced-'+order.lower()+'-baseline1_{job_id}',
      'comparison_scope':'same-node','ppl_scope':'四个比较case各自独立固定PPL；准备段另有独立PPL，非共享',
      'note':'开发平衡对照；准备段明确单独保存、不纳入收益统计，不能称正式评测成绩。每段仍保留全部r10，不丢首次/慢样本。两节点分别ABBA/BAAB，比较段位置互补；仍需观察节点、残留缓存及非线性漂移。已有逐bit数值验证通过，本轮以SHA核验确认复用相同产物。未证明稳定模型收益前不替换部署。'
    }
    (r/(order+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
