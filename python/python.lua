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

local api = {
    reload=function()
        reload()
    end,

    -- EVENT
    is_key_down=iskeydown,
    is_key_up=iskeyup,
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
        return seq.view.id
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

