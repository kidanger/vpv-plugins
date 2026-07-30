from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import api

_DATE_RE = re.compile(r"((19|20)\d\d-?[01]\d-?[0-3]\d)")

LABEL_TEMPLATE = os.getenv("LABEL", "")
LABEL_AREA_PATH = os.getenv("LABEL_AREA", "")

# Label cycle order (6 classes)
LABELS = [
    "ON",
    "ON-unsure",
    "OFF-unsure",
    "OFF",
    "CLOUDY",
    "NA",
]

# (fill_color, fill_opacity)
LABEL_STYLES: dict[str, tuple[str, str]] = {
    "NA": ("magenta", "1.0"),
    "CLOUDY": ("cyan", "1.0"),
    "ON": ("green", "1.0"),
    "OFF": ("red", "1.0"),
    "ON-unsure": ("#99FF99", "0.8"),
    "OFF-unsure": ("#FF9999", "0.8"),
}


def parse_date(filename: str) -> Optional[str]:
    """Extract YYYYMMDD from filename."""
    m = _DATE_RE.search(filename)
    if not m:
        return None
    return m.group(1).replace("-", "")


def expand_label_path(date_str: str) -> Path:
    return Path(LABEL_TEMPLATE.format(date=date_str))


def cycle_label(current: Optional[str]) -> str:
    if current is None or current not in LABELS:
        return LABELS[0]
    return LABELS[(LABELS.index(current) + 1) % len(LABELS)]


@dataclass
class State:
    cur_filename: str
    ref_transform: object  # rasterio Affine
    ref_crs: object  # rasterio CRS
    area_polys: list[list[tuple[int, int]]] = field(default_factory=list)
    labels: dict[str, dict[tuple[int, int], str]] = field(default_factory=dict)
    last_date: Optional[str] = None
    hovered_label: Optional[str] = None
    svg_visible: bool = True


def _pixel_to_lonlat(state: State, col: int, row: int) -> tuple[float, float]:
    import rasterio.transform
    from rasterio.crs import CRS
    from rasterio.warp import transform as warp_transform

    x, y = rasterio.transform.xy(state.ref_transform, row, col)
    wgs84 = CRS.from_epsg(4326)
    lons, lats = warp_transform(state.ref_crs, wgs84, [x], [y])
    return lons[0], lats[0]


def _lonlat_to_pixel(state: State, lon: float, lat: float) -> tuple[int, int]:
    from rasterio.crs import CRS
    from rasterio.warp import transform as warp_transform

    wgs84 = CRS.from_epsg(4326)
    xs, ys = warp_transform(wgs84, state.ref_crs, [lon], [lat])
    col, row = ~state.ref_transform * (xs[0], ys[0])
    return col, row


def _load_geojson(state: State, date_str: str):
    path = expand_label_path(date_str)
    if not path.exists():
        state.labels[date_str] = {}
        return
    try:
        with open(path) as f:
            gj = json.load(f)
        pixels: dict[tuple[int, int], str] = {}
        for feat in gj["features"]:
            props = feat["properties"]
            label = props["label"]
            col = props["col"]
            row = props["row"]
            if label and col is not None and row is not None:
                pixels[(int(col), int(row))] = label
        state.labels[date_str] = pixels
    except Exception as e:
        print(f"geolabeler: failed to load {path}: {e}", file=sys.stderr)
        state.labels[date_str] = {}


def _save_geojson(state: State, date_str: str):
    path = expand_label_path(date_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    features = []
    for (col, row), label in state.labels.get(date_str, {}).items():
        try:
            lon, lat = _pixel_to_lonlat(state, col, row)
        except Exception as e:
            print(
                f"geolabeler: pixel_to_lonlat failed for ({col},{row}): {e}",
                file=sys.stderr,
            )
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "label": label,
                    "col": col,
                    "row": row,
                    "image_filename": state.cur_filename,
                },
            }
        )
    gj = {"type": "FeatureCollection", "features": features}
    with open(path, "w") as f:
        json.dump(gj, f, indent=2)


def _build_svg(state: State, date_str: Optional[str]) -> str:
    parts = ['<svg width="1" height="1">']

    for poly in state.area_polys:
        if len(poly) < 2:
            continue
        pts = " ".join(f"{col},{row}" for col, row in poly)
        parts.append(
            f'  <polygon points="{pts}" fill="none" stroke="yellow"'
            f' stroke-width="0.2" stroke-opacity="0.8"/>'
        )

    if date_str and date_str in state.labels:
        for (col, row), label in state.labels[date_str].items():
            style = LABEL_STYLES.get(label)
            if not style:
                continue
            fill, opacity = style
            parts.append(
                f' <rect x="{col}" y="{row}" width="1" height="1"'
                f'  fill="{fill}" fill-opacity="{opacity}"'
                f" />"
            )
            parts.append(
                f' <rect x="{col}" y="{row}" width="1" height="1"'
                f'  stroke="white" stroke-width="0.1"'
                f" />"
            )

    if state.hovered_label:
        style = LABEL_STYLES[state.hovered_label]
        fill, opacity = style
        parts.append(
            f'  <text display="absolute" x="8" y="40" font-size="36"'
            f' fill="{fill}" >'
            f"{state.hovered_label}</text>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


def setup() -> Optional[State]:
    import rasterio

    sequences = api.get_sequences()
    if not sequences:
        print("geolabeler: no sequences found", file=sys.stderr)
        return None

    ref_seq = sequences[0]
    col_obj = ref_seq.collection
    if not col_obj or col_obj.length == 0:
        print("geolabeler: first sequence has no images", file=sys.stderr)
        return None

    ref_filename = col_obj.get_filename(0)
    try:
        with rasterio.open(ref_filename) as ds:
            ref_transform = ds.transform
            ref_crs = ds.crs
    except Exception as e:
        print(
            f"geolabeler: failed to open reference {ref_filename}: {e}", file=sys.stderr
        )
        return None

    state = State(
        ref_transform=ref_transform, ref_crs=ref_crs, cur_filename=ref_filename
    )

    if LABEL_AREA_PATH:
        try:
            with open(LABEL_AREA_PATH) as f:
                area_gj = json.load(f)
            for feat in area_gj.get("features", []) + [area_gj]:
                geom = feat.get("geometry", {})
                gtype = geom.get("type")
                if gtype == "Polygon":
                    for ring in geom.get("coordinates", []):
                        poly = [_lonlat_to_pixel(state, lon, lat) for lon, lat in ring]
                        state.area_polys.append(poly)
                elif gtype == "MultiPolygon":
                    for polygon in geom.get("coordinates", []):
                        for ring in polygon:
                            poly = [
                                _lonlat_to_pixel(state, lon, lat) for lon, lat in ring
                            ]
                            state.area_polys.append(poly)
        except Exception as e:
            print(f"geolabeler: failed to load LABEL_AREA: {e}", file=sys.stderr)

    return state


FIRST = True
STATE: Optional[State] = None


def on_tick():
    global FIRST, STATE

    if FIRST:
        FIRST = False
        if not LABEL_TEMPLATE:
            return
        STATE = setup()

    if not STATE:
        return
    state = STATE

    focused = api.get_focused_window()
    if not focused:
        return
    seq = focused.current_sequence
    if not seq:
        return
    filename = seq.current_filename
    if not filename:
        return

    state.cur_filename = filename
    date_str = parse_date(filename)
    svg_dirty = False

    # Load labels when date changes
    if date_str != state.last_date:
        if date_str and date_str not in state.labels:
            _load_geojson(state, date_str)
        state.last_date = date_str
        svg_dirty = True

    # Toggle SVG visibility
    if api.is_key_pressed("j", repeat=False):
        state.svg_visible = not state.svg_visible
        svg_dirty = True

    # Key handling (non-repeat to avoid cycling too fast)
    if date_str:
        mx, my = api.get_mouse_position()
        px = (int(round(mx)), int(round(my)))

        # Update hovered label
        pixels = state.labels.get(date_str, {})
        hovered = pixels.get(px)
        if hovered != state.hovered_label:
            state.hovered_label = hovered
            svg_dirty = True

        if api.is_key_pressed("l", repeat=False):
            pixels = state.labels.setdefault(date_str, {})
            pixels[px] = cycle_label(pixels.get(px))
            _save_geojson(state, date_str)
            state.svg_visible = True
            svg_dirty = True

        elif api.is_key_pressed("k", repeat=False):
            if api.is_key_down("control"):
                pixels.clear()
                _save_geojson(state, date_str)
                state.svg_visible = True
                svg_dirty = True
            else:
                pixels = state.labels.get(date_str, {})
                if px in pixels:
                    del pixels[px]
                    _save_geojson(state, date_str)
                    state.svg_visible = True
                    svg_dirty = True

    else:
        if state.hovered_label is not None:
            state.hovered_label = None
            svg_dirty = True

    # Rebuild SVG when content changes
    if svg_dirty:
        if state.svg_visible:
            current_svg = _build_svg(state, date_str)
            svg_to_send = current_svg if state.svg_visible else ""
            for s in api.get_sequences():
                s.put_script_svg("geolabeler", svg_to_send)
                break
        else:
            for s in api.get_sequences():
                s.put_script_svg("geolabeler")
