import re
from dateutil.parser import parse

from api import get_windows

datere = re.compile(r'.*(\d{4}-?\d{2}-?\d{2}([tT]\d{6})?).*')

def on_tick():
    for w in get_windows():
        filename = w.current_filename
        seq = w.current_sequence
        seq.put_script_svg('date', '')
        if not filename: continue
        if not seq: continue
        date = datere.match(filename)
        if not date: continue
        date = parse(date.group(1))
        svg = f'''
            <svg width="1" height="1">
                <text font-size="50" fill="#00FF00" display="absolute">{date}</text>
            </svg>
        '''
        seq.put_script_svg('date', svg)

