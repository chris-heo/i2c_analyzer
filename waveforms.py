from __future__ import annotations
from enum import Enum
#from dataclasses import dataclass
from typing import List, Optional, Union, Iterator
from pathlib import Path
import csv
import math
import array
import struct
import gzip

class AnalogWaveform:
    def __init__(self) -> None:
        """Initialize an empty analog waveform."""
        self.data: List[float] = []
        self.time_offset: float = 0
        self.time_interval: Optional[float] = None
    
    @classmethod
    def from_saleae_csv(cls, filename: Union[str, Path]) -> List[AnalogWaveform]:
        """
        Create AnalogWaveform instances from a Saleae CSV file.
        
        Args:
            filename: Path to the CSV file
            
        Returns:
            List of AnalogWaveform instances, one per data column
        """
        try:
            with open(filename, "r", newline='') as fh:
                reader = csv.reader(fh)
                headers = next(reader)
                
                # Initialize waveforms for each data column (excluding time column)
                waveforms = [cls() for _ in range(len(headers) - 1)]
                
                # Process first two rows to establish timing parameters
                first_row = next(reader)
                second_row = next(reader)
                
                base_time = float(first_row[0])
                time_interval = float(second_row[0]) - base_time
                
                # Set timing parameters for all waveforms
                for wf in waveforms:
                    wf.time_offset = base_time
                    wf.time_interval = time_interval
                
                # Process first two rows' data
                for i, value in enumerate(first_row[1:]):
                    waveforms[i].data.append(float(value))
                for i, value in enumerate(second_row[1:]):
                    waveforms[i].data.append(float(value))
                
                # Process remaining rows
                for row in reader:
                    if len(row) < 2:  # Skip empty or malformed rows
                        continue
                    for i, value in enumerate(row[1:]):
                        waveforms[i].data.append(float(value))
                        
                return waveforms
                
        except (FileNotFoundError, csv.Error) as e:
            raise ValueError(f"Error reading CSV file: {e}")
        except ValueError as e:
            raise ValueError(f"Error parsing numeric values: {e}")
        
    @classmethod
    def from_saleae_bin(cls, filename: str, gzip_compressed: bool = False) -> AnalogWaveform:
        expected_version = 0
        TYPE_ANALOG = 1
        if gzip_compressed is True:
            f= gzip.open(filename, "rb")
        else:
            f = open(filename, 'rb')

        identifier = f.read(8)
        if identifier != b"<SALEAE>":
            raise Exception("Not a saleae file")

        version, datatype = struct.unpack('=ii', f.read(8))

        if version != expected_version or datatype != TYPE_ANALOG:
            raise Exception("Unexpected data type: {}".format(datatype))

        # Parse analog-specific data
        begin_time, sample_rate, downsample, num_samples = struct.unpack('=dqqq', f.read(32))

        wf = cls()
        wf.time_offset = begin_time
        wf.time_interval = downsample / sample_rate

        # Parse samples
        wf.data = array.array("f")
        wf.data.fromfile(f, num_samples)
    
        return wf

    def value_at_index(self, index: float, interpolate: bool = True) -> float:
        """
        Get the value at a specific index, optionally interpolating between points.
        
        Args:
            index: The index to query (can be fractional)
            interpolate: Whether to interpolate between points
            
        Returns:
            The value at the specified index
        """
        if not self.data:
            raise ValueError("No data available")
            
        i2 = math.ceil(index)
        if i2 >= len(self.data):
            return self.data[-1]
        if i2 <= 0:
            return self.data[0]
            
        if not interpolate:
            return self.data[i2]
            
        v2 = self.data[i2]
        v1 = self.data[i2 - 1]
        fraction = index - i2 + 1
        return v1 + (v2 - v1) * fraction
    
    def time_at_index(self, index: int) -> float:
        """Convert index to time value."""
        if self.time_interval is None:
            raise ValueError("Time interval not set")
        return self.time_offset + self.time_interval * index
    
    def index_at_time(self, time: float, limit: bool = True) -> float:
        """
        Convert time to index value.
        
        Args:
            time: The time to convert
            limit: Whether to limit the result to valid indices
            
        Returns:
            The corresponding index
        """
        if self.time_interval is None:
            raise ValueError("Time interval not set")
            
        index = (time - self.time_offset) / self.time_interval
        
        if not limit:
            return index
            
        return max(0, min(index, len(self.data) - 1))
    
    def get_range_index(self, start: Optional[int] = None, end: Optional[int] = None) -> List[float]:
        """
        Get data within specified index range.
        
        Args:
            start: Start index (inclusive)
            end: End index (inclusive)
            
        Returns:
            List of values within the specified range
        """
        if not self.data:
            return []
            
        start = max(0, math.floor(start) if start is not None else 0)
        end = min(len(self.data) - 1, math.ceil(end) if end is not None else len(self.data) - 1)
        
        if start > end:
            raise ValueError("Start index must be less than or equal to end index")
            
        return self.data[start:end + 1]
    
    def get_range_time(self, start: Optional[float] = None, end: Optional[float] = None) -> List[float]:
        """
        Get data within specified time range.
        
        Args:
            start: Start time
            end: End time
            
        Returns:
            List of values within the specified time range
        """
        if self.time_interval is None:
            raise ValueError("Time interval not set")
            
        start_idx = (math.floor((start - self.time_offset) / self.time_interval)
                    if start is not None else 0)
        end_idx = (math.ceil((end - self.time_offset) / self.time_interval)
                  if end is not None else len(self.data) - 1)
                  
        return self.get_range_index(start_idx, end_idx)
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __iter__(self) -> Iterator[float]:
        return iter(self.data)

class Edge:
    def __init__(self, waveform: DigitalWaveform, i_start: float, i_end: float) -> None:
        self.dw = waveform
        
        self.i_start = i_start
        self.i_end = i_end
        self.slope = None

        self.slope_prev = None
        self.slope_next = None

    @staticmethod
    def _interpolate_index(digital_waveform, level: float, index: int):
        v2 = digital_waveform.awf.data[index]
        if index == 0:
            return index
        
        v1 = digital_waveform.awf.data[index - 1]

        return index - 1 + (level - v1) / (v2 - v1)
    
    def get_time(self, interpolated: bool = False):
        ad = self.dw.awf
        return ad.time_at_index(self.i_end if interpolated is True else math.ceil(self.i_end))

    @property
    def t1(self):
        return self.dw.awf.time_at_index(self.i_start)

    @property
    def t2(self):
        return self.dw.awf.time_at_index(self.i_end)

    @property
    def transition_time(self):
        return self.t2 - self.t1

    @property
    def v1(self):
        return self.dw.awf.value_at_index(self.i_start)

    @property
    def v2(self):
        return self.dw.awf.value_at_index(self.i_end)

    @property
    def slewrate(self):
        dt = (self.i_end - self.i_start) * self.dw.awf.time_interval
        if dt == 0:
            return None
        return (self.v2 - self.v1) / dt

class RisingEdge(Edge):
    def __init__(self, waveform: "DigitalWaveform", i_start, i_end):
        i_start = Edge._interpolate_index(waveform, waveform.threshold_lo, math.ceil(i_start))
        i_end = Edge._interpolate_index(waveform, waveform.threshold_hi, math.ceil(i_end))
        super().__init__(waveform, i_start, i_end)
        self.slope = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} index={self.i_start}->{self.i_end}>"

class FallingEdge(Edge):
    def __init__(self, waveform: "DigitalWaveform", i_start, i_end):
        i_start = Edge._interpolate_index(waveform, waveform.threshold_hi, math.ceil(i_start))
        i_end = Edge._interpolate_index(waveform, waveform.threshold_lo, math.ceil(i_end))
        super().__init__(waveform, i_start, i_end)
        self.slope = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} index={self.i_start}->{self.i_end}>"

class SignalState(Enum):
    LO = 0
    LO_RISE = 1
    HI_RISE = 2
    HI = 3
    HI_FALL = 4
    LO_FALL = 5
    UNKNOWN = 6

    @property
    def is_low_state(self) -> bool:
        return self in (SignalState.LO, SignalState.LO_RISE, SignalState.LO_FALL)
    
    @property
    def is_high_state(self) -> bool:
        return self in (SignalState.HI, SignalState.HI_RISE, SignalState.HI_FALL)

class DigitalWaveform:
    def __init__(self, analog_data: AnalogWaveform, threshold_lo: float, threshold_hi: float):
        """
        Initialize DigitalWaveform with analog data and threshold values.
        
        Args:
            analog_data: Source analog waveform data
            threshold_lo: Lower threshold voltage
            threshold_hi: Higher threshold voltage
        """
        self.awf = analog_data
        self.threshold_lo = threshold_lo
        self.threshold_hi = threshold_hi
        self.transitions = self._compute_transitions()

    def time_at_index(self, index: int) -> float:
        """Get time value at given index."""
        return self.awf.time_at_index(index)

    def _get_state(self, voltage: float, prev_state: SignalState = SignalState.UNKNOWN) -> SignalState:
        """
        Determine signal state based on voltage and previous state.
        Uses a more efficient state transition logic with early returns.
        """
        if voltage >= self.threshold_hi:
            if prev_state.is_low_state:
                return SignalState.HI_RISE
            if prev_state in (SignalState.HI_FALL, SignalState.UNKNOWN):
                return SignalState.HI
        elif voltage < self.threshold_lo:
            if prev_state.is_high_state:
                return SignalState.LO_FALL
            if prev_state in (SignalState.LO_RISE, SignalState.UNKNOWN):
                return SignalState.LO
        else:  # voltage between thresholds
            if prev_state in (SignalState.LO, SignalState.LO_FALL):
                return SignalState.LO_RISE
            if prev_state in (SignalState.HI, SignalState.HI_RISE):
                return SignalState.HI_FALL
        
        return prev_state

    def level_at(self, index: Union[int, float], interpolate: bool = True) -> Optional[bool]:
        """
        Get digital level at given index.
        
        Returns:
            True for high, False for low, None for undefined
        """
        voltage = self.awf.value_at_index(index, interpolate)
        if voltage >= self.threshold_hi:
            return True
        if voltage < self.threshold_lo:
            return False
        return None

    def _compute_transitions(self) -> List[Edge]:
        """
        Compute signal transitions using a more efficient single-pass algorithm.
        """
        transitions = []
        prev_slope = None
        prev_state = SignalState.UNKNOWN
        marker: Optional[tuple[int, SignalState]] = None
        
        for i, voltage in enumerate(self.awf.data):
            state = self._get_state(voltage, prev_state)
            
            if state == SignalState.UNKNOWN or prev_state == SignalState.UNKNOWN:
                prev_state = state
                continue
                
            if state != prev_state:
                if state in (SignalState.LO_RISE, SignalState.HI_FALL):
                    marker = (i, state)
                elif state == SignalState.HI_RISE and marker and marker[1] == SignalState.LO_RISE:
                    slope = RisingEdge(self, marker[0], i)
                    self._link_slope(slope, prev_slope)
                    transitions.append(slope)
                    prev_slope = slope
                elif state == SignalState.LO_FALL and marker and marker[1] == SignalState.HI_FALL:
                    slope = FallingEdge(self, marker[0], i)
                    self._link_slope(slope, prev_slope)
                    transitions.append(slope)
                    prev_slope = slope
                
                prev_state = state
        
        return transitions

    @staticmethod
    def _link_slope(current_slope: Edge, prev_slope: Optional[Edge]) -> None:
        """Helper method to link adjacent slopes."""
        current_slope.slope_prev = prev_slope
        if prev_slope is not None:
            prev_slope.slope_next = current_slope


    def _find_first_after(self, index):
        left = 0
        right = len(self.transitions) - 1
        result = None

        while left <= right:
            mid = (left + right) // 2
            if self.transitions[mid].i_end > index:
                # This could be our answer, but let's check if there's an earlier one
                result = self.transitions[mid]
                right = mid - 1
            else:
                # Too early, look in right half
                left = mid + 1

        return result

#    def next_from_index_old(self, i_start, slope = None, i_end = None):
#        cls = None
#        if slope is True:
#            cls = RisingEdge
#        elif slope is False:
#            cls = FallingEdge
#
#        if i_end is None:
#            i_end = len(self.awf.data)
#
#        #FIXME: implement better search algorithm
#        for tr in self.transitions:
#            if (cls is None or isinstance(tr, cls)) and tr.i_end > i_start and tr.i_end < i_end:
#                return tr
#
#        return None

    def next_from_index(self, i_start, slope = None, i_end = None):
        cls = None
        if slope is True:
            cls = RisingEdge
        elif slope is False:
            cls = FallingEdge

        if i_end is None:
            i_end = len(self.awf.data)

        tr = self._find_first_after(i_start)

        while tr is not None:
            if (cls is None or isinstance(tr, cls)) and tr.i_end > i_start and tr.i_end < i_end:
                return tr
            tr = tr.slope_next
        
        return None


#    def next_from_index(self, i_start, slope = None, i_end = None):
#        cls = None
#        if slope is True:
#            cls = RisingEdge
#        elif slope is False:
#            cls = FallingEdge
#
#
#        left = 0
#        right = len(self.transitions) - 1
#        result = None
#
#        while left <= right:
#            mid = (left + right) // 2
#            current = self.transitions[mid]
#            
#            # Check if current event matches all criteria
#            is_right_type = cls is None or isinstance(current, cls)
#            is_after_start = current.i_end > i_start
#            is_before_end = i_end is None or current.i_end < i_end
#            
#            if is_after_start and is_before_end:
#                if is_right_type:
#                    # This could be our answer, but let's check if there's an earlier one
#                    result = current
#                    right = mid - 1
#                else:
#                    # Since list is sorted by timestamp, not type,
#                    # we need to check both directions
#                    # First check left side for earlier matches
#                    right = mid - 1
#                    # Also remember to scan right for next matching type
#                    # Check remaining self.transitions to the right
#                    for i in range(mid + 1, right + 1):
#                        #if (self.transitions[i].type == event_type and 
#                        if ((cls is None or isinstance(self.transitions[i], cls)) and
#                            self.transitions[i].i_end > i_start and
#                            (i_end is None or self.transitions[i].i_end < i_end)):
#                            result = self.transitions[i]
#                            break
#            elif not is_after_start:
#                left = mid + 1
#            else:
#                right = mid - 1
#
#        return result
