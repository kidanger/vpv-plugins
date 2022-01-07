import re
import datetime
from dateutil.parser import parse

from api import *

active = False
imgscache = []
seqs_that_uses_coords = None

parseisodate = lambda s: datetime.datetime.fromisoformat(s)
parsesatdate = lambda s: datetime.datetime.strptime(s, '%Y%m%d')

def on_tick():
    global active, imgscache, seqs_that_uses_coords
    if is_key_pressed('l'):
        active = True
    if not active:
        return

    imgs = [w.current_filename for w in get_windows()]
    if imgs == imgscache:
        return
    imgscache = imgs

    if not seqs_that_uses_coords:
        seqs_that_uses_coords = []
        for w in get_windows():
            seq = w.current_sequence
            img = w.current_filename
            try:
                f = open(f'{img}.coords')
            except FileNotFoundError:
                continue
            lines = f.read().strip()
            lines = lines.split('\n')
            coords = map(lambda l: l.split(' '), lines)
            coords = map(lambda c: (parseisodate(c[0]), float(c[1])), coords)
            coords = sorted(coords, key=lambda c: c[0])
            coords = list(coords)
            seqs_that_uses_coords.append((seq, coords))

    for seq, coords in seqs_that_uses_coords:
        dates = [re.search(r'.*(\d{4}-?\d{2}-?\d{2}([tT]\d{6})?).*', img) for img in imgs]
        dates = filter(lambda d: d, dates)
        dates = map(lambda d: d.group(1), dates)
        dates = map(lambda d: parse(d), dates)
        try:
            curdate = next(dates)
        except StopIteration:
            seq.put_script_svg('date-to-plot')
            return

        try:
            idx = next(i for i, c in enumerate(coords) if c[0] > curdate)
        except StopIteration:
            idx = len(coords)-1

        # TODO: get startx and endx from the previous/next image
        # and not the coords in the file
        startx = coords[max(0,idx-1)][1]
        print(startx, idx, coords[max(0,idx-1)])
        midx = coords[idx][1]
        endx = coords[min(idx+1,len(coords)-1)][1]
        startx += (midx - startx) / 2
        endx -= (endx - midx) / 2

        code = f'''
            <svg width="1" height="1">
                <rect width="{endx-startx}" height='1000' x='{startx}' y='0' fill='#000000' fill-opacity='0.25'></rect>
            </svg>
        '''
        seq.put_script_svg('date-to-plot', code)

