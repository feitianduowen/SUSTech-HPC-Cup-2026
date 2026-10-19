import hashlib
import json
import subprocess
import sys
from pathlib import Path
src,target=map(Path,sys.argv[1:3])
expected='d81235049384534c167caea52b85a694f6103d14'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if '--snapshot' in sys.argv:
    revision=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip()
    if revision!=expected: raise ValueError('Unexpected source revision')
    subprocess.check_call(['git','-C',str(src),'diff','--exit-code','--quiet'])
    names=subprocess.check_output(['git','-C',str(src),'ls-files','-z']).decode().split(chr(0))
    data={'revision':revision,'files':{name:digest(src/name) for name in names if name and (src/name).is_file()}}
    target.write_text(json.dumps(data,indent=2))
else:
    data=json.loads(target.read_text())
    if data['revision']!=expected: raise ValueError('Unexpected source revision')
    bad=[name for name,sha in data['files'].items() if not (src/name).is_file() or digest(src/name)!=sha]
    if bad: raise ValueError('Source mismatch: '+str(bad))
print(json.dumps({'revision':data['revision'],'verified_files':len(data['files']),'all_match':True}))
