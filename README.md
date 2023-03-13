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

## Selection-to-temporal-profile

This plug-in is meant for time series analysis. It allows you to compute the average pixel value inside the selection for all the images and display the time series. Different modes are available for analyzing the time series : 

 - RAW : no processing of the data
 - PERC95 : values of the time series above percentile 95 are removed. It allows, for instance, filtering clouds for regions with small cloud cover. 
 - PERC95-RM30 : It adds a rolling mean of 30 days for displaying the time series. 
 - PERC95-BFAST : It fits the time series with two sinus functions with periods of 365 and 180 days and a linear function. 
 - PERC95-ThymeBoost : It fits the time series with two sinus functions with periods of 365 and 180 days and a piecewise linear function. Practical for detecting breakpoint changes in the time series. 
 - PERC90-[...] : The same modes are available but with filtering above the percentile 90 for more cloudy regions. 

Click on `'m'` to pop up the time series and on `'y'` to change the mod iteratively. 

Example : 
![ts](/images/ex-s2-timeseries.png)
