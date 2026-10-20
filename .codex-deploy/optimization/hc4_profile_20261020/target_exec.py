import json
import subprocess
import sys
import time
from pathlib import Path

out=Path(sys.argv[1]); phase=sys.argv[2]; command=sys.argv[3:]
(out/(phase+'.command.json')).write_text(json.dumps({'argv':command,'diagnostic_unscored':True},indent=2))
with (out/(phase+'.json')).open('w') as stdout, (out/'bench.log').open('w') as stderr, (out/'events.jsonl').open('w') as events:
    child=subprocess.Popen(command,stdout=stdout,stderr=subprocess.PIPE,universal_newlines=True,bufsize=1)
    (out/'target.pid').write_text(str(child.pid))
    for line in child.stderr:
        stderr.write(line); stderr.flush()
        events.write(json.dumps({'time_unix':time.time(),'text':line.rstrip()})+'\n');events.flush()
    code=child.wait()
(out/'target.exit').write_text(str(code))
if code==0:
    x=json.loads((out/(phase+'.json')).read_text())[0]
    assert len(x['samples_ns'])==len(x['samples_ts'])==10
    assert (x['n_threads'],x['n_batch'],x['n_ubatch'],x['n_gpu_layers'],x['type_k'],x['type_v'])==(38,2048,512,0,'f16','f16')
    assert (x['n_prompt'],x['n_gen'],x['n_depth'])==((2048,0,0) if phase=='pp' else (0,128,2048))
raise SystemExit(code)
