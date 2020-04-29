local lib
local curwin

local function str2win(str)
    for i, w in pairs(get_windows()) do
        if w.id == str then
            return w
        end
    end
end
local function str2seq(str)
    for i, s in pairs(get_sequences()) do
        if s.id == str then
            return s
        end
    end
end
local function str2view(str)
    for i, v in pairs(get_views()) do
        if v.id == str then
            return v
        end
    end
end
local function str2player(str)
    for i, p in pairs(get_players()) do
        if p.id == str then
            return p
        end
    end
end
local function str2image(str)
    return get_image_by_id(str)
end

local api = {
    config_get=function(key)
        return _G[key]
    end,
    config_set=function(key, val)
        _G[key] = val
    end,
    reload=function()
        reload()
    end,

    -- EVENT
    is_key_pressed=iskeypressed,
    is_key_down=iskeydown,
    is_key_released=iskeyreleased,
    is_mouse_clicked=ismouseclicked,
    get_mouse_position=function()
        return {gHoveredPixel.x, gHoveredPixel.y}
    end,

    -- WINDOW
    new_window=function()
        return new_window().id
    end,
    get_windows=function()
        local wins = {}
        for i, w in pairs(get_windows()) do
            table.insert(wins, w.id)
        end
        return wins
    end,
    window_is_focused=function(win)
        return curwin and win == curwin.id
    end,
    window_is_opened=function(win)
        return str2win(win).opened
    end,
    window_set_opened=function(win, val)
        str2win(win).opened = val
    end,
    window_get_position=function(win)
        local pos = str2win(win).position
        return {pos.x, pos.y}
    end,
    window_set_position=function(win, pos)
        local win = str2win(win)
        win.position = ImVec2(pos[1], pos[2])
        win.force_geometry = true
    end,
    window_get_size=function(win)
        local pos = str2win(win).size
        return {pos.x, pos.y}
    end,
    window_set_size=function(win, size)
        local win = str2win(win)
        win.size = ImVec2(size[1], size[2])
        win.force_geometry = true
    end,
    window_get_current_sequence=function(id)
        local win = str2win(id)
        local seq = win.sequences[win.index+1]
        return seq.id
    end,
    window_get_current_filename=function(id)
        local win = str2win(id)
        local seq = win.sequences[win.index+1]
        local filename = seq.collection:get_filename(seq.player.frame - 1)
        return filename
    end,
    window_take_screenshot=function(id)
        local win = str2win(id)
        win.screenshot = true
    end,

    -- SEQUENCE
    new_sequence=function()
        return new_sequence().id
    end,
    get_sequences=function()
        local seqs = {}
        for i, s in pairs(get_sequences()) do
            table.insert(seqs, s.id)
        end
        return seqs
    end,
    sequence_get_view=function(id)
        local seq = str2seq(id)
        return seq.view and seq.view.id
    end,
    sequence_get_player=function(id)
        local seq = str2seq(id)
        return seq.player and seq.player.id
    end,
    sequence_get_image=function(id)
        local seq = str2seq(id)
        return seq.image and seq.image.id
    end,

    -- VIEW
    new_view=function()
        return new_view().id
    end,
    get_views=function()
        local views = {}
        for i, v in pairs(get_views()) do
            table.insert(views, v.id)
        end
        return views
    end,
    view_get_center=function(id)
        local view = str2view(id)
        return {view.center.x, view.center.y}
    end,
    view_set_center=function(id, pos)
        local view = str2view(id)
        view.center = ImVec2(pos[1], pos[2])
    end,
    view_get_zoom=function(id)
        local view = str2view(id)
        return view.zoom
    end,
    view_set_zoom=function(id, val)
        local view = str2view(id)
        view.zoom = val
    end,

    -- PLAYER
    new_player=function()
        return new_player().id
    end,
    get_players=function()
        local players = {}
        for i, v in pairs(get_players()) do
            table.insert(players, v.id)
        end
        return players
    end,
    player_get_frame=function(id)
        local player = str2player(id)
        return player.frame
    end,
    player_set_frame=function(id, val)
        local player = str2player(id)
        player.frame = val
        player:check_bounds()
    end,
    player_get_fps=function(id)
        local player = str2player(id)
        return player.fps
    end,
    player_set_fps=function(id, val)
        local player = str2player(id)
        player.fps = val
    end,
    player_get_playing=function(id)
        local player = str2player(id)
        return player.playing
    end,
    player_set_playing=function(id, val)
        local player = str2player(id)
        player.playing = val
    end,
    player_get_bouncy=function(id)
        local player = str2player(id)
        return player.bouncy
    end,
    player_set_bouncy=function(id, val)
        local player = str2player(id)
        player.bouncy = val
    end,
    player_get_opened=function(id)
        local player = str2player(id)
        return player.opened
    end,
    player_set_opened=function(id, val)
        local player = str2player(id)
        player.opened = val
    end,
    player_get_current_min_frame=function(id)
        local player = str2player(id)
        return player.current_min_frame
    end,
    player_set_current_min_frame=function(id, val)
        local player = str2player(id)
        player.current_min_frame = val
        player:check_bounds()
    end,
    player_get_current_max_frame=function(id)
        local player = str2player(id)
        return player.current_max_frame
    end,
    player_set_current_max_frame=function(id, val)
        local player = str2player(id)
        player.current_max_frame = val
        player:check_bounds()
    end,
    player_get_min_frame=function(id)
        local player = str2player(id)
        return player.min_frame
    end,
    player_get_max_frame=function(id)
        local player = str2player(id)
        return player.max_frame
    end,

    -- IMAGE
    image_get_pixels_from_coords=function(id, xs, ys)
        local im = str2image(id)
        return image_get_pixels_from_coords(im, xs, ys)
    end,
}

local function getfifo()
    local h = io.popen 'mktemp'
    local fifo = h:read("*l")
    h:close()
    assert(os.execute(('rm %q && mkfifo %q'):format(fifo, fifo)))
    return fifo
end

local function init(plugins)
    local path = plugins.path .. '/python'
    package.path = package.path ..  ";" .. path .. "/?/init.lua;" .. path .. "/?.lua"
    lib = require 'lib'

    local fin = getfifo()
    local fout = getfifo()
    local cmd = ('python %s/python/plugins.py %s %s &'):format(plugins.path, fin, fout)
    lib.launch(fin, fout, cmd, api)
    lib.call('init')
end

local function on_tick(...)
    lib.call('on_tick', ...)
end

local function on_window_tick(w, focused)
    if focused then curwin = w end
    lib.call('on_window_tick', w.id, focused)
end

local function load(...)
    lib.call('load', ...)
end

return {
    init=init,
    on_tick=on_tick,
    on_window_tick=on_window_tick,
    load=load,
}

