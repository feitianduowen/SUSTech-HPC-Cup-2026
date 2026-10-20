import hashlib
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parent
manifest=json.loads((root/'frozen_builds.json').read_text())
src=Path(manifest['source_file'])
assert hashlib.sha256(src.read_bytes()).hexdigest()==manifest['source_sha256']
records={}
for name,build in manifest['builds'].items():
    folder=Path(build['root'])/'build/bin'
    rows={}
    for filename,expected in build['files'].items():
        p=folder/filename
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual==expected,(str(p),actual,expected)
        rows[filename]=actual
    dependencies={}
    for binary in ['llama-bench','llama-perplexity']:
        text=subprocess.check_output(['ldd',str(folder/binary)],universal_newlines=True)
        assert 'not found' not in text,text
        dependencies[binary]=text
        for line in text.splitlines():
            cols=line.split()
            if cols and cols[0].startswith(('libggml','libllama')) and len(cols)>2 and cols[1]=='=>':
                assert Path(cols[2]).resolve().parent==folder.resolve(),line
    records[name]={'build_root':build['root'],'sha256':rows,'ldd':dependencies}
print(json.dumps({'status':'PASS','source_sha256':manifest['source_sha256'],'builds':records,'prior_differential_gate':manifest['prior_actual_library_checks']},indent=2))
