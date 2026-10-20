import json
import shutil
import subprocess
import sys
from pathlib import Path

old=Path(__file__).resolve().parent
root=old.parent/'hc4_post_v2_20261020'
root.mkdir(exist_ok=True)
for name in ['ops.original.cpp','hc_check.cpp','bench.py']:
    shutil.copyfile(old/name,root/name)
shutil.copyfile(old/'fastpath_v2.inc',root/'fastpath.inc')
script=(old/'prepare.py').read_text(encoding='utf-8')
start=script.index("fast = '''")
end=script.index('candidate = original',start)
script=script[:start]+"fast = (here/'fastpath.inc').read_text(encoding='utf-8') + '\\n'\n"+script[end:]
script=script.replace('20261020-hc4-post','20261020-hc4-post-v2').replace("variant = 'hc4-post'","variant = 'hc4-post-v2'")
script=script.replace(".replace('softmax-rows','hc4-post')",".replace('softmax-rows','hc4-post-v2')")
script=script.replace("prefix='confirm-hc4-post-'","prefix='confirm-hc4-post-v2-'")
script=script.replace("candidate = original[:pos] + fast + original[pos:]","candidate = original[:pos] + fast + original[pos:]\ncandidate = candidate.replace('#include <cmath>', '#include <cmath>\\n\\n#if defined(__AVX2__) && defined(__FMA__)\\n#include <immintrin.h>\\n#endif', 1)")
script=script.replace('qwen38_hc4_','qwen38_hc4v2_')
(root/'prepare.py').write_text(script,encoding='utf-8',newline='\n')
subprocess.run([sys.executable,str(root/'prepare.py')],check=True)
for order,prior in [('abba','4340907'),('baab','4340908')]:
    path=root/('submission_'+order+'.json')
    spec=json.loads(path.read_text(encoding='utf-8'))
    spec['retry_of']=prior
    spec['purpose']='修复'+prior+'的HC-post浮点融合差异：显式AVX2八通道及标量尾段，初始乘法寄存器舍入屏障后按原版顺序四次FMA，无comb时保持独立乘法与加法；其他形状保留原版。'
    spec['config']=spec['config'].replace('仅修改','仅修改')+'；v2显式SIMD/FMA和空汇编寄存器屏障，源码guard AVX2/FMA；原版编译汇编已确认mul→按流FMA，无comb为mul→add。'
    spec['note']='v1 '+prior+'逐bit差分失败（972组/42341535值，860892处不同），未做算子微基准/PPL/整模测速；v1保留。v2不放宽逐bit门槛，修复编译器融合边界后重新从构建验证。'+spec['note']
    path.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(root)
