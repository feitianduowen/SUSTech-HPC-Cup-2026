import json
import os
import subprocess
import sys
import time
from pathlib import Path

root=Path(sys.argv[1])
cases=[]
for threads in [1,38]:
    for variant in ['plain','broad','hot']:
        directory=root/(variant+'_t'+str(threads))
        directory.mkdir()
        command=[str(root/('probe-'+variant)),str(threads),'10']
        environment=os.environ.copy()
        environment['PROF_DIR']=str(root/'profiles'/variant)
        environment['INTEL_PROF_DYN_PREFIX']='diagnostic_'+str(threads)
        environment.pop('INTEL_PROF_DUMP_INTERVAL',None)
        environment.pop('INTEL_PROF_DUMP_CUMULATIVE',None)
        begin=time.monotonic()
        with (directory/'stdout.json').open('w') as output,(directory/'stderr.log').open('w') as error:
            try:
                result=subprocess.run(command,stdout=output,stderr=error,env=environment,timeout=60)
                code=result.returncode
            except subprocess.TimeoutExpired:
                code=124
        record={'name':directory.name,'variant':variant,'threads':threads,'returncode':code,'wall_seconds':time.monotonic()-begin,'command':command,'path':str(directory),'diagnostic_only':True}
        if code==0:
            record['result']=json.loads((directory/'stdout.json').read_text())
            assert record['result']['status']=='PASS' and record['result']['mismatches']==0
        cases.append(record)
        (root/'cases-progress.json').write_text(json.dumps(cases,indent=2))
        print(json.dumps(record),flush=True)

# Capture the broadly instrumented graph's actual hot functions on this
# allocation. Diagnostic counters and VTune data are never merged into PGO.
vtune='/share/intel/oneapi-2023.1/vtune/2023.1.0/bin64/vtune'
environment=os.environ.copy()
environment['PROF_DIR']=str(root/'profiles/broad')
environment['INTEL_PROF_DYN_PREFIX']='vtune_diagnostic'
profile={}
with (root/'profile-target.log').open('w') as log:
    target=subprocess.Popen([str(root/'probe-broad'),'38','1000000'],stdout=log,stderr=log,env=environment)
    try:
        time.sleep(1)
        command=[vtune,'-collect','hotspots','-knob','sampling-mode=hw','-knob','enable-stack-collection=true','-knob','sampling-interval=10','-duration','10','-target-pid',str(target.pid),'-r',str(root/'vtune')]
        with (root/'vtune.log').open('w') as output:
            try:
                profile['returncode']=subprocess.run(command,stdout=output,stderr=subprocess.STDOUT,env=environment,timeout=50).returncode
            except subprocess.TimeoutExpired:
                profile['returncode']=124
        profile['command']=command
    finally:
        if target.poll() is None:
            target.terminate()
            try:target.wait(timeout=5)
            except subprocess.TimeoutExpired:target.kill();target.wait()
if profile.get('returncode')==0:
    for name,args in [('summary',['-report','summary']),('hotspots',['-report','hotspots','-group-by','function','-format','csv','-csv-delimiter','comma','-limit','40'])]:
        with (root/('report-'+name+'.log')).open('w') as output:
            try:
                code=subprocess.run([vtune]+args+['-r',str(root/'vtune'),'-report-output',str(root/(name+'.txt' if name=='summary' else name+'.csv'))],stdout=output,stderr=subprocess.STDOUT,timeout=50).returncode
            except subprocess.TimeoutExpired:code=124
        profile[name+'_report_returncode']=code
summary={'runtime_probe_cases':cases,'vtune':profile,'interpretation':'Synthetic diagnostic only: same host, 1-thread then38-thread configurations, plain/broad-PGO/hot-source-PGO sequential. Matrix256x256 times256x64 followed by16 add nodes;10 graph iterations. No model, PPL, official PP/TG or Score. All child timeouts are retained. Diagnostic profiles must never be used as completed model-training profiles.'}
(root/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary),flush=True)
