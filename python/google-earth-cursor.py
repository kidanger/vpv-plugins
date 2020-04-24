from api import *

try:
    import rpcm
except ImportError as e:
    print('Cannot import rpcm:', e)

def on_tick():
    if is_mouse_clicked(2):
        x, y = get_mouse_position()
        img = get_current_filename()
        try:
            lon, lat = rpcm.localization(img, x, y, 0)
        except Exception as e:
            print('Error while localization:', e)
        else:
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

