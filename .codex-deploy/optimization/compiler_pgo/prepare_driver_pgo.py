import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
text=(here/'pipeline_ggml_pgo.lsf').read_text(encoding='utf-8')
text=text.replace('cp "$ROOT/pipeline_ggml_pgo.lsf" "$OUT/pipeline.lsf"','cp "$ROOT/pipeline_driver_pgo.lsf" "$OUT/pipeline.lsf"')
text=text.replace('ggml_pgo_only.cmake','ggml_pgo_driver.cmake')
text=text.replace('stage BUILD_CONTROL\n','stage LINK_PROBE\nbash "$ROOT/pgo_link_probe.sh" "$OUT/link-probe" > "$OUT/link-probe.log" 2>&1\nstage BUILD_CONTROL\n')
text=text.replace('"$ROOT/check_pgo_scope.py"','"$ROOT/check_driver_scope.py"')
text=text.replace('"$ROOT/write_manifest_ggml.py"','"$ROOT/write_manifest_driver.py"')
(here/'pipeline_driver_pgo.lsf').write_bytes(text.encode())
check=(here/'check_pgo_scope.py').read_text(encoding='utf-8')
check=check.replace("out={'mode':mode,'ggml':0,'other':0,'examples':{}}","out={'mode':mode,'ggml':0,'other':0,'driver':0,'examples':{}}")
check=check.replace("    elif source.endswith('/src/llama-vocab.cpp'):","    elif source.endswith('/tools/llama-bench/main.cpp'):\n        out['driver']+=1\n        if mode=='gen': assert '-prof-gen=threadsafe' in command and '-no-prof-gen' not in command,command\n        if mode=='use': assert '-prof-use=nomerge' in command and '-no-prof-use' not in command,command\n        out['examples'][source]=command\n    elif source.endswith('/src/llama-vocab.cpp'):")
check=check.replace("out['other']==1","out['other']==1 and out['driver']==1")
check=check.replace("assert out['ggml']", "    elif mode in ['gen','use']:\n        disable='-no-prof-gen' if mode=='gen' else '-no-prof-use'\n        enable='-prof-gen=threadsafe' if mode=='gen' else '-prof-use=nomerge'\n        assert disable in command and command.rfind(disable)>command.rfind(enable),source+'\\n'+command\nassert out['ggml']")
(here/'check_driver_scope.py').write_bytes(check.encode())
manifest=(here/'write_manifest_ggml.py').read_text(encoding='utf-8').replace('GGML backend only; llama/common/tools keep plain Intel optimization in gen and use stages','GGML backend plus thin llama-bench main; cold llama/common/bench-impl compile and link unprofiled in gen/use')
(here/'write_manifest_driver.py').write_bytes(manifest.encode())
for level,parent in [(3,'4336889'),(2,'4336627')]:
    spec=json.loads((here/('ggml_only_O'+str(level)+'.json')).read_text(encoding='utf-8'))
    spec.update(script=remote+'/pipeline_driver_pgo.lsf',kind='PGO入口/共享库链接修复及构建/PPL',retry_of=parent,purpose='Intel O'+str(level)+'：修复选择性PGO的运行库链接；先验证三层共享库探针，再完整训练/反馈编译/固定PPL',lsf_args=['-J','qwen38_O'+str(level)+'_pgo_driver'])
    spec['config']+='；薄llama-bench/main.cpp保留PGO编译和链接；冷llama/common/bench-impl等同时compile+link禁用PGO；开始先进行main→cold DSO→hot DSO链接/正常退出/非空dyn探针（不加载模型、不计分）'
    spec['note']='4336889在BUILD_GEN链接llama-bench失败：libipgo.a引用__start___pgoseg_addr，DSO missing from command line；尚未训练。新修复：薄main保留插桩启动运行库，冷模块同时禁用compile/link PGO。三层共享库探针必须链接、正常退出并产生非空dyn后才完整构建。探针计数与训练计数目录分开。先O3，流程成功后才O2。所有失败保留，正式PPL/测速参数不变；仍未给出PGO性能结论。'
    (here/('driver_O'+str(level)+'.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print('Prepared driver/shared-library PGO repair.')
