import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
root = Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo')
jid,level = sys.argv[1:]
out = root/'results'/jid
builds = root/'builds'/jid
data = {'job_id':jid,'opt_level':level,'compiler':'Intel Classic 2021.9','pgo_scope':'GGML backend plus thin llama-bench main; cold llama/common/bench-impl compile and link unprofiled in gen/use','source':'d81235049384534c167caea52b85a694f6103d14','source_path':'/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native','builds':{},'training':'Synthetic PP64 and TG8@D64; verbose plus 15s OS observation and 60s cumulative PGO counter dumps; 38 threads; profile branch counters only; unscored; no WikiText training','profile_count':len(list((out/'profiles').glob('*.dyn'))),'updated_at':datetime.now(timezone(timedelta(hours=8))).isoformat()}
for ordinal,name in [('01','control'),('02','pgo')]:
    gate=json.loads((out/(ordinal+'_'+name)/'perplexity_result.json').read_text())
    if gate['status']!='PASS': raise ValueError('PPL gate failed: '+name)
    data['builds'][name]={'root':str(builds/name),'ppl':gate,'artifacts':{}}
    for file in sorted((builds/name/'build/bin').iterdir()):
        if file.is_file() and (file.name.startswith('lib') or file.name in ['llama-cli','llama-server','llama-bench','llama-perplexity']):
            data['builds'][name]['artifacts'][file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
data['dpi_sha256']=hashlib.sha256((out/'profiles/pgopti.dpi').read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps(data,ensure_ascii=False))
