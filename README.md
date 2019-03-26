
Add to your `~/.vpvrc`:

```lua
local path = os.getenv('HOME') .. '/.vpv'
local plugins = assert(loadfile(path .. '/plugins.lua'))(path)
plugins.load('log', 'core/log')
plugins.load('shortkey', 'core/shortkey')

plugins.shortkey.register('f1', load_user_config, 'reload user config')

function gui()
    text(plugins.log 'get')
    plugins.shortkey.gui()
end

function on_tick()
    plugins.manager.on_tick()
end

function on_window_tick(w, focused)
    plugins.manager.on_window_tick(w, focused)
end
```

