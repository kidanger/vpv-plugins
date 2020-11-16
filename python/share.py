"""
Required:
$ pip install rangehttpserver

How it works:
    - if the envvar VPV_PROXY_COMMAND is defined, launch it. it is expected to print a remote_url
    - creates a temporary directory
    - for each image in each sequence, creates a symlink to it in the temp directory
    - creates a index.html file that contains the urls of the images (arranged in sequences)
    - opens an http server to serve the images and the index.html (on port 3395)

Without proxy:
HOST:[python http server] <-> CLIENTS:[vpv gdal image loader (http)]

With a simple ssh proxy that forwards the connections from a public port:
HOST:[python http server] <-> PROXY:[ssh] <-> CLIENTS:[vpv gdal image loader (http)]
This is useful if the HOST is behind a firewall. However, the connection from the proxy to the clients will be http (not secure).
Example of VPV_PROXY_COMMAND:
$ export VPV_PROXY_COMMAND="echo \"http://<server-ip>:8895\"; exec ssh -N -R :8895:localhost:PORT <server>"
where 8895 is an example of public port on the server (and "GatewayPorts clientspecified" in the sshd config).

With a ssh proxy and an https proxy on the same server:
HOST:[python http server] <-> PROXY:[ssh] <-> PROXY:[https proxy] <-> CLIENTS:[vpv gdal image loader (https)]
This is useful if the proxy is a public server, with an https proxy running.
Example of VPV_PROXY_COMMAND:
$ export VPV_PROXY_COMMAND="echo \"https://<server-ip>:3000\"; exec ssh -N -R :8895:localhost:PORT <server>"
where 8895 is now a private port on the server, but 3000 corresponds to the https proxy (that will talk with the port 8895).
"""

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

    if 'VPV_PROXY_COMMAND' in os.environ:
        cmd = os.environ['VPV_PROXY_COMMAND']
        cmd = cmd.replace('PORT', str(port))

        print('[INFO] running proxy command:', cmd)
        proxy = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        atexit.register(os.kill, proxy.pid, signal.SIGTERM)

        remote_url = proxy.stdout.readline().decode('utf-8').strip()
    else:
        print('[INFO] VPV_PROXY_COMMAND not in environnement, ignoring the proxy')
        remote_url = f'http://localhost:{port}'
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

        print('Send the following command to users. They need to have the GDAL support for vpv.')
        print('-----------')
        print(f"bash -c 'VPVCMD=<(curl {remote_url}) vpv'")
        print('-----------')


if __name__ == '__main__':
    create_server()
    with open(f'{tmpdir.name}/index.html', 'w') as f:
        f.write('test test2')
    print(f'bash -c "VPVCMD=<(curl {remote_url}) vpv"')
    input()

