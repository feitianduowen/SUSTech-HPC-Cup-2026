import concurrent.futures
import hashlib
import io
import json
import os
import sys
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx512')
base=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native')
manifest=json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json').read_text())
compute='--compute' in sys.argv
target=root/('source-v2' if compute else 'source')
target.mkdir(exist_ok=False)
def copy(item):
    name,expected=item
    data=(base/name).read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Baseline changed: '+name)
    dest=target/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(data)
    mode=(base/name).stat().st_mode & 0o777
    os.chmod(str(dest),mode)
    return name,data,mode
count=0
with tarfile.open(str(root/('official-source-compute.tar.gz' if compute else 'official-source.tar.gz')),'w:gz') as archive:
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for name,data,mode in pool.map(copy,manifest['files'].items()):
            entry=tarfile.TarInfo('source/'+name)
            entry.size=len(data)
            entry.mode=mode
            archive.addfile(entry,io.BytesIO(data))
            count+=1
            if count%500==0:print('COPIED',count,flush=True)
assert count==len(manifest['files'])
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
result={'revision':manifest['revision'],'verified_files':count,'all_match':True,'independent_regular_files':True,'base_source':str(base),'new_source':str(target),'created_at':stamp}
(root/'source-origin-verification.json').write_text(json.dumps(result,indent=2))
(root/('compute-source.ready' if compute else 'source.ready')).write_text(stamp)
print(json.dumps(result),flush=True)
