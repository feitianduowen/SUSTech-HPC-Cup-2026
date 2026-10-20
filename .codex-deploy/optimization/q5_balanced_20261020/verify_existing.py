import concurrent.futures
import hashlib
import json
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-q5-mask')
source=root/'sources/q5-mask-4338563'
identity=json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json').read_text())
replacement=json.loads((root/'manifest.json').read_text())['variants']['q5-mask']
def verify(item):
    name,sha=item
    if name==replacement['file']:sha=replacement['sha256']
    p=source/name
    assert p.is_file() and p.stat().st_nlink==1
    assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,name
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(verify,identity['files'].items()))
print(json.dumps({'all_match':True,'verified_files':len(identity['files']),'source':str(source),'reused_source_job':'4338563','base_commit':identity['revision'],'changed_files':[replacement['file']],'reason':'Balanced ABBA/BAAB model confirmation; existing immutable candidate source/build reused without recompilation.'}))
