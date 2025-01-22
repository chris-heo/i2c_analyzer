import numpy as np
import math
import statistics
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from simplestats import Simplestats
from waveforms import DigitalWaveform, RisingEdge, FallingEdge

class I2cBitInfo:
    def __init__(self, bits, v_bus, dw_scl, dw_sda):
        self.bits = bits

        self.v_bus = v_bus

        self.figure = None
        self.axis = None

        self.x_data = np.array([])
        self.y_data = np.array([])

        for bit in self.bits:
            i = bit.index
            #if bit.sda_value is not True: # level of SDA to be shown
            #    continue
            tr_next = dw_scl.next_from_index(i, True)
            di = tr_next.slope_prev.i_end - i
            i_start = math.floor(i - di)
            i_end = math.ceil(i + di)

            awf = dw_sda.awf

            pts = awf.get_range_index(i_start, i_end)
            t = [(x * awf.time_interval + awf.time_offset - awf.time_at_index(i)) * 1e6 for x in list(range(i_start, i_end + 1))]

            self.x_data = np.append(self.x_data, t)
            self.y_data = np.append(self.y_data, pts)

    def draw_plot(self, size_x = 8, size_y = 6):
        # Create a 2D histogram of the data
        # Adjust bins for resolution and range to your data
        x_bins = np.linspace(-1.5, 1.5, 250)
        y_bins = np.linspace(-0.5, self.v_bus + 1, 400)
        hist, x_edges, y_edges = np.histogram2d(self.x_data, self.y_data, bins=[x_bins, y_bins])

        # Transpose the histogram for correct orientation in imshow
        hist = hist.T

        # Plot the graded display
        self.figure = plt.figure(figsize=(size_x, size_y))
        self.axis = self.figure.add_subplot()

        im = plt.imshow(hist, extent=[x_bins[0], x_bins[-1], y_bins[0], y_bins[-1]],
                origin='lower', aspect='auto', cmap='inferno', norm=PowerNorm(gamma=0.3))
        #cmap: hot, plasma, inferno
        self.figure.colorbar(im, label='Sample Density')
        self.axis.set_xlabel('Time [µs]')
        self.axis.set_ylabel('Amplitude [V]')
        #plt.savefig("density.svg", format="svg")
        #plt.show()

        return self.figure


    def info(self):
        stats = Simplestats(self.y_data)
        lvlinfo = stats.level_info()

        info = {
            "min" : stats.min, "low_value" : None, "low_stddev" : None, "low_count" : None,
            "high_value" : None, "high_stddev" : None, "high_count" : None, "max" : stats.max, 
            "warnings" : []
        }

        def warn(s):
            print(s)
            info["warnings"].append(s)

        if stats.min < -0.5:
            warn("WARNING: voltage on bus is < -0.5 V")
        if stats.max > self.v_bus + 0.5:
            warn("WARNING: voltage on bus is > v_bus + 0.5 V")
        elif stats.max > 5.5:
            warn("WARNING: voltage on bus is > 5.5 V")

        if lvlinfo['low']['value'] is not None:
            info["low_value"] = lvlinfo['low']['value']
            info["low_stddev"] = lvlinfo['low']['stddev']
            info["low_count"] = lvlinfo['low']['cnt']

            print(f"LO: min={stats.min:.3f}V value={lvlinfo['low']['value']:.3f}V stddev={lvlinfo['low']['stddev']:.3f}V")
            if self.v_bus > 2 and lvlinfo["low"]["value"] > 0.4:
                warn("WARNING: low level voltage is > 0.4 V for v_bus > 2 V")
            elif self.v_bus <= 2 and lvlinfo["low"]["value"] > 0.2 * self.v_bus:
                warn("WARNING: low level voltage is > 0.2 V * v_bus for v_bus <= 2 V")
        
        if lvlinfo['high']['value'] is not None:
            info["high_value"] = lvlinfo['high']['value']
            info["high_stddev"] = lvlinfo['high']['stddev']
            info["high_count"] = lvlinfo['high']['cnt']
            print(f"HI: max={stats.max:.3f}V value={lvlinfo['high']['value']:.3f}V stddev={lvlinfo['high']['stddev']:.3f}V")

        return info
    
class I2cCrosstalk:
    def __init__(self, aggressor: DigitalWaveform, rising_edge: bool, victim: DigitalWaveform, v_bus, title: str = None):
        self.aggressor = aggressor
        self.rising_edge = rising_edge
        self.victim = victim
        self.v_bus = v_bus
        self.title = title

        self.figure = None
        self.axis = None

    def draw_plot(self, size_x = 8, size_y = 6):
        slopes = list(filter(lambda o: o.slope == self.rising_edge, self.aggressor.transitions))

        t_tr = statistics.median(map(lambda o: o.transition_time, slopes)) * 5

        awf = self.victim.awf

        x_data = np.array([])
        y_data = np.array([])

        for slope in slopes:
            t_ref = (slope.t2 + slope.t1) / 2
            i_start = math.floor(awf.index_at_time(t_ref - t_tr))
            i_end = math.ceil(awf.index_at_time(t_ref + t_tr))

            pts = awf.get_range_index(i_start, i_end)
            #t = [(awf.time_offset + x * awf.time_interval - (t_ref + slope.transition_time)) * 1e6 for x in list(range(i_start, i_end+1))]
            t = [(awf.time_offset + x * awf.time_interval - t_ref) * 1e6 for x in list(range(i_start, i_end+1))]

            x_data = np.append(x_data, t)
            y_data = np.append(y_data, pts)

        x_bins = np.linspace(-1, 1, 250)
        y_bins = np.linspace(-0.5, self.v_bus + 1, 400)
        hist, x_edges, y_edges = np.histogram2d(x_data, y_data, bins=[x_bins, y_bins])

        # Transpose the histogram for correct orientation in imshow
        hist = hist.T

        self.figure = plt.figure(figsize=(size_x, size_y))
        self.axis = self.figure.add_subplot()
        #
        im = self.axis.imshow(hist, extent=[x_bins[0], x_bins[-1], y_bins[0], y_bins[-1]],
                origin='lower', aspect='auto', cmap='inferno', norm=PowerNorm(gamma=0.3))
        #cmap: hot, plasma, inferno
        self.figure.colorbar(im, label='Sample Density')
        self.axis.set_xlabel('Time [µs]')
        self.axis.set_ylabel('Amplitude [V]')
        if self.title is not None:
            self.axis.set_title(self.title)
        #plt.show()
        return self.figure

class I2cTransitiontime:
    def __init__(self, i2c_transactions, scl: bool = True):
        self.i2c_transactions = i2c_transactions

        addresses = self.i2c_transactions.i2c_addresses()

        self.figure = None
        self.axis = None

        self.stats = { "rise" : None, "fall" : None}

        self.scl = scl
        if scl is True:
            getslopes = lambda tr: tr.get_scl_slopes()
        else:
            getslopes = lambda tr: tr.get_sda_slopes()
        
        self.data = []
        self.data_all = { "rise" : [], "fall" : [] }
        for ag in addresses:
            trsf = self.i2c_transactions.filter(ag.address)
            tmp = { "address" : ag.address, "rise" : [], "fall" : [] }
            for tr in trsf:
                slopes = getslopes(tr)
                for slope in slopes:
                    slope_time = slope.transition_time * 1e9 # this smells.
                    if isinstance(slope, RisingEdge):
                        tmp["rise"].append(slope_time)
                        self.data_all["rise"].append(slope_time)
                    else:
                        tmp["fall"].append(slope_time)
                        self.data_all["fall"].append(slope_time)
            
            self.data.append(tmp)

    def draw_plot(self, bin_width: float = 0.1):
        #bin_width = 0.0001 # bin width in ns
        # this implementation is dirty

        def make_diagram(what, plt_axis, bin_width: float = 0.0001):

            bins = np.arange(min(self.data_all[what]), max(self.data_all[what]) + bin_width, bin_width)

            #data_weights = np.ones(len(data_all[what])) / len(data_all[what]) * 100
            for i, item in enumerate(self.data):
                color = plt.rcParams['axes.prop_cycle'].by_key()['color'][i] + "60"

                plt_axis.hist(item[what], bins, color=color, label=f"Addr 0x{item['address']:02X}, {len(item[what])} edges")

            if what == "rise":
                meh = "from low to high"
                slope = "rising"
            else:
                meh = "from high to low"
                slope = "falling"

            plt_axis.set_xlabel(f'Transition time {meh} [ns]')
            plt_axis.set_ylabel('Count')
            plt_axis.legend()
            plt_axis.title.set_text(f"{'SCL' if self.scl is True else 'SDA'} {slope} edge transition time")

        px = 1 / plt.rcParams['figure.dpi']
        self.figure, self.axis = plt.subplots(1, 2, figsize=(640 * 2 * px, 480 * px))

        make_diagram("fall", self.axis[0], bin_width)
        make_diagram("rise", self.axis[1], bin_width)

        return self.figure

        