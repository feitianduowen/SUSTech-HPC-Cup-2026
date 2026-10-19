import json
from pathlib import Path

root = Path(__file__).resolve().parent
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
text = (root/'pipeline_ggml_pgo.lsf').read_text(encoding='utf-8')
text = text.replace('pipeline_ggml_pgo.lsf','pipeline_ggml_pgo_v2.lsf').replace('ggml_pgo_only.cmake','ggml_pgo_targets_v2.cmake').replace('check_pgo_scope.py','check_pgo_scope_v2.py')
# Verify effective compile and link scope immediately after configuration,
# before spending a complete build on another incorrect target scope.
old = '    cmake --build "$dest" --target "${targets[@]}" -j 40 > "$logs/build.log" 2>&1'
new = '    python3 "$ROOT/check_pgo_scope_v2.py" "$dest/compile_commands.json" "$mode" > "$logs/pgo-scope-prebuild.json"\n'+old
assert old in text
text = text.replace(old,new)
(root/'pipeline_ggml_pgo_v2.lsf').write_bytes(text.encode())
spec = json.loads((root/'ggml_only_O3.json').read_text(encoding='utf-8'))
spec.update(script=remote+'/pipeline_ggml_pgo_v2.lsf',retry_of='4336889',kind='GGML定向PGO V2/链接修复/训练/PPL',purpose='修复4336889选择性PGO链接失败及未排除静态库：递归处理全部非GGML目标的编译与链接，重新验证训练流程',lsf_args=['-J','qwen38_O3_ggml_pgo_v2'])
spec['config']+='；V2递归枚举全部实际CMake目标，非GGML静态/对象库禁止插桩，非GGML动态库和可执行文件编译及链接均关闭PGO；配置后先检查全部compile_commands和动态link.txt；原始源码及此前构建保留'
spec['note']='4336889 control固定PPL=2.7767 PASS；gen最终链接因__start___pgoseg_addr/DSO missing退出，未训练。本次不用未完成计数；全新作业构建目录。修复旧规则遗漏llama-common-base/cpp-httplib等目标及非GGML链接仍启用-prof-gen的问题。保留全部失败记录；训练正常退出、参数校验、计数合并、反馈编译及独立固定PPL后才能用于测速。O2仍等待公共流程验证。'
(root/'ggml_v2_O3.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(root/'pipeline_ggml_pgo_v2.lsf')
