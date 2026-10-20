import json
import struct
import sys
from pathlib import Path

out=Path(sys.argv[1])
a=(out/'baseline.bin').read_bytes()
b=(out/'candidate.bin').read_bytes()
x=json.loads((out/'baseline-check.json').read_text())
y=json.loads((out/'candidate-check.json').read_text())
assert x==y and x['status']=='PASS' and x['cases']==144
assert len(a)==len(b)==4*x['values']
bad=sum(a[i:i+4]!=b[i:i+4] for i in range(0,len(a),4))
result={'status':'PASS' if bad==0 else 'FAIL','cases':x['cases'],'values':x['values'],'bit_mismatches':bad,'repetitions':3,'threads':[1,38],'baseline':'production Intel original actual GGML library','candidate':'new independent Intel library','note':'8 weight types, 9 shapes, 1/38 threads; row tails, token threshold37/38/39, batch2; repeated execution bitwise stable; no model throughput score'}
(out/'library-correctness.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
if bad:raise SystemExit(1)
