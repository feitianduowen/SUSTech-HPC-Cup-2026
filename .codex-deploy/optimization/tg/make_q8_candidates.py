"""Generate independent Q8 AVX2 patches and a standalone diagnostic kernel file."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path


def extract_function(source: str, name: str) -> str:
    start = source.index(name)
    start = source.rfind("\n", 0, start) + 1
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def avx2_body(width: int, independent: bool) -> str:
    lines = ["    __m256 acc = _mm256_setzero_ps();"]
    if independent:
        for index in range(1, width):
            lines.append(f"    __m256 acc{index} = _mm256_setzero_ps();")
    lines.extend(["", f"    for (; ib + {width - 1} < nb; ib += {width}) {{"])
    for index in range(width):
        at = "ib" if index == 0 else f"ib + {index}"
        lines.append(f"        const __m256 d{index} = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[{at}].d) * GGML_CPU_FP16_TO_FP32(y[{at}].d));")
    for index in range(width):
        at = "ib" if index == 0 else f"ib + {index}"
        lines.extend([
            f"        const __m256i qx{index} = _mm256_loadu_si256((const __m256i *) x[{at}].qs);",
            f"        const __m256i qy{index} = _mm256_loadu_si256((const __m256i *) y[{at}].qs);",
            f"        const __m256 q{index} = mul_sum_i8_pairs_float(qx{index}, qy{index});",
        ])
    lines.append("")
    for index in range(width):
        acc = f"acc{index}" if independent and index else "acc"
        lines.append(f"        {acc} = _mm256_fmadd_ps(d{index}, q{index}, {acc});")
    lines.extend(["    }", ""])
    if independent:
        if width == 2:
            lines.append("    acc = _mm256_add_ps(acc, acc1);")
        else:
            lines.append("    acc = _mm256_add_ps(_mm256_add_ps(acc, acc1), _mm256_add_ps(acc2, acc3));")
        lines.append("")
    lines.extend([
        "    for (; ib < nb; ++ib) {",
        "        const __m256 d = _mm256_set1_ps(GGML_CPU_FP16_TO_FP32(x[ib].d) * GGML_CPU_FP16_TO_FP32(y[ib].d));",
        "        const __m256i qx = _mm256_loadu_si256((const __m256i *) x[ib].qs);",
        "        const __m256i qy = _mm256_loadu_si256((const __m256i *) y[ib].qs);",
        "        const __m256 q = mul_sum_i8_pairs_float(qx, qy);",
        "        acc = _mm256_fmadd_ps(d, q, acc);",
        "    }",
        "",
        "    sumf = hsum_float_8(acc);",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    original = extract_function(source, "void ggml_vec_dot_q8_0_q8_0(")
    head, rest = original.split("#if defined(__AVX2__)\n", 1)
    _, tail = rest.split("#elif defined(__AVX__)\n", 1)
    variants = {"baseline": original}
    manifest = {"source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(), "candidates": {}}
    args.out.mkdir(parents=True, exist_ok=True)
    target = "ggml/src/ggml-cpu/arch/x86/quants.c"
    for width, independent in [(2, False), (4, False), (2, True), (4, True)]:
        name = f"{'a' if independent else 'u'}{width}"
        updated = head + "#if defined(__AVX2__)\n" + avx2_body(width, independent) + "#elif defined(__AVX__)\n" + tail
        variants[name] = updated
        patch = "".join(difflib.unified_diff(source.splitlines(True), source.replace(original, updated, 1).splitlines(True), fromfile=f"a/{target}", tofile=f"b/{target}"))
        (args.out / f"q8-{name}.patch").write_text(patch, encoding="ascii", newline="\n")
        manifest["candidates"][name] = {"width": width, "independent_accumulators": independent, "preserves_fma_order": not independent}

    kernels = """/* Diagnostic extraction; generated from the unchanged production source. */
#include <assert.h>
#include <immintrin.h>
#include <stddef.h>
#include <stdint.h>
#define QK8_0 32
#define GGML_RESTRICT restrict
#define UNUSED(x) (void) (x)
#define GGML_CPU_FP16_TO_FP32(x) _cvtsh_ss(x)
typedef struct { uint16_t d; int8_t qs[QK8_0]; } block_q8_0;
_Static_assert(sizeof(block_q8_0) == 34, "Q8_0 ABI");
"""
    for name in ["hsum_float_8", "sum_i16_pairs_float", "mul_sum_us8_pairs_float", "mul_sum_i8_pairs_float"]:
        kernels += "\n" + extract_function(source, f" {name}(") + "\n"
    for name, function in variants.items():
        kernels += "\n" + function.replace("void ggml_vec_dot_q8_0_q8_0(", f"__attribute__((noinline)) void q8_{name}(", 1) + "\n"
    (args.out / "q8-kernels.c").write_text(kernels, encoding="ascii", newline="\n")
    (args.out / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
