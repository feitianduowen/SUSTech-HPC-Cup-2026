import json
from pathlib import Path

root=Path(__file__).resolve().parent
text=(root/'mkl_same_node.lsf').read_text(encoding='utf-8')
last=text.rindex('for name in baseline mkl; do')
text=text[:last]+text[last:].replace('for name in baseline mkl; do','for name in mkl baseline; do',1)
text=text.replace('qwen38_policy5_mkl_paired','qwen38_policy5_mkl_reverse').replace('cp "$ROOT/mkl_same_node.lsf"','cp "$ROOT/mkl_reverse.lsf"')
(root/'mkl_reverse.lsf').write_bytes(text.encode())
spec=json.loads((root/'mkl_same_node.json').read_text(encoding='utf-8'))
spec['script']=spec['script'].replace('mkl_same_node.lsf','mkl_reverse.lsf')
spec['purpose']='MKL首轮4337539完成后反序确认：MKL先执行完整PPL/PP10/TG10，再原版，检查原版先执行时偏低的PP是否为顺序或缓存影响'
spec['config']=spec['config'].replace('baseline PPL→PP10→TG10→mkl PPL→PP10→TG10','mkl PPL→PP10→TG10→baseline PPL→PP10→TG10')
spec['case_prefix']='confirm-policy5-reverse'
spec['baseline_case']='confirm-policy5-reverse-baseline_{job_id}'
spec['retry_of']='4337539'
spec['note']='首轮4337539：baseline PP33.064954/TG2.961111，MKL PP48.795946/TG2.950859，各10次且两版独立PPL通过现行5%门槛。TG无改善，PP差异可能含顺序/缓存影响，不直接归因于MKL。本次同节点反序、两版再次独立固定PPL后各完整十次PP/TG；与首轮跨节点，仍保留节点影响限制。保留全部原始样本，开发自测非正式成绩；不修改源码、模型、生产部署或PGO构建。'
(root/'mkl_reverse.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(root/'mkl_reverse.lsf')
