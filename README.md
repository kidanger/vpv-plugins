1. clone this repository to `~/.vpv`
2. add to your `~/.vpvrc`:

```lua
local path = os.getenv('HOME') .. '/.vpv'
local plugins = assert(loadfile(path .. '/plugins.lua'))(path)
plugins.load('log', 'core/log')
plugins.load('shortkey', 'core/shortkey')

plugins.shortkey.register('f1', load_user_config, 'reload user config')

gui = plugins.manager.gui
on_tick = plugins.manager.on_tick
on_window_tick = plugins.manager.on_window_tick
```

