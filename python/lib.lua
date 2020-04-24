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
   local func = msg.method
   local chunk = assert(load('return ' .. func))
   local res = chunk()(table.unpack(msg.params))
   return res
end

local function call(func, ...)
   lastid = lastid - 1
   local id = lastid
   local msg = json.encode {id=id, method=func, params={...}}
   fin:write(msg .. '\n')
   fin:flush()

   local line = json.decode(assert(fout:read('*l')))

   while line.id ~= id do
      local msg = json.encode {id=line.id, result=evaluate(line)}
      fin:write(msg .. '\n')
      fin:flush()

      line = json.decode(assert(fout:read('*l')))
   end

   lastid = lastid + 1
   return line.result
end

return {
   launch=launch,
   call=call,
}

