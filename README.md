1. clone this repository to `~/.vpv`
2. add to your `~/.vpvrc`:

```lua
local path = os.getenv('HOME') .. '/.vpv'
local plugins = assert(loadfile(path .. '/plugins.lua'))(path)
plugins.load('log', 'core/log')
plugins.load('shortkey', 'core/shortkey')

plugins.load('python', 'python/python')
plugins.python.load 'show-date'
plugins.python.load 'selection-to-temporal-profile'

plugins.shortkey.register('f1', load_user_config, 'reload user config')

gui = plugins.manager.gui
on_tick = plugins.manager.on_tick
on_window_tick = plugins.manager.on_window_tick
```

## Selection-to-temporal-profile

This plug-in is meant for time series analysis. It allows you to compute the average pixel value inside the selection for all the images and display the time series. 

Different processing modes are available for analyzing the time series : 
 - RAW : no processing of the data
 - CLOUD-F : outliers (cloudly image) detected from the derivative are removed. 
 - RM30 : It adds a rolling mean of 30 days for displaying the time series. 
 - BEAST :  Bayesian Ensemble Algorithm for Change-Point Detection and Time Series Decomposition is integrated. More info here: https://github.com/zhaokg/Rbeast
 
Different vision modes are available for analyzing the time series : 
- FOCUS : if you have several opened sequences, it pops up the time series from the active one. 
- ALL : if you have several opened sequences, it pops up the time series from all sequences.

Click on `'m'` to pop up the time series and select the vision mode and on `'y'` to change the processing mode iteratively. 

Example : 
![ts](/images/ex-s2-timeseries.png)

In this example, the BEAST model from the RGB channels are displayed as well as the detected season (scp) and trend (tcp) change points. 
