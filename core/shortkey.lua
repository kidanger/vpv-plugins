local log
local registered = {}

local function check(key)
    if type(key) == 'table' then
        local modifiers = {control=false, alt=false, shift=false}
        for _, k in ipairs(key) do
            if modifiers[k] ~= nil then
                modifiers[k] = true
            end
            if not check(k) then
                return false
            end
        end
        for k, v in pairs(modifiers) do
            if not v and check(k) then
                return false
            end
        end
        return true
    end
    if key == 'control' or key == 'shift' or key == 'alt' then
        return iskeydown(key)
    end
    return iskeypressed(key)
end

local function on_tick()
    for _, r in ipairs(registered) do
        if check(r.keys) then
            log('[shortkey] "' .. r.name .. '" triggered')
            r.fn()
        end
    end
end

local function register(keys, fn, name)
    name = name or ''
    table.insert(registered, {keys=keys, fn=fn, name=name})
end

local function gui()
    for _, r in ipairs(registered) do
        local keys = r.keys
        if type(keys) == 'table' then
            keys = table.concat(r.keys, '+')
        end
        if r.name and button(keys .. ': ' .. r.name) then
            r.fn()
        end
    end
end

return {
    init=function(plugins)
        plugins.manager.add_hook_tick(on_tick)
        log = plugins.log
    end,
    register=register,
    check=check,
    gui=gui,
}

