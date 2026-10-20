import json
import struct
import math
import sys
from pathlib import Path
out=Path(sys.argv[1])
a=(out/'baseline.bin').read_bytes();b=(out/'candidate.bin').read_bytes()
x=json.loads((out/'baseline-check.json').read_text());y=json.loads((out/'candidate-check.json').read_text())
assert x==y and x['status']=='PASS' and x['cases']==144
assert len(a)==len(b)==4*x['values']
bit=bad=0;maxerr=0.0
for i in range(0,len(a),4):
    va=struct.unpack_from('f',a,i)[0];vb=struct.unpack_from('f',b,i)[0]
    bit+=a[i:i+4]!=b[i:i+4]
    err=abs(va-vb);maxerr=max(maxerr,err)
    bad+=not(math.isfinite(va) and math.isfinite(vb)) or err>1e-4+5e-5*abs(va)
result={'status':'PASS' if not bad and not bit else 'FAIL','cases':144,'values':x['values'],'bit_mismatches':bit,'tolerance_failures':bad,'max_abs_error':maxerr,'tolerance':'bit-exact required; ordered Q5 loop unrolling','repetitions':3}
(out/'library-correctness.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if bad or bit:raise SystemExit(1)
