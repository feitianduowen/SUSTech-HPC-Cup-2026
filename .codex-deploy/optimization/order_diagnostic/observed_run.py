"""Read-only observations of one owned child; diagnostic timings are unscored."""
import argparse
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path

def read(path):
    try: return Path(path).read_text()
    except OSError: return None

def node_pages(text):
    result={'model_kb':{},'other_kb':{}}
    for line in (text or '').splitlines():
        parts=line.split()
        size=next((int(x.split('=')[1]) for x in parts if x.startswith('kernelpagesize_kB=')),4)
        bucket=result['model_kb' if any(x.startswith('file=') and '.gguf' in x for x in parts) else 'other_kb']
        for part in parts:
            if part.startswith('N') and '=' in part and part[1:part.index('=')].isdigit():
                k,v=part.split('='); bucket[k]=bucket.get(k,0)+int(v)*size
    return result

def sample(pid):
    start=time.monotonic()
    proc=Path('/proc')/str(pid)
    row={'time_unix':time.time(),'pid':pid}
    stat=read(proc/'stat')
    if stat:
        fields=stat.rsplit(')',1)[1].split()
        row.update(minor_faults=int(fields[7]),major_faults=int(fields[9]),cpu_seconds=(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'),last_cpu=int(fields[36]))
    row['status']='\n'.join(x for x in (read(proc/'status') or '').splitlines() if x.split(':')[0] in ['VmRSS','VmHWM','Threads','Cpus_allowed_list','Mems_allowed_list','voluntary_ctxt_switches','nonvoluntary_ctxt_switches'])
    row['io']=read(proc/'io')
    row['numa']=node_pages(read(proc/'numa_maps'))
    row['host_meminfo']='\n'.join(x for x in (read('/proc/meminfo') or '').splitlines() if x.split(':')[0] in ['MemAvailable','MemFree','Cached','SwapCached','SwapFree','Dirty','Writeback'])
    row['host_vmstat']='\n'.join(x for x in (read('/proc/vmstat') or '').splitlines() if x.startswith(('numa_','pgmajfault ','pgfault ','pgmigrate_','pswpin ','pswpout ')))
    row['node_meminfo']={str(p):read(p) for p in Path('/sys/devices/system/node').glob('node[0-9]*/meminfo')}
    row['sampling_seconds']=time.monotonic()-start
    return row

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--timeout',type=int,default=3600)
    parser.add_argument('--interval',type=int,default=30)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    assert args.command and args.timeout>0 and args.interval>0
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    # One helper process owns exactly one measured child and captures its rusage.
    command=args.command
    output.with_suffix('.command.json').write_text(json.dumps({'argv':command,'sampling_interval_seconds':args.interval,'timeout_seconds':args.timeout,'diagnostic_unscored':True},indent=2))
    start=time.monotonic(); started=time.time(); timed_out=False
    with output.with_suffix('.json').open('w') as stdout, output.with_suffix('.stderr.log').open('w') as stderr, output.with_suffix('.observations.jsonl').open('w') as observations:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        next_sample=0
        while child.poll() is None:
            elapsed=time.monotonic()-start
            if elapsed>=next_sample:
                try: row=sample(child.pid)
                except (OSError,ValueError,IndexError) as error: row={'time_unix':time.time(),'pid':child.pid,'sampling_error':str(error)}
                observations.write(json.dumps(row)+'\n'); observations.flush()
                next_sample=elapsed+args.interval
            if elapsed>=args.timeout:
                timed_out=True
                try: os.killpg(child.pid,signal.SIGTERM)
                except ProcessLookupError: pass
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try: os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError: pass
                    child.wait()
                break
            time.sleep(0.5)
        code=child.wait()
    usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    result={'returncode':code,'timed_out':timed_out,'started_unix':started,'ended_unix':time.time(),'wall_seconds':time.monotonic()-start,'user_cpu_seconds':usage.ru_utime,'system_cpu_seconds':usage.ru_stime,'major_faults':usage.ru_majflt,'minor_faults':usage.ru_minflt,'max_rss_kb':usage.ru_maxrss,'voluntary_context_switches':usage.ru_nvcsw,'involuntary_context_switches':usage.ru_nivcsw,'diagnostic_unscored':True}
    output.with_suffix('.result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    return 124 if timed_out else code

if __name__=='__main__': raise SystemExit(main())
