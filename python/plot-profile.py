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

H = 150
W = 300

def trace(seq, image, start, end):
    import numpy as np
    def dist(p):
        d1 = np.hypot(p[0]-start[0], p[1]-start[1])
        d2 = np.hypot(end[0]-start[0], end[1]-start[1])
        return d1 / d2 if d2 else 0

    # get the samples
    pos = list(bresenham(start[0], start[1], end[0], end[1]))
    xs, ys = zip(*pos)
    samples = np.array(image.get_pixels_from_coords(*zip(*pos)))

    # function to convert samples into the plot coordinates
    ma = np.max(samples)
    mi = np.min(samples)
    def plot(samples):
        # TODO: normalize using the colormap
        s = [(dist(p)*W, (1-(s-mi)/(ma-mi))*H) for p, s in zip(pos, samples)]
        return [(x,y) for x, y in s]

    code = '<svg width="1" height="1">'
    # draw the segment
# <circle r='1' cx='{start[0]+0.5}' cy='{start[1]+0.5}' fill='#eeeeee' fill-opacity='0.5'></rect>
    code += f'''
<polyline stroke="#11ee11" stroke-width="-2" points="{start[0]+0.5},{start[1]+0.5} {end[0]+0.5},{end[1]+0.5}"/>
<polyline stroke="#111111" stroke-width="-1" points="{start[0]+0.5},{start[1]+0.5} {end[0]+0.5},{end[1]+0.5}"/>
'''
    # draw the rectangle for the plot
    code += f'''
<rect display='absolute' width="{W}" height='{H}' x='0' y='0' fill='#eeeeee' fill-opacity='0.85'></rect>
'''
    # draw the plot (max 3 channels)
    for i, c in zip(range(samples.shape[1]), ('#dd3333', '#33dd33', '#3333dd')):
        code += f'''
<polyline display='absolute' stroke="{c}" stroke-width="1"
points="{' '.join(str(x)+','+str(y) for x, y in plot(samples[:,i]))}"/>
'''
    code += '</svg>'
    seq.put_script_svg('plot-profile', code)

def clear(seq):
    seq.put_script_svg('plot-profile')

start = None
end = None
closed = False
curimage = None

def on_tick():
    window = get_focused_window()
    if not window or not window.current_sequence:
        return

    seq = window.current_sequence

    global start, end, curimage, closed

    changed = False

    if start and not closed:
        end_ = get_mouse_position()
        if end_ != end:
            end = end_
            changed = True

    if is_key_pressed('x', repeat=False):
        start = get_mouse_position()
        end = None
        closed = False
    if is_key_released('x'):
        curimage = None
        closed = True
        if get_mouse_position() == start:
            start = None
            end = None
            closed = False
            clear(seq)

    # TODO: support many sequences at the same time (require add-svg-from-code)

    image = seq.image
    isanewimage = image and (image.id != curimage.id if curimage else True)
    if (isanewimage or changed) and start and end:
        curimage = image
        trace(seq, image, start, end)

