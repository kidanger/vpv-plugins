import os
import sqlite3
from api import *

db = None

def init():
    global db
    dbpath = os.path.expanduser('~/.cache/vpv/restore-image-settings.sqlite')
    os.makedirs(os.path.dirname(dbpath), exist_ok=True)
    db = sqlite3.connect(dbpath)

    cur = db.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS colormaps(
        filename text,
        radius real,
        center0 real,
        center1 real,
        center2 real,
        shader text
        )
        ''')

def save(f, c):
    cur = db.cursor()
    cur.execute('delete from colormaps where filename = ?', (f,))
    cur.execute('insert into colormaps (filename, radius, center0, center1, center2, shader) values (?, ?, ?, ?, ?, ?)', (f, c.radius, *c.center, c.shader))
    db.commit()

def load(f, c):
    cur = db.cursor()
    for radius, center0, center1, center2, shader in cur.execute('select radius, center0, center1, center2, shader \
                                                                  from colormaps where filename = ?', (f,)):
        c.shader = shader
        c.center = (center0, center1, center2)
        c.radius = radius

filenames = {}
cur = {}
def on_tick():
    global olds
    for i, w in enumerate(get_windows()):
        f = w.current_filename
        c = w.current_sequence.colormap
        if not c or not c.shader:
            continue
        h = hash((c.shader, tuple(c.center), c.radius))
        if i not in filenames or filenames[i] != f:
            filenames[i] = f
            load(f, c)
        elif not i in cur or cur[i] != h:
            cur[i] = h
            save(f, c)

