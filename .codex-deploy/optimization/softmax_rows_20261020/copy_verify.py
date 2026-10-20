import concurrent.futures
import hashlib
import json
import os
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261020-softmax-rows')
variant=os.environ['SOURCE_VARIANT']
manifest=json.loads((root/'manifest.json').read_text())['variants'][variant]
base=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native')
identity=json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json').read_text())
target=root/'sources'/(variant+'-'+os.environ['LSB_JOBID'])
target.mkdir(parents=True,exist_ok=False)
replacement=(root/'variants'/variant/manifest['file']).read_bytes()
assert hashlib.sha256(replacement).hexdigest()==manifest['sha256']
def copy(item):
    name,sha=item
    data=(base/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==sha,name
    if name==manifest['file']:data=replacement
    dest=target/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as stream:stream.write(data)
    os.chmod(str(dest),(base/name).stat().st_mode & 0o777)
    assert dest.stat().st_nlink==1
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==(manifest['sha256'] if name==manifest['file'] else sha)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(copy,identity['files'].items()))
print(json.dumps({'base_commit':identity['revision'],'verified_files':len(identity['files']),'new_source':str(target),'changed_files':[manifest['file']],'independent_regular_files':True,'original_unchanged':True,'all_match':True}))
