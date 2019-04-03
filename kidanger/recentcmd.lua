
local path = os.getenv('HOME') .. '/.vpv'
local file = path .. '/cmds'

local p = {}
local list = {}
local has = {}
local currentcmd = ''

function p.init()
    local f = io.open(file, 'r')
    if not f then return end
    for l in f:lines() do
        table.insert(list, l)
        has[l] = true
    end
end

local function write()
    local f = assert(io.open(file, 'w'))
    f:write(table.concat(list, '\n'))
    f:close()
end

function p.gui()
    text 'List of commands'
    for i, c in ipairs(list) do
        if button(c) then
            set_terminal_command(c)
        end
        sameline()
        if button('remove##'..c) then
            table.remove(list, i)
            has[c] = false
            write()
        end
    end

    text('current commandline:')
    sameline()
    local c = get_terminal_command()
    text(c)
    if #c ~= 0 and not has[c] and (sameline() or button 'add') then
        table.insert(list, c)
        has[c] = true
        write()
    end
end

return p

