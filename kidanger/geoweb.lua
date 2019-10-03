
local geofiles = {}
local prevs = {}
local cache = {}
local curid = 0

local html = [[
<!DOCTYPE html>
<html>
<head>
	<title>Map</title>
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.0.3/dist/leaflet.css" />
	<script src="https://unpkg.com/leaflet@1.0.3/dist/leaflet.js"></script>
	<style> body {padding: 0; margin: 0; } html, body, #map {height: 100%%; width: 100%%; } </style> </head>
<body>
<div id="map"></div>
</body>
<script>

var map = L.map("map");
map.panTo(new L.LatLng(40.737, -73.923));

var Esri_WorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
});
Esri_WorldImagery.addTo(map);

var data = {};
var data_layer = null;

function tick() {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function(){
        if(xmlhttp.readyState == 4){
            var dat = JSON.parse(xmlhttp.responseText);
            var eq = JSON.stringify(dat) == JSON.stringify(data);
            if (!eq) {
                data = dat;
                if (data_layer)
                    data_layer.remove(map);
                data_layer = new L.GeoJSON(dat);
                map.flyToBounds(data_layer.getBounds(), {padding: [10, 10], animate: true})
                data_layer.addTo(map);
            }
        }
    };
    xmlhttp.open("GET","%s",true);
    xmlhttp.send();
}

setInterval(tick, 250);

</script>
</html>
]]

local function generate(seq, img)
    local geofile = geofiles[seq:get_id()]
    if not cache[img] then
        cache[img] = curid
        curid = curid + 1
    end

    local iid = cache[img]
    if os.execute(('cp %q.%d %q 2>/dev/null'):format(geofile, iid, geofile)) then
        return
    end

    --local prg = 'rio bounds'
    local prg = 'rpcm footprint'
    local cmd = ('%s %q >%q.%d && cp %q.%d %q &'):format(
        prg, img, geofile, iid, geofile, iid, geofile)
    print(cmd)
    local ok, err = os.execute(cmd)
    if not ok then
        print('err:', ok, err)
    end
end

local function launch(window)
    local seq = window.sequences[window.index+1]
    local id = seq:get_id()
    local img = seq.collection:get_filename(seq.player.frame-1)
    local page = os.tmpname() .. '.html'
    geofiles[id] = os.tmpname()
    local file = io.open(page, 'w+')
    file:write(html:format(geofiles[id]))
    file:close()
    local cmd = ('/usr/bin/chromium-browser --user-data-dir=~/.cache/chromium-temp --allow-file-access-from-files --no-default-browser-check --no-first-run %q &'):format(page)
    print(cmd)
    os.execute(cmd)
    print('geoweb started, a browser should open.')
end

function on_window_tick(window, focused)
    local seq = window.sequences[window.index+1]
    local id = seq:get_id()
    if not geofiles[id] then return end

    local img = seq.collection:get_filename(seq.player.frame-1)
    if prevs[id] ~= img then
        prevs[id] = img
        generate(seq, img)
    end
end

return {
    on_window_tick=on_window_tick,
    launch=launch,
}

