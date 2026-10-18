#!/usr/bin/env python3
import json, os, subprocess, sys, time
from pathlib import Path

out = Path(sys.argv[1])
cmd = sys.argv[2:]
with (out / 'bench.json').open('w') as stdout, (out / 'bench.log').open('w') as stderr, (out / 'events.jsonl').open('w') as events:
    p = subprocess.Popen(cmd, stdout=stdout, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)
    (out / 'target.pid').write_text(str(p.pid))
    (out / 'command.json').write_text(json.dumps(cmd, indent=2))
    for line in p.stderr:
        stderr.write(line)
        stderr.flush()
        events.write(json.dumps({'time': time.time(), 'text': line.rstrip()}) + '\n')
        events.flush()
    rc = p.wait()
    (out / 'target.exit').write_text(str(rc))
sys.exit(rc)
