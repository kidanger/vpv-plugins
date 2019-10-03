-- usage: env LABELBOX=<file> vpv <imgs> svg:/tmp/labelbox.svg

local filename = os.getenv 'LABELBOX'

if not filename then
    return {}
end

local function generate_svg(seq, img)
    local buf = ''
    buf = buf .. '<svg width="1" height="1">'
    buf = buf .. '<text display="absolute" font-size="20" fill="orange">LabelBox active</text>'
    local f = assert(io.open(filename, 'r'))
    for l in f:lines() do
        if l:find(('^%s'):format(img)) then
            local x, y = l:match '^.*,(-?%d+),(-?%d+)$'
            x = x + 0.5
            y = y + 0.5
            buf = buf .. (('<circle cx="%f" cy="%f" r="2" fill="red" fill-opacity="0.2" />\n'):format(x, y))
            buf = buf .. (('<circle cx="%f" cy="%f" r="2" stroke="orange" stroke-width="0.2" />\n'):format(x, y))
        end
    end
    f:close()
    buf = buf .. '</svg>'

    local svg = io.open('/tmp/labelbox.svg', 'w')
    svg:write(buf)
    svg:close()
end

local function append_point(img, x, y)
    local f = assert(io.open(filename, 'a'))
    f:write(('%s,%d,%d\n'):format(img, x, y))
    f:close()
end

local prev
function on_window_tick(window, focused)
    if not focused then return end

    local x, y = gHoveredPixel.x, gHoveredPixel.y
    local seq = window.sequences[window.index+1]
    local img = seq.collection:get_filename(seq.player.frame-1)
    if iskeypressed 'l' then
        append_point(img, x, y)
        generate_svg(seq, prev)
    end
    if prev ~= img then
        prev = img
        generate_svg(seq, prev)
    end
end

return {
    on_window_tick=on_window_tick,
}

