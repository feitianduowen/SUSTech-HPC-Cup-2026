from pathlib import Path

root = Path(__file__).parent / 'package'
path = root / 'build.sh'
text = path.read_text(encoding='utf-8')
text = text.replace('-fp-model=strict -ffp-contract=off', '-fp-model=precise -ffp-contract=fast')
marker = '    -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx \\\n'
text = text.replace(marker, marker + '    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--no-as-needed,/lib64/libm.so.6,--as-needed" \\\n    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--no-as-needed,/lib64/libm.so.6,--as-needed" \\\n')
path.write_text(text, encoding='utf-8', newline='\n')
