from api import *

import os
import signal
import atexit
import tempfile
import threading
import functools
import subprocess

import http.server
from RangeHTTPServer import RangeRequestHandler

thread = None
tmpdir = None
remote_url = None

def create_server(port=3395):
    global thread, tmpdir, remote_url

    if 'VPV_PROXY_COMMAND' not in os.environ:
        raise RuntimeError('VPV_PROXY_COMMAND not in environnement variable')
    cmd = os.environ['VPV_PROXY_COMMAND']
    cmd = cmd.replace('PORT', str(port))

    print('[INFO] running proxy command:', cmd)
    proxy = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    atexit.register(os.kill, proxy.pid, signal.SIGTERM)

    remote_url = proxy.stdout.readline().decode('utf-8').strip()
    tmpdir = tempfile.TemporaryDirectory()

    handler = functools.partial(RangeRequestHandler, directory=tmpdir.name)
    thread = threading.Thread(target=lambda: http.server.test(HandlerClass=handler, port=port))
    thread.daemon = True
    thread.start()

    print('[INFO]', remote_url, '->', tmpdir.name)

def on_tick():
    if is_key_pressed('n'):
        create_server()

        seqs = []
        for s in get_sequences():
            urlnames = []
            col = s.collection
            for i in range(col.length):
                name = col.get_filename(i)
                newname = name.replace('/', '%')
                os.symlink(os.path.realpath(name), os.path.join(tmpdir.name, newname))
                urlname = f'/vsicurl/{remote_url}/{newname}'
                urlnames.append(urlname)
            seqs.append('::'.join(urlnames))

        with open(f'{tmpdir.name}/index.html', 'w') as f:
            f.write(' '.join(seqs))

        print('Send the following command to others:')
        print('-----------')
        print(f'bash -c "VPVCMD=<(curl {remote_url}) vpv"')
        print('-----------')


if __name__ == '__main__':
    create_server()
    with open(f'{tmpdir.name}/index.html', 'w') as f:
        f.write('test test2')
    print(f'bash -c "VPVCMD=<(curl {remote_url}) vpv"')
    input()

