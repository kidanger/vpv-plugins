
local logs = {}
local dirty = false
local str = ''

return function (text)
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

