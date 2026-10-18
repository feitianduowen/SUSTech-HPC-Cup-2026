import json
from pathlib import Path

root = Path(__file__).parent
response = json.loads((root / 'evidence/server_smoke_result.json').read_text(encoding='utf-8'))
model_id = response['models']['data'][0]['id']
for path in (root / 'package/README.md', Path('D:/compete/Qwen38_CPU_部署说明.md')):
    text = path.read_text(encoding='utf-8')
    text = text.replace('"model":"Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf"',
                        '"model":' + json.dumps(model_id))
    path.write_text(text, encoding='utf-8', newline='\n')
