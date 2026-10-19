#!/bin/bash
set -euo pipefail
PROBE=${1:?probe output directory}
mkdir -p "$PROBE/src" "$PROBE/profiles"
cat > "$PROBE/src/hot.cpp" <<'CPP'
extern "C" int hot(int n) { int sum=0; for(int i=0;i<n;i++) sum+=i; return sum; }
CPP
cat > "$PROBE/src/cold.cpp" <<'CPP'
extern "C" int hot(int); extern "C" int cold(int n) { return hot(n); }
CPP
cat > "$PROBE/src/main.cpp" <<'CPP'
extern "C" int cold(int); int main() { return cold(128)==8128 ? 0 : 1; }
CPP
cat > "$PROBE/src/CMakeLists.txt" <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(qwen_pgo_link_probe LANGUAGES CXX)
add_library(pgo_hot SHARED hot.cpp)
add_library(pgo_cold SHARED cold.cpp)
target_compile_options(pgo_cold PRIVATE -no-prof-gen)
target_link_options(pgo_cold PRIVATE -no-prof-gen)
target_link_libraries(pgo_cold PUBLIC pgo_hot)
add_executable(pgo_link_probe main.cpp)
target_link_libraries(pgo_link_probe PRIVATE pgo_cold)
CMAKE
flags="-gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441 -prof-gen=threadsafe -prof-dir $PROBE/profiles"
cmake -S "$PROBE/src" -B "$PROBE/build" -DCMAKE_CXX_COMPILER=icpc -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "-DCMAKE_CXX_FLAGS=$flags" "-DCMAKE_EXE_LINKER_FLAGS=-prof-gen=threadsafe -prof-dir $PROBE/profiles" "-DCMAKE_SHARED_LINKER_FLAGS=-prof-gen=threadsafe -prof-dir $PROBE/profiles" > "$PROBE/configure.log" 2>&1
cmake --build "$PROBE/build" -j 2 > "$PROBE/build.log" 2>&1
PROF_DIR="$PROBE/profiles" "$PROBE/build/pgo_link_probe" > "$PROBE/run.log" 2>&1
python3 - "$PROBE" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1])
profiles=list((p/'profiles').glob('*.dyn'))
assert profiles and all(x.stat().st_size>0 for x in profiles),'Probe ran but no non-empty profile dump'
d={'link_and_run':'PASS','normal_exit':True,'nonempty_profile_files':len(profiles),'scope':'profiled main and hot shared library, unprofiled cold shared library','profiles':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in profiles}}
(p/'result.json').write_text(json.dumps(d,indent=2))
print(json.dumps(d))
PY
