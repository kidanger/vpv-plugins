import datetime
import os
import re
import time

import api


mpl = api.LazyLoader("matplotlib")
plt = api.LazyLoader("matplotlib.pyplot")
pd = api.LazyLoader("pandas")
np = api.LazyLoader("numpy")
rasterio = api.LazyLoader("rasterio")

try:
    import Rbeast as rb
    from Rbeast.plotbeast import get_scp, get_tcp, getfield, isempty, isfield, np_sqrt

    def get_Yts(x, hasSeason, hasData):
        Yts = x.trend.Y
        SD2 = x.trend.SD**2 + x.sig2[0]
        if hasSeason:
            Yts, SD2 = (Yts + x.season.Y, SD2 + x.season.SD**2)
        SD = np_sqrt(SD2)
        YtsSD = np.stack([Yts - SD, Yts + SD])
        if hasData:
            Yerr = x.data - Yts
        else:
            Yerr = []
        return (Yts, YtsSD, Yerr)

    def beast(signal, time, deltat=48, season="harmonic", hasOutlier=True, ocp_max=10):
        # metadata
        metadata = lambda: None
        metadata.isRegular = False  # data is irregularly-spaced
        metadata.time = rb.args()
        metadata.time.datestr = [str(x) for x in signal.index.tolist()]
        metadata.time.strfmt = "YYYY-mm-dd HH:MM:SS"  # times of individulal images/data points: the unit here is fractional year (e.g., 2004.232)
        metadata.deltaTime = deltat  # regular interval used to aggregate the irregular time series (1/12 = 1/12 year = 1 month)
        metadata.period = 1.0  # the period is 1.0 year, so freq= 1.0 /(1/12) = 12 data points per period
        metadata.startime = 0.0  # the start time of the time series
        metadata.missingValue = float("nan")
        metadata.season = "harmonic"
        metadata.hasOutlierCmpnt = hasOutlier
        metadata.ocp_max = ocp_max

        # prior
        prior = lambda: None
        prior.outlierMaxKnotNum = ocp_max
        prior.precPriorType = "uniform"
        prior.seasonMaxOrder = 5

        # extra
        extra = lambda: None
        extra.printProgressBar = False
        extra.printOptions = True

        results = rb.beast123(
            np.expand_dims(signal.values, axis=[1, 2]),
            metadata=metadata,
            prior=prior,
            extra=extra,
        )
        indexes = (signal.index - datetime.datetime(1970, 1, 1)).total_seconds()
        a = (indexes[-1] - indexes[0]) / (results.time[-1] - results.time[0])
        b = indexes[0]
        time = [
            datetime.datetime.fromtimestamp(a * (x - results.time[0]) + b)
            for x in results.time
        ]
        return results, time, a, b

    def wrapper_beast(signal, re_period, hasOutlier=True, ocp_max=10):
        results, time, a, b = beast(
            signal,
            [x.to_pydatetime() for x in signal.index],
            deltat=re_period,
            season="harmonic",
            hasOutlier=hasOutlier,
            ocp_max=ocp_max,
        )
        hasSeason = isfield(results, "season") and not isempty(results.season)
        hasOutlier = isfield(results, "outlier") and not isempty(results.outlier)
        hasData = isfield(results, "data") and not isempty(getfield(results, "data"))

        Yts, YtsSD, _ = get_Yts(results, hasSeason, hasData)
        t_cp, _, t_ncp, _, t_cpPr, _, _, _ = get_tcp(results, "median")
        s_cp, _, s_ncp, _, s_cpPr, _, _, _ = get_scp(results, "median")

        return results, Yts, YtsSD, t_cp, t_ncp, t_cpPr, s_cp, s_ncp, s_cpPr, time, a, b

    MOD = ["RAW", "CLOUD-F", "RM30", "BEAST"]
except:
    MOD = ["RAW", "CLOUD-F", "RM30"]


dmap = {
    "gray": "Greys",
    "jet": "jet",
    "opticalFlow": "copper",
    "default": "Reds",
    "turbo": "turbo",
}

seq_cmap_name = [
    "Greys",
    "Purples",
    "Blues",
    "Greens",
    "Oranges",
    "Reds",
    "YlOrBr",
    "YlOrRd",
    "OrRd",
    "PuRd",
    "RdPu",
    "BuPu",
    "GnBu",
    "PuBu",
    "YlGnBu",
    "PuBuGn",
    "BuGn",
    "YlGn",
]


# vpv
def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "trunc({n},{a:.2f},{b:.2f})".format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)),
    )
    return new_cmap


def color(list_df, date, lims):
    if len(list_df) == 3:
        return (np.array([df[0].loc[date] for df in list_df]) / lims[1] + 0.2).clip(
            0, 1
        )
    else:
        return "lime"


def diff(l):
    return l[1] - l[0]


def date_parser(sdate):
    import dateutil.parser

    date6 = re.findall(r".*(\d{4}-?\d{2}-?\d{2}([tT]\d{6})?).*", sdate)
    date8 = re.findall(r"((19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01]))", sdate)
    date = []
    for l in [date6, date8]:
        if len(l) > 0:
            date.extend(l[0])
    for d in sorted(date, key=len):
        try:
            fdate = dateutil.parser.parse(d)
        except:
            pass
    return fdate


def cloud_filtering(signal: pd.Series, signal_std: pd.Series):
    # compute alpha for cleaning the slope without cutting too much signal
    prep1 = signal.mean() + 3 * signal.std()
    prep2 = signal_std.mean() + 3 * signal_std.std()
    alpha = ((signal > prep1) + (signal_std > prep2)).sum() / signal.shape[0]
    alpha_ = 1 - alpha

    slope = pd.Series(np.gradient(signal.values), signal.index, name="slope")
    slope_safe = slope.copy()
    slope_safe[slope > slope.quantile(alpha_)] = np.nan
    slope_safe[slope < slope.quantile(alpha)] = np.nan
    slope_p = slope > slope_safe.mean() + slope_safe.std()
    slope_m = slope < slope_safe.mean() - slope_safe.std()
    cond = slope_p.shift(1) + slope_m.shift(-1)
    signal_clean = signal.copy()
    ocp_max = signal_clean[cond == 2].count()
    signal_clean[cond == 2] = np.nan

    return signal_clean.interpolate("linear"), ocp_max


def wrapper_preprocessing(dfs, mod=""):
    datap = []
    for df in dfs:
        datap.append(preprocessing(df, mod))
    return datap


def is_empty(self):
    """Return True if there is no visible artist in the figure"""

    children = self.get_children()
    if len(children) < 1:
        return True

    for child in self.get_children():
        if child.get_visible():
            return False

    return True


def preprocessing(df, mod):
    mean = df[0].copy()
    std = df[1].copy()
    label = None
    args = None

    if "CLOUD-F" in mod:
        mean, _ = cloud_filtering(mean, std)
        std, _ = cloud_filtering(std, std)

    if "RM" in mod:
        mean_raw, _ = cloud_filtering(mean, std)
        std_raw, _ = cloud_filtering(std, std)
        days = int(mod.split("RM")[1].split("-")[0])
        mean = mean_raw.interpolate("linear").rolling(f"{days}D").mean()
        std = std_raw.interpolate("linear").rolling(f"{days}D").mean()

    if "BEAST" in mod:
        _, ocp_max = cloud_filtering(mean, std)
        print("ocp_max = ", ocp_max)
        index = (mean.index - mean.index[0]).to_series().dt.days
        re_period = int((index - index.shift()).mean()) / 365.25
        results, mean, std, t_cp, t_ncp, t_cpPr, s_cp, s_ncp, s_cpPr, time, a, b = (
            wrapper_beast(mean, re_period, ocp_max=1.25 * int(ocp_max))
        )
        args = results, t_cp, t_ncp, t_cpPr, s_cp, s_ncp, s_cpPr, time, a, b

    return {"mean": mean, "std": std, "label": label, "args": args}


def plotting(
    ax,
    datap,
    lims=None,
    cmap=None,
    norm=lambda x: x,
    label=None,
    mod=None,
    grid=True,
    key=0,
    format_is_date=True,
):
    if mod is None:
        mod = "RAW"

    mean = datap["mean"]
    std = datap["std"]
    label_ = datap["label"]
    args = datap["args"]

    if label is None:
        label = label_
    else:
        label = " ".join([label, label_])

    if mod == "RAW" or "RM" in mod:
        lw = 0.75
    else:
        lw = 1.0

    # plot
    text = []
    alines = []
    legend = []
    if "BEAST" in mod:
        results, t_cp, t_ncp, t_cpPr, s_cp, s_ncp, s_cpPr, time, a, b = args
        scatter = []

        # lines
        lines = ax.plot(time, mean, lw=lw, color=cmap(0.5), label=label, zorder=3)
        lines += ax.plot(
            time,
            results.trend.Y,
            color=cmap(0.25),
            label="trend",
            zorder=2,
            lw=2,
            linestyle="dashed",
        )
        # lines += ax.plot(time, results.season.Y + results.trend.Y.mean(), color=cmap(0.65), label='season', zorder=0, lw=0.75)
        fill = ax.fill_between(
            time, std[0, :], std[1, :], alpha=0.25, color=cmap(0.25), lw=0, zorder=1
        )

        ylim = list(ax.get_ylim())
        if lims is not None and diff(lims) < diff(ylim):
            ax.set_ylim(lims)

        # lines
        for i in range(t_ncp):
            alines.append(
                ax.axvline(
                    datetime.datetime.fromtimestamp(
                        (t_cp[i] - results.time[0]) * a + b
                    ),
                    lw=1,
                    color=cmap(0.5),
                    linestyle="dashdot",
                )
            )
            text.append(
                ax.text(
                    datetime.datetime.fromtimestamp(
                        (t_cp[i] - results.time[0]) * a + b
                    ),
                    min(ylim[1] * (0.1 + 0.05 * (i + key)), ylim[1] * 0.9),
                    f" p:{t_cpPr[i]:.1f}",
                    color=cmap(0.5),
                    fontsize=6,
                )
            )

        for i in range(s_ncp):
            alines.append(
                ax.axvline(
                    datetime.datetime.fromtimestamp(
                        (s_cp[i] - results.time[0]) * a + b
                    ),
                    lw=1,
                    color=cmap(0.5),
                    linestyle="--",
                )
            )
            text.append(
                ax.text(
                    datetime.datetime.fromtimestamp(
                        (s_cp[i] - results.time[0]) * a + b
                    ),
                    max(ylim[1] * (0.9 - 0.05 * (i + key)), ylim[1] * 0.1),
                    f" p:{s_cpPr[i]:.1f}",
                    color=cmap(0.5),
                    fontsize=6,
                )
            )

        custom_lines = [
            mpl.lines.Line2D([0], [0], color=cmap(0.5), lw=1, linestyle="dashdot"),
            mpl.lines.Line2D([0], [0], color=cmap(0.5), lw=1, linestyle="--"),
        ]

        legend = [ax.legend(custom_lines, ["tcp", "scp"])]

    else:
        lines = ax.plot(
            mean.index, mean.values, lw=lw, color=cmap(0.5), label=label, zorder=3
        )
        scatter = ax.scatter(
            mean.index,
            mean.values,
            marker="+",
            s=10,
            color=cmap(0.5),
            linewidths=0.75,
            zorder=4,
        )
        fill = ax.fill_between(
            mean.index,
            mean - std,
            mean + std,
            alpha=0.25,
            color=cmap(0.25),
            lw=0,
            zorder=1,
        )

        ylim = list(ax.get_ylim())
        if lims is not None and diff(lims) < diff(ylim):
            ax.set_ylim(lims)

    if grid:
        ax.grid(True, alpha=0.5, linestyle="--", lw=0.5)

    if label is not None:
        ax.legend(prop={"size": 8})
    elif len(legend) > 0:
        pass
    else:
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
        legend = []

    if format_is_date:
        locator = mpl.dates.AutoDateLocator(minticks=1, maxticks=20)
        formatter = mpl.dates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

    return lines + [scatter, fill] + text + alines + legend


class Figure:
    def __init__(
        self, seqs, mode_vision="FOCUS", selection=None, sharex=True, sharey=False
    ):
        self.formats = ["png", "jpeg", "tif", "tiff"]

        # sequences
        self.seqs = {i: seq for i, seq in enumerate(seqs)}
        self.complex = {key: False for key in self.seqs.keys()}
        self.selection = selection

        # vision
        self.mode_vision = mode_vision
        if self.mode_vision == "FOCUS":
            seq_id = api.get_focused_window().current_sequence.id
            self.old_key = int(seq_id.split(" ")[-1]) - 1
            self.seqs = {self.old_key: self.seqs[self.old_key]}
        elif self.mode_vision == "ALL":
            pass

        # shared by seq
        self.old_selection = None

        # unique by seq
        self.old_frame = {key: 1 for key, seq in self.seqs.items()}
        self.format_is_date = {key: True for key, seq in self.seqs.items()}
        self.colormap = {key: seq.colormap for key, seq in self.seqs.items()}
        self.files_path = {
            key: [
                seq.collection.get_filename(i)
                for i in range(seq.collection.length)
                if seq.collection.get_filename(i).split(".")[-1].lower() in self.formats
            ]
            for key, seq in self.seqs.items()
        }

        self.lim_frame = {key: len(self.files_path[key]) for key in self.seqs.keys()}

        self.data = {
            key: self.get_data(self.selection, key) for key in self.seqs.keys()
        }
        self.datap = {
            key: wrapper_preprocessing(self.data[key]) for key in self.seqs.keys()
        }

        self.cmap = {key: lambda x: None for key in self.seqs.keys()}
        self.old_shader = {key: "Gray" for key in self.seqs.keys()}

        self.lims = {key: None for key in self.seqs.keys()}
        self.line = {key: None for key in self.seqs.keys()}
        self.texts = {key: [] for key in self.seqs.keys()}
        self.plots = {key: [] for key in self.seqs.keys()}
        self.norm = {key: None for key in self.seqs.keys()}
        self.cax = {key: None for key in self.seqs.keys()}
        self.mod = {key: "" for key in self.seqs.keys()}

        # check if the len of the seq > 2
        index_len = np.where(
            np.array([len(seq) for seq in self.files_path.values()]) < 2
        )[0]
        for i in index_len:
            del self.seqs[i]

        assert len(self.seqs) >= 1, "The sequence is not a time series"

        # figure
        self.sharex = sharex
        self.sharey = sharey
        self.nrows = len(self.seqs)
        self.ncols = 1
        self.figsize = (self.ncols * 8, self.nrows * 2.5)
        self.fig, self.ax = self.figure(self.nrows, self.ncols, self.figsize)
        self.ax = {list(self.mod.keys())[i]: self.ax[i] for i in range(len(self.ax))}

    def safe_frame(self, frame, key):
        return min(frame - 1, self.lim_frame[key] - 1)

    def figure(self, nrows, ncols, figsize):
        fig, ax = plt.subplots(
            nrows, ncols, figsize=figsize, sharex=self.sharex, sharey=self.sharey
        )
        if ncols == 1 and nrows == 1:
            return fig, [ax]
        else:
            return fig, ax

    def get_data(self, selection, key):
        self.old_selection = selection
        tpc, blc = selection
        a, b, c, d = (
            min(tpc[1], blc[1]),
            max(tpc[1], blc[1]),
            min(blc[0], tpc[0]),
            max(blc[0], tpc[0]),
        )
        print(a, b, c, d)
        window = rasterio.windows.Window.from_slices(rows=(a, b), cols=(c, d))
        print("window: ", window)
        shape = (
            rasterio.open(os.path.abspath(self.files_path[key][0]))
            .read(window=window)
            .shape[0]
        )
        list_bands = (
            self.colormap[key].bands
            if len(self.colormap[key].bands) == shape
            else range(shape)
        )
        return self.get_dataframe(self.files_path[key], window, list_bands, key)

    def get_dataframe(self, files_path, window, list_bands, key):
        list_bands = list(np.array(list_bands) + 1)
        rasters = np.array(
            [
                rasterio.open(os.path.abspath(file)).read(list_bands, window=window)
                for file in files_path
            ]
        )
        n = rasters.shape[0]

        try:
            date = pd.to_datetime([date_parser(file) for file in files_path])
        except:
            date = range(len(files_path))
            self.format_is_date[key] = False

        if np.iscomplexobj(rasters):
            self.complex[key] = True
            r_rasters = rasters.real
            i_rasters = rasters.imag
            r_dfs = [
                pd.DataFrame(r_rasters[:, i].reshape(n, -1), index=date).sort_index()
                for i in range(r_rasters.shape[1])
            ]
            i_dfs = [
                pd.DataFrame(i_rasters[:, i].reshape(n, -1), index=date).sort_index()
                for i in range(i_rasters.shape[1])
            ]
            dfs = r_dfs + i_dfs
        else:
            dfs = [
                pd.DataFrame(rasters[:, i].reshape(n, -1), index=date).sort_index()
                for i in range(rasters.shape[1])
            ]

        return [(df.mean(axis=1), df.std(axis=1)) for df in dfs]

    def get_date(self, key, frame):
        try:
            date = date_parser(self.files_path[key][self.safe_frame(frame, key)])
            sdate = date.strftime("%Y/%m/%d")
        except:
            print("no date -> one unit between two frames")
            date = self.files_path[key].index(
                self.files_path[key][self.safe_frame(frame, key)]
            )
            sdate = date

        return date, sdate

    def get_cmap(self, key, colormap):
        # match colormap
        self.old_shader[key] = colormap.shader

        if len(self.data[key]) == 3:
            self.cmap[key] = [
                mpl.colormaps["Reds"],
                mpl.colormaps["Greens"],
                mpl.colormaps["Blues"],
            ]

        elif len(self.data[key]) == 2:
            self.cmap[key] = [mpl.colormaps["Blues"], mpl.colormaps["YlOrBr"]]

        elif len(self.data[key]) == 4:
            self.cmap[key] = [
                mpl.colormaps["Reds"],
                mpl.colormaps["Greens"],
                mpl.colormaps["Blues"],
                mpl.colormaps["Greys"],
            ]

        elif self.old_shader[key] in dmap:
            ckey = dmap[self.old_shader[key]]
            self.cmap[key] = [mpl.colormaps[ckey]]

        else:
            self.cmap[key] = [mpl.colormaps[name] for name in seq_cmap_name]

        # colormap scale
        lims = list()
        for i in range(len(self.data[key])):
            lims.append(colormap.get_range(i + 1))
        diffs = [diff(l) for l in lims]
        self.lims[key] = lims[diffs.index(max(diffs))]

        self.norm[key] = mpl.colors.Normalize(
            vmin=self.lims[key][0], vmax=self.lims[key][1]
        )

    def open(self, key, update=False):
        if update:
            self.ax[key].cla()
            cmap = self.colormap[key]

        else:
            cmap = api.get_sequences()[key].colormap

        # cmap
        self.get_cmap(key, colormap=cmap)

        # Plot
        self.update_plot(key)

        # Cursor
        self.update_cursor(self.seqs[key].player.frame, key)

        # Ax Title
        import mpl_toolkits.axes_grid1

        divider = mpl_toolkits.axes_grid1.make_axes_locatable(self.ax[key])
        self.cax[key] = divider.append_axes("top", size="12%", pad=0)
        self.cax[key].get_xaxis().set_visible(False)
        self.cax[key].get_yaxis().set_visible(False)
        self.cax[key].set_facecolor("black")

        folder = os.path.basename(os.path.dirname(self.files_path[key][0]))
        txt = " - ".join([cfig.seqs[key].id, folder])
        at = mpl.offsetbox.AnchoredText(
            txt,
            loc="center left",
            prop=dict(backgroundcolor="black", size=7, color="white"),
        )
        self.cax[key].add_artist(at)

        if update:
            plt.draw()
        else:
            plt.show(block=False)  # silent

        return self.ax[key]

    def open_all(self):
        for key in self.seqs.keys():
            self.open(key)

        return self.fig

    def close(self):
        plt.close(self.fig)
        return None

    def update_plot_all(self, selection, mod):
        self.update_data(selection, mod)
        for key in self.seqs.keys():
            self.update_plot(key)

        plt.draw()

    def update_data(self, selection, mod):
        self.data = {key: self.get_data(selection, key) for key in self.seqs.keys()}
        self.update_preprocessing(mod)

    def update_preprocessing(self, mod):
        self.datap = {
            key: wrapper_preprocessing(self.data[key], mod) for key in self.seqs.keys()
        }

    def update_plot(self, key, draw=False):
        mod = self.mod[key]

        if len(self.plots[key]) > 0:
            for plot in self.plots[key]:
                if isinstance(plot, list):
                    for p in plot:
                        p.remove()
                elif plot is not None:
                    plot.remove()

        plots = []
        if len(self.data[key]) == 1:
            # 1-variable
            plot = plotting(
                self.ax[key],
                self.datap[key][0],
                cmap=self.cmap[key][0],
                lims=self.lims[key],
                norm=self.norm[key],
                mod=mod,
                key=key,
                format_is_date=self.format_is_date[key],
            )
            plots.extend(plot)

        elif len(self.data[key]) <= 3:
            # rgb or complex
            if self.complex[key]:
                labels = ["r-comp", "i-comp"]
            else:
                labels = [None] * 3

            for i in range(len(self.data[key])):
                plot = plotting(
                    self.ax[key],
                    self.datap[key][i],
                    lims=self.lims[key],
                    cmap=self.cmap[key][i],
                    norm=self.norm[key],
                    label=labels[i],
                    mod=mod,
                    key=key,
                    format_is_date=self.format_is_date[key],
                )
                plots.extend(plot)

        elif len(self.data[key]) == 4:
            # rgbi
            for i in range(len(self.data[key])):
                plot = plotting(
                    self.ax[key],
                    self.datap[key][i],
                    lims=self.lims[key],
                    cmap=self.cmap[key][i],
                    norm=self.norm[key],
                    mod=mod,
                    key=key,
                    format_is_date=self.format_is_date[key],
                )
                plots.extend(plot)
        else:
            print("WIP")
            for i in range(len(self.data[key])):
                plot = plotting(
                    self.ax[key],
                    self.datap[key][i],
                    lims=self.lims[key],
                    cmap=self.cmap[key][i],
                    norm=self.norm[key],
                    mod=mod,
                    key=key,
                    format_is_date=self.format_is_date[key],
                )
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
        if self.line[key] is not None:
            self.line[key].remove()

        if self.texts[key] is not None:
            for t in self.texts[key]:
                t.remove()

        self.line[key] = self.ax[key].axvline(
            date, color="black", alpha=0.35, lw=4, zorder=2
        )
        lim = self.ax[key].get_ylim()[1]
        if isinstance(date, int):
            delta = 0
        else:
            delta = datetime.timedelta(days=3)

        texts = [
            self.ax[key].text(
                date + delta,
                lim * 0.85,
                sdate,
                color="white",
                fontsize=7,
                bbox=dict(facecolor="black", edgecolor=None, boxstyle="round", alpha=1),
                zorder=10,
            )
        ]

        for i in range(len(self.data[key])):
            try:
                texts.append(
                    self.ax[key].text(
                        date,
                        lim * (0.75 - 0.08 * i),
                        f"{self.data[key][i][0][date] : .2f}",
                        color=self.cmap[key][i](0.5),
                        fontsize=7,
                        zorder=2,
                    )
                )
            except:
                texts.append(
                    self.ax[key].text(
                        date,
                        lim * (0.75 - 0.05 * i),
                        " error",
                        color="k",
                        fontsize=7,
                        zorder=2,
                    )
                )
        self.texts[key] = texts

        if draw:
            plt.draw()

    def update_rolling_mean(self, key, mod="RAW"):
        self.mod[key] = mod
        self.update_plot(key)

        folder = os.path.basename(os.path.dirname(self.files_path[key][0]))
        txt = " - ".join([cfig.seqs[key].id, folder, mod])
        at = mpl.offsetbox.AnchoredText(
            txt,
            loc="center left",
            prop=dict(backgroundcolor="black", size=7, color="white"),
        )
        self.cax[key].cla()
        self.cax[key].add_artist(at)


fig = None
cfig = None
start = None
N = 0
M = 1
V = 0
mod = "RAW"

MOD_V = ["FOCUS", "ALL"]


def on_tick():
    global fig, cfig, start, N, M, V, mod

    window = api.get_focused_window()
    if not window or not window.current_sequence:
        return

    seq = window.current_sequence
    seqs = api.get_sequences()
    players = api.get_players()
    view = seq.view
    if not view:
        return

    # OPEN FIGURE and VISION MODE
    if (api.get_selection() is not None) and api.is_key_pressed("m", repeat=False):
        mpl.use("Qt5Agg")
        mod_v = MOD_V[V % len(MOD_V)]

        if fig is not None:
            cfig.close()
            seq.put_script_svg("mode")

        cfig = Figure(seqs, mode_vision=mod_v, selection=api.get_selection())
        fig = cfig.open_all()

        svg = f""" 
        <svg xmlns="http://www.w3.org/2000/svg">
        <g>
            <rect x="5" y="50"  width="{len(mod_v)*10}" height="15" fill="grey" fill-opacity='0.25' stroke="green" display="absolute"></rect>
            <text x="10" y="50"  font-family="Verdana" font-size="15" fill="green" display="absolute">{mod_v}</text>
        </g>
        </svg>"""
        seq.put_script_svg("mode", svg)
        print("open", fig)
        V += 1

    # UPDATE FIGURE
    if cfig is not None:
        seq_id = api.get_focused_window().current_sequence.id
        key = int(seq_id.split(" ")[-1]) - 1

        # UPDATE SELECTION IN FOCUS MODE
        if (
            (api.get_selection() is not None)
            and (api.get_selection() != cfig.old_selection)
            and cfig.mode_vision == "FOCUS"
            and key != cfig.old_key
        ):
            cfig.seqs[cfig.old_key].put_script_svg("mode")
            cfig.close()

            cfig = Figure(
                seqs, mode_vision=cfig.mode_vision, selection=api.get_selection()
            )
            fig = cfig.open_all()

            svg = f""" 
            <svg xmlns="http://www.w3.org/2000/svg">
            <g>
                <rect x="5" y="50" width="{len(cfig.mode_vision)*10}" height="15" fill="grey" fill-opacity='0.25' stroke="green" display="absolute"></rect>
                <text x="10" y="50" font-family="Verdana" font-size="15" fill="green" display="absolute">{cfig.mode_vision}</text>
            </g>
            </svg>"""
            cfig.seqs[key].put_script_svg("mode", svg)
            print("open", fig)

        if len(players) == 1:
            key = list(cfig.seqs.keys())[0]

            # CURSOR UPDATE
            if seqs[key].player.frame != cfig.old_frame[key]:
                cfig.update_cursor_all(seqs[0].player.frame)

            # PLOT UPDATE
            elif (
                (fig is not None and api.get_selection() is not None)
                and (api.get_selection() != cfig.old_selection)
                and not api.is_mouse_clicked(0)
            ):
                cfig.update_plot_all(api.get_selection(), mod)

        elif len(players) > 1:
            for key in cfig.seqs:
                if seqs[key].player.frame != cfig.old_frame[key]:
                    cfig.update_cursor(seqs[key].player.frame, key, draw=True)

                elif (
                    fig is not None
                    and api.get_selection() is not None
                    and api.get_selection() != cfig.old_selection
                ):
                    cfig.data[key] = cfig.get_data(api.get_selection(), key)
                    cfig.update_plot(key, draw=True)

        # FIGURE STYLE UPDATE
        for key in cfig.seqs:
            if seqs[key].colormap.shader != cfig.old_shader[key]:
                cfig.open(key, update=True)

            if cfig.lims[key] != seqs[key].colormap.get_range(1):
                N += 1
                if N == 1:
                    start = time.time()
                elif N > 20 or time.time() - start > 0.5:
                    cfig.open(key, update=True)
                    N = 0

        # PREPROCESSING MODE
        if api.is_key_pressed("y", repeat=False) and api.get_selection() is not None:
            mod = MOD[M % len(MOD)]
            cfig.update_preprocessing(mod)
            for key in cfig.seqs:
                cfig.update_rolling_mean(key, mod)
            M += 1

    if fig is not None:
        if fig.stale:
            fig.canvas.draw_idle()
        fig.canvas.flush_events()
