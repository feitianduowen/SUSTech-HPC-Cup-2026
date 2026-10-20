import collections
import json
import re
import subprocess
import sys
from pathlib import Path

out = Path(sys.argv[1])
result = {}
for name, library in zip(['baseline', 'candidate'], sys.argv[2:]):
    rows = subprocess.check_output(['nm', '-D', '-S', library], universal_newlines=True).splitlines()
    item = next(r.split() for r in rows if r.split() and r.split()[-1] == 'ggml_gemv_q4_K_8x8_q8_K')
    start, size = int(item[0], 16), int(item[1], 16)
    code = subprocess.check_output(['objdump', '-d', '--no-show-raw-insn', '--start-address='+hex(start), '--stop-address='+hex(start+size), library], universal_newlines=True)
    (out / ('q4-'+name+'-assembly.txt')).write_text(code)
    counts = collections.Counter(line.split()[1] for line in code.splitlines() if re.match(r'^\s+[0-9a-f]+:\s', line))
    result[name] = {'function_bytes': size, 'static_mnemonics': dict(counts), 'masked_vpshufd': sum('vpshufd' in line and '{%k' in line for line in code.splitlines())}
result['scope'] = 'Static instructions include all loop/remainder code, not runtime counts or measured throughput.'
(out / 'q4-assembly-stats.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
