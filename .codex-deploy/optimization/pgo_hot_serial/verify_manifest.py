import hashlib
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
assert manifest['source'] == 'd81235049384534c167caea52b85a694f6103d14'
checked = 0
for name, build in manifest['builds'].items():
    assert build['ppl']['status'] == 'PASS'
    for artifact, sha in build['artifacts'].items():
        path = Path(build['root'])/'build/bin'/artifact
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError('Artifact changed: '+str(path))
        checked += 1
assert checked > 8
print(json.dumps({'parent_job':manifest['job_id'],'opt_level':manifest['opt_level'],'all_match':True,'checked':checked}))
