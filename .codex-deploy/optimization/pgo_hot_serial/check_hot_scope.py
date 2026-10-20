import json
import sys
from pathlib import Path

path,mode = Path(sys.argv[1]),sys.argv[2]
expected = ['ggml/src/ggml-cpu/arch/x86/quants.c', 'ggml/src/ggml-cpu/llamafile/sgemm.cpp', 'tools/llama-bench/main.cpp']
flag = '-prof-gen=default' if mode=='gen' else '-prof-use=nomerge'
active=[]
for row in json.loads(path.read_text()):
    hot = any(row['file'].endswith(x) for x in expected)
    command = row['command']
    assert (flag in command)==hot, row
    if hot:
        assert '-prof-dir ' in command and '-no-prof-' not in command,row
        active.append(row['file'])
    else:
        assert '-prof-gen' not in command and '-prof-use' not in command,row
assert len(active)==3,active
print(json.dumps({'phase':mode,'profiled_sources':active,'expected_count':3,'status':'PASS'},indent=2))
