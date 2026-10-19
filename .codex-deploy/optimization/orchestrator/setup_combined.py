import subprocess
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
base=Path('/work/apac2602/qwen38-cpu/llama.cpp')
dest=root/'sources/native-concat-u2'
status=root/'combined-source.status'
status.write_text('PREPARING\n')
try:
    if not dest.exists():
        subprocess.check_call(['git','-C',str(base),'worktree','add','-b','codex/cpu-native-concat-u2',str(dest),'d81235049384534c167caea52b85a694f6103d14'])
    diff=subprocess.check_output(['git','-C',str(dest),'diff','--stat']).decode().strip()
    if not diff:
        patches=[str(root/'patches'/name) for name in ['q8-u2.patch','concat-rows.patch']]
        subprocess.check_call(['git','-C',str(dest),'apply','--check']+patches)
        subprocess.check_call(['git','-C',str(dest),'apply']+patches)
    diff=subprocess.check_output(['git','-C',str(dest),'diff','--','ggml'])
    (root/'results/native-concat-u2.source.patch').write_bytes(diff)
    status.write_text('READY\n')
except Exception:
    status.write_text('FAILED\n')
    raise
