import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'orchestrator'))
from ppl_policy5 import reassess

reference=json.loads((root/'evidence/ppl_policy_reference.json').read_text(encoding='utf-8'))

class RuleTests(unittest.TestCase):
    def record(self,value):
        result=copy.deepcopy(reference)
        result.update(ppl=value,status='FAIL',baseline_ppl=2.7696,elapsed_seconds=10)
        return result

    def test_saved_results_and_inclusive_boundaries(self):
        for value,expected in [(2.63112,'PASS'),(2.90808,'PASS'),(2.63111999,'FAIL'),(2.90808001,'FAIL'),(2.7893,'PASS'),(2.8403,'PASS')]:
            with self.subTest(value=value):
                self.assertEqual(reassess(self.record(value),reference)['verdict'],expected)

    def test_other_requirements_are_still_required(self):
        changes=[{'elapsed_seconds':591},{'status':'TIMEOUT'},{'baseline_ppl':2.7767},{'ppl':float('nan')},{'ppl':None},{'schema':'wrong'}]
        for change in changes:
            with self.subTest(change=change):
                result=self.record(2.7893)
                result.update(change)
                self.assertEqual(reassess(result,reference)['verdict'],'无法确认')
        wrong=self.record(2.7893)
        wrong['conditions']['threads']=37
        self.assertEqual(reassess(wrong,reference)['verdict'],'无法确认')
        self.assertEqual(reassess(None,reference)['verdict'],'未运行')

    def test_exact_embedded_gate_with_synthetic_files(self):
        # This executes the real gate validator, with tiny synthetic fixture
        # files. It is a policy test, not a model PPL run or an LSF submission.
        gate=(root/'compiler_pgo/ppl_gate.lsf').read_text(encoding='utf-8')
        marker=gate.index('# Require a completed, finite PPL')
        begin=gate.index("<<'PY'\n",marker)+len("<<'PY'\n")
        code=gate[begin:gate.index('\nPY\n',begin)]
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            model=folder/'test.gguf'; model.write_bytes(b'model-fixture')
            data=folder/'data.txt'; data.write_bytes(b'text-fixture')
            fixture=copy.deepcopy(reference)
            fixture['conditions']['model_files_path_and_size']=[[str(model.resolve()),model.stat().st_size]]
            fixture['conditions']['data_sha256']=hashlib.sha256(data.read_bytes()).hexdigest()
            ref=folder/'reference.json'; ref.write_text(json.dumps(fixture),encoding='utf-8')
            for value,expected in [('2.63112','PASS'),('2.90808','PASS'),('2.63111999','FAIL'),('2.90808001','FAIL'),('2.7893','PASS')]:
                with self.subTest(gate_value=value):
                    log=folder/'ppl.log'
                    log.write_text('calculating perplexity over 2 chunks, n_ctx=512, batch_size=512\nFinal estimate: PPL = '+value+'\n',encoding='utf-8')
                    output=folder/'result.json'
                    args=[str(log),str(output),str(ref),str(model),str(data),'512','2','512','256','38','5','5']
                    run=subprocess.run([sys.executable,'-c',code]+args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    self.assertEqual(run.returncode,0 if expected=='PASS' else 2,run.stderr.decode())
                    result=json.loads(output.read_text(encoding='utf-8'))
                    self.assertEqual(result['status'],expected)
                    self.assertEqual(result['tolerance_percent'],5)
            log.write_text('calculating perplexity over 2 chunks, n_ctx=512, batch_size=512\n[1]2.7767,',encoding='utf-8')
            run=subprocess.run([sys.executable,'-c',code]+args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertNotEqual(run.returncode,0,'Partial output must not pass')

    def test_fixed_operational_parameters(self):
        for path in [root/'compiler_pgo/ppl_gate.lsf',root/'q8_avx2_v2/ppl_gate.lsf',root/'source_v2/ppl_gate.lsf']:
            text=path.read_text(encoding='utf-8')
            for declaration in ['PPL_CTX=512','PPL_CHUNKS=2','PPL_BATCH=512','PPL_UBATCH=256','PPL_TIMEOUT_SECONDS=590','THREADS=38','REPS=10','BATCH=2048','UBATCH=512']:
                self.assertIn(declaration,text,str(path))

if __name__=='__main__':
    unittest.main(verbosity=2)
