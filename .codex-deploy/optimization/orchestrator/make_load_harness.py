from pathlib import Path
root=Path(__file__).parent
text=(root/'benchmark_runtime.lsf').read_text()
text=text.replace('RESULT_DIR="/work/apac2602/qwen38-cpu/optimization/20261018-v1/results/runtime_${EXPERIMENT_POLICY:?}_${LSB_JOBID}"','RESULT_DIR="${EXPERIMENT_OUTPUT_DIR:?set case output directory}"')
text=text.replace('prefix=()\ncase ', 'prefix=()\nspeed_extra=()\ncase ')
text=text.replace('    *) error "Unknown development policy";;','    reference) ;;\n    copy-interleave) prefix=(numactl --interleave=all); speed_extra=(-lm none);;\n    *) error "Unknown development policy";;')
text=text.replace('declare -p prefix >', 'declare -p prefix speed_extra >')
text=text.replace('COMMON_ARGS=(\n','COMMON_ARGS=(\n    "${speed_extra[@]}"\n')
(root/'benchmark_load_mode.lsf').write_bytes(text.encode())
