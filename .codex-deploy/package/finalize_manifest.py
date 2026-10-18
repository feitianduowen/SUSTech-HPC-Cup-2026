import hashlib
import json
from pathlib import Path
import re
import sys

root = Path('/work/apac2602/qwen38-cpu')
job = sys.argv[1]
status = (root / 'deployment.status').read_text()
assert status.startswith('READY job=' + job + ' '), status
ppl = json.loads((root / ('llama_bench_results_' + job) / 'perplexity_result.json').read_text())
server = json.loads((root / 'logs/server_smoke_result.json').read_text())
assert ppl['status'] == 'PASS'
assert server['status'] == 'PASS' and server['job_id'] == job
cache = {}
for line in (root / 'llama.cpp/build/CMakeCache.txt').read_text().splitlines():
    match = re.match(r'([^:#]+):[^=]+=(.*)', line)
    if match:
        cache[match[1]] = match[2]
compilers = {}
compiler_ids = {}
compiler_versions = {}
for language in ('C', 'CXX'):
    info = next((root / 'llama.cpp/build/CMakeFiles').glob('*/CMake' + language + 'Compiler.cmake')).read_text()
    compiler_ids[language] = re.search(r'set\(CMAKE_' + language + r'_COMPILER_ID "([^"]+)"\)', info).group(1)
    assert compiler_ids[language] in ('Intel', 'IntelLLVM')
    compiler_versions[language] = re.search(r'set\(CMAKE_' + language + r'_COMPILER_VERSION "([^"]+)"\)', info).group(1)
    compilers[language] = re.search(r'set\(CMAKE_' + language + r'_COMPILER "([^"]+)"\)', info).group(1)
assert compilers['C'].endswith(('/icc', '/icx'))
assert compilers['CXX'].endswith(('/icpc', '/icpx'))
revision = (root / 'reference/source_revision.txt').read_text().strip()
assert revision.startswith('d81235049384534c167caea52b85a694f6103d14 ')
artifact_hashes = {}
bin_dir = root / 'llama.cpp/build/bin'
files = list(bin_dir.glob('lib*.so')) + [bin_dir / name for name in (
    'llama-cli', 'llama-server', 'llama-bench', 'llama-perplexity')]
for path in files:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    artifact_hashes[path.name] = digest.hexdigest()
manifest = {
    'status': 'READY', 'validation_job': job, 'validation_host': server['host'],
    'source_revision': revision, 'compiler': compiler_ids['CXX'] + ' ' + compiler_versions['CXX'],
    'c_compiler': compilers['C'], 'cxx_compiler': compilers['CXX'],
    'c_flags': cache['CMAKE_C_FLAGS'], 'cxx_flags': cache['CMAKE_CXX_FLAGS'],
    'exe_linker_flags': cache['CMAKE_EXE_LINKER_FLAGS'],
    'shared_linker_flags': cache['CMAKE_SHARED_LINKER_FLAGS'],
    'cpu_only': all(cache[key] == 'OFF' for key in (
        'GGML_CUDA', 'GGML_HIP', 'GGML_METAL', 'GGML_VULKAN', 'GGML_OPENCL', 'GGML_SYCL', 'GGML_RPC')),
    'ppl': ppl['ppl'], 'ppl_status': ppl['status'],
    'ppl_relative_difference_percent': ppl['relative_difference_percent'],
    'server_status': server['status'], 'completion_sample': server['completion']['content'],
    'model_assets': json.loads((root / 'logs/assets.json').read_text()),
    'artifact_sha256': artifact_hashes,
    'full_performance_benchmark_run': False,
}
assert manifest['cpu_only']
(root / 'deployment_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({key: manifest[key] for key in ('status', 'compiler', 'ppl', 'ppl_status',
                                              'ppl_relative_difference_percent', 'server_status')}))
