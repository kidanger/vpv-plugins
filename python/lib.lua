local json = require 'json'

local fout
local fin
local api
local function launch(fin_, fout_, cmd, api_)
   os.execute(cmd)
   fout = io.open(fout_, 'r')
   fin = io.open(fin_, 'w')
   api = api_
end

local function evaluate(msg)
   if not api[msg.method] then
      print('API error:', msg.method)
   end
   return api[msg.method](table.unpack(msg.params))
end

local lastid = 0
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

