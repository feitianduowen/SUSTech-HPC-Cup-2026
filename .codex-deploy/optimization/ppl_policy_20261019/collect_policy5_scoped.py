import hashlib
import fcntl
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

deploy = Path('/work/apac2602/qwen38-cpu')
root = deploy/'optimization/20261018-v1'
wanted = {'4337539'}
tz = timezone(timedelta(hours=8))
date_pattern = r'\w{3} \w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2} \d{4}'

def parse_date(value):
    return datetime.strptime(value,'%a %b %d %H:%M:%S %Y').replace(tzinfo=tz).isoformat()

jobs = {}
cached = {}
cache_path = root/'results/job_registry.json'
if '--recent' in sys.argv and cache_path.is_file():
    previous = json.loads(cache_path.read_text())
    cached = {row['job_id']:row for row in previous['jobs'] if row.get('state') in ['DONE','EXIT'] and row.get('finish_time')}
for index,arg in enumerate(sys.argv[:-1]):
    if arg == '--refresh-job':
        cached.pop(sys.argv[index+1],None)
rejected = []
submissions = root/'results/submission_registry.jsonl'
if submissions.exists():
    for line in submissions.read_text().splitlines():
        spec = json.loads(line)
        if 'job_id' in spec and spec['job_id'] not in wanted: continue
        if 'job_id' in spec:
            if spec['job_id'] in cached:
                jobs[spec['job_id']]=cached[spec['job_id']]
                jobs[spec['job_id']]['submission']=spec
            else:
                jobs[spec['job_id']] = {'job_id':spec['job_id'],'submission':spec,'logs':[],'measurements':[],'evidence':[],'submit_time':spec['submitted_at_client'],'state':'PEND'}
        else:
            rejected.append(spec)
for jid,row in cached.items():
    jobs.setdefault(jid,row)
for path in sorted((deploy/'logs').glob('*.out')):
    match = re.match(r'(\d+)\.',path.name)
    if not match:
        continue
    jid = match[1]
    if jid not in wanted: continue
    if jid in cached:
        continue
    raw = path.read_bytes()
    text = raw.decode('utf-8',errors='replace')
    row = jobs.setdefault(jid, {'job_id':jid,'logs':[],'measurements':[],'evidence':[]})
    row['logs'].append(str(path))
    row['stdout_sha256'] = hashlib.sha256(raw).hexdigest()
    for field, pattern in [('submit_time',r'was submitted.*? at ('+date_pattern+')'),('start_time',r'Started at ('+date_pattern+')'),('finish_time',r'Results reported at ('+date_pattern+')')]:
        m = re.search(pattern,text,re.S)
        if m:
            row[field] = parse_date(m[1])
    m = re.search(r'Job was executed on host\(s\) <([^>]+)>',text)
    if m:
        row['exec_host'] = m[1]
    m = re.search(r'Subject: Job \d+: <([^>]+)>',text)
    if m:
        row['job_name'] = m[1]
    row['state'] = 'DONE' if 'Successfully completed.' in text else ('EXIT' if 'Exited with exit code' in text else 'RUN')
    row['compiler_observations'] = [line for line in text.splitlines() if any(s in line for s in ['compiler identification is','icc (ICC)','icpc (ICC)','oneAPI DPC++/C++ Compiler','gcc (GCC)'])][:8]
    row['lsf_summary'] = text[text.rfind('Subject: Job '):] if 'Subject: Job ' in text else ''

active = []  # active state from the job's own stdout/status; scheduler query separate
if active:
    result = subprocess.run(['bjobs','-l',*active],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,timeout=30)
    (root/'results/active_jobs_detail.txt').write_text(result.stdout)
    for fragment in re.split(r'(?m)^Job <',result.stdout)[1:]:
        block = 'Job <'+fragment
        m = re.search(r'Job <(\d+)>',block)
        if not m or m[1] not in jobs:
            continue
        row = jobs[m[1]]
        row['evidence'].append({'path':'LSF bjobs -l','text':block[:100000]})
        job_name = re.search(r'Job Name <([^>]+)>',block)
        if job_name:
            row['job_name'] = job_name[1]
        state = re.search(r'Status <(\w+)>',block)
        if state:
            row['state'] = state[1]
        for field, label in [('submit_time','Submitted from host'),('start_time','Started')]:
            stamp = re.search(r'(\w{3} \w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}): '+label,block)
            if stamp:
                year = int(row['submit_time'][:4]) if 'submit_time' in row else datetime.now(tz).year
                row[field] = parse_date(stamp[1]+' '+str(year))
        host = re.search(r'Started.*?on Host\(s\) <([^>]+)>',block,re.S)
        if host:
            row['exec_host'] = host[1]

directories = list(deploy.glob('llama_bench_results_*')) + list((root/'results').iterdir())
for d in directories:
    m = re.search(r'_(\d+)$',d.name)
    if not m or m[1] in cached or m[1] not in jobs or not d.is_dir():
        continue
    row = jobs[m[1]]
    record = {'name':d.name,'path':str(d),'ppl':None,'pp':None,'tg':None}
    for key, name in [('ppl','perplexity_result.json'),('pp','pp2048.json'),('tg','tg128_d2048.json')]:
        try:
            record[key] = json.loads((d/name).read_text())
        except (OSError,ValueError):
            pass
    if any(record[k] is not None for k in ['ppl','pp','tg']):
        row['measurements'].append(record)
    for filename in ['status','test.log','build-test.log','microbench.log','analysis.json','micro_analysis.json','assembly_comparison.json','node_analysis.json'] + [p.name for p in d.glob('*.summary.json')]:
        p = d/filename
        if p.is_file():
            row['evidence'].append({'path':str(p),'text':p.read_text(errors='replace')[:100000]})

for jid, row in jobs.items():
    if jid in cached:
        continue
    d = deploy/'llama.cpp/build_logs'/jid
    for filename in ['environment.txt','selected_cmake_cache.txt']:
        p = d/filename
        if p.is_file():
            row['evidence'].append({'path':str(p),'text':p.read_text(errors='replace')[:100000]})

for d in (root/'logs').glob('build_*'):
    jid = d.name.rsplit('_',1)[-1]
    if jid not in jobs or jid in cached:
        continue
    row = jobs[jid]
    for filename in ['status','CMakeCache.txt','quantize-tests.log']:
        p = d/filename
        if p.is_file():
            row['evidence'].append({'path':str(p),'text':p.read_text(errors='replace')[:100000]})

for jid,row in jobs.items():
    if jid in cached:
        continue
    spec=row.get('submission',{})
    if not spec.get('script'):
        continue
    experiment=Path(spec['script']).resolve().parent
    if experiment==root or deploy/'optimization' not in experiment.parents:
        continue
    run=experiment/'results'/jid
    gate=run/'ppl/perplexity_result.json'
    ppl=json.loads(gate.read_text()) if gate.is_file() else None
    prefix=spec.get('case_prefix','memory')
    for case in sorted(run.glob('[0-9][0-9]_*')):
        if not case.is_dir(): continue
        name=case.name.split('_',1)[1]
        own_gate=case/'perplexity_result.json'
        case_ppl=json.loads(own_gate.read_text()) if own_gate.is_file() else ppl
        record={'name':prefix+'-'+name+'_'+jid,'path':str(case),'ppl':case_ppl,'pp':None,'tg':None,'ppl_gate_path':str(own_gate if own_gate.is_file() else gate),'ppl_scope':'每个构建独立固定PPL校验' if own_gate.is_file() else '同作业同一Intel构建共享固定PPL门槛，不是每case独立重跑','baseline_name':spec.get('baseline_case','memory-auto-default_{job_id}').format(job_id=jid)}
        record['os_monitoring'] = prefix=='memory'
        if spec.get('ppl_scope'):
            record['ppl_scope'] = spec['ppl_scope']
        for key in ['pp','tg']:
            path=case/(key+'.json')
            if not path.exists(): path=case/('pp2048.json' if key=='pp' else 'tg128_d2048.json')
            record[key+'_file']=str(path)
            try: record[key]=json.loads(path.read_text())
            except (OSError,ValueError): pass
        row['measurements'].append(record)
        for filename in ['result.json','pp.command.json','tg.command.json']:
            p=case/filename
            if p.is_file():row['evidence'].append({'path':str(p),'text':p.read_text(errors='replace')[:100000]})
    for filename in ['plan.json','summary.json','status.json','job.status','binary_sha256.json','environment.txt','manifest.json','source-verification.json','profile-sha256.txt','profmerge.log','control-build/configure.command','control-build/quantize-tests.log','pgo-build/configure.command','pgo-build/profile-diagnostics.txt','pgo-build/quantize-tests.log','training-pp.command','training-tg.command','gen-build/configure.command','gen-build/pgo-scope.json','control-build/pgo-scope.json','pgo-build/pgo-scope.json','training-validation.json','training-pp.log','training-tg.log','correctness.json','fallback-correctness.json','library-correctness.json','compile.log','compile-avx2.log','sha256.txt','avx512-assembly.txt']:
        p=run/filename
        if p.is_file():row['evidence'].append({'path':str(p),'text':p.read_text(errors='replace')[:100000]})

for jid,row in jobs.items():
    run=deploy/'optimization/20261019-compiler-pgo/results'/jid
    for name in ['gen-build/build.log','link-probe/result.json','configuration_amendment.json','relink-result.json','original.command','original.log','no_as_needed.command','no_as_needed.log','shared_intel.command','shared_intel.log','gen-build/pgo-scope-prebuild.json','control-reuse.txt','control-parent-sha256.txt','training-pp.log','training-tg.log','training-os.jsonl']:
        file=run/name
        if file.is_file():
            with file.open('rb') as handle:
                size=file.stat().st_size
                handle.seek(max(0,size-20000))
                tail=handle.read().decode('utf-8',errors='replace')
            row['evidence'].append({'path':str(file),'text':tail})
    policy_run=deploy/'optimization/20261019-ppl-policy5/results'/jid
    for name in ['policy.json','pipeline.lsf','baseline.sha256.txt','mkl.sha256.txt','baseline.ldd.txt','mkl.ldd.txt','baseline.CMakeCache.txt','mkl.CMakeCache.txt']:
        file=policy_run/name
        if file.is_file():row['evidence'].append({'path':str(file),'text':file.read_text(errors='replace')[:20000]})
    for evidence in row['evidence']:
        if evidence['path'].endswith('/environment.txt'):
            match=re.search(r'^r13n[0-9]+$',evidence['text'],re.M)
            if match and not row.get('exec_host'): row['exec_host']='40*'+match[0]
data = {'updated_at':datetime.now(tz).isoformat(),'timezone':'Asia/Hong_Kong UTC+08:00','source':'LSF stdout completion summaries; active bjobs -l; original result JSON; diagnostic logs','jobs':sorted(jobs.values(),key=lambda r:int(r['job_id'])),'rejected_submissions':rejected}
if '4336625' in jobs and '4336625' not in cached:
    extra=deploy/'optimization/20261019-user-hc-numa/results/4336625'
    for filename in ['status','environment.txt','hc_compile.log','hc_test.log','numa_compile.log','numa_test.log']:
        path=extra/filename
        if path.is_file():jobs['4336625']['evidence'].append({'path':str(path),'text':path.read_text(errors='replace')[:100000]})
data['admission_evidence'] = []
path = deploy/'optimization/20261019-ppl-policy5/policy5_scoped_snapshot.json'
tmp = path.with_suffix('.tmp')
tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
tmp.replace(path)
print(json.dumps({'jobs':len(jobs),'updated_at':data['updated_at'],'path':str(path)}))
