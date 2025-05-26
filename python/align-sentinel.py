import datetime
import re

from api import get_windows, is_key_pressed
from dateutil.parser import parse

datere = re.compile(r".*((19|20)\d\d-?[01]\d-?[0-3]\d([tT]\d{2}:?\d{2}:?\d{2})?).*")


def on_tick():
    if is_key_pressed("F4"):
        for w in get_windows():
            seq = w.current_sequence
            if not seq:
                continue
            col = seq.collection
            new_filenames: list[tuple[datetime.datetime, str]] = []
            for i in range(col.length):
                filename = col.get_filename(i)
                date = datere.match(filename)
                if not date:
                    continue
                try:
                    date = parse(date.group(1))
                except:
                    continue
                new_filenames.append((date, filename))
            new_filenames.sort(key=lambda k: k[0])
            seq.set_glob("::".join(filename for _, filename in new_filenames))
