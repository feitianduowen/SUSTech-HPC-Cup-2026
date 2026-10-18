import hashlib
import json
import os
import struct
from pathlib import Path

ref = json.loads(Path(os.environ['PPL_BASELINE_JSON']).read_text())
assert ref['schema'] == 'llama_cpp_ppl_regression_v1'
assert ref['status'] == 'REFERENCE_RECORDED'
assert ref['ppl'] == 2.7696 and ref['tolerance_percent'] == 0.5
records = []
for name, size in ref['conditions']['model_files_path_and_size']:
    path = Path(name)
    assert path.stat().st_size == size, name
    with path.open('rb') as stream:
        magic, version = struct.unpack('<4sI', stream.read(8))
    assert magic == b'GGUF' and version in (2, 3), name
    records.append({'path': name, 'size': size, 'gguf_version': version})
assert len(records) == 4
digest = hashlib.sha256(Path(os.environ['PPL_DATA']).read_bytes()).hexdigest()
assert digest == '173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08'
assert digest == ref['conditions']['data_sha256']
print(json.dumps({'model_shards': records, 'data_sha256': digest, 'baseline_ppl': ref['ppl']}, indent=2))
