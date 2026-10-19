import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


script = Path(sys.argv[1]).read_text(encoding='utf-8')
start = script.index('import hashlib\nimport json\nimport math\n')
code = script[start:script.index('\nPY\nthen',start)]
assert 'PPL_MAX_REL_DIFF_PERCENT=5.0' in script


def adjacent(value, step):
    bits = struct.unpack('>Q',struct.pack('>d',value))[0]
    return struct.unpack('>d',struct.pack('>Q',bits+step))[0]


cases = [('lower',2.63112,True),('upper',2.90808,True),
         ('below_lower',adjacent(2.63112,-1),False),
         ('above_upper',adjacent(2.90808,1),False),
         ('inside_lower',adjacent(2.63112,1),True),
         ('inside_upper',adjacent(2.90808,-1),True),
         ('baseline',2.7696,True),('former_fail',2.8403,True),
         ('outside',3.0,False),('nonfinite','NaN',False),
         ('mismatched_conditions',2.7696,False)]
results = []
with tempfile.TemporaryDirectory(prefix='ppl-policy-unit-') as directory:
    root = Path(directory)
    model = root/'fixture.gguf'; model.write_bytes(b'unit-test-only')
    data = root/'fixture.txt'; data.write_bytes(b'unit-test-only\n')
    conditions = {'model_files_path_and_size':[[str(model.resolve()),model.stat().st_size]],
                  'data_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
                  'ppl_ctx':512,'ppl_chunks':2,'ppl_batch':512,'ppl_ubatch':256,
                  'threads':38,'kv_cache_k':'f16','kv_cache_v':'f16',
                  'numa':'distribute','warmup':False,'gpu_layers':0}
    for name,value,expected in cases:
        condition = dict(conditions)
        if name=='mismatched_conditions':
            condition['ppl_ubatch']=128
        reference = {'schema':'llama_cpp_ppl_regression_v1','status':'REFERENCE_RECORDED',
                     'ppl':2.7696,'tolerance_percent':0.5,'conditions':condition}
        baseline = root/'reference.json';baseline.write_text(json.dumps(reference))
        log = root/'fixture.log'
        log.write_text('calculating perplexity over 2 chunks, n_ctx=512, batch_size=512\nFinal estimate: PPL = '+str(value)+'\n')
        result = root/'result.json'
        if result.exists():result.unlink()
        args = [str(log),str(result),str(baseline),str(model),str(data),'512','2','512','256','38','5.0','1']
        run = subprocess.run([sys.executable,'-c',code]+args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        passed = run.returncode==0
        assert passed==expected,(name,run.returncode,run.stdout,run.stderr)
        if result.exists():
            record=json.loads(result.read_text())
            assert record['tolerance_percent']==5.0
            assert record['policy_id']=='20261019-ppl-tolerance-5pct'
            assert record['accepted_ppl_interval']==[2.63112,2.90808]
            assert record['conditions']==conditions
        assert json.loads(baseline.read_text())==reference
        results.append({'case':name,'expected_acceptance':expected,'verified':True})
print(json.dumps({'unit_tests_only':True,'no_model_inference':True,'cases':results,'passed':len(results)}))
