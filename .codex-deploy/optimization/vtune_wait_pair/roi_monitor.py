import json
import subprocess
import sys
import time
from pathlib import Path
from observed_run import sample

out=Path(sys.argv[1]); vtune=sys.argv[2]; seconds=float(sys.argv[3])
state={'requested_window_seconds':seconds,'marker':'prompt run 1/10','status':'WAITING_FOR_MARKER'}
def save():
    (out/'roi.json').write_text(json.dumps(state,indent=2))
def control(action):
    start=time.time()
    with (out/(action+'.log')).open('w') as log:
        try:
            r=subprocess.run([vtune,'-command',action,'-r',str(out/'vtune')],stdout=log,stderr=subprocess.STDOUT,timeout=45)
            code=r.returncode
        except subprocess.TimeoutExpired: code=124
    result={'requested_unix':start,'completed_unix':time.time(),'returncode':code}
    state[action]=result;save()
    return code

deadline=time.monotonic()+3700
last_sample=0
save()
with (out/'process_observations.jsonl').open('w') as observations:
    while time.monotonic()<deadline:
        if (out/'collector.exit').exists() or (out/'target.exit').exists(): break
        events=out/'events.jsonl'
        if 'resume' not in state and events.exists():
            matching=[]
            for line in events.read_text().splitlines():
                if 'prompt run 1/10' not in line: continue
                try: matching.append(json.loads(line))
                except ValueError: pass
            if matching:
                state['marker_seen_unix']=matching[0]['time_unix']
                if control('resume')!=0:
                    state['status']='RESUME_FAILED';save();raise SystemExit(1)
                state['status']='COLLECTING';save()
        if 'resume' in state and 'pause' not in state and time.time()-state['resume']['completed_unix']>=seconds:
            if control('pause')!=0:
                state['status']='PAUSE_FAILED';save();raise SystemExit(1)
            state['status']='PAUSED_WINDOW_COMPLETE'
            state['control_interval_seconds']=state['pause']['completed_unix']-state['resume']['completed_unix']
            save()
        if (out/'target.pid').exists() and time.monotonic()-last_sample>=30:
            try:
                row=sample(int((out/'target.pid').read_text()))
                row['roi_status']=state['status']
                observations.write(json.dumps(row)+'\n');observations.flush()
            except (OSError,ValueError,IndexError): pass
            last_sample=time.monotonic()
        time.sleep(0.2)
if state.get('status')!='PAUSED_WINDOW_COMPLETE':
    state['status']='WINDOW_INCOMPLETE';save();raise SystemExit(1)
state['target_end_seen_unix']=time.time();save()
