from api import *

def try_rpcm(img, x, y):
    try:
        import rpcm
    except ImportError as e:
        print('Cannot import rpcm:', e)
        return
    try:
        rpc = rpcm.rpc_from_geotiff(img)
        import srtm4
        z = srtm4.srtm4(rpc.lon_offset, rpc.lat_offset)
        lon, lat = rpc.localization(x, y, z)
    except Exception as e:
        print('Error while localization:', e)
        return
    return lon, lat

def on_tick():
    curwin = get_focused_window()
    if curwin and is_mouse_clicked(2):
        x, y = get_mouse_position()
        img = curwin.current_filename

        dat = None
        if dat is None:
            dat = try_rpcm(img, x, y)
        if dat is None:
            return

        lon, lat = dat
        print(lon, lat)
        with open('/tmp/vpvcursor.kml', 'w') as f:
            f.write(f'''\
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name></name>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>
</kml>''')

