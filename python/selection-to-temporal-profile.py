

import matplotlib as mpl
import matplotlib.colors as colors
from matplotlib.offsetbox import AnchoredText
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.signal import lombscargle
import matplotlib.dates as mdates
mpl.use("Qt5Agg")
import matplotlib.pyplot as plt
import rasterio
from rasterio import windows
import os
import re
import time 
import numpy as np
import pandas as pd
from dateutil.parser import parse
import api
from datetime import timedelta
from ThymeBoost import ThymeBoost as tb

dmap = {
    'gray':'Greys',
    'jet':'jet',
    'opticalFlow':'copper',
    'default':'Reds',
    'turbo':'turbo'
}

seq_cmap_name = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', \
                      'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', \
                      'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']

#harmonic reg
from scipy.optimize import curve_fit


def func1(t, a, b, p, c):
    return a * np.sin(2 * np.pi * (1/365.25) *t + p) + b * t + c

def func2(t, a1, a2, b, p1, p2, c):
    return a1 * np.sin(2 * np.pi * (1/365.25)*t + p1) + a2 * np.sin(2 * np.pi * (2/365.25)*t + p2) + b * t + c

list_func = [func1, func2]

def harmonic_reg(df):

    index = (df.index - df.index[0]).to_series().dt.total_seconds().div(60*60*24, fill_value=0).astype(int)
    df = df.reset_index().dropna()

    if df.shape[0] > 30 : 
        mod = 1
    else :
        mod = 0

    func = list_func[mod]

    guess_c = df[0].values.mean()
    guess_a = [1.] * (mod+1)
    guess = guess_a  + [0.] + [0.] * (mod+1) + [guess_c]
   
    #fit
    return (index, *curve_fit(func, index.values[df.index], df[0].fillna(df[0].mean()).replace([np.inf, -np.inf], df[0].mean()).values, p0=guess), func)

def thymeboost_fitter(mean, re_period, std_re_period):

    mean = mean.fillna(mean.mean()).replace([np.inf, -np.inf], mean.mean())

    if std_re_period < 1:
        y = mean 
    else :
        y = mean.resample('1D').interpolate('linear').resample(f'{re_period}D').mean()

    boosted_model = tb.ThymeBoost(approximate_splits=True,
                                verbose=0,
                                cost_penalty=.01,
                                regularization=1.25)

    output = boosted_model.fit(y,
                            trend_estimator='linear',
                            seasonal_estimator='fourier',
                            fourier_order = 2,
                            seasonal_period=365//re_period,
                            split_cost='mae',
                            global_cost='maicc',
                            fit_type='local')
    
    return output

#vpv 
def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap

def color(list_df, date, lims):
    if len(list_df) == 3:
        return (np.array([df[0].loc[date] for df in list_df])/lims[1] + 0.2).clip(0,1)
    else:
        return 'lime'

def diff(l):
    return l[1] - l[0]

def date_parser(sdate):
    date6 = re.findall('.*(\d{4}-?\d{2}-?\d{2}([tT]\d{6})?).*', sdate)
    date8 = re.findall('((19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))', sdate)
    date = []
    for l in [date6, date8]:
        if len(l)>0:
            date.extend(l[0])
    for d in sorted(date, key=len):
        try :
            fdate = parse(d)
        except:
            pass
    return fdate 

def preprocessing(df, mod):

    mean  = df[0].copy()
    std = df[1].copy()
    mean_raw = df[0].copy()
    std_raw = df[1].copy()
    label = None
    
    
    if 'PERC' in mod:
        q = int(mod.split('PERC')[1].split('-')[0]) / 100

        mean_raw[mean_raw > mean_raw.quantile(q)] = np.nan
        std_raw[std_raw > std_raw.quantile(q)] = np.nan

        mean = mean_raw.interpolate('linear')
        std = std_raw.interpolate('linear')

    if 'RM' in mod:
        days = int(mod.split('RM')[1].split('-')[0])

        mean = mean_raw.interpolate('linear').rolling(f'{days}D').mean()
        std = std_raw.interpolate('linear').rolling(f'{days}D').mean()

    if 'BFAST' in mod: 
        mean_index, mean_popt, mean_pcov, mean_func = harmonic_reg(mean_raw)
        perr = np.sqrt(np.diag(mean_pcov)).mean()
        label = f'p-err : {perr :.2f}'
        mean = pd.DataFrame(data = np.array([mean_func(t, *mean_popt) for t in mean_index]), index=mean_raw.index) 

    if 'ThymeBoost' in mod:
        index = (mean.index - mean.index[0]).to_series().dt.days
        re_period = int((index - index.shift()).mean())
        std_re_period = (index - index.shift()).std()
        output = thymeboost_fitter(mean.copy(), re_period, std_re_period)
        mean = output['yhat']
        std = output['trend']
        std_raw = output['yhat'] - output['yhat_lower']

    return mean_raw, std_raw, mean, std, label 

def plotting(ax, df, lims=None, cmap=None, norm=lambda x:x, label=None, mod=None, grid=True):

    if mod is None:
        mod = 'RAW'

    mean_raw, std_raw, mean, std, label_  = preprocessing(df, mod)

    if label is None:
        label = label_
    else :
        label = ' '.join([label,label_]) 

    if mod == 'RAW' or 'RM' in mod:
        lw = 0.75
    else :
        lw = 1.
    #plot 
    lines = ax.plot(mean.index, mean.values, lw=lw, color=cmap(0.5), label=label, zorder=3)
    if 'BFAST' in mod:
        scatter = ax.scatter(mean_raw.index, mean_raw.values, marker='+', s=8, \
            color=cmap(0.5), linewidths=0.75, zorder=4, alpha=0.5)
        fill = ax.fill_between(mean.index, mean_raw.values, mean[0].values, alpha=0.25, color=cmap(0.25), lw=0, zorder=1)
    elif 'ThymeBoost' in mod:
        scatter = ax.scatter(mean_raw.index, mean_raw.values, marker='+', s=8, \
            color=cmap(0.5), linewidths=0.75, zorder=4, alpha=0.5)
        lines += ax.plot(std.index, std.values, lw=0.75, color=cmap(0.4), label=label, zorder=2, linestyle=(5,(10,3)))
        fill = ax.fill_between(mean.index, mean.values + std_raw.values, mean.values - std_raw.values , alpha=0.25, color=cmap(0.25), lw=0, zorder=1)
    else :
        scatter = ax.scatter(mean.index, mean.values, marker='+', s=10, \
            color=cmap(0.5), linewidths=0.75, zorder=4)
        fill = ax.fill_between(mean.index, mean-std, mean+std, alpha=0.25, color=cmap(0.25), lw=0, zorder=1)


    ylim = list(ax.get_ylim())
    if lims is not None and diff(lims) < diff(ylim):
        ax.set_ylim(lims)

    if grid:
        ax.grid(True, alpha=0.5, linestyle='--', lw=0.5)

    if label is not None:
        ax.legend(prop={'size': 8})
    else:
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()

    locator = mdates.AutoDateLocator(minticks=1, maxticks=20)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    return lines + [scatter, fill]


class Figure:

    def __init__(self, seqs, selection=None, sharex=True, sharey=False):
        
        self.formats = ['png', 'jpeg', 'tif', 'tiff']
        
        #sequences
        self.seqs = {i: seq for i,seq in enumerate(seqs)}
        self.complex = [False for key in self.seqs.keys()] 
        self.selection = selection

        #shared by seq
        self.old_selection = None

        #unique by seq
        self.old_frame = [1 for seq in self.seqs.values()]
        self.colormap = [seq.colormap for seq in self.seqs.values()] 
        self.files_path = [[seq.collection.get_filename(i) for i in range(seq.collection.length) \
            if seq.collection.get_filename(i).split('.')[-1].lower() in self.formats] for seq in self.seqs.values()]

        self.lim_frame = [len(self.files_path[key]) for key in self.seqs.keys()]
        self.data = [self.get_data(self.selection, key) for key in self.seqs.keys()]

        self.cmap = [lambda x:None for key in self.seqs.keys()] 
        self.old_shader = ['Gray' for key in self.seqs.keys()] 
        
        self.lims = [None for key in self.seqs.keys()]  
        self.line = [None for key in self.seqs.keys()]  
        self.texts = [[] for key in self.seqs.keys()]  
        self.plots = [[] for key in self.seqs.keys()] 
        self.norm = [None for key in self.seqs.keys()] 
        self.cax = [None for key in self.seqs.keys()] 
        self.mod = [None for key in self.seqs.keys()]

        #check if the len of the seq > 2 
        index_len = np.where(np.array([len(seq) for seq in self.files_path]) < 2)[0]
        for i in index_len:
            del self.seqs[i]

        assert len(self.seqs) >= 1, 'The sequence is not a time series'

        #figure 
        self.sharex = sharex
        self.sharey = sharey
        self.nrows = len(self.seqs)
        self.ncols = 1
        self.figsize = (self.ncols * 8, self.nrows * 2.5)
        self.fig, self.ax = self.figure(self.nrows, self.ncols, self.figsize)
        

    def safe_frame(self, frame, key):
        return min(frame-1, self.lim_frame[key]-1)

    def figure(self, nrows, ncols, figsize):
        fig, ax = plt.subplots(nrows, ncols, figsize=figsize, sharex=self.sharex, sharey=self.sharey)
        if ncols == 1 and nrows == 1:
            return fig, [ax]
        else:
            return fig, ax


    def get_data(self, selection, key): 
        self.old_selection = selection
        tpc, blc = selection 
        a,b,c,d = min(tpc[1], blc[1]), max(tpc[1], blc[1]), min(blc[0],tpc[0]), max(blc[0],tpc[0])
        window = windows.Window.from_slices(rows=(a,b), cols=(c,d))
        print('window: ',window)
        shape = rasterio.open(os.path.abspath(self.files_path[key][0])).read(window=window).shape[0]
        list_bands = self.colormap[key].bands if len(self.colormap[key].bands) == shape else range(shape)
        return self.get_dataframe(self.files_path[key], window, list_bands, key)

    def get_dataframe(self, files_path, window, list_bands, key):
        list_bands = list(np.array(list_bands) + 1)
        rasters = np.array([rasterio.open(os.path.abspath(file)).read(list_bands, window=window) for file in files_path])
        n = rasters.shape[0]
        try :
            date = pd.to_datetime([date_parser(os.path.basename(file)) for file in files_path])
        except :
            date = range(len(files_path))

        if np.iscomplexobj(rasters):
            self.complex[key] = True
            r_rasters = rasters.real
            i_rasters = rasters.imag
            r_dfs = [pd.DataFrame(r_rasters[:,i].reshape(n, -1), index=date).sort_index() for i in range(r_rasters.shape[1])]
            i_dfs = [pd.DataFrame(i_rasters[:,i].reshape(n, -1), index=date).sort_index() for i in range(i_rasters.shape[1])]
            dfs = r_dfs + i_dfs
        else : 
            dfs = [pd.DataFrame(rasters[:,i].reshape(n, -1), index=date).sort_index() for i in range(rasters.shape[1])]

        return [(df.mean(axis=1), df.std(axis=1)) for df in dfs]

    def get_date(self, key, frame): 
        try :
            date = date_parser(os.path.basename(self.files_path[key][self.safe_frame(frame, key)]))
            sdate = date.strftime('%Y/%m/%d')
        except :
            print('no date -> one unit between two frames')
            date = self.files_path[key].index(os.path.basename(self.files_path[key][self.safe_frame(frame, key)]))
            sdate = date

        return date, sdate

    def get_cmap(self, key, colormap): 

        #match colormap 
        self.old_shader[key] = colormap.shader

        if len(self.data[key]) == 3:
            self.cmap[key] = [
                mpl.colormaps['Reds'],
                mpl.colormaps['Greens'],
                mpl.colormaps['Blues']
            ]

        elif len(self.data[key]) == 2:
            self.cmap[key] = [
                mpl.colormaps['Blues'],
                mpl.colormaps['YlOrBr']
            ]

        elif len(self.data[key]) == 4:
            self.cmap[key] = [
                mpl.colormaps['Reds'],
                mpl.colormaps['Greens'],
                mpl.colormaps['Blues'],
                mpl.colormaps['Greys']
            ]

        elif self.old_shader[key] in dmap:
            ckey = dmap[self.old_shader[key]]
            self.cmap[key] = [mpl.colormaps[ckey]]

        else :
            self.cmap[key] = [mpl.colormaps[name] for name in seq_cmap_name]
        
        #colormap scale
        lims = list()
        for i in range(len(self.data[key])):
            lims.append(colormap.get_range(i+1))
        diffs = [diff(l) for l in lims]
        self.lims[key] = lims[diffs.index(max(diffs))]
        
        self.norm[key] = mpl.colors.Normalize(vmin=self.lims[key][0], vmax=self.lims[key][1])

    def open(self, key, update=False): 
        if update:
            self.ax[key].cla()
            cmap = self.colormap[key]

        else:
            cmap = api.get_sequences()[key].colormap

        #cmap
        self.get_cmap(key, colormap=cmap)

        #Plot 
        self.update_plot(key)

        #Cursor
        self.update_cursor(self.seqs[key].player.frame, key)

        #Ax Title
        divider = make_axes_locatable(self.ax[key])
        self.cax[key] = divider.append_axes("top", size="12%", pad=0)
        self.cax[key].get_xaxis().set_visible(False)
        self.cax[key].get_yaxis().set_visible(False)
        self.cax[key].set_facecolor('black')

        at = AnchoredText(self.seqs[key].id, loc='center left',
                        prop=dict(backgroundcolor='black',
                                    size=7, color='white'))
        self.cax[key].add_artist(at)
        
        if update:
            plt.draw()
        else:
            plt.show(block=False) #silent 

        return self.ax[key] 

    def open_all(self):
        for key in self.seqs.keys():
            self.open(key)

        return self.fig

    def close(self):
        plt.close(self.fig)
        return None 

    def update_plot_all(self):
        for key in self.seqs.keys():
            self.data[key] = self.get_data(api.get_selection(), key)
            self.update_plot(key)

        plt.draw()

    def update_plot(self, key, draw=False): 
        
        mod = self.mod[key] 

        if len(self.plots[key])>0:
            for plot in self.plots[key]:
                plot.remove()

        plots = []
        if len(self.data[key]) == 1:
            #1-variable
            plot = plotting(self.ax[key], self.data[key][0], cmap=self.cmap[key][0], lims=self.lims[key], norm=self.norm[key], mod=mod)
            plots.extend(plot)

        elif len(self.data[key]) <= 3:
            #rgb or complex 
            if self.complex[key]:
                labels = ['r-comp', 'i-comp']
            else :
                labels = [None]*3

            for i in range(len(self.data[key])):
                plot = plotting(self.ax[key], self.data[key][i], lims=self.lims[key], \
                    cmap=self.cmap[key][i], norm=self.norm[key], label=labels[i], mod=mod)
                plots.extend(plot)

        elif len(self.data[key]) == 4:
            #rgbi
            for i in range(len(self.data[key])):
                plot = plotting(self.ax[key], self.data[key][i], lims=self.lims[key], \
                                cmap=self.cmap[key][i], norm=self.norm[key], mod=mod)
                plots.extend(plot)
        else :
            print('WIP')
            for i in range(len(self.data[key])):
                plot = plotting(self.ax[key], self.data[key][i], lims=self.lims[key], \
                                cmap=self.cmap[key][i], norm=self.norm[key], mod=mod)
                plots.extend(plot)

        if draw:
            plt.draw()

        self.plots[key] = plots 

        return plots

    def update_cursor_all(self, frame):
        for key in self.seqs.keys():
            self.update_cursor(frame, key)

        plt.draw()

    def update_cursor(self, frame, key, draw=False): 
        
        self.old_frame[key] = frame
        date, sdate = self.get_date(key, frame)
        if self.line[key] is not None : 
            self.line[key].remove()

        if self.texts[key] is not None:
            for t in self.texts[key]:
                t.remove()

        self.line[key] = self.ax[key].axvline(date, color='lime', alpha=0.45, lw=4, zorder=2)
        lim = self.ax[key].get_ylim()[1]
        if isinstance(date, int):
            delta = 0
        else : 
            delta = timedelta(days=3)
        
        texts = [self.ax[key].text(date + delta, lim*0.85, sdate, color = 'k', fontsize=7,\
             bbox=dict(facecolor='lime', edgecolor='lime', boxstyle='round', alpha=0.45), zorder=2)]

        for i in range(len(self.data[key])):
            try :
                texts.append(self.ax[key].text(date, lim*(0.75 - 0.08 * i), f'{self.data[key][i][0][date] : .2f}',\
                     color = self.cmap[key][i](0.5), fontsize=7, zorder=2))
            except:
                texts.append(self.ax[key].text(date, lim*(0.75 - 0.05 * i), ' error', color = 'k', fontsize=7, zorder=2))
        self.texts[key] = texts 

        if draw:
            plt.draw()

    def update_rolling_mean(self, key, mod='RAW'):
        self.mod[key] = mod
        self.update_plot(key)
        ####

        txt = " ".join([cfig.seqs[key].id,mod])
        at = AnchoredText(txt, loc='center left',
                prop=dict(backgroundcolor='black',
                            size=7, color='white'))
        self.cax[key].cla()
        self.cax[key].add_artist(at)

    
fig = None
cfig = None
start = None
N = 0
M = 1
MOD = ['RAW', 'PERC95', 'PERC95-RM30', 'PERC95-BFAST', 'PERC95-ThymeBoost', 'PERC90', 'PERC90-RM30', 'PERC90-BFAST', 'PERC90-ThymeBoost']
def on_tick():
    global fig, cfig, start, N, M

    window = api.get_focused_window()
    if not window or not window.current_sequence:
        return

    seq = window.current_sequence
    seqs = api.get_sequences()
    players = api.get_players()
    view = seq.view
    if not view:
        return
    
    if api.is_key_pressed('m', repeat=False) and api.get_selection() is not None:
        if fig is None : 
            old_selection = api.get_selection()
            cfig = Figure(seqs, selection=old_selection)
            fig = cfig.open_all()
            print('open', fig)
        else:
            print('closed', fig)
            fig = cfig.close()

    if cfig is not None:

        if len(players) == 1:
            
            if seqs[0].player.frame != cfig.old_frame[0]:
                cfig.update_cursor_all(seqs[0].player.frame)

            elif fig is not None and api.get_selection() is not None and api.get_selection() != cfig.old_selection:    
                cfig.update_plot_all()

        elif len(players) > 1:
            for key in cfig.seqs:
                if (seqs[key].player.frame != cfig.old_frame[key]):
                    cfig.update_cursor(seqs[key].player.frame,key, draw=True)

                elif fig is not None  \
                    and api.get_selection() is not None and api.get_selection() != cfig.old_selection:
                    cfig.data[key] = cfig.get_data(api.get_selection(), key)
                    cfig.update_plot(key, draw=True)

        for key in cfig.seqs:
            if seqs[key].colormap.shader != cfig.old_shader[key]:
                    cfig.open(key, update=True)

            if cfig.lims[key] != seqs[key].colormap.get_range(1):
                N+=1
                if N == 1:
                    start = time.time()
                elif N > 20 or time.time() - start > 0.5:
                    cfig.open(key, update=True)
                    N = 0

        if api.is_key_pressed('y', repeat=False) and api.get_selection() is not None:
            mod = MOD[M%len(MOD)]
            seq_id = api.get_focused_window().current_sequence.id
            key = int(seq_id.split(' ')[-1]) - 1
            cfig.update_rolling_mean(key, mod)
            M+=1

    if fig is not None:
        if fig.stale:
            fig.canvas.draw_idle()
        fig.canvas.flush_events()