import json,shlex,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1])
root=out.parent.parent
build=root/'builds/4337222/gen/build/tools/llama-bench'
original=shlex.split((build/'CMakeFiles/llama-bench.dir/link.txt').read_text())
results=[]
for name,extra in [('original',[]),('no_as_needed',['-Wl,--no-as-needed']),('shared_intel',['-shared-intel'])]:
    command=list(original)
    command[command.index('-o')+1]=str(out/('llama-bench-'+name))
    command[command.index('-prof-dir')+1]=str(out/'nontraining-profiles')
    insert=next(i for i,x in enumerate(command) if x.endswith('main.cpp.o'))
    command[insert:insert]=extra
    (out/(name+'.command')).write_text(' '.join(shlex.quote(x) for x in command)+'\n')
    with (out/(name+'.log')).open('w') as log:
        completed=subprocess.run(command,cwd=str(build),stdout=log,stderr=subprocess.STDOUT,timeout=180)
    results.append({'variant':name,'returncode':completed.returncode,'link_pass':completed.returncode==0,'executable_run':False,'note':'Link-only diagnostic; never runs old instrumented objects or loads the model; old build and profiles remain read-only.'})
(out/'relink-result.json').write_text(json.dumps({'baseline':'original link command from failed 4337222','results':results},indent=2))
print(json.dumps(results))
assert results[0]['returncode']!=0,'Original failure did not reproduce'
assert any(x['link_pass'] for x in results[1:]),'No repair variant links'
