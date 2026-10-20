import difflib
import hashlib
import json
from pathlib import Path

r=Path(__file__).resolve().parent
old=r.parent/'q5_mask_20261019'
root='/work/apac2602/qwen38-cpu/optimization/20261020-q5-paircvt'
identity=json.loads((r.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
name='ggml/src/ggml-cpu/arch/x86/quants.c'
raw=(Path('D:/compete/q8-avx2-v2/source')/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode();a=text.index('void ggml_vec_dot_q5_1_q8_1(');b=text.index('#elif defined(__AVX__)',a)
part=text[a:b]
before='''        const __m256 dx = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[ib].d));

        summs += GGML_CPU_FP16_TO_FP32(x[ib].m) * GGML_CPU_FP16_TO_FP32(y[ib].s);'''
after='''#if defined(__F16C__) || defined(__AVX512F__)
        // Convert d_x, m_x, d_y, s_y together instead of four table lookups.
        // Keep the original scale products and accumulator order below.
        uint32_t xdm, yds;
        memcpy(&xdm, &x[ib].d, sizeof(xdm));
        memcpy(&yds, &y[ib].d, sizeof(yds));
        const __m128 scales = _mm_cvtph_ps(_mm_unpacklo_epi32(
                _mm_cvtsi32_si128((int) xdm), _mm_cvtsi32_si128((int) yds)));
        const __m256 dx = _mm256_set1_ps(_mm_cvtss_f32(scales));
        const __m256 dy = _mm256_set1_ps(_mm_cvtss_f32(_mm_shuffle_ps(scales, scales, 0xaa)));
        const float mx = _mm_cvtss_f32(_mm_shuffle_ps(scales, scales, 0x55));
        const float sy = _mm_cvtss_f32(_mm_shuffle_ps(scales, scales, 0xff));
        summs += mx * sy;
#else
        const __m256 dx = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[ib].d));
        const __m256 dy = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(y[ib].d));
        summs += GGML_CPU_FP16_TO_FP32(x[ib].m) * GGML_CPU_FP16_TO_FP32(y[ib].s);
#endif'''
assert part.count(before)==1
part=part.replace(before,after)
late='''        const __m256 dy = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(y[ib].d));
        const __m256i qy'''
assert part.count(late)==1
part=part.replace(late,'        const __m256i qy')
data=(text[:a]+part+text[b:]).encode()
p=r/'variants/q5-paircvt'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
(r/'q5-paircvt.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
(r/'manifest.json').write_text(json.dumps({'base_commit':identity['revision'],'variants':{'q5-paircvt':{'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}}},indent=2),encoding='utf-8')
for f in ['copy_verify.py','ppl_gate.lsf','matmul_check.cpp','compare.py','disassemble.py']:
    s=(old/f).read_text(encoding='utf-8').replace('20261019-q5-mask','20261020-q5-paircvt').replace('bit-exact required; integer-only unpack change','bit-exact required; finite FP16 conversion batching')
    (r/f).write_bytes(s.encode())
s=(old/'dot_check.cpp').read_text(encoding='utf-8')
marker='        if(std::fclose(out))return 9;'
assert s.count(marker)==1
extra='''        // Every finite FP16 bit pattern in each of the four scale fields.
        // Compare actual production and candidate libraries, not a copied kernel.
        for(int field=0;field<4;++field)for(unsigned bits=0;bits<65536;++bits) {
            if((bits&0x7c00u)==0x7c00u)continue; // NaN/Inf are not finite scales
            uint8_t ax[sizeof(Q5)],ay[sizeof(Q8)];
            fill(ax,ay,1,0,0x314159u);
            Q5 a;Q8 b;std::memcpy(&a,ax,sizeof(a));std::memcpy(&b,ay,sizeof(b));
            if(field==0)a.d=uint16_t(bits);
            if(field==1)a.m=uint16_t(bits);
            if(field==2)b.d=uint16_t(bits);
            if(field==3)b.s=uint16_t(bits);
            float first=0;
            for(int repeat=0;repeat<3;++repeat) {
                float value=0;fn(32,&value,0,&a,0,&b,0,1);
                if(!std::isfinite(value))return 6;
                if(repeat==0)first=value;
                else if(std::memcmp(&value,&first,4))return 7;
            }
            if(std::fwrite(&first,4,1,out)!=1)return 8;
            ++cases;
        }
'''
(r/'dot_check.cpp').write_bytes(s.replace(marker,extra+marker).encode())
s=(old/'bench.py').read_text(encoding='utf-8').replace('8480','262432').replace('Q5 actual-library','Q5 paired-FP16-conversion actual-library')
(r/'bench.py').write_bytes(s.encode())
s=(old/'build_and_pair.lsf').read_text(encoding='utf-8').replace('20261019-q5-mask','20261020-q5-paircvt').replace('q5-mask','q5-paircvt').replace('q5_mask','q5_paircvt')
s=s.replace('objdump -d --disassemble=ggml_vec_dot_q5_1_q8_1 "$BIN/libggml-cpu.so"','python3 "$ROOT/disassemble.py" "$BIN/libggml-cpu.so"')
s=s.replace("grep -Eq 'vpbroadcastb.*%k[0-7]|vpmovm2b'", "grep -Eq 'vcvtph2ps'")
(r/'build_and_pair.lsf').write_bytes(s.encode())
d=json.loads((old/'submission.json').read_text(encoding='utf-8'))
d.update(script=root+'/build_and_pair.lsf',kind='Q5_1四参数FP16转换源码候选',purpose='Q5_1 x Q8_1每块四个FP16缩放参数一次F16C转换，替代四次FP16查表；乘法及累加顺序保持。独立原版源码，仅quants.c修改，不叠加Q5掩码或其他补丁。',environment={'SOURCE_VARIANT':'q5-paircvt'},lsf_args=['-J','qwen38_q5_paircvt'],case_prefix='confirm-q5-paircvt',baseline_case='confirm-q5-paircvt-baseline_{job_id}')
d['config']=d['config'].replace('实际Q5函数8480组输入3重复与原版逐bit一致，反汇编检查新掩码指令','实际Q5函数262432组输入3重复与原版逐bit一致（原8480用例+63488有限FP16位模式×4参数），反汇编检查vcvtph2ps').replace('掩码','转换')
d['note']='只面向有限FP16缩放参数；包含正负零、subnormal和最大有限值，各参数完整有限位模式逐bit验证。硬件转换不是fast-math，仍使用Intel precise/no-ftz；不假定NaN载荷与原表完全相同。'+d['note']
(r/'submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'variant':'q5-paircvt','source_sha256':hashlib.sha256(data).hexdigest(),'direct_dot_cases':262432}))
