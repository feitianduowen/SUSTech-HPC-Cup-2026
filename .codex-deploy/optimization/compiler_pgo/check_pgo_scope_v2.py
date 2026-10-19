import json
import shlex
import sys
from pathlib import Path

path = Path(sys.argv[1])
mode = sys.argv[2]
result = {'mode':mode,'ggml':0,'other':0,'links_checked':0,'examples':{}}
enable = '-prof-gen=threadsafe' if mode=='gen' else '-prof-use=nomerge'
disable = '-no-prof-gen' if mode=='gen' else '-no-prof-use'
for row in json.loads(path.read_text()):
    source = row['file']
    command = row['command']
    group = 'ggml' if '/ggml/' in source else 'other'
    result[group] += 1
    if mode != 'plain':
        assert enable in command,command
        if group == 'ggml':
            assert disable not in command,source
        else:
            assert disable in command and command.rfind(disable)>command.rfind(enable),command
    if source.endswith(('quants.c','llama-vocab.cpp','build-info.cpp','httplib.cpp')):
        result['examples'][source] = command
if mode != 'plain':
    for file in path.parent.rglob('link.txt'):
        command = file.read_text()
        if enable not in command:
            continue
        # Link files under ggml belong to the profiled backend; other dynamic
        # targets must not pull a separate PGO runtime into unprofiled modules.
        if '/ggml/' not in str(file):
            assert disable in command and command.rfind(disable)>command.rfind(enable),command
        result['links_checked'] += 1
assert result['ggml']>0 and result['other']>0
print(json.dumps(result,indent=2))
