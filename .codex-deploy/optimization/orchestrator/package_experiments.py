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
    z.writestr('archive_sha256.json',json.dumps(manifest,indent=2))
print(json.dumps({'path':str(archive),'files':len(files),'bytes':archive.stat().st_size}))
