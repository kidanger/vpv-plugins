from api import *

olds = None

def on_tick():
    global olds
    s = get_selection()
    if s and s != olds:
        olds = s
        with open('/tmp/vpv-selection', 'w') as f:
            f.write(f'{s[0][0]} {s[0][1]} {s[1][0]} {s[1][1]}\n')


