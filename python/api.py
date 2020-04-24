
con = None

def is_mouse_clicked(button):
    assert isinstance(button, int)
    return con.call('ismouseclicked', button)

def get_mouse_position():
    return con.call('get_mouse_position')

def get_current_filename():
    return con.call('get_current_filename')

