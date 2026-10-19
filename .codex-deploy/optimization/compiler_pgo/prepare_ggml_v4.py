import json
from pathlib import Path

root=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
text=(root/'pipeline_ggml_pgo_v3.lsf').read_text(encoding='utf-8')
text=text.replace('pipeline_ggml_pgo_v3.lsf','pipeline_ggml_pgo_v4.lsf')
assert 'training pp 1200 -p 64 -n 0' in text
assert 'training tg 900 -p 0 -n 8 -d 64' in text
text=text.replace('training pp 1200 -p 64 -n 0','training pp 3600 -p 64 -n 0')
text=text.replace('training tg 900 -p 0 -n 8 -d 64','training tg 3600 -p 0 -n 8 -d 64')
(root/'pipeline_ggml_pgo_v4.lsf').write_bytes(text.encode())
spec=json.loads((root/'ggml_v3_O3.json').read_text(encoding='utf-8'))
spec.update(script=remote+'/pipeline_ggml_pgo_v4.lsf',retry_of='4337257',kind='GGML定向PGO V4/训练时限修复/PPL',purpose='4337257链接已通过但1200秒训练限时在权重重排第41层超时；基于持续进展证据扩大非计分PP/TG训练时限，重新生成完整独立计数',lsf_args=['-J','qwen38_O3_ggml_pgo_v4'])
spec['config']=spec['config'].replace('训练PP1200s/TG900s限时','训练PP3600s/TG3600s限时')
spec['note']='4337257 TRAIN_PP_UNSCORED exit124，20分钟仍在模型初始化/repack，已推进blk.41；末端RSS约71.6GiB、单线程持续消耗CPU，非死锁证据。训练PP JSON为空，TG/合并/反馈/PPL均未运行；三个非空dyn仅作为超时诊断，绝不用于新训练或正式成果。新作业独立gen构建和计数，仍只读复用4337216通过SHA256核验的control PPL2.7767，PP64和TG8@D64各r1/38线程不计分、各允许3600s（每个进程都需加载重排）。正式PPL590s及正式PP/TG十次参数完全保持。另一路薄main PGO试验由账户并行工作管理，本次不重复提交。'
(root/'ggml_v4_O3.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(root/'pipeline_ggml_pgo_v4.lsf')
