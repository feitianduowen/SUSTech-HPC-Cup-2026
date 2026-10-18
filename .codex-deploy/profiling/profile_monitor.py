#!/usr/bin/env python3
import json, os, subprocess, sys, time
from pathlib import Path

out, vtune, marker = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
resumed = False
pidstat = None
last_sample = 0
deadline = time.time() + 7200
with (out / 'system.jsonl').open('w') as stats:
    while time.time() < deadline:
        if (out / 'target.pid').exists():
            pid = int((out / 'target.pid').read_text())
            if not resumed and (out / 'events.jsonl').exists() and marker in (out / 'events.jsonl').read_text():
                start = time.time()
                with (out / 'resume.log').open('w') as log:
                    rc = subprocess.call([vtune, '-command', 'resume', '-r', str(out / 'vtune')], stdout=log, stderr=subprocess.STDOUT)
                (out / 'resume.json').write_text(json.dumps({'requested': start, 'completed': time.time(), 'returncode': rc}))
                resumed = True
            if pidstat is None:
                try:
                    pidstat = subprocess.Popen(['pidstat', '-t', '-u', '-r', '-w', '-p', str(pid), '5'], stdout=(out / 'pidstat.txt').open('w'), stderr=subprocess.STDOUT)
                except OSError:
                    pidstat = False
            if time.time() - last_sample >= 5:
                try:
                    proc = Path('/proc') / str(pid)
                    status = {}
                    for line in (proc / 'status').read_text().splitlines():
                        key, value = line.split(':', 1)
                        if key in ['VmRSS', 'VmHWM', 'Threads', 'Cpus_allowed_list', 'Mems_allowed_list']:
                            status[key] = value.strip()
                    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
                    nodes = {}
                    for line in (proc / 'numa_maps').read_text().splitlines():
                        parts = line.split()
                        page_kb = next((int(x.split('=')[1]) for x in parts if x.startswith('kernelpagesize_kB=')), 4)
                        for item in parts:
                            if item.startswith('N') and '=' in item and item[1:item.index('=')].isdigit():
                                node, pages = item.split('=')
                                nodes[node] = nodes.get(node, 0) + int(pages) * page_kb
                    record = {'time': time.time(), 'status': status, 'cpu_seconds': (int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK'), 'minor_faults': int(fields[7]), 'major_faults': int(fields[9]), 'numa_kb': nodes}
                    stats.write(json.dumps(record) + '\n')
                    stats.flush()
                    last_sample = time.time()
                except (OSError, ValueError, ProcessLookupError):
                    pass
        if (out / 'target.exit').exists() or (out / 'collector.exit').exists():
            break
        time.sleep(0.2)
if pidstat:
    pidstat.terminate()
if not resumed:
    sys.exit('ROI marker not reached')
