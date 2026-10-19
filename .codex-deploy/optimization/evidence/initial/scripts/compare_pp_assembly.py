import collections, hashlib, json, re, subprocess, sys
from pathlib import Path

root=Path(sys.argv[1])
result={}
for name in ['reference','candidate']:
    text=subprocess.check_output(['objdump','-d','-C','--no-show-raw-insn',str(root/(name+'.o'))]).decode()
    sections=re.split(r'(?m)^[0-9a-f]+ <',text)
    functions=[]
    for section in sections[1:]:
        symbol,_,body=section.partition('>:\n')
        if 'tinyBLAS_Q0_AVX<block_q8_0, block_q8_0, float>::gemm4xN<4>' not in symbol:
            continue
        instructions=[]
        for line in body.splitlines():
            match=re.match(r'\s*[0-9a-f]+:\s+(\S+)(.*)',line)
            if match:
                instructions.append((match[1],match[2].strip()))
        functions.append({'symbol':symbol,'instructions':len(instructions),'mnemonics':dict(collections.Counter(x[0] for x in instructions))})
    result[name]=functions
    symbols=subprocess.check_output(['nm','-S','-C','--defined-only',str(root/(name+'.o'))]).decode()
    subprocess.check_call(['objcopy','--dump-section','.text='+str(root/(name+'.text')),str(root/(name+'.o'))])
    data=(root/(name+'.text')).read_bytes()
    for line in symbols.splitlines():
        if 'tinyBLAS_Q0_AVX<block_q8_0, block_q8_0, float>::gemm4xN<4>' in line:
            fields=line.split(None,3)
            offset,size=int(fields[0],16),int(fields[1],16)
            functions[0]['code_bytes']=size
            functions[0]['code_sha256']=hashlib.sha256(data[offset:offset+size]).hexdigest()
(root/'assembly_comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
