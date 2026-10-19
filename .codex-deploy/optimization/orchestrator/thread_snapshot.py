import json
import os
import socket
import sys
import time
from pathlib import Path

result={'time':time.time(),'host':socket.gethostname(),'processes':[]}
for p in Path('/proc').iterdir():
    if not p.name.isdigit(): continue
    try:
        if p.stat().st_uid != os.getuid(): continue
        cmd=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
        if not cmd or not cmd[0].endswith(('/llama-bench','/llama-perplexity')): continue
        proc={'pid':int(p.name),'command':cmd,'threads':[],'numa_kb':{}}
        for t in (p/'task').iterdir():
            fields=(t/'stat').read_text().rsplit(')',1)[1].split()
            masks={}
            for line in (t/'status').read_text().splitlines():
                key,value=line.split(':',1)
                if key in ['Cpus_allowed_list','Mems_allowed_list','State']:
                    masks[key]=value.strip()
            proc['threads'].append({'tid':int(t.name),'state':fields[0],'cpu_seconds':(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'),'processor':int(fields[36]),**masks})
        for line in (p/'numa_maps').read_text().splitlines():
            parts=line.split()
            category='gguf' if '.gguf' in line else ('anonymous' if any(x.startswith('anon=') for x in parts) else 'other')
            size=next((int(x.split('=')[1]) for x in parts if x.startswith('kernelpagesize_kB=')),4)
            nodes=proc['numa_kb'].setdefault(category,{})
            for part in parts:
                if part.startswith('N') and '=' in part and part[1:part.index('=')].isdigit():
                    key,value=part.split('=');nodes[key]=nodes.get(key,0)+int(value)*size
        result['processes'].append(proc)
    except (OSError,ValueError,ProcessLookupError):
        pass
freq={}
for p in Path('/sys/devices/system/cpu').glob('cpu[0-9]*/cpufreq/scaling_cur_freq'):
    try: freq[p.parent.parent.name]=int(p.read_text())
    except OSError: pass
result['cpu_frequency_khz_snapshot']=freq
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
path=out/('threads_numa_%d.json'%int(time.time()))
path.write_text(json.dumps(result,indent=2))
for proc in result['processes']:
    counts={}
    for t in proc['threads']:
        key=t['Cpus_allowed_list'];counts[key]=counts.get(key,0)+1
    print(json.dumps({'host':result['host'],'pid':proc['pid'],'command':proc['command'],'affinity_threads':counts,'numa_kb':proc['numa_kb']}))
