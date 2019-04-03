
local path = ...

package.path = package.path ..  ";" .. path .. "/?/init.lua;" .. path .. "/?.lua"

local plugins = {}
plugins.manager = {}

local function is_valid_plugin(p)
    return type(p) == 'table' and p._is_plugin and p.on_tick and not p._masked
end

plugins.manager.on_tick = function()
    for _, p in pairs(plugins) do
        if is_valid_plugin(p) and p.on_tick then
            p.on_tick()
        end
    end
end

plugins.manager.on_window_tick = function(...)
    for _, p in pairs(plugins) do
        if is_valid_plugin(p) and p.on_window_tick then
            p.on_window_tick(...)
        end
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
        pl._is_plugin = true
        print(('✔ plugin \'%s\' loaded'):format(pkg))
    end)
    if not status then
        print(('✗ plugin \'%s\' %s'):format(pkg, err))
    end
end

plugins.manager.gui = function()
    text 'List of plugins (click to expand)'
    for n, p in pairs(plugins) do
        if type(p) ~= 'table' or p == plugins.manager or not p._is_plugin then
            goto continue
        end
        local nstr = '- ' .. n
        if p._opened then
            nstr = nstr .. ' (opened)'
        end
        if button(nstr) then
            p._opened = not p._opened
        end
        sameline()
        if not p._masked then
            if button('disable##'..n) then
                p._masked = true
            end
        else
            if button('re-enable##'..n) then
                p._masked = false
            end
        end
        if p._opened and p.gui then
            p.gui()
        end
        ::continue::
    end
    text '---'
end

return plugins

