local lib

local curwin
function get_current_window()
    return curwin
end

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
    local cmd = ('python %s/python/google-earth-cursor.py %s %s &'):format(plugins.path, fin, fout)
    lib.launch(fin, fout, cmd)
end

local function on_window_tick(window, focused)
    if focused then
        curwin = window
    end
    lib.call('on_window_tick', focused)
end

return {
    init=init,
    on_window_tick=on_window_tick,
}


