from pathlib import Path

root = Path(__file__).parent / 'package'
env = root / 'env.sh'
text = env.read_text(encoding='utf-8').replace('gcc/12.2.0 compiler/2023.1.0', 'gcc/11.2.0 icc/2023.1.0')
text = text.replace('export CC=icx', 'export CC=icc').replace('export CXX=icpx', 'export CXX=icpc')
env.write_text(text, encoding='utf-8', newline='\n')
path = root / 'build.sh'
text = path.read_text(encoding='utf-8').replace('-DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx', '-DCMAKE_C_COMPILER=icc -DCMAKE_CXX_COMPILER=icpc')
text = text.replace('icx --version', 'icc --version').replace('icpx --version', 'icpc --version')
old = '--gcc-toolchain=/share/base/e5/gcc/12.2.0 -fp-model=precise -ffp-contract=fast'
c = '-gcc-name=/share/base/e5/gcc/11.2.0/bin/gcc -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
cxx = '-gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
text = text.replace('-DCMAKE_C_FLAGS="' + old + '"', '-DCMAKE_C_FLAGS="' + c + '"')
text = text.replace('-DCMAKE_CXX_FLAGS="' + old + '"', '-DCMAKE_CXX_FLAGS="' + cxx + '"')
path.write_text(text, encoding='utf-8', newline='\n')
path = root / 'benchmark.lsf'
text = path.read_text(encoding='utf-8').replace('icx --version', 'icc --version').replace('icpx --version', 'icpc --version')
path.write_text(text, encoding='utf-8', newline='\n')
