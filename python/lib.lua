local json = require 'json'

local function trim(s)
   return s:match'^%s*(.*%S)' or ''
end

local fout
local fin
local function launch(fin_, fout_, cmd)
   os.execute(cmd)
   fout = io.open(fout_, 'r')
   fin = io.open(fin_, 'w')
end

local lastid = 0

local function evaluate(msg)
   local func = msg.func
   local chunk = assert(load('return ' .. func))
   local res = chunk()(table.unpack(msg.args))
   return res
end

local function call(func, ...)
   lastid = lastid - 1
   local id = lastid
   local msg = json.encode {type='request', func=func, args={...}}
   fin:write(tostring(id) .. ' ' .. msg .. '\n')
   fin:flush()

   local nn = assert(fout:read('*number'))
   local line = json.decode(assert(fout:read('*l')))

   while nn ~= id do
      local msg = json.encode {type='reply', response=evaluate(line)}
      fin:write(tostring(nn) .. ' ' .. msg .. '\n')
      fin:flush()

      nn = assert(fout:read('*number'))
      line = json.decode(assert(fout:read('*l')))
   end

   lastid = lastid + 1
   return line.response
end

return {
   launch=launch,
   call=call,
}

