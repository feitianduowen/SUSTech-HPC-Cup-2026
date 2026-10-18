import json, os, re, subprocess, time
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261018-v1')
deadline=time.time()+1800
while time.time()<deadline:
    log=(root/'concat-setup.log').read_text(errors='replace')
    if 'HEAD is now at d812350' in log:
        break
    time.sleep(5)
else:
    raise RuntimeError('checkout not ready')
src=root/'sources/concat'
subprocess.check_call(['git','-C',str(src),'apply','--check',str(root/'patches/concat-rows.patch')])
subprocess.check_call(['git','-C',str(src),'apply',str(root/'patches/concat-rows.patch')])
def submit(script, env, dependency=None):
    args=['bsub']
    if dependency:
        args+=['-w',dependency]
    with (root/'scripts'/script).open() as stdin:
        text=subprocess.check_output(args,stdin=stdin,env=dict(os.environ,**env),cwd=str(root)).decode()
    print(text,flush=True)
    return int(re.search(r'Job <(\d+)>',text)[1])
build=submit('build_variant.lsf',{'EXPERIMENT_VARIANT':'concat'})
test=submit('concat_test.lsf',{},'done(%d)'%build)
bench=submit('benchmark_variant.lsf',{'EXPERIMENT_VARIANT':'concat'},'done(%d)'%test)
(root/'results/concat_jobs.json').write_text(json.dumps({'build':build,'test':test,'benchmark':bench},indent=2))
