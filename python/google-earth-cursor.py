import sys
try:
    import rpcm
except ImportError as e:
    print('Cannot import rpcm:', e)
import json
import threading

def evaluate(dat):
    function = dat['func']
    res = eval(function)(*dat['args'])
    return res

class Connection:
    lastid = 0

    def __init__(self, fin, fout):
        self.fout = open(fout, 'w')
        self.fin = open(fin, 'r')
        self.already_got = []

    def call(self, func, *args):
        assert threading.current_thread() is threading.main_thread()
        self.lastid += 1
        msg = {'type': 'request', 'func': func, 'args': args}
        id = self.send(self.lastid, msg)
        nn, r = self.receive()

        while nn != id:
            msg = {'type': 'reply', 'response': evaluate(r)}
            self.send(nn, msg)
            nn, r = self.receive()

        self.lastid -= 1
        return r['response']

    def send(self, n, msg):
        dat = json.dumps(msg)
        self.fout.write(str(n) + ' ' + dat + '\n')
        self.fout.flush()
        return n

    def receive(self):
        line = self.fin.readline()
        if not line:
            # let's assume vpv was closed
            sys.exit(0)
        n, line = line.split(' ', 1)
        return int(n), json.loads(line)

    def serve(self):
        while True:
            n, line = c.receive()
            msg = {'type': 'reply', 'response': evaluate(line)}
            c.send(n, msg)

def is_mouse_clicked(button):
    return c.call('ismouseclicked', button)

def get_mouse_position():
    return c.call('''function()
            return {gHoveredPixel.x, gHoveredPixel.y}
    end''')

def get_current_filename():
    return c.call('''function()
        local curwin = get_current_window()
        local seq = curwin.sequences[curwin.index+1]
        local filename = seq.collection:get_filename(seq.player.frame - 1)
        return filename
    end''')

def on_window_tick(focused):
    if not focused:
        return

    if is_mouse_clicked(2):
        x, y = get_mouse_position()
        img = get_current_filename()
        try:
            lon, lat = rpcm.localization(img, x, y, 0)
        except Exception as e:
            print('Error while localization:', e)
        else:
            print(lon, lat)
            with open('/tmp/vpvcursor.kml', 'w') as f:
                f.write(f'''\
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name></name>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>
</kml>''')

fin, fout = sys.argv[1:]
c = Connection(fin, fout)
c.serve()

