import json, os, sys, time
from pathlib import Path

out = Path(sys.argv[1])
watch = Path(sys.argv[2]) if len(sys.argv)>2 else None
deadline = time.time()+7200
idle = 0
with out.open('w') as stream:
    while time.time()<deadline and (watch is not None or idle<4):
        if watch is not None and watch.exists() and watch.read_text().strip() in ['READY','FAILED']:
            break
        found = False
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                if proc.stat().st_uid != os.getuid():
                    continue
                cmd = (proc/'cmdline').read_bytes().split(b'\0')
                if not cmd or not cmd[0].endswith(b'/llama-bench'):
                    continue
                found = True
                fields = (proc/'stat').read_text().rsplit(')',1)[1].split()
                status = {}
                for line in (proc/'status').read_text().splitlines():
                    k,v = line.split(':',1)
                    if k in ['VmRSS','Threads','Cpus_allowed_list','Mems_allowed_list']:
                        status[k]=v.strip()
                nodes = {}
                for line in (proc/'numa_maps').read_text().splitlines():
                    parts = line.split()
                    size = next((int(x.split('=')[1]) for x in parts if x.startswith('kernelpagesize_kB=')),4)
                    for part in parts:
                        if part.startswith('N') and '=' in part and part[1:part.index('=')].isdigit():
                            k,v=part.split('=')
                            nodes[k]=nodes.get(k,0)+int(v)*size
                stream.write(json.dumps({'time':time.time(),'pid':int(proc.name),'command':[x.decode(errors='replace') for x in cmd if x], 'status':status,'numa_kb':nodes,'cpu_seconds':(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'),'minor_faults':int(fields[7]),'major_faults':int(fields[9])})+'\n')
                stream.flush()
            except (OSError,ValueError,ProcessLookupError):
                pass
        idle = 0 if found else idle+1
        time.sleep(15)
