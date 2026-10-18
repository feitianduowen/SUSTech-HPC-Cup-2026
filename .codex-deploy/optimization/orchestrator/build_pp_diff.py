import json, shlex, subprocess, sys
from pathlib import Path

root = Path('/work/apac2602/qwen38-cpu')
experiment = root/'optimization/20261018-v1'
out = Path(sys.argv[1])
base = root/'llama.cpp'
candidate = experiment/'sources/pp-reuse'
commands = json.loads((base/'build/compile_commands.json').read_text())
entry = next(c for c in commands if c['file'].endswith('/llamafile/sgemm.cpp'))
original = shlex.split(entry['command'])
flags = original[1:original.index('-o')]
flags += ['-I'+str(base/'ggml/src/ggml-cpu/llamafile')]
for name, src in [('reference',base/'ggml/src/ggml-cpu/llamafile/sgemm.cpp'),('candidate',Path(sys.argv[2]) if len(sys.argv)>2 else candidate/'ggml/src/ggml-cpu/llamafile/sgemm.cpp')]:
    cmd = [original[0]]+flags+['-Dllamafile_sgemm=sgemm_'+name,'-c',str(src),'-o',str(out/(name+'.o'))]
    subprocess.check_call(cmd)
libdir = base/'build/bin'
cmd = [original[0]]+flags+[str(experiment/'scripts/pp-diff.cpp'),str(out/'reference.o'),str(out/'candidate.o'),'-L'+str(libdir),'-lggml-cpu','-lggml-base','-Wl,-rpath,'+str(libdir),'-Wl,--no-as-needed,/lib64/libm.so.6,--as-needed','-o',str(out/'pp-diff')]
subprocess.check_call(cmd)
subprocess.check_call([str(out/'pp-diff')])
for name in ['reference','candidate']:
    with (out/(name+'.asm')).open('w') as f:
        subprocess.check_call(['objdump','-d',str(out/(name+'.o'))],stdout=f)
