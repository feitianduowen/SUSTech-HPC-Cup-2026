import json
import sys
from pathlib import Path

rows=json.loads(Path(sys.argv[1]).read_text())
mode=sys.argv[2]
out={'mode':mode,'ggml':0,'other':0,'examples':{}}
for row in rows:
    source=row['file']
    command=row['command']
    if '/ggml/src/' in source:
        out['ggml']+=1
        if mode=='gen': assert '-prof-gen=threadsafe' in command and '-no-prof-gen' not in command,source
        if mode=='use': assert '-prof-use=nomerge' in command and '-no-prof-use' not in command,source
        if source.endswith('quants.c') or source.endswith('quants.cpp'):out['examples'][source]=command
    elif source.endswith('/src/llama-vocab.cpp'):
        out['other']+=1
        if mode=='gen':assert '-no-prof-gen' in command and command.rfind('-no-prof-gen')>command.rfind('-prof-gen=threadsafe'),command
        if mode=='use':assert '-no-prof-use' in command and command.rfind('-no-prof-use')>command.rfind('-prof-use=nomerge'),command
        out['examples'][source]=command
assert out['ggml']>0 and out['other']==1
print(json.dumps(out,indent=2))
