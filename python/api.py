from typing import NewType, List, Tuple

Vec2i = Tuple[int, int]

con = None

def reload_images() -> None:
    return con.call('reload')

def set_config(key: str, val):
    return con.call('config_set', key, val)

def get_config(key: str):
    return con.call('config_get', key)

def is_key_pressed(key: str, repeat: bool=True) -> bool:
    return con.call('is_key_pressed', key, repeat)

def is_key_down(key: str) -> bool:
    return con.call('is_key_down', key)

def is_key_released(key: str) -> bool:
    return con.call('is_key_released', key)

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
        seq = con.call('window_get_current_sequence', self.id)
        return seq and Sequence(seq)

# .addProperty("index", &Window::index)
# .addProperty("sequences", &Window::sequences)
# .addProperty("always_on_top", &Window::alwaysOnTop)
# .addProperty("dont_layout", &Window::dontLayout)

    @property
    def current_filename(self) -> str:
        return con.call('window_get_current_filename', self.id)

    def take_screenshot(self):
        return con.call('window_take_screenshot', self.id)

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
        id = con.call('sequence_get_view', self.id)
        assert id
        return View(id)

    @property
    def player(self):
        id = con.call('sequence_get_player', self.id)
        assert id
        return Player(id)

    @property
    def image(self):
        id = con.call('sequence_get_image', self.id)
        return id and Image(id)

    def put_script_svg(self, key: str, value: str="") -> bool:
        return con.call('sequence_put_script_svg', self.id, key, value)

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


class Player:

    def __init__(self, id):
        self.id = id

    @property
    def frame(self) -> int:
        return con.call('player_get_frame', self.id)

    @frame.setter
    def frame(self, frame: int):
        return con.call('player_set_frame', self.id, frame)

    @property
    def fps(self) -> float:
        return con.call('player_get_fps', self.id)

    @fps.setter
    def fps(self, fps: float):
        return con.call('player_set_fps', self.id, fps)

    @property
    def playing(self) -> bool:
        return con.call('player_get_playing', self.id)

    @playing.setter
    def playing(self, playing: bool):
        return con.call('player_set_playing', self.id, playing)

    @property
    def bouncy(self) -> bool:
        return con.call('player_get_bouncy', self.id)

    @bouncy.setter
    def bouncy(self, bouncy: bool):
        return con.call('player_set_bouncy', self.id, bouncy)

    @property
    def opened(self) -> bool:
        return con.call('player_get_opened', self.id)

    @opened.setter
    def opened(self, opened: bool):
        return con.call('player_set_opened', self.id, opened)

    @property
    def current_max_frame(self) -> int:
        return con.call('player_get_current_max_frame', self.id)

    @current_max_frame.setter
    def current_max_frame(self, current_max_frame: int):
        return con.call('player_set_current_max_frame', self.id, current_max_frame)

    @property
    def current_min_frame(self) -> int:
        return con.call('player_get_current_min_frame', self.id)

    @current_min_frame.setter
    def current_min_frame(self, current_min_frame: int):
        return con.call('player_set_current_min_frame', self.id, current_min_frame)

    @property
    def max_frame(self) -> int:
        return con.call('player_get_max_frame', self.id)

    @property
    def min_frame(self) -> int:
        return con.call('player_get_min_frame', self.id)

def new_player() -> Player:
    return Player(con.call('new_player'))

def get_players() -> List[Player]:
    return [Player(p) for p in con.call('get_players')]


class Image:

    def __init__(self, id):
        self.id = id

    def get_pixels_from_coords(self, xs, ys) -> List[List[float]]:
        return con.call('image_get_pixels_from_coords', self.id, xs, ys)

