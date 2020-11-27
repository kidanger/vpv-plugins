from api import *

olds = None

def on_tick():
    global olds
    w = get_focused_window()
    if w:
        s = w.current_filename
        if s and s != olds:
            olds = s
            with open('/tmp/vpv-currentimage', 'w') as f:
                f.write(f'{s}')


