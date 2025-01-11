from typing import List, Tuple

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

def get_mouse_position_ui() -> Vec2i:
    return con.call('get_mouse_position_ui')

def get_selection() -> Tuple[Vec2i,Vec2i]:
    return con.call('get_selection')

class _Ided:

    def __init__(self, id):
        self.id = id

    def __eq__(self, o):
        return self.id == o.id

    def __hash__(self):
        return hash(self.id)


class Window(_Ided):

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


class Sequence(_Ided):

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
    def colormap(self):
        id = con.call('sequence_get_colormap', self.id)
        assert id
        return id and Colormap(id)

    @property
    def image(self):
        id = con.call('sequence_get_image', self.id)
        return id and Image(id)

    @property
    def collection(self):
        id = con.call('sequence_get_collection', self.id)
        return id and ImageCollection(id)

    def put_script_svg(self, key: str, value: str="") -> bool:
        return con.call('sequence_put_script_svg', self.id, key, value)

    def set_glob(self, glob: str):
        return con.call('sequence_set_glob', self.id, glob)

    @property
    def current_filename(self) -> str:
        return con.call('sequence_get_current_filename', self.id)


def new_sequence() -> Sequence:
    return Sequence(con.call('new_sequence'))

def get_sequences() -> List[Sequence]:
    return [Sequence(s) for s in con.call('get_sequences')]


class View(_Ided):

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


class Player(_Ided):

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


class Colormap(_Ided):

    def get_range(self, n: int) -> List[float]:
        return con.call('colormap_get_range', self.id, n)

    @property
    def shader(self) -> str:
        return con.call('colormap_get_shader', self.id)

    @shader.setter
    def shader(self, shader: str):
        return con.call('colormap_set_shader', self.id, shader)

    @property
    def center(self) -> str:
        return con.call('colormap_get_center', self.id)

    @center.setter
    def center(self, center: str):
        return con.call('colormap_set_center', self.id, center)

    @property
    def radius(self) -> str:
        return con.call('colormap_get_radius', self.id)

    @radius.setter
    def radius(self, radius: str):
        return con.call('colormap_set_radius', self.id, radius)

    @property
    def bands(self) -> Tuple[int,int,int]:
        return con.call('colormap_get_bands', self.id)

    @bands.setter
    def bands(self, bands: Tuple[int,int,int]):
        return con.call('colormap_set_bands', self.id, bands)

class Image(_Ided):

    @property
    def size(self) -> Vec2i:
        return con.call('image_get_size', self.id)

    @property
    def channels(self) -> int:
        return con.call('image_get_channels', self.id)

    def get_pixels_from_coords(self, xs, ys) -> List[List[float]]:
        return con.call('image_get_pixels_from_coords', self.id, xs, ys)

class ImageCollection(_Ided):

    @property
    def length(self) -> int:
        return con.call('collection_get_length', self.id)

    def get_filename(self, index: int) -> str:
        return con.call('collection_get_filename', self.id, index)



# from https://stackoverflow.com/a/78312617
class LazyLoader:
    "thin shell class to wrap modules.  load real module on first access and pass thru"

    def __init__(me, modname):
        me._modname = modname
        me._mod = None

    def __getattr__(me, attr):
        "import module on first attribute access"

        try:
            return getattr(me._mod, attr)

        except Exception as e:
            if me._mod is None:
                # module is unset, load it
                import importlib

                me._mod = importlib.import_module(me._modname)
            else:
                # module is set, got different exception from getattr ().  reraise it
                raise e

        # retry getattr if module was just loaded for first time
        # call this outside exception handler in case it raises new exception
        return getattr(me._mod, attr)

