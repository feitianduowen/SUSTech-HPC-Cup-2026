import hashlib
import json
import tarfile
from pathlib import Path

local=Path(__file__).resolve().parent
destination=Path('D:/compete/q8-avx512-v1').resolve()
identity=json.loads((local.parent/'compiler_pgo/source_identity.json').read_text())
change=json.loads((local/'patch_manifest.json').read_text())
with tarfile.open(local/'official-source-compute.tar.gz','r:gz') as archive:
    members=[]
    for entry in archive.getmembers():
        target=(destination/entry.name).resolve()
        if not target.is_relative_to(destination):raise ValueError('Archive path escaped destination')
        if entry.name=='source/'+change['file']:continue
        if target.exists() and entry.isfile():
            data=archive.extractfile(entry).read()
            if target.read_bytes()!=data:raise ValueError('Preserve existing local edit: '+str(target))
            continue
        members.append(entry)
    archive.extractall(destination,members=members,filter='data')
for name,original_sha in identity['files'].items():
    expected=change['modified_sha256'] if name==change['file'] else original_sha
    assert hashlib.sha256((destination/'source'/name).read_bytes()).hexdigest()==expected,name
(destination/'source-verification.json').write_text(json.dumps({'files_verified':len(identity['files']),'changed_files':[change['file']],'base_commit':identity['revision'],'all_match':True},indent=2))
print(destination/'source')
