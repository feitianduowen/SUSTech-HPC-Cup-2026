from pathlib import Path

root = Path(__file__).parent / 'package'
env = root / 'env.sh'
text = env.read_text(encoding='utf-8')
if 'compiler/2023.1.0' not in text:
    text = text.replace('module load cmake/3.28.1 gcc/12.2.0',
                        'module use /share/intel/oneapi-2023.1/modulefiles\nmodule load cmake/3.28.1 gcc/12.2.0 compiler/2023.1.0\nexport CC=icx\nexport CXX=icpx')
env.write_text(text, encoding='utf-8', newline='\n')

for name in ('build.sh', 'benchmark.lsf'):
    path = root / name
    text = path.read_text(encoding='utf-8')
    text = text.replace('module load cmake/3.28.1\nmodule load gcc/12.2.0',
                        'source /work/apac2602/qwen38-cpu/scripts/env.sh')
    if name == 'build.sh':
        text = text.replace('    -DCMAKE_BUILD_TYPE=Release \\\n',
                            '    -DCMAKE_BUILD_TYPE=Release \\\n    -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx \\\n    -DCMAKE_C_FLAGS="--gcc-toolchain=/share/base/e5/gcc/12.2.0 -fp-model=strict -ffp-contract=off" \\\n    -DCMAKE_CXX_FLAGS="--gcc-toolchain=/share/base/e5/gcc/12.2.0 -fp-model=strict -ffp-contract=off" \\\n')
        text = text.replace('    gcc --version | head -n 1\n    g++ --version | head -n 1',
                            '    icx --version | head -n 1\n    icpx --version | head -n 1')
    else:
        text = text.replace('    gcc --version | head -n 1\n    g++ --version | head -n 1',
                            '    icx --version | head -n 1\n    icpx --version | head -n 1')
    path.write_text(text, encoding='utf-8', newline='\n')

path = root / 'bootstrap.lsf'
text = path.read_text(encoding='utf-8')
if 'build-gcc-reference' not in text:
    text = text.replace('cd /work/apac2602/qwen38-cpu\n', '''cd /work/apac2602/qwen38-cpu
if [[ -f llama.cpp/build/CMakeCache.txt ]] && grep -q '^CMAKE_C_COMPILER:FILEPATH=.*/gcc$' llama.cpp/build/CMakeCache.txt; then
  test ! -e llama.cpp/build-gcc-reference
  mv llama.cpp/build llama.cpp/build-gcc-reference
fi
''', 1)
path.write_text(text, encoding='utf-8', newline='\n')
