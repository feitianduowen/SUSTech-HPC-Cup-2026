import array
import json
import subprocess
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization/20261020-hc4-post')
out=root/'results/4340908'
rows=[]
with (out/'baseline.bin').open('rb') as a,(out/'candidate.bin').open('rb') as b:
    for threads in [1,3,38]:
        for e,t in [(1,1),(7,3),(16,1),(31,39),(32,3),(33,1),(257,3),(2560,1),(2560,39)]:
            for hc in [1,2,4,8]:
                for layout in [0,1,2]:
                    for mixing in [0,1,2]:
                        n=e*t*hc*4
                        aa=a.read(n);bb=b.read(n)
                        assert len(aa)==len(bb)==n
                        if aa!=bb:
                            av=array.array('f');av.frombytes(aa)
                            bv=array.array('f');bv.frombytes(bb)
                            diffs=[abs(float(x)-float(y)) for x,y in zip(av,bv) if x!=y]
                            rows.append({'threads':threads,'embd':e,'tokens':t,'hc':hc,'layout':layout,'mixing':mixing,'mismatches':sum(x!=y for x,y in zip(memoryview(aa).cast('I'),memoryview(bb).cast('I'))),'max_absolute_error':max(diffs) if diffs else 0})
    assert not a.read(1) and not b.read(1)
diagnostic={'different_cases':len(rows),'all_hc4':all(r['hc']==4 for r in rows),'all_contiguous_innermost':all(r['layout'] in [0,1] for r in rows),'all_dense_comb':all(r['mixing']==2 for r in rows),'mismatches':sum(r['mismatches'] for r in rows),'max_absolute_error':max(r['max_absolute_error'] for r in rows),'cases':rows}
(out/'difference-diagnostic.json').write_text(json.dumps(diagnostic,indent=2))
print(json.dumps({k:v for k,v in diagnostic.items() if k!='cases'}))
for name,lib in [('baseline',Path('/work/apac2602/qwen38-cpu/llama.cpp/build/bin/libggml-cpu.so')),('candidate',root/'sources/hc4-post-4340908/build/bin/libggml-cpu.so')]:
    symbols=subprocess.check_output(['nm','-S',str(lib)],universal_newlines=True).splitlines()
    matches=[r.split() for r in symbols if 'ggml_compute_forward_dsv4_hc_post' in r and '_f32' not in r]
    assert len(matches)==1,matches
    sym=matches[0];start=int(sym[0],16);end=start+int(sym[1],16)
    asm=subprocess.check_output(['objdump','-d','-C','--no-show-raw-insn','--start-address='+hex(start),'--stop-address='+hex(end),str(lib)],universal_newlines=True)
    (root/(name+'-hc.asm')).write_text(asm)
    relevant=[r for r in asm.splitlines() if any(op in r for op in ['mulss','addss','mulps','addps','fmadd','fmsub'])]
    print(name+' arithmetic instructions:')
    print('\n'.join(relevant[:65]))
