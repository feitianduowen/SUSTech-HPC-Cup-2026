import difflib
import hashlib
import json
import re
from pathlib import Path

base = Path('D:/compete/.codex-deploy/optimization')
out = base / 'q4_tree_20261020'
out.mkdir(exist_ok=False)
relative = 'ggml/src/ggml-cpu/arch/x86/repack.cpp'
original = Path('D:/compete/q8-avx2-v2/source') / relative
identity = json.loads((base / 'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
data = original.read_bytes()
assert hashlib.sha256(data).hexdigest() == identity['files'][relative]
text = data.decode()
start = text.index('void ggml_gemv_q4_K_8x8_q8_K(')
end = text.index('\nvoid ggml_gemv_iq4_nl_8x8_q8_0', start)
body = text[start:end]
for lane in [0, 1]:
    pattern = r'                    iacc_' + str(lane) + r' = _mm256_add_epi16\(iacc_' + str(lane) + r', (_mm256_maddubs_epi16\(.*\))\);'
    matches = list(re.finditer(pattern, body))
    assert len(matches) == 8
    # VPADDW is modulo 2^16; reparenthesizing only these integer additions
    # preserves every lane, including wraparound, before the original VPMADDWD.
    terms = [m.group(1) for m in matches]
    lines = ['                    // Balanced modulo-2^16 integer sum; floating-point chain unchanged.']
    for j, term in enumerate(terms):
        lines.append('                    const __m256i q4_tree_%d_%d = %s;' % (lane, j, term))
    lines.append('                    iacc_%d = _mm256_add_epi16(' % lane)
    lines.append('                        _mm256_add_epi16(_mm256_add_epi16(q4_tree_%d_0, q4_tree_%d_1), _mm256_add_epi16(q4_tree_%d_2, q4_tree_%d_3)),' % ((lane,) * 4))
    lines.append('                        _mm256_add_epi16(_mm256_add_epi16(q4_tree_%d_4, q4_tree_%d_5), _mm256_add_epi16(q4_tree_%d_6, q4_tree_%d_7)));' % ((lane,) * 4))
    body = body[:matches[0].start()] + '\n'.join(lines) + body[matches[-1].end():]
modified = (text[:start] + body + text[end:]).encode()
target = out / 'variants/q4-int-tree' / relative
target.parent.mkdir(parents=True)
target.write_bytes(modified)
(out / 'q4-int-tree.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True), modified.decode().splitlines(True), fromfile='a/'+relative, tofile='b/'+relative)), encoding='utf-8')
manifest = {'base_commit': identity['revision'], 'variants': {'q4-int-tree': {'file': relative, 'original_sha256': hashlib.sha256(data).hexdigest(), 'sha256': hashlib.sha256(modified).hexdigest()}}}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
for name in ['copy_verify.py', 'ppl_gate.lsf', 'matmul_check.cpp', 'compare.py']:
    content = (base / 'q5_unroll_20261020' / name).read_text(encoding='utf-8')
    content = content.replace('20261020-q5-unroll', '20261020-q4-tree').replace('ordered Q5 loop unrolling', 'Q4 integer balanced-add tree')
    (out / name).write_text(content, encoding='utf-8', newline='\n')
print(json.dumps(manifest))
