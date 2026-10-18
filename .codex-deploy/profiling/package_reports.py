#!/usr/bin/env python3
import hashlib, json, sys, zipfile
from pathlib import Path

root = Path(sys.argv[1])
deploy = root.parent.parent
assert json.loads((root / 'analysis.json').read_text())['pp2048']['workload_valid']
assert json.loads((root / 'analysis.json').read_text())['tg128_d2048']['workload_valid']
for name in ['pp2048', 'tg128_d2048']:
    logs = sorted((root / name / 'vtune/data.0').glob('amplxe-perf*.log'))
    (root / name / 'collector-perf.log').write_text('\n'.join('FILE: '+p.name+'\n'+p.read_text(errors='replace') for p in logs))
files = [(p, p.relative_to(root).as_posix()) for p in root.iterdir() if p.is_file() and p.suffix in ['.json', '.txt', '.log', '.ready', '.md', '.png']]
for name in ['pp2048', 'tg128_d2048']:
    files += [(p, p.relative_to(root).as_posix()) for p in (root / name).iterdir() if p.is_file() and p.stat().st_size > 0]
for name in ['profile_probe.py', 'profile_probe.lsf', 'profile_exec.py', 'profile_monitor.py', 'profile_cases.lsf', 'profile_status.py', 'analyze_profiles.py', 'verify_profile_artifacts.py', 'export_extra_profile_reports.sh']:
    files.append((deploy / 'scripts' / name, 'reproduction/' + name))
files.append((deploy / 'profiling/README.md', 'reproduction/README.md'))
files.append((deploy / 'reference/task_rules_CN_20261018.md', 'reproduction/task_rules_CN.md'))
manifest = {rel: hashlib.sha256(p.read_bytes()).hexdigest() for p,rel in files}
(root / 'reports_sha256.json').write_text(json.dumps(manifest, indent=2))
with zipfile.ZipFile(str(root / 'reports.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
    for path, rel in files:
        archive.write(str(path), rel)
    archive.write(str(root / 'reports_sha256.json'), 'reports_sha256.json')
print(json.dumps({'archive': str(root/'reports.zip'), 'files': len(files), 'bytes': (root/'reports.zip').stat().st_size}))
