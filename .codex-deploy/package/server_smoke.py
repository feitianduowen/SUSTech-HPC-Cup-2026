import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import Request, urlopen

root = Path(os.environ['QWEN_DEPLOY'])
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
base = 'http://127.0.0.1:' + str(port)
args = [str(root / 'llama.cpp/build/bin/llama-server'), '-m', os.environ['MODEL'],
        '-t', '38', '-tb', '38', '-ngl', '0', '--numa', 'distribute',
        '-c', '2048', '-b', '512', '-ub', '256', '-ctk', 'f16', '-ctv', 'f16',
        '-np', '1', '--host', '127.0.0.1', '--port', str(port), '--no-webui', '--no-warmup']
started = time.monotonic()
with (root / 'logs/server_smoke.log').open('w') as log:
    proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 360
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError('Server exited early: ' + str(proc.returncode))
            try:
                with urlopen(base + '/health', timeout=3) as response:
                    health = json.load(response)
                if health.get('status') == 'ok':
                    break
            except Exception:
                pass
            time.sleep(2)
        else:
            raise RuntimeError('Server readiness timed out')
        with urlopen(base + '/v1/models', timeout=10) as response:
            models = json.load(response)
        request = Request(base + '/completion',
                          data=json.dumps({'prompt': 'The capital of France is', 'n_predict': 12,
                                           'temperature': 0, 'seed': 1}).encode(),
                          headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=240) as response:
            completion = json.load(response)
        assert completion.get('content') and completion.get('tokens_predicted', 0) > 0
        chat_request = Request(base + '/v1/chat/completions',
                               data=json.dumps({'model': models['data'][0]['id'],
                                                'messages': [{'role': 'user', 'content': 'Reply with exactly OK.'}],
                                                'max_tokens': 32, 'temperature': 0,
                                                'chat_template_kwargs': {'enable_thinking': False}}).encode(),
                               headers={'Content-Type': 'application/json'})
        with urlopen(chat_request, timeout=240) as response:
            chat_completion = json.load(response)
        message = chat_completion['choices'][0]['message']
        assert message.get('content') or message.get('reasoning_content')
        result = {'status': 'PASS', 'health': health, 'models': models,
                  'completion': completion, 'chat_completion': chat_completion,
                  'seconds': time.monotonic() - started,
                  'host': socket.gethostname(), 'job_id': os.environ.get('LSB_JOBID')}
        (root / 'logs/server_smoke_result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('Server smoke PASS: ' + completion['content'], flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
