import json
import sys
from pathlib import Path

factor, root = sys.argv[1:]
keys = ['CMAKE_C_COMPILER','CMAKE_CXX_COMPILER','CMAKE_BUILD_TYPE','CMAKE_C_FLAGS','CMAKE_CXX_FLAGS','CMAKE_C_FLAGS_RELEASE','CMAKE_CXX_FLAGS_RELEASE','GGML_LLAMAFILE','GGML_OPENMP','GGML_BLAS','GGML_NATIVE','CMAKE_EXE_LINKER_FLAGS','CMAKE_SHARED_LINKER_FLAGS']
def read(name):
    d={}
    for line in (Path(root)/name/'build/CMakeCache.txt').read_text().splitlines():
        if '=' in line and ':' in line.split('=',1)[0]:
            k,v=line.split('=',1); k=k.split(':',1)[0]
            if k in keys: d[k]=v
    assert set(d)==set(keys), d
    assert Path(d['CMAKE_C_COMPILER']).name=='icc'
    assert Path(d['CMAKE_CXX_COMPILER']).name=='icpc'
    return d
a,b=read('baseline'),read('candidate')
expected=dict(a)
if factor=='tinyblas':
    assert a['GGML_LLAMAFILE']=='ON'
    expected['GGML_LLAMAFILE']='OFF'
elif factor=='optlevel':
    for k in ['CMAKE_C_FLAGS_RELEASE','CMAKE_CXX_FLAGS_RELEASE']:
        assert a[k]=='-O3 -DNDEBUG'
        expected[k]='-O2 -DNDEBUG'
elif factor=='fpmodel':
    for k in ['CMAKE_C_FLAGS','CMAKE_CXX_FLAGS']:
        assert a[k].count('-fp-model precise')==1
        expected[k]=a[k].replace('-fp-model precise','-fp-model fast=1')
else: raise ValueError(factor)
assert expected==b, (expected,b)
print(json.dumps({'factor':factor,'baseline':a,'candidate':b,'single_factor_verified':True},indent=2))
