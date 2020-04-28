from api import *

# from https://github.com/encukou/bresenham/
def bresenham(x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    for x in range(dx + 1):
        yield x0 + x*xx + y*yx, y0 + x*xy + y*yy
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy

start = None
end = None

H = 200
W = 300

def trace():
    import numpy as np
    import iio
    def dist(p):
        d1 = np.hypot(p[0]-start[0], p[1]-start[1])
        d2 = np.hypot(end[0]-start[0], end[1]-start[1])
        return d1 / d2

    # get the samples
    # TODO: ask sequence.image.get_pixels()
    u = iio.read(get_focused_window().current_filename)
    pos = list(bresenham(start[0], start[1], end[0], end[1]))
    samples = np.array([u[p[1], p[0]] for p in pos])

    # function to convert samples into the plot coordinates
    ma = np.max(samples)
    mi = np.min(samples)
    def plot(samples):
        s = [(dist(p)*W, (1-(s-mi)/(ma-mi))*H) for p, s in zip(pos, samples)]
        return [(x,y) for x, y in s]

    # TODO: instead of a file, give the svg directly to vpv
    with open('/tmp/profile-plot.svg', 'w') as f:
        f.write('<svg width="1" height="1">')
        # draw the rectangle for the plot
        f.write(f'''
<rect display='absolute' width="{W}" height='{H}' x='0' y='0' fill='#eeeeee' fill-opacity='0.7'></rect>
''')
        # draw the plot (max 3 channels)
        for i, c in zip(range(samples.shape[1]), ('#dd3333', '#33dd33', '#3333dd')):
            f.write(f'''
<polyline display='absolute' stroke="{c}" stroke-width="1"
    points="{' '.join(str(x)+','+str(y) for x, y in plot(samples[:,i]))}"/>
''')
        # draw the segment
        # TODO: live-draw it while selecting the end of the segment
        f.write(f'''
<circle r='1' cx='{start[0]+0.5}' cy='{start[1]+0.5}' fill='#eeeeee'></rect>
<polyline stroke="#11ee11" stroke-width="2" points="{start[0]+0.5},{start[1]+0.5} {end[0]+0.5},{end[1]+0.5}"/>
<polyline stroke="#111111" stroke-width="1" points="{start[0]+0.5},{start[1]+0.5} {end[0]+0.5},{end[1]+0.5}"/>
''')
        f.write('</svg>')

def on_tick():
    global start, end
    if is_key_pressed('y'):
        if not start:
            start = get_mouse_position()
        elif not end:
            end = get_mouse_position()

    if start and end and get_focused_window():
        try:
            trace()
        except Exception as e:
            print(e)
        start = None
        end = None

    # TODO: check if image has changed and redraw
    # TODO: support many sequences at the same time


