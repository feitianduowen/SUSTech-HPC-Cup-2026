import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

parser = argparse.ArgumentParser(description='Submit an LSF job and persist its experiment metadata.')
parser.add_argument('spec',help='JSON containing script, purpose, config, baseline, kind, optional environment/lsf_args')
args = parser.parse_args()
root = Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
spec = json.loads(Path(args.spec).read_text())
for field in ['script','purpose','config','baseline','kind']:
    if not isinstance(spec.get(field),str) or not spec[field].strip():
        raise ValueError('Required non-empty field: '+field)
environment = os.environ.copy()
environment.update(spec.get('environment',{}))
with Path(spec['script']).open() as script:
    result = subprocess.run(['bsub']+spec.get('lsf_args',[]),stdin=script,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,env=environment)
stamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
record = dict(spec,submitted_at_client=stamp,submission_output=result.stdout,return_code=result.returncode)
match = re.search(r'Job <(\d+)>',result.stdout)
if match:
    record['job_id'] = match[1]
with (root/'results/submission_registry.jsonl').open('a') as stream:
    stream.write(json.dumps(record,ensure_ascii=False)+'\n')
print(result.stdout,end='')
if result.returncode != 0 or not match:
    raise SystemExit(result.returncode or 1)
print('REGISTERED '+record['job_id'])
