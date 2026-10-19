import hashlib
import json
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx512')
assert (root/'compute-source.ready').is_file()
manifest=json.loads((root/'patch_manifest.json').read_text())
target=root/'source-v2'/manifest['file']
original=target.read_bytes()
assert hashlib.sha256(original).hexdigest()==manifest['original_sha256']
modified=(root/'scripts/quants.modified.c').read_bytes()
assert hashlib.sha256(modified).hexdigest()==manifest['modified_sha256']
assert target.stat().st_nlink==1, 'Source target must not be hard linked'
target.write_bytes(modified)
manifest['original_preserved_at']='/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native/'+manifest['file']
manifest['new_source']=str(root/'source-v2')
assert hashlib.sha256(Path(manifest['original_preserved_at']).read_bytes()).hexdigest()==manifest['original_sha256']
(root/'source-modification.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
