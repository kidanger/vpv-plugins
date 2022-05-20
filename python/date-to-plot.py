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
        code = '''
            <svg width="1" height="1">
        '''
        found = False
        for i, img in enumerate(imgs):
            curdate = re.search(r'.*(\d{4}-?\d{2}-?\d{2}([tT]\d{6})?).*', img)
            if not curdate:
                continue
            found = True
            curdate = curdate.group(1)
            try:
                curdate = parse(curdate)
            except:
                continue

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
            width = max(1, endx - startx)

            color = ['#000000', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'][i]
            code += f'''
                <rect width="{width}" height='10000' x='{startx}' y='0' fill='{color}' fill-opacity='0.25'></rect>
            '''

        if found:
            code += '''
                </svg>
            '''
            seq.put_script_svg('date-to-plot', code)
        else:
            seq.put_script_svg('date-to-plot')
