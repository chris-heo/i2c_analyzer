from waveforms import *
from simplestats import Simplestats
from typing import List
from dataclasses import dataclass

class I2cStartcondition:
    def __init__(self, transaction, sda_transition: Edge, restart: bool = False) -> None:
        self.transaction = transaction
        self.sda_transition = sda_transition
        self.restart = False

    @property
    def index(self):
        return self.sda_transition.i_end
    
    @property
    def time(self):
        return self.sda_transition.dw.time_at_index(self.index)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} transition={self.sda_transition} restart={self.restart}>"
    
    def serialize(self):
        return { "type" : "Start", "time" : self.time }
 
class I2cStopcondition:
    def __init__(self, transaction, sda_transition: Edge) -> None:
        self.transaction = transaction
        self.sda_transition = sda_transition

    @property
    def index(self):
        return self.sda_transition.i_end

    @property
    def time(self):
        return self.sda_transition.dw.time_at_index(self.index)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} transition={self.sda_transition}>"
    
    def serialize(self):
        return { "type" : "Stop", "time" : self.time }

class I2cBit:
    def __init__(self, parent, scl_transition: Edge, sda_value) -> None:
        self.parent = parent
        self.scl_transition = scl_transition
        self.sda_value = sda_value

    @property
    def index(self):
        return self.scl_transition.i_end
    
    @property
    def bit_time(self):
        analyzer = self.parent.transaction.analyzer
        #prev_trans = analyzer.scl_data.prev_from_index(self.scl_transition.index, False)
        next_trans = analyzer.scl_data.next_from_index(self.scl_transition.index, False)
        prev_trans = next_trans.slope_prev
        if prev_trans is None or next_trans is None:
            return None
        
        dt = analyzer.scl_data.time_at_index(next_trans.index) - analyzer.scl_data.time_at_index(prev_trans.index)

        return dt
    
    def __repr__(self):
        return f"<{self.__class__.__name__} sda={self.sda_value} scl_index={self.scl_transition.i_end}>"
    
    @property
    def scl_high_time(self):
        if (fall := self.scl_transition.slope_next) is None:
            return None
        return  fall.t2 - self.scl_transition.t2
    
    @property
    def scl_low_time(self):
        if (fall := self.scl_transition.slope_next) is None:
            return None
        if (next_rise := fall.slope_next) is None:
            return None
        return next_rise.t2 - fall.t2
    
    @property
    def scl_period(self):
        if (fall := self.scl_transition.slope_next) is None:
            return None
        if (next_rise := fall.slope_next) is None:
            return None
        
        return next_rise.t2 - self.scl_transition.t2
    
    @property
    def sda_level_data(self):
        if (fall := self.scl_transition.slope_next) is None:
            return None
        analyzer: I2cAnalyzer = self.parent.transaction.analyzer
        return analyzer.sda_data.awf.get_range_index(self.scl_transition.i_end, fall.i_end)
    
    @property
    def sda_level(self):
        return Simplestats(self.sda_level_data)

class I2cDataByte:
    def __init__(self, transaction) -> None:
        self.transaction = transaction
        self.bits = []
        self.value = None
        self.ack = None
        self.is_complete = False

    def addbit(self, scl_transition, sda_value: bool):
        #FIXME: don't accept more than 9 bits
        self.bits.append(I2cBit(self, scl_transition, sda_value))
        return self.done()

    def done(self):
        if len(self.bits) == 9:
            self.is_complete = True
            self.value = 0
            for i in range(0, 8):
                self.value <<= 1
                if self.bits[i].sda_value == True:
                    self.value |= 1
            
            self.ack = not self.bits[8].sda_value
            return True
        return False
    
    @property
    def bit_time(self):
        bit_times = [bit.bit_time for bit in self.bits]
        return Simplestats(bit_times)

    def __repr__(self) -> str:
        byte_str = self.value
        if byte_str is not None:
            byte_str = f"0x{self.value:02X}"
        return f"<{self.__class__.__name__} byte={byte_str} ack={self.ack} complete={self.is_complete}>"
    
    def serialize(self):
        return { "value" : self.value, "ack" : self.ack, "complete" : self.is_complete }

class I2cAddressByte:
    def __init__(self, transaction) -> None:
        self.transaction = transaction
        self.bits = []
        self.value = None
        self.read = None
        self.ack = None
        self.is_complete = False

    def addbit(self, scl_transition, sda_value: bool):
        self.bits.append(I2cBit(self, scl_transition, sda_value))
        return self.done()

    def done(self):
        if len(self.bits) == 9:
            self.is_complete = True
            self.value = 0
            for i in range(0, 7):
                self.value <<= 1
                if self.bits[i].sda_value == True:
                    self.value |= 1
            
            #print(f"R/!W: {self.bits[7].sda_value}")
            self.read = self.bits[7].sda_value # something's wrong here
            self.ack = not self.bits[8].sda_value
            return True
        return False
    
    @property
    def frequency(self):
        freqs = [bit.frequency for bit in self.bits]
        return min(freqs), sum(freqs) / len(freqs), max(freqs)

    def __repr__(self) -> str:
        address_str = self.value
        if address_str is not None:
            address_str = f"0x{self.value:02X}"
        return f"<{self.__class__.__name__} addr={address_str} read={self.read} ack={self.ack} complete={self.is_complete}>"
    
    def serialize(self):
        return { "value" : self.value, "read" : self.read, "ack" : self.ack, "complete" : self.is_complete }
    

class I2cTransaction:
    def __init__(self, analyzer) -> None:
        self.analyzer: I2cAnalyzer = analyzer
        self.start_condition = None
        self.obj_address: I2cAddressByte = None
        self.obj_data: List[I2cDataByte] = []
        self.stop_condition = None

        self.index_start = None
        self.index_end = None

    @property
    def address(self) -> int | None:
        if self.obj_address is None or self.obj_address.is_complete is False:
            return None
        
        return self.obj_address.value
    
    @property
    def access_read(self) -> bool | None:
        if self.obj_address is None or self.obj_address.is_complete is False:
            return None
        return self.obj_address.read
    
    @property
    def addr_acked(self) -> bool | None:
        if self.obj_address is None or self.obj_address.is_complete is False:
            return None
        return self.obj_address.ack
    
    @property
    def data(self) -> list:
        retval = []
        for item in self.obj_data:
            retval.append(item.data if item.is_complete is True else None)

        return retval
    
    @property
    def is_complete(self) -> bool:
        if self.start_condition is None or self.obj_address is None or self.stop_condition is None:
            return False
        return True

    @property
    def t_startcondition(self) -> float:
        if self.start_condition is None:
            return None
        else:
            return self.start_condition.time
            #return self.analyzer.sda_data.time_at_index(self.start_condition.index)

    @property
    def t_stopcondition(self) -> float:
        if self.stop_condition is None:
            return None
        else:
            return self.stop_condition.time
            #return self.analyzer.sda_data.time_at_index(self.stop_condition.index)

    def __repr__(self):
        start_info = "[no start condition]"
        if self.start_condition is not None:
            start_info = f"start_time={self.t_startcondition:0.7f}s"

        addr_info = "[no address info]"
        if self.obj_address is not None:
            address_str = ""
            if self.obj_address.value is not None:
                address_str = f"0x{self.obj_address.value:02X}"
            addr_info = f"addr={address_str} access_type={'R' if self.access_read is True else 'W'} addr_acked={self.addr_acked}"

        stop_info = "[no stop condition]"
        if self.stop_condition is not None:
            stop_info = f"stop_time={self.t_stopcondition:0.7f}s"

        data_info = " ".join([(f"{d.value:02X}" + ("n" if d.ack is False else "a")) if d.is_complete is True else "!!" for d in self.obj_data])
        return f"<{self.__class__.__name__} {start_info} {addr_info} data=[{data_info}] {stop_info}>"
        
    def get_bits(self, address: bool = False, address_ack: bool = False, data: bool = False, data_ack: bool = False):
        result = []

        if self.obj_address is not None:
            if address is True:
                result.extend(self.obj_address.bits[0:8])
        
            if address_ack is True:
                result.extend(self.obj_address.bits[8:9])
        
        if data is True or data_ack is True:
            for d in self.obj_data:
                if data is True:
                    result.extend(d.bits[0:8])
                if data_ack is True:
                    result.extend(d.bits[8:9])

        return result
    
    def get_sda_slopes(self):
        result = []
        slope = self.analyzer.sda_data.next_from_index(self.index_start)
        result.append(slope)
        while (slope := slope.slope_next) is not None:
            if slope is None or slope.i_end is None or self.index_end is None or slope.i_end > self.index_end:
                break
            result.append(slope)
        
        return result
    
    def get_scl_slopes(self):
        result = []
        slope = self.analyzer.scl_data.next_from_index(self.index_start)
        result.append(slope)
        while (slope := slope.slope_next) is not None:
            if slope is None or slope.i_end is None or self.index_end is None or slope.i_end > self.index_end:
                break
            result.append(slope)
        
        return result
    
    @classmethod
    def next_transaction(cls, analyzer: "I2cAnalyzer", startindex: int = 0):
        self = cls(analyzer)

        scld = self.analyzer.scl_data
        sdad = self.analyzer.sda_data

        i = startindex

        self.start_condition = analyzer._next_start(i)

        if self.start_condition is None:
            return self
        
        #print(f"got start condition: {self.start_condition}")
        
        i = self.start_condition.index
        self.index_start = i

        #print(f"START at {analyzer.tstr(i)}")

        data = I2cAddressByte(self)

        while True:
            # check if there is a start/stop condition before the next bit
            # in the current state (after a tart condition or after data latched), SCL is high
            # look for the next falling slope, if there is any change of SDA before that 
            # (i.e. during SCL is high), there has been a STOP or RESTART condition
            scl_trans = scld.next_from_index(i, False)
            if scl_trans is None:
                # no transition -> premature end of transaction
                #print(f"could not find SCL fall after {analyzer.tstr(i)} -> end of transmission")
                return self

            sda_trans = sdad.next_from_index(i, None, scl_trans.i_end)
            #print(f"checking next SDA transition between {analyzer.tstr(i)} ... {analyzer.tstr(scl_trans.i_end)}: {sda_trans}")
            if sda_trans is not None:
                if isinstance(sda_trans, RisingEdge): # STOP condition
                    #print(f"STOP condition at {analyzer.tstr(sda_trans.i_end)} -> end of transmission")
                    #print(f"residual data: {data}")

                    self.stop_condition = I2cStopcondition(self, sda_trans)
                    self.index_end = sda_trans.i_end
                    #FIXME: is the transaction complete? set self.completetransaction = True
                    return self
                else: # RESTART condition
                    #print(f"RESTART condition at {analyzer.tstr(sda_trans.i_end)} -> end of transmission")
                    #print(f"residual data: {data}")
                    self.stop_condition = I2cStartcondition(self, sda_trans, True)
                    self.index_end = sda_trans.i_end #FIXME: is this correct? 
                    # or rather just i - restart condition must be re-detected by next transaction detection
                    #FIXME: is the transaction complete? set self.completetransaction = True
                    return self
                
            scl_trans = scld.next_from_index(i, True) # next rising edge of SCL
            if scl_trans is None:
                #print("premature end of data")
                return self
            if data.addbit(scl_trans, sdad.level_at(scl_trans.i_end)) is True:
                # byte transmission is done
                if isinstance(data, I2cAddressByte):
                    #print(f"address byte completely received: {data}")
                    self.obj_address = data
                else:
                    #print(f"data byte completely received: {data}")
                    self.obj_data.append(data)

                # check if a STOP or RESTART condition follows

                data = I2cDataByte(self)

            i = scl_trans.i_end

class I2cAnalyzer:
    def __init__(self, sda_data: DigitalWaveform, scl_data: DigitalWaveform) -> None:
        self.sda_data = sda_data
        self.scl_data = scl_data

    def tstr(self, index):
        if isinstance(index, Edge):
            index = index.i_end
            #35.646 233 5
        return f"{index} [{self.sda_data.time_at_index(index):0.7f} s]"
    
    def _next_start(self, index):
        while True:
            
            slope = self.sda_data.next_from_index(index, False)
            #print(f"looking for start condition after {index}: {slope}")
            #slope, = self.sda_data.next2(index, False, interpolate=True)
            if slope is None:
                return None
            
            scl_level = self.scl_data.level_at(slope.i_end)
            #print(f"  SCL level at {slope.i_end} is {scl_level}")
            
            if scl_level is True:
                #print(f"START condition at {self.tstr(slope.i_end)}")
                return I2cStartcondition(self, slope)
            
            index = slope.i_end + 1
    
    def _next_stop(self, index):
        while True:
            slope = self.sda_data.next_from_index(index, True)
            if slope is None:
                return None
            if self.scl_data.level_at(slope.i_end) is True:
                return I2cStopcondition(self, slope)
            
    def get_transactions(self):
        index = 0
        transactions = []
        while True:
            tr = I2cTransaction.next_transaction(self, index)
            transactions.append(tr)
            
            if tr is None or tr.index_end is None:
                break

            if index == tr.index_end:
                raise Exception("Could not find next transaction (stuck in inf loop)")
            
            index = tr.index_end
            
            if isinstance(tr.stop_condition, I2cStartcondition):
                # restart condition, need to move the cursor a bit to catch the (re-)start
                index -= 1

        return I2cTransactions(transactions)

class I2cTransactions:
    def __init__(self, items):
        self.items: List[I2cTransaction] = items

    def __len__(self) -> int:
        return len(self.items)

    def i2c_addresses(self):
        @dataclass
        class I2CAddress:
            address: int
            read: bool
            write: bool
            read_count: int
            write_count: int
        tmp = {}
        for tr in self.items:
            
            if (addr := tr.address) is not None:
                #addr = (addr << 1) | (1 if tr.access_read else 0)
                if addr not in tmp:
                    tmp[addr] = I2CAddress(addr, False, False, 0, 0)
                
                if tr.access_read is True:
                    tmp[addr].read = True
                    tmp[addr].read_count += 1
                else:
                    tmp[addr].write = True
                    tmp[addr].write_count += 1


        return list(tmp.values())
    
    def filter(self, address: Union[int, None] = None, read: Union[bool, None] = None):
        items = []
        for item in self.items:
            if (address is None or item.address == address) and (read is None or item.access_read == read):
                items.append(item)
        
        return I2cTransactions(items)
    
    def get_bits(self, address: bool = False, address_ack: bool = False, data: bool = False, data_ack: bool = False):
        result = []

        for item in self.items:
            result.extend(item.get_bits(address, address_ack, data, data_ack))

        return result
    
    def __getitem__(self, index):
        return self.items[index]
