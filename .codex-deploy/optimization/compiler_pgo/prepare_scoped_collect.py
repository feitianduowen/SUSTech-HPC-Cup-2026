from pathlib import Path

here=Path(__file__).resolve().parent
source=(here.parent/'orchestrator/collect_job_registry.py').read_text(encoding='utf-8')
source=source.replace("registry_lock = (root/'results/job_registry.lock').open('a')\nfcntl.flock(registry_lock.fileno(), fcntl.LOCK_EX)","wanted = {'4336626','4336627','4336716','4336889','4337216','4337222','4337257','4337425','4337427','4337448','4337488'}")
source=source.replace("        spec = json.loads(line)","        spec = json.loads(line)\n        if 'job_id' in spec and spec['job_id'] not in wanted: continue")
source=source.replace("    jid = match[1]", "    jid = match[1]\n    if jid not in wanted: continue")
# Only the scoped snapshot is written; no shared collection lock or old files.
source=source.replace("active = [jid for jid,r in jobs.items() if 'finish_time' not in r]", "active = []  # active state from the job's own stdout/status; scheduler query separate")
source=source.replace("data['admission_evidence'] = [{'path':str(p),'text':p.read_text(errors='replace')} for p in sorted((deploy/'optimization').glob('*/admission_snapshot.txt'))]", "data['admission_evidence'] = []")
source=source.replace("\npath = root/'results/job_registry.json'", "\npath = deploy/'optimization/20261019-compiler-pgo/pgo_scoped_snapshot.json'")
marker="data = {'updated_at':"
pos=source.index(marker)
source=source[:pos]+'''for jid,row in jobs.items():
    run=deploy/'optimization/20261019-compiler-pgo/results'/jid
    for name in ['gen-build/build.log','link-probe/result.json','configuration_amendment.json','relink-result.json','original.command','original.log','no_as_needed.command','no_as_needed.log','shared_intel.command','shared_intel.log','gen-build/pgo-scope-prebuild.json','control-reuse.txt','control-parent-sha256.txt','training-pp.log','training-tg.log','training-os.jsonl']:
        file=run/name
        if file.is_file():
            with file.open('rb') as handle:
                size=file.stat().st_size
                handle.seek(max(0,size-20000))
                tail=handle.read().decode('utf-8',errors='replace')
            row['evidence'].append({'path':str(file),'text':tail})
    for evidence in row['evidence']:
        if evidence['path'].endswith('/environment.txt'):
            match=re.search(r'^r13n[0-9]+$',evidence['text'],re.M)
            if match and not row.get('exec_host'): row['exec_host']='40*'+match[0]
'''+source[pos:]
source=source.replace("'training-pp.command','training-tg.command'", "'training-pp.command','training-tg.command','gen-build/configure.command','gen-build/pgo-scope.json','control-build/pgo-scope.json','pgo-build/pgo-scope.json','training-validation.json','training-pp.log','training-tg.log'")
(here/'collect_pgo_scoped.py').write_bytes(source.encode())
print(here/'collect_pgo_scoped.py')
