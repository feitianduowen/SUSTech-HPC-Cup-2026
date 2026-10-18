import difflib
from pathlib import Path
root=Path(__file__).parent
old=Path('D:/compete/.codex-deploy/profiling/source/sgemm.cpp').read_text(encoding='utf-8')
start=old.index('    NOINLINE void gemm4xN(')
point=old.index('                for (int64_t j = 0; j < RN; ++j) {',start)
new=old[:point]+'''#if defined(__INTEL_COMPILER)
                #pragma unroll
#endif
'''+old[point:]
(root/'sgemm-unroll.cpp').write_bytes(new.encode('utf-8'))
(root/'pp-unroll.patch').write_bytes(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/ggml/src/ggml-cpu/llamafile/sgemm.cpp',tofile='b/ggml/src/ggml-cpu/llamafile/sgemm.cpp')).encode())
