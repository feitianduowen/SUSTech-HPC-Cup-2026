import difflib
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
base=Path('D:/compete/q8-avx2-v2/source')
identity=json.loads((here.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
variants={}

name='ggml/src/ggml-cpu/llamafile/sgemm.cpp'
raw=(base/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode()
start=text.index('class tinyBLAS_Q0_AVX {')
end=text.index('#endif // __AVX__',start)
part=text[start:end]
old='''        int64_t duty = (tiles + nth - 1) / nth;
        int64_t start = duty * ith;
        int64_t end = start + duty;
        if (end > tiles)
            end = tiles;'''
new='''        // Give each worker floor(tiles/nth) jobs, then distribute the tail.
        // Keep contiguous tiles and the arithmetic inside each tile unchanged.
        const int64_t duty = tiles / nth;
        const int64_t extra = tiles % nth;
        const int64_t start = duty * ith + MIN((int64_t) ith, extra);
        const int64_t end = start + duty + (ith < extra);'''
assert part.count(old)==3
modified=text[:start]+part.replace(old,new)+text[end:]
variants['gemm-balanced']=(name,raw,modified.encode())

name='ggml/src/ggml-cpu/ggml-cpu.c'
raw=(base/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode()
start=text.index('void ggml_compute_forward_mul_mat(')
end=text.index('// ggml_compute_forward_mul_mat_id',start)
part=text[start:end]
assert part.count('    #if 0')==1 and part.count('    #else')==1
part=part.replace('    #if 0','''        // For multi-token F32 input, each worker quantizes complete rows.
        // Small token counts and F16/BF16 widening retain block striping.
        if (src1->type == GGML_TYPE_F32 && ne11 >= nth) {''',1)
part=part.replace('    #else','        } else {',1)
start_cond=part.index('        if (src1->type == GGML_TYPE_F32 && ne11 >= nth) {')
finish=part.index('    #endif',start_cond)
part=part[:finish]+'        }'+part[finish+len('    #endif'):]
lines=part.splitlines(True)
inside=False
for i,line in enumerate(lines):
    if line.startswith('        if (src1->type == GGML_TYPE_F32 && ne11 >= nth) {'):
        inside=True
        continue
    if inside and line.startswith('        } else {'):
        continue
    if inside and line.rstrip()=='        }':
        # Match only the branch closing after the former preprocessor region.
        if i+1<len(lines) and lines[i+1].rstrip()=='    }':
            inside=False
            continue
    if inside and line.strip():lines[i]='    '+line
part=''.join(lines)
modified=text[:start]+part+text[end:]
variants['row-quant']=(name,raw,modified.encode())
manifest={'base_commit':identity['revision'],'variants':{}}
for variant,(name,raw,data) in variants.items():
    out=here/'variants'/variant/name
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(data)
    patch=''.join(difflib.unified_diff(raw.decode().splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    (here/(variant+'.patch')).write_bytes(patch.encode())
    manifest['variants'][variant]={'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}
(here/'manifest.json').write_bytes(json.dumps(manifest,indent=2).encode())
print(json.dumps(manifest,indent=2))
