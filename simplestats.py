import statistics

class Simplestats:
    def __init__(self, data):
        self.data = data

    def __len__(self) -> int:
        return len(self.data)
    
    @property
    def min(self):
        return min(self.data)
    
    @property
    def avg(self):
        return sum(self.data) / len(self.data)
    
    @property
    def mode(self):
        return statistics.mode(self.data)
    
    def mode_precision(self, ndigits):
        return statistics.mode([round(x, ndigits) for x in self.data])
    
    @property
    def median(self):
        return statistics.median(self.data)
    
    @property
    def max(self):
        return max(self.data)
    
    def find_dominant_voltages(self, num_levels = 2, bandwidth_factor = 0.05, min_peak_height = None, min_peak_height_rel = None):
        from scipy.stats import gaussian_kde
        from scipy.signal import find_peaks
        import numpy as np
        """
        Find dominant voltage levels in waveform data using KDE (Kernel Density Estimation).
        Particularly useful for PAM4 signals which have 4 distinct levels.
        
        Parameters:
        num_levels (int): Expected number of voltage levels (default 4 for PAM4)
        bandwidth_factor (float): Controls KDE bandwidth, smaller values detect narrower peaks
        min_peak_height (float): Minimum height for peak detection, defaults to 20% of max density
        
        Returns:
        tuple: (voltage_levels, density_curve, voltage_points)
            - voltage_levels: Array of detected dominant voltage levels
            - density_curve: KDE density values for plotting
            - voltage_points: Voltage points used for density calculation
        """
        # Create kernel density estimation
        kde = gaussian_kde(self.data)
        kde.set_bandwidth(bw_method=bandwidth_factor)
        
        # Generate points for density evaluation
        voltage_points = np.linspace(min(self.data), max(self.data), 1000)
        density = kde(voltage_points)
        
        if min_peak_height_rel is None:
            min_peak_height = 0.2

        # Find peaks in density
        if min_peak_height is None:
            min_peak_height = min_peak_height_rel * max(density)
        
        peaks, _ = find_peaks(density, height=min_peak_height, distance=50)
        
        # Get voltage levels from peak locations
        voltage_levels = voltage_points[peaks]
        
        # Sort voltage levels from highest to lowest
        voltage_levels = np.sort(voltage_levels)[::-1]
        
        # If we found more or fewer peaks than expected, adjust bandwidth and try again
        if len(voltage_levels) != num_levels:
            print(f"Warning: Found {len(voltage_levels)} levels instead of expected {num_levels}")
            print("Consider adjusting bandwidth_factor or min_peak_height")
        
        return voltage_levels, density, voltage_points
    
    def level_info(self, min_peak_height_rel = 0.1):
        import numpy as np
        data = np.array(self.data)
        levels, _, _ = self.find_dominant_voltages(2, min_peak_height_rel)

        result = { "high" : { "value" : None, "stddev" : None, "cnt" : None },  "low" : { "value" : None, "stddev" : None, "cnt" : None } }

        for i, level in enumerate(levels):
            window = abs(data - level) < (abs(level) * 0.05)
            points_near_level = data[window]
            stddev = np.std(points_near_level)
            
            # drrrty
            key = "low" if level < self.median else "high"
            result[key] = { "value" : level, "stddev" : stddev, "cnt" : len(points_near_level) }

        return result

    def __repr__(self):
        return f"<{self.__class__.__name__} len={len(self)} min={self.min} avg={self.avg} mode={self.mode} median={self.median} max={self.max}>"
    
    def serialize(self):
        return {
            "len" : len(self),
            "min" : self.min,
            "avg" : self.avg,
            "mode" : self.mode,
            "median" : self.median,
            "max" : self.max,
        }