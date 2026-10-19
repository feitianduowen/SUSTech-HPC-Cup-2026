import hashlib
import json
import tarfile
from pathlib import Path

local=Path(__file__).resolve().parent
destination=Path('D:/compete/q8-avx512-v1').resolve()
identity=json.loads((local.parent/'compiler_pgo/source_identity.json').read_text())
change=json.loads((local/'patch_manifest.json').read_text())
seen=set()
with tarfile.open(local/'official-github.tar.gz','r|gz') as archive:
    for member in archive:
        if not member.isfile() or '/' not in member.name:continue
        name=member.name.split('/',1)[1]
        if name not in identity['files']:continue
        data=archive.extractfile(member).read()
        if hashlib.sha256(data).hexdigest()!=identity['files'][name]:raise ValueError('Source hash mismatch: '+name)
        target=(destination/'source'/name).resolve()
        if not target.is_relative_to(destination):raise ValueError('Invalid source path')
        if name==change['file']:
            assert hashlib.sha256(target.read_bytes()).hexdigest()==change['modified_sha256']
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if target.read_bytes()!=data:raise ValueError('Preserve existing local change: '+name)
            else:
                with target.open('xb') as file:file.write(data)
        seen.add(name)
        if len(seen)%500==0:print('VERIFIED',len(seen),flush=True)
missing=set(identity['files'])-seen
if missing:raise ValueError('Missing source files: '+str(sorted(missing)))
result={'base_commit':identity['revision'],'verified_files':len(seen),'changed_files':[change['file']],'all_match':True,'archive_source':'https://codeload.github.com/ggml-org/llama.cpp/tar.gz/'+identity['revision'],'verification_reference':'Remote official source SHA256 snapshot, not GitHub filenames alone'}
(destination/'source-verification.json').write_text(json.dumps(result,indent=2))
(destination/'q8-avx512-ordered.patch').write_bytes((local/'q8-avx512-ordered.patch').read_bytes())
(destination/'patch_manifest.json').write_bytes((local/'patch_manifest.json').read_bytes())
print(json.dumps(result,indent=2),flush=True)
