from __future__ import annotations

import time
from functools import partial
import os
import json
import concurrent.futures
import glob
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import api


@dataclass(frozen=True)
class Token:
    name: str
    start: str
    end: str

    def __repr__(self) -> str:
        return f"[{self.start}-{self.name}-{self.end}]"


GroundtruthEntry = dict[Token, str]


@dataclass(frozen=True)
class Object:
    text: str
    confidence: float
    text_confidence: float
    polygon: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]
    token: Token

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """x, y, width, height"""
        f = 1.5  # manually fitted, TODO: understand where does this come from
        minx = int(f * min(p[0] for p in self.polygon))
        miny = int(f * min(p[1] for p in self.polygon))
        maxx = int(f * max(p[0] for p in self.polygon))
        maxy = int(f * max(p[1] for p in self.polygon))
        return minx, miny, maxx - minx + 1, maxy - miny + 1


@dataclass(frozen=True)
class Prediction:
    image_name: str
    values: dict[Token, str]
    objects: list[Object]


@dataclass(frozen=True)
class LabeledImage:
    image_path: str
    set_name: str
    groundtruth: dict[Token, str]


@dataclass
class State:
    ground_truths: dict[api.Window, list[LabeledImage]]
    predictions_results: dict[api.Window, tuple[str, list[Prediction]]]
    current_hovered: Optional[Token] = None
    last_update: float = 0.0

    def refresh_all(self):
        tnow = time.time()
        if tnow - self.last_update < 0.05:
            return
        self.last_update = tnow

        mousex, mousey = api.get_mouse_position_ui()

        def mouse_in_win(win: api.Window) -> tuple[int, int]:
            wx, wy = win.position
            return mousex - wx, mousey - wy

        gt_win, labeled_images = next(iter(self.ground_truths.items()))
        gt_seq = gt_win.current_sequence
        filename = gt_seq.current_filename
        name = Path(filename).stem

        possible_images = [img for img in labeled_images if img.image_path == filename]
        if not possible_images:
            return

        image = possible_images[0]

        font_color = "#111111"
        font_size = 16
        width = 370

        def show_panel(
            win: api.Window,
            source: str,
            values: dict[Token, str],
            groundtruth: Optional[dict[Token, str]] = None,
        ) -> Optional[Token]:
            seq = win.current_sequence
            mx, my = mouse_in_win(win)

            y = 4
            svg = """
            <svg width="1" height="1">
            """
            svg += f"""
            <rect display="absolute" x="0" y="0" width="{width}" height="2000" fill="#EEEEEE" fill-opacity="1" />
            """
            svg += f"""
            <text display="absolute" x="4" y="{y}" fill="{font_color}" font-size="{font_size}">from: {source}</text>
            """
            y += int(font_size * 1.3)
            svg += f"""
            <text display="absolute" x="4" y="{y}" fill="{font_color}" font-size="{font_size}">set: {image.set_name}</text>
            """
            y += int(font_size * 2)

            hovered = None
            for token, value in sorted(
                values.items(), key=lambda it: it[0].start + " " + it[0].end
            ):
                color = font_color
                if groundtruth and token in groundtruth:
                    gtvalue = groundtruth[token]
                    if gtvalue == value:
                        color = "#004400"
                    elif gtvalue.lower() == value.lower():
                        color = "#664400"
                    else:
                        color = "#660000"

                starty = y

                svg += f"""
                    <text display="absolute" x="4" y="{y}" fill="{font_color}" font-size="{font_size}">{token.name}</text>
                """
                y += int(font_size * 1.3)
                svg += f"""
                    <text display="absolute" x="30" y="{y}" fill="{color}" font-size="{font_size}">{value}</text>
                """
                y += int(font_size * 2)

                if (
                    my > starty + font_size / 2
                    and my < y + font_size / 2
                    and mx > 0
                    and mx < width
                ):
                    hovered = token

            svg += """
            </svg>
            """
            seq.put_script_svg("panel", svg)
            return hovered

        updated_hovered = show_panel(
            gt_win, source="ground-truth", values=image.groundtruth
        )

        for win, (pred_name, predictions) in self.predictions_results.items():
            seq = win.current_sequence
            possible_predictions = [p for p in predictions if p.image_name == name]
            if not possible_predictions:
                seq.put_script_svg("panel")
                seq.put_script_svg("objects")
                continue

            prediction = possible_predictions[0]
            hovered = show_panel(
                win,
                source=pred_name,
                values=prediction.values,
                groundtruth=image.groundtruth,
            )
            if hovered:
                updated_hovered = hovered

            if self.current_hovered is not None:
                svg = """
                <svg width="1" height="1">
                """
                for obj in prediction.objects:
                    if obj.token != self.current_hovered:
                        continue
                    x, y, w, h = obj.rect
                    svg += f"""
                    <rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="red" />
                    <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="red" fill-opacity="{obj.confidence}" />
                    """
                for obj in prediction.objects:
                    if obj.token != self.current_hovered:
                        continue
                    x, y, w, h = obj.rect
                    svg += f"""
                    <text x="{x-10}" y="{y-35}" fill="blue" font-size="40">{obj.text}</text>
                    """
                svg += """
                </svg>
                """
                seq.put_script_svg("objects", svg)
            else:
                seq.put_script_svg("objects")

        if updated_hovered != self.current_hovered:
            self.current_hovered = updated_hovered
            self.last_update = 0.0  # trigger a redraw


def read_tokens(path: str) -> list[Token]:
    import yaml

    with open(path) as f:
        data = yaml.safe_load(f)

    tokens = [
        Token(name=name, start=d["start"], end=d["end"]) for name, d in data.items()
    ]
    return tokens


def decode_values(line: str, tokens: list[Token]) -> dict[Token, str]:
    groundtruth = {}
    starts: dict[Token, int] = {}
    for t in tokens:
        assert t.end == "", "token.end not supported yet"
        try:
            i1 = line.index(t.start)
        except ValueError:
            continue

        starts[t] = i1

    for t, start in starts.items():
        after = [j for j in starts.values() if j > start]
        if not after:
            end = len(line)
        else:
            end = min(after)
        value = line[start:end]
        value = value.removeprefix(t.start)
        value = value.removesuffix(t.end)
        groundtruth[t] = value

    return groundtruth


def read_labels(
    path: str,
) -> tuple[list[Token], list[LabeledImage]]:
    dir = os.path.dirname(path)
    tokens = read_tokens(os.path.join(dir, "tokens.yml"))

    with open(path) as f:
        labels = json.load(f)

    def order(setname: str) -> str:
        if setname.lower().startswith("train"):
            return "_0"
        if setname.lower().startswith("val"):
            return "_1"
        if setname.lower().startswith("eva"):
            return "_1"
        if setname.lower().startswith("test"):
            return "_2"
        return setname.lower()

    def decode(set_name: str, image_path: str, line: str) -> LabeledImage:
        groundtruth = decode_values(line, tokens)
        return LabeledImage(
            image_path=os.path.join(dir, image_path),
            set_name=set_name,
            groundtruth=groundtruth,
        )

    # concat Train/Val/Test, decode the labels
    sets = sorted(labels.keys(), key=order)
    images = [decode(s, img_name, v) for s in sets for img_name, v in labels[s].items()]
    return tokens, images


def read_prediction(tokens: list[Token], path: str) -> Prediction:
    with open(path) as f:
        data = json.load(f)

    image_name = Path(path).stem
    values = decode_values(data["text"], tokens)

    objects = []
    token = None
    for obj in data["objects"]:
        c = obj["text"]

        for t in tokens:
            if c == t.start:
                token = t
                break

        assert token
        objects.append(
            Object(
                text=c,
                confidence=obj["confidence"],
                text_confidence=obj["text_confidence"],
                polygon=obj["polygon"],
                token=token,
            )
        )

    return Prediction(image_name=image_name, values=values, objects=objects)


FIRST = True
STATE: Optional[State] = None


def setup() -> Optional[State]:
    predictions_results = {}
    tokens = None
    all_groundtruths = {}
    images_glob = None
    for win in api.get_windows():
        seq = win.current_sequence
        name = seq.current_filename

        if name.startswith("dan:labels:"):
            assert (
                not all_groundtruths
            ), "for now, the plugin does not support multiple ground-truth sequences"
            label_path = name.removeprefix("dan:labels:")
            tokens, gt = read_labels(label_path)
            all_groundtruths[win] = gt
            images_glob = "::".join(img.image_path for img in gt)

        if name.startswith("dan:prediction:"):
            predictions_glob = name.removeprefix("dan:prediction:")
            predictions = glob.glob(predictions_glob)
            assert (
                tokens is not None
            ), "use dan:labels: before dan:prediction:, in order to get the tokens"
            with concurrent.futures.ThreadPoolExecutor() as pool:
                read_pred = partial(read_prediction, tokens)
                predictions = list(pool.map(read_pred, predictions))
            predictions_results[win] = (predictions_glob, predictions)

    if not all_groundtruths:
        print(
            "couldn't find labels... Did you forget to specify dan:labels:path/labels.json?",
            file=sys.stderr,
        )
        return None

    state = State(
        ground_truths=all_groundtruths,
        predictions_results=predictions_results,
    )

    assert images_glob
    for win in state.ground_truths.keys():
        win.current_sequence.set_glob(images_glob)
    for win in state.predictions_results.keys():
        win.current_sequence.set_glob(images_glob)

    return state


def on_tick():
    global FIRST, STATE
    if FIRST:
        STATE = setup()
        FIRST = False
    if not STATE:
        return
    state = STATE

    # TODO: if press shift + left/right, go to next image with prediction (skip unpredicted ones)

    state.refresh_all()
