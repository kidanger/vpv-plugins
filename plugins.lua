
local path = ...

package.path = package.path ..  ";" .. path .. "/?/init.lua;" .. path .. "/?.lua"

local plugins = {}
plugins.manager = {}

plugins.manager.hooks_window_tick = {}
plugins.manager.add_hook_window_tick = function(fn)
    table.insert(plugins.manager.hooks_window_tick, fn)
end

plugins.manager.hooks_tick = {}
plugins.manager.add_hook_tick = function(fn)
    table.insert(plugins.manager.hooks_tick, fn)
end

plugins.manager.on_tick = function()
    for _, p in ipairs(plugins.manager.hooks_tick) do
        p()
    end
end

plugins.manager.on_window_tick = function(...)
    for _, p in ipairs(plugins.manager.hooks_window_tick) do
        p(...)
    end
end

plugins.load = function (name, pkg)
    local status, err = pcall(function()
        package.loaded[pkg] = nil
        local pl = require(pkg)
        plugins[name] = pl
        if type(pl) == 'table' and pl.init then
            pl.init(plugins)
        end
    end)
    if not status then
        print('error loading plugin ', name, err)
    end
end

return plugins

