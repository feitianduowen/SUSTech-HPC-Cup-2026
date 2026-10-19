import hashlib,json,zipfile
from pathlib import Path
root=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
files=[]
for folder in ['scripts','patches','results','logs']:
    for p in (root/folder).rglob('*'):
        if not p.is_file():
            continue
        if p.suffix in ['.json','.csv','.jsonl','.txt','.log','.md','.lsf','.py','.c','.cpp','.patch','.out','.err'] or p.name in ['status','sha256.txt','CMakeCache.txt','completed.txt']:
            if p.stat().st_size < 50*1024*1024:
                files.append(p)
archive=root/'experiment_evidence.zip'
with zipfile.ZipFile(str(archive),'w',zipfile.ZIP_DEFLATED) as z:
    manifest={}
    for p in files:
        data=p.read_bytes()
        rel=p.relative_to(root).as_posix()
        z.writestr(rel,data)
        manifest[rel]=hashlib.sha256(data).hexdigest()
    deploy=root.parent.parent
    references=[deploy/'deployment_manifest.json',deploy/'deployment.status',deploy/'reference/task_rules_CN_20261018.md']
    for d in deploy.glob('llama_bench_results_*'):
        references+=list(d.glob('*.json'))+list(d.glob('environment.txt'))
    references+=list((deploy/'logs').glob('*.out'))+list((deploy/'logs').glob('*.err'))
    for p in references:
        if not p.is_file():
            continue
        rel='reference/'+p.relative_to(deploy).as_posix()
        data=p.read_bytes()
        z.writestr(rel,data)
        manifest[rel]=hashlib.sha256(data).hexdigest()
    for p in [root/'Qwen38_CPU_experiment_log.xlsx',root/'optimization_report.md',root/'logging_workflow.md']:
        if p.is_file():
            data=p.read_bytes()
            z.writestr(p.name,data)
            manifest[p.name]=hashlib.sha256(data).hexdigest()
    memory=root.parent/'20261019-memory'
    if memory.exists():
        for p in memory.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.jsonl','.log','.md','.py','.lsf','.txt','.out','.err'] and p.stat().st_size<50*1024*1024:
                data=p.read_bytes()
                rel='memory_20261019/'+p.relative_to(memory).as_posix()
                z.writestr(rel,data)
                manifest[rel]=hashlib.sha256(data).hexdigest()
    compiler=root.parent/'20261019-compiler-pgo'
    if compiler.exists():
        candidates=list(compiler.iterdir())+list((compiler/'results').rglob('*'))
        for p in candidates:
            if p.is_file() and (p.suffix in ['.json','.jsonl','.log','.md','.py','.lsf','.txt','.out','.err','.command','.strace'] or p.name=='job.status') and p.stat().st_size<50*1024*1024:
                data=p.read_bytes()
                rel='compiler_pgo_20261019/'+p.relative_to(compiler).as_posix()
                z.writestr(rel,data)
                manifest[rel]=hashlib.sha256(data).hexdigest()
    z.writestr('archive_sha256.json',json.dumps(manifest,indent=2))
print(json.dumps({'path':str(archive),'files':len(files),'bytes':archive.stat().st_size}))
(root/'archive.ready').write_text(json.dumps({'bytes':archive.stat().st_size,'files':len(manifest)}))
