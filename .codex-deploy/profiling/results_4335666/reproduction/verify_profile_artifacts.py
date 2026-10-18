#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path
root, out = Path(sys.argv[1]), Path(sys.argv[2])
manifest = json.loads((root / 'deployment_manifest.json').read_text())
checks = {}
for name, expected in manifest['artifact_sha256'].items():
    digest = hashlib.sha256()
    with (root / 'llama.cpp/build/bin' / name).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    actual = digest.hexdigest()
    checks[name] = {'expected': expected, 'actual': actual, 'match': actual == expected}
result = {'all_match': all(c['match'] for c in checks.values()), 'checks': checks}
out.write_text(json.dumps(result, indent=2))
print(json.dumps({'all_match': result['all_match'], 'artifact_count': len(checks)}))
sys.exit(0 if result['all_match'] else 1)
