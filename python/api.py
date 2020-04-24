import typing

WinId = typing.NewType('WinId', str)

con = None

def is_mouse_clicked(button: int):
    return con.call('ismouseclicked', button)

def get_mouse_position():
    return con.call('get_mouse_position')

def get_current_filename():
    return con.call('get_current_filename')

def get_windows():
    return [Window(WinId(w)) for w in con.call('get_windows')]

def window_is_focused(win: WinId):
    return con.call('window_is_focused', win)

def window_get_current_filename(win: WinId):
    return con.call('window_get_current_filename', win)


class Window:

    def __init__(self, id: WinId):
        self.id = id

    @property
    def focused(self):
        return window_is_focused(self.id)

    @property
    def current_filename(self):
        return window_get_current_filename(self.id)

