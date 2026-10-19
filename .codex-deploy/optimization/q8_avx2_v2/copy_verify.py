import concurrent.futures
import hashlib
import json
import os
from pathlib import Path

root = Path('/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2')
variant = os.environ['Q8_VARIANT']
assert variant in ['schedule4','schedule4_prefetch16']
base = Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native')
identity = json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json').read_text())
manifest = json.loads((root/'scripts/manifest.json').read_text())
target = root/'sources'/variant
target.mkdir(parents=True,exist_ok=False)
changed = 'ggml/src/ggml-cpu/arch/x86/quants.c'
modified = (root/'variants'/variant/'quants.c').read_bytes()
assert hashlib.sha256(modified).hexdigest() == manifest['variants'][variant]['sha256']
def copy(item):
    name,expected = item
    original = base/name
    data = original.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Baseline changed: '+name)
    data = modified if name == changed else data
    dest = target/name
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as file:
        file.write(data)
    os.chmod(str(dest),original.stat().st_mode & 0o777)
    assert dest.stat().st_nlink == 1
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == (manifest['variants'][variant]['sha256'] if name == changed else expected)
    return name
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    copied = list(pool.map(copy,identity['files'].items()))
assert len(copied) == len(identity['files'])
assert hashlib.sha256((base/changed).read_bytes()).hexdigest() == manifest['original_sha256']
print(json.dumps({'variant':variant,'base_commit':identity['revision'],'verified_files':len(copied),'all_match':True,'changed_files':[changed],'independent_regular_files':True,'new_source':str(target),'original_unchanged':True}))
