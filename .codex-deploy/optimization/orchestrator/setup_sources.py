import json, subprocess
from pathlib import Path

base = Path('/work/apac2602/qwen38-cpu/llama.cpp')
root = Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
for name in ['scripts', 'patches', 'sources', 'results', 'logs']:
    (root/name).mkdir(parents=True, exist_ok=True)
for name in ['native', 'q8-u2', 'q8-a4', 'pp-reuse', 'diagnostic']:
    dest = root/'sources'/name
    if not dest.exists():
        subprocess.check_call(['git', '-C', str(base), 'worktree', 'add', '-b', 'codex/cpu-'+name, str(dest), 'd81235049384534c167caea52b85a694f6103d14'])
    rev = subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD']).decode().strip()
    assert rev == 'd81235049384534c167caea52b85a694f6103d14'
(root/'setup.ready').write_text('sources prepared\n')
print(str(root))
