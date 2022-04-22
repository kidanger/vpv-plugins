local VPV_VIEWS = os.getenv 'VPV_VIEWS'

if not VPV_VIEWS then
    return {}
end

local function read_views(s)
    local t = {}
    for l in s:lines() do
        local x1, y1, x2, y2 = l:match('([^,]+),([^,]+),([^,]+),([^,]+)')
        table.insert(t, {
            p1=ImVec2(tonumber(x1), tonumber(y1)),
            p2=ImVec2(tonumber(x2), tonumber(y2)),
        })
    end
    return t
end

local function update_views()
    if not VPV_VIEWS then return end
    local f = io.open(VPV_VIEWS, 'r')
    if not f then return end
    local lines = read_views(f)
    f:close()
    local windows = get_windows()
    if #lines ~= #windows then return end
    for i, line in ipairs(lines) do
        local win = windows[i]
        local seq = win.sequences[win.index+1]
        local rect = ImRect(line.p1, line.p2)
        seq.view.center = rect:get_center()/seq.image.size
        seq.view.zoom = math.min(win.size.x/rect:get_width(), win.size.y/rect:get_height())
    end
    os.execute(('rm -f %q'):format(VPV_VIEWS))
end

function on_window_tick(w, focused)
    if not focused then return end
    update_views()
end

return {
    on_window_tick=on_window_tick,
}
