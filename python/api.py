
con = None

def is_mouse_clicked(button):
    return con.call('ismouseclicked', button)

def get_mouse_position():
    return con.call('''function()
            return {gHoveredPixel.x, gHoveredPixel.y}
    end''')

def get_current_filename():
    return con.call('''function()
        local curwin = get_current_window()
        local seq = curwin.sequences[curwin.index+1]
        local filename = seq.collection:get_filename(seq.player.frame - 1)
        return filename
    end''')


