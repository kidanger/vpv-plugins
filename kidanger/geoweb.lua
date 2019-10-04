--[[
Add this to your ~/.vpvrc:
    plugins.load('geoweb', 'kidanger/geoweb')
    plugins.shortkey.register('f2', plugins.geoweb.launch, 'start geoweb')

You might also need to change the browser command (example for OSX):
    plugins.geoweb.set_browser '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome'
]]

local geofiles = {}
local prevs = {}
local cache = {}
local curid = 0
local browser = '/usr/bin/chromium-browser --user-data-dir=/home/anger/.cache/chromium-temp --allow-file-access-from-files --no-default-browser-check --no-first-run'

local html = [[
<!DOCTYPE html>
<html>
<head>
	<title>Map</title>
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.5.1/dist/leaflet.css" />
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

var objects = [%s];
var data_layer = null;
var changed = false;

var colors = ['blue', 'green', 'red', 'yellow', 'cyan', 'pink'];
for (var o in objects) {
    setInterval(tick, 250, o, objects[o]);
}

function tick(i, file) {
    check(i, file);
    if (changed) {
        changed = false;
        if (data_layer)
            data_layer.remove(map);

        data_layer = new L.GeoJSON(objects, { style: function(f) {
            var i = objects.indexOf(f.geometry);
            return { color: colors[i%%colors.length], opacity: 0.5 };
        }});
        map.flyToBounds(data_layer.getBounds(), {padding: [10, 10], animate: true})
        data_layer.addTo(map);
    }
}

function check(i, file) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function(){
        if(xmlhttp.readyState == 4){
            var dat = JSON.parse(xmlhttp.responseText);
            var eq = JSON.stringify(dat) == JSON.stringify(objects[i]);
            if (!eq) {
                objects[i] = dat;
                changed = true;
            }
        }
    };
    xmlhttp.open("GET", file, true);
    xmlhttp.send();
}

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

local function set_browser(cmd)
    browser = cmd
end

local function launch()
    -- allocate geofiles
    for i, seq in pairs(get_sequences()) do
        local id = seq:get_id()
        local img = seq.collection:get_filename(seq.player.frame-1)
        geofiles[id] = os.tmpname()
        generate(seq, img)
    end

    -- build and save the html page
    local page = os.tmpname() .. '.html'
    local file = io.open(page, 'w+')
    local list = ''
    for _, f in pairs(geofiles) do
        list = list .. ('%q,'):format(f)
    end
    file:write(html:format(list))
    file:close()

    -- launch the browser
    local cmd = ('%s %q &'):format(browser, page)
    print(cmd)
    os.execute(cmd)
    print('geoweb started, a browser should open.')
end

local function on_window_tick(window, focused)
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
    set_browser=set_browser,
}

