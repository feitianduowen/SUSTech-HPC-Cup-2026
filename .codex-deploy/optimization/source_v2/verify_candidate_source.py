import hashlib
import json
from pathlib import Path
root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx512')
identity=json.loads(Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json').read_text())
change=json.loads((root/'source-modification.json').read_text())
bad=[]
for name,sha in identity['files'].items():
    expected=change['modified_sha256'] if name==change['file'] else sha
    file=root/'source-v2'/name
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=expected:bad.append(name)
if bad:raise ValueError('Unexpected source changes: '+str(bad))
old=Path(change['original_preserved_at'])
assert hashlib.sha256(old.read_bytes()).hexdigest()==change['original_sha256']
print(json.dumps({'base_commit':identity['revision'],'files_verified':len(identity['files']),'changed_files':[change['file']],'previous_source_unchanged':True,'all_match':True}))
