import hashlib,json,subprocess
from pathlib import Path
root=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
data={}
for name in ['native','q8-u2','q8-a4','pp-reuse','diagnostic','concat']:
    src=root/'sources'/name
    if not (src/'build/bin/llama-bench').exists():
        continue
    diff=subprocess.check_output(['git','-C',str(src),'diff','--','ggml']).decode()
    (root/'results'/(name+'.source.patch')).write_text(diff)
    artifacts={}
    for p in (src/'build/bin').iterdir():
        if p.is_file() and (p.name in ['llama-bench','llama-perplexity','llama-cli','llama-server'] or p.name.endswith('.so')):
            artifacts[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    data[name]={'source_revision':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip(),'source_diff_sha256':hashlib.sha256(diff.encode()).hexdigest(),'artifacts':artifacts}
(root/'results/candidate_identities.json').write_text(json.dumps(data,indent=2))
print('Captured',len(data),'candidate builds')
