from typing import NewType, List, Tuple

Vec2i = Tuple[int, int]

con = None

def reload_images() -> None:
    return con.call('reload')

def is_key_down(key: str) -> bool:
    return con.call('is_key_down', key)

def is_key_up(key: str) -> bool:
    return con.call('is_key_up', key)

def is_mouse_clicked(button: int) -> bool:
    return con.call('is_mouse_clicked', button)

def get_mouse_position() -> Vec2i:
    return con.call('get_mouse_position')


class Window:

    def __init__(self, id):
        self.id = id

    @property
    def focused(self) -> bool:
        return con.call('window_is_focused', self.id)

    @property
    def opened(self) -> bool:
        return con.call('window_is_opened', self.id)

    @opened.setter
    def opened(self, val: bool):
        return con.call('window_set_opened', self.id, val)

    @property
    def position(self) -> Vec2i:
        return con.call('window_get_position', self.id)

    @position.setter
    def position(self, pos: Vec2i):
        return con.call('window_set_position', self.id, pos)

    @property
    def size(self) -> Vec2i:
        return con.call('window_get_size', self.id)

    @size.setter
    def size(self, size: Vec2i):
        return con.call('window_set_size', self.id, size)

    @property
    def current_sequence(self):
        return Sequence(con.call('window_get_current_sequence', self.id))

# .addProperty("index", &Window::index)
# .addProperty("sequences", &Window::sequences)
# .addProperty("always_on_top", &Window::alwaysOnTop)
# .addProperty("dont_layout", &Window::dontLayout)

    @property
    def current_filename(self) -> str:
        return con.call('window_get_current_filename', self.id)

def new_window() -> Window:
    return Window(con.call('new_window'))

def get_windows() -> List[Window]:
    return [Window(w) for w in con.call('get_windows')]

def get_focused_window() -> Window:
    for w in get_windows():
        if w.focused:
            return w


class Sequence:

    def __init__(self, id):
        self.id = id

    @property
    def view(self):
        return View(con.call('sequence_get_view', self.id))

def new_sequence() -> Sequence:
    return Sequence(con.call('new_sequence'))

def get_sequences() -> List[Sequence]:
    return [Sequence(s) for s in con.call('get_sequences')]


class View:

    def __init__(self, id):
        self.id = id

    @property
    def center(self) -> Vec2i:
        return con.call('view_get_center', self.id)

    @center.setter
    def center(self, pos: Vec2i):
        return con.call('view_set_center', self.id, pos)

    @property
    def zoom(self) -> float:
        return con.call('view_get_zoom', self.id)

    @zoom.setter
    def zoom(self, val: float):
        return con.call('view_set_zoom', self.id, val)

def new_view() -> View:
    return View(con.call('new_view'))

def get_views() -> List[View]:
    return [View(v) for v in con.call('get_views')]

