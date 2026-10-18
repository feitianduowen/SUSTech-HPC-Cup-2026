import difflib
from pathlib import Path

original=Path('D:/compete/.codex-deploy/profiling/source/ops.cpp').read_text(encoding='utf-8')
start=original.index('static void ggml_compute_forward_concat_f32(')
point=original.index('    const int ith = params->ith;',start)
insert='''    if (ggml_is_contiguous_rows(src0) && ggml_is_contiguous_rows(src1) && ggml_is_contiguous_rows(dst)) {
        const int32_t dim = ggml_get_op_params_i32(dst, 0);
        GGML_ASSERT(dim >= 0 && dim < 4);
        const ggml_tensor * sources[] = { src0, src1 };
        for (int source = 0; source < 2; ++source) {
            const ggml_tensor * src = sources[source];
            const int64_t nr = ggml_nrows(src);
            const size_t row_bytes = ggml_row_size(src->type, src->ne[0]);
            const size_t offset = source == 0 ? 0 : src0->ne[dim]*dst->nb[dim];
            const int64_t rows_per_thread = nr/params->nth;
            const int64_t remainder = nr%params->nth;
            const int64_t row_begin = rows_per_thread*params->ith + MIN(params->ith, remainder);
            const int64_t row_end = row_begin + rows_per_thread + (params->ith < remainder);
            for (int64_t row = row_begin; row < row_end; ++row) {
                const int64_t i1 = row % src->ne[1];
                const int64_t i2 = (row/src->ne[1]) % src->ne[2];
                const int64_t i3 = row/(src->ne[1]*src->ne[2]);
                const char * x = (const char *) src->data + i1*src->nb[1] + i2*src->nb[2] + i3*src->nb[3];
                char * y = (char *) dst->data + offset + i1*dst->nb[1] + i2*dst->nb[2] + i3*dst->nb[3];
                memcpy(y, x, row_bytes);
            }
        }
        return;
    }

'''
new=original[:point]+insert+original[point:]
out=Path(__file__).parent
(out/'concat-rows.patch').write_bytes(''.join(difflib.unified_diff(original.splitlines(True),new.splitlines(True),fromfile='a/ggml/src/ggml-cpu/ops.cpp',tofile='b/ggml/src/ggml-cpu/ops.cpp')).encode())
