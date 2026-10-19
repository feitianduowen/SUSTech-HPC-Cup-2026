import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
text=(here/'pipeline_short_train.lsf').read_text(encoding='utf-8')
text=text.replace('cp "$ROOT/pipeline_short_train.lsf" "$OUT/pipeline.lsf"','cp "$ROOT/pipeline_ggml_pgo.lsf" "$OUT/pipeline.lsf"\ncp "$ROOT/ggml_pgo_only.cmake" "$OUT/ggml_pgo_only.cmake"')
text=text.replace('local command=(cmake -S "$SRC" -B "$dest"','local command=(cmake -S "$SRC" -B "$dest"\n        "-DCMAKE_PROJECT_INCLUDE=$OUT/ggml_pgo_only.cmake" "-DQWEN_PGO_PHASE=$mode"')
text=text.replace('python3 "$ROOT/write_manifest_short.py"','python3 "$ROOT/write_manifest_ggml.py"')
# Snapshot the effective per-translation-unit flags as evidence of selective PGO.
text=text.replace('cp "$dest/CMakeCache.txt" "$logs/CMakeCache.txt"','cp "$dest/CMakeCache.txt" "$logs/CMakeCache.txt"\n    cp "$dest/compile_commands.json" "$logs/compile_commands.json"\n    python3 "$ROOT/check_pgo_scope.py" "$dest/compile_commands.json" "$mode" > "$logs/pgo-scope.json"')
(here/'pipeline_ggml_pgo.lsf').write_bytes(text.encode())
manifest=(here/'write_manifest_short.py').read_text(encoding='utf-8').replace("'compiler':'Intel Classic 2021.9'", "'compiler':'Intel Classic 2021.9','pgo_scope':'GGML backend only; llama/common/tools keep plain Intel optimization in gen and use stages'")
(here/'write_manifest_ggml.py').write_bytes(manifest.encode())
spec=json.loads((here/'short_O3.json').read_text(encoding='utf-8'))
spec.update(script=remote+'/pipeline_ggml_pgo.lsf',kind='GGML定向PGO构建/训练/PPL',retry_of='4336716',
    purpose='修复全程序插桩在tokenizer初始化阶段超时：仅GGML保留PGO，冷初始化模块保持普通Intel优化；通过训练后反馈编译/PPL',
    lsf_args=['-J','qwen38_O3_ggml_pgo'],
    note='4336626/4336627的control固定PPL均2.7767 PASS，但PP1024训练900s超时。4336716短PP64训练仍1200s超时，-v末尾停在init_tokenizer，未进入模型计算；周期计数仅作失败诊断，不当作完成训练。本次gen对llama/common/bench等非GGML目标追加-no-prof-gen，use对同组追加-no-prof-use，GGML保留threadsafe计数/反馈；CMake DEFER及compile_commands检查实际生效。所有构建独立目录；训练正常退出和JSON校验后才合并及反馈构建，最后固定PPL。O2等待公共训练流程确认。无完整测速分数。')
spec['config']+='；PGO范围仅GGML后端；llama/common/tools在gen追加-no-prof-gen、use追加-no-prof-use；源代码/模型/固定PPL及正式PP/TG参数不改'
(here/'ggml_only_O3.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
second=json.loads((here/'short_O2.json').read_text(encoding='utf-8'))
second.update(script=spec['script'],kind=spec['kind'],retry_of='4336627',purpose=spec['purpose'].replace('修复','Intel O2复测：修复',1),lsf_args=['-J','qwen38_O2_ggml_pgo'],note=spec['note']+' 此spec待O3公共训练流程成功后再提交。')
second['config']+='；PGO范围仅GGML后端；llama/common/tools在gen追加-no-prof-gen、use追加-no-prof-use；源代码/模型/固定PPL及正式PP/TG参数不改'
(here/'ggml_only_O2.json').write_bytes(json.dumps(second,ensure_ascii=False,indent=2).encode())
print('Prepared GGML-only PGO retry spec.')
