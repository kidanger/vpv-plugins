local lib

local curwin

local api = {
    ismouseclicked=ismouseclicked,
    get_mouse_position=function ()
        return {gHoveredPixel.x, gHoveredPixel.y}
    end,
    get_current_filename=function ()
        local seq = curwin.sequences[curwin.index+1]
        local filename = seq.collection:get_filename(seq.player.frame - 1)
        return filename
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

