import getpass
import json
import sys
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
password = getpass.getpass('SSH password: ')
client.connect('172.18.6.10', port=18188, username='apac2602', password=password,
               look_for_keys=False, allow_agent=False, timeout=20, auth_timeout=20)
del password
transport = client.get_transport()
transport.set_keepalive(30)
print('CONNECTED host fingerprint SHA256 (hex): ' + transport.get_remote_server_key().get_fingerprint().hex(), flush=True)
for line in sys.stdin:
    try:
        request = json.loads(line)
        if 'put' in request:
            with client.open_sftp() as sftp:
                sftp.put(request['put'], request['remote'])
            print('UPLOADED', request['remote'], flush=True)
            continue
        if 'get' in request:
            with client.open_sftp() as sftp:
                sftp.get(request['get'], request['local'])
            print('DOWNLOADED', request['local'], flush=True)
            continue
        channel = transport.open_session()
        channel.exec_command(request['cmd'])
        started = time.monotonic()
        while True:
            if channel.recv_ready():
                sys.stdout.write(channel.recv(65536).decode('utf-8', errors='replace'))
                sys.stdout.flush()
            if channel.recv_stderr_ready():
                sys.stdout.write(channel.recv_stderr(65536).decode('utf-8', errors='replace'))
                sys.stdout.flush()
            if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                break
            if time.monotonic() - started > request.get('timeout', 50):
                channel.close()
                raise TimeoutError('remote command time limit exceeded')
            time.sleep(0.05)
        print('\nREMOTE_EXIT=' + str(channel.recv_exit_status()), flush=True)
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), flush=True)
