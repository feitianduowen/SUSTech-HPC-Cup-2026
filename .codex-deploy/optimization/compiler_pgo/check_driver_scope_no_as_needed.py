import json
import sys
from pathlib import Path

rows=json.loads(Path(sys.argv[1]).read_text())
mode=sys.argv[2]
out={'mode':mode,'ggml':0,'other':0,'driver':0,'examples':{}}
for row in rows:
    source=row['file']
    command=row['command']
    if '/ggml/src/' in source:
        out['ggml']+=1
        if mode=='gen': assert '-prof-gen=threadsafe' in command and '-no-prof-gen' not in command,source
        if mode=='use': assert '-prof-use=nomerge' in command and '-no-prof-use' not in command,source
        if source.endswith('quants.c') or source.endswith('quants.cpp'):out['examples'][source]=command
    elif source.endswith('/tools/llama-bench/main.cpp'):
        out['driver']+=1
        if mode=='gen': assert '-prof-gen=threadsafe' in command and '-no-prof-gen' not in command,command
        if mode=='use': assert '-prof-use=nomerge' in command and '-no-prof-use' not in command,command
        out['examples'][source]=command
    elif source.endswith('/src/llama-vocab.cpp'):
        out['other']+=1
        if mode=='gen':assert '-no-prof-gen' in command and command.rfind('-no-prof-gen')>command.rfind('-prof-gen=threadsafe'),command
        if mode=='use':assert '-no-prof-use' in command and command.rfind('-no-prof-use')>command.rfind('-prof-use=nomerge'),command
        out['examples'][source]=command
    elif mode in ['gen','use']:
        # Includes third-party, static and object-library sources outside GGML.
        disable='-no-prof-gen' if mode=='gen' else '-no-prof-use'
        enable='-prof-gen=threadsafe' if mode=='gen' else '-prof-use=nomerge'
        assert disable in command and command.rfind(disable)>command.rfind(enable),source+'\n'+command
assert out['ggml']>0 and out['other']==1 and out['driver']==1
out['cold_links_checked']=0
if mode in ['gen','use']:
    disable='-no-prof-gen' if mode=='gen' else '-no-prof-use'
    enable='-prof-gen=threadsafe' if mode=='gen' else '-prof-use=nomerge'
    for file in Path(sys.argv[1]).parent.rglob('link.txt'):
        target=file.parent.name.removesuffix('.dir') if hasattr(str,'removesuffix') else file.parent.name[:-4]
        command=file.read_text()
        if target.startswith('ggml') or target=='llama-bench' or not ('/icpc ' in command or '/icc ' in command):continue
        assert disable in command and command.rfind(disable)>command.rfind(enable),str(file)+'\n'+command
        out['cold_links_checked']+=1
    assert out['cold_links_checked']>0
print(json.dumps(out,indent=2))
