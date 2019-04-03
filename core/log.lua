
local logs = {}
local dirty = false
local str = ''

local logmt = {}
local log = setmetatable({}, logmt)

function logmt:__call(text)
    if text == 'get' then
        if dirty then
            str = table.concat(logs, '\n')
            dirty = false
        end
        return str
    end
    table.insert(logs, text)
    dirty = true
end

function log.gui()
    text('logs:\n' .. (log 'get') .. '\n---')
    if button 'clear logs' then
        logs = {}
        dirty = true
    end
end

return log

