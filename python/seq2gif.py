from api import *

import os

seq = None
win = None
oldconfigscreenshot = None
FILES = '/tmp/screenshot_%05d.png'
ALLFILES = '/tmp/screenshot_*.png'
OUTPUT = '/tmp/out_%03d.gif'

frames = []
hasframe = {}

def on_tick():
    global win, seq, oldconfigscreenshot, frames, hasframe

    if not seq and is_key_pressed(';'):
        win = get_focused_window()
        seq = win.current_sequence
        player = seq.player
        player.frame = 1
        frames = []
        hasframe = {}
        player.opened = True
        player.playing = False

        oldconfigscreenshot = get_config('SCREENSHOT')
        set_config('SCREENSHOT', FILES)
        os.system('rm {}'.format(ALLFILES))

        print('Configure the FPS, bounds and bounce and close the player (click on the cross) to create a gif of the sequence.')
        print('Press ; again to abort.')
        return

    if not seq:
        return

    if is_key_pressed(';'):
        print('Gif aborted.')
        seq = None
        return

    if seq.player.opened:
        return
    elif not frames:
        player = seq.player
        player.frame = player.current_min_frame
        frames = list(range(player.current_min_frame, player.current_max_frame+1))
        player.playing = False

    seq.player.frame += 1

    if seq.player.frame not in hasframe:
        win.take_screenshot()
        hasframe[seq.player.frame] = True
        return

    hasall = True
    for f in frames:
        if f not in hasframe:
            hasall = False
            break

    if hasall and seq.player.frame == frames[2]:
        set_config('SCREENSHOT', oldconfigscreenshot)
        files = [FILES % i for i in range(1, len(frames)+1)]
        if seq.player.bouncy:
            files += files[-2:0:-1]
        n = 0
        while True:
            output = OUTPUT % n
            if not os.path.exists(output):
                break
            n += 1
        cmd = 'echo "Converting to gif..." && convert -delay 1x{} {} {} && echo "All done!" &'.format(seq.player.fps, ' '.join(files), output)
        print(cmd)
        os.system(cmd)
        seq = None

