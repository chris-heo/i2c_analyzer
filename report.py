from waveforms import *
from i2c_dissector import *
import json
import argparse
import os

p = argparse.ArgumentParser(description="Creates a I2C analysis report")
p.add_argument("-vbus", "--bus_voltage", type=float, default=5, help="Nominal voltage of the I2C bus (default: %(default)s)")
p.add_argument("-tl", "--threshold_low", type=float, default=30, help="Threshold for low level in percent (default: %(default)s)")
p.add_argument("-th", "--threshold_high", type=float, default=70, help="Threshold for high level in percent (default: %(default)s)")
p.add_argument("-f", "--filetype", type=str, required=True, choices=["saleae_bin", "saleae_csv"], help=" ".join([
    "File format of the analog data (options: %(choices)s).",
    "For saleae_bin, 2 arguments: SCL file, SDA file."
    "For saleae_csv, 3 arguments: CSV file, SCL column, SDA column (both column numbers are 0-based)."
]))
p.add_argument('rest', nargs=argparse.REMAINDER)

try:
    args = p.parse_args()
except:
    #p.print_help()
    exit(0)

assert args.bus_voltage > 0, "Bus voltage must be > 0 V"
assert 0 < args.threshold_low < args.threshold_high, "Low threshold must be between 0 % and high threshold"
assert args.threshold_low < args.threshold_high < 100, "High threshold must be between low threshold and 100 %"

v_bus = args.bus_voltage
v_lo = v_bus * args.threshold_low / 100
v_hi = v_bus * args.threshold_high / 100


print("Loading waveforms")

aw_scl = None
aw_sda = None

def file_load_saleae_bin(filename):
    if not os.path.exists(filename):
        print(f"file '{filename}' could not be found.")
        return None
    fnlower = filename.lower()

    if fnlower.endswith(".bin"):
        return AnalogWaveform.from_saleae_bin(filename, False)
    elif fnlower.endswith(".bin.gz"):
        return AnalogWaveform.from_saleae_bin(filename, True)
    else:
        print("File type not supported (yet)")
        exit(-1)

if args.filetype == "saleae_bin":
    assert len(args.rest) == 2, "2 arguments (SCL file, SDA file) expected"
    scl_file = args.rest[0]
    sda_file = args.rest[1]
    aw_scl = file_load_saleae_bin(scl_file)
    aw_sda = file_load_saleae_bin(sda_file)
elif args.filetype == "saleae_csv":
    assert len(args.rest) == 3, "3 arguments (file, SCL column, SDA column) expected"
    filename = args.rest[0]
    scl_col = int(args.rest[1])
    sda_col = int(args.rest[2])

    scl_file = f"{filename}:{scl_col}"
    sda_file = f"{filename}:{sda_col}"

    aws = AnalogWaveform.from_saleae_csv(filename)
    assert len(aws) >= 2, "2 or more columns in file expected, less found."

    aw_scl = aws[scl_col]
    aw_sda = aws[sda_col]
else:
    print("You should not be able to see this.")
    exit()

if aw_scl is None or aw_sda is None:
    print("At least one waveform could not be loaded.")
    exit(-1)

data = {
    "bus" : {
        "voltage" : v_bus,
        "threshold_hi" : v_hi,
        "threshold_lo" : v_lo
    },
    "info" : {
        "scl_file" : scl_file,
        "sda_file" : sda_file,
    },
    "transactions" : [],
    "bitstats" : [],
    "crosstalk" : [],
    "transitiontimes" : {},
}

if len(aw_sda) != len(aw_scl):
    print(f"Error: Waveform sample count of SDA ({len(aw_sda)}) and SCL ({len(aw_scl)}) don't match.")
    exit(-1)

def samplerate(interval):
    if interval <= 0:
        return "Error"
    return f"{1e-6 / interval:.3f} MHz"

if aw_sda.time_interval != aw_scl.time_interval:
    print(f"Error: Waveform sample rate of SDA ({samplerate(aw_sda.time_interval)}) and SCL ({samplerate(aw_scl.time_interval)}) don't match.")
    exit(-1)

print(f"{len(aw_scl)} samples at {samplerate(aw_scl.time_interval)}")

data["info"]["samples"] = len(aw_scl)
data["info"]["samplerate"] = 1 / aw_scl.time_interval

print(f"Resampling as digital waveforms. V_hi = {v_hi:.3f} V; V_lo = {v_lo:.3f} V. This may take a while...")
print()

dw_scl = DigitalWaveform(aw_scl, v_lo, v_hi)
print(f"Found {len(dw_scl.transitions)} transitions on SCL")
dw_sda = DigitalWaveform(aw_sda, v_lo, v_hi)
print(f"Found {len(dw_sda.transitions)} transitions on SDA")

print()
ia = I2cAnalyzer(dw_sda, dw_scl)
transactions = ia.get_transactions()

print(f"Found {len(transactions)} I2C transactions:")

i2c_addresses = transactions.i2c_addresses()
ttgroups = []
for item in i2c_addresses:
    print(f"  Device 0x{item.address:02X}: {item.write_count} writes, {item.read_count} reads")
    ttgroups.append({ "address" : item.address, "writes" : item.write_count, "reads" : item.read_count })
    
data["bus"]["addresses"] = ttgroups

#region Transactions
print()
print("== Transactions ==")
for i, tr in enumerate(transactions):

    data["transactions"].append({ 
        "start" : None if tr.start_condition is None else tr.start_condition.serialize(),
        "address" : None if tr.obj_address is None else tr.obj_address.serialize(),
        "data" : [o.serialize() for o in tr.obj_data],
        "stop" : None if tr.stop_condition is None else tr.stop_condition.serialize(),
    })

    s = f"  {i:>4} "
    if (ts := tr.t_startcondition) is not None:
        s += f"{ts:>10.6f}s"
    else:
        s += "---- ? ----"
    
    s += " -> "

    if (ts := tr.t_stopcondition) is not None:
        s += f"{ts:>10.6f}s"
    else:
        s += "---- ? ----"

    addr_info = "[addr?]"
    if tr.obj_address is not None:
        addr_str = ""
        if tr.obj_address.value is not None:
            addr_str = f"{tr.obj_address.value:02X}"
        addr_info = f"{addr_str}{'R' if tr.access_read is True else 'W'}{'a' if tr.addr_acked is True else 'n'}"

    s += f" {addr_info}: "

    s += " ".join([(f"{d.value:02X}" + ("n" if d.ack is False else "a")) if d.is_complete is True else "!!" for d in tr.obj_data])

    print(s)

#region Bit statistics
print()
print("== Bit statistics ==")

import i2cvisualizer

for ag in i2c_addresses:
    # Bits read from devices
    info = {
        "address" : ag.address,
        "read" : None,
        "write" : None,
    }

    print(f"Bits read from device 0x{ag.address:02X}")
    trsf = transactions.filter(ag.address, True)
    bits = trsf.get_bits(False, True, True, False)
    trsf = transactions.filter(ag.address, False) # ACK bits
    bits.extend(trsf.get_bits(False, True, False, True))
    read_bits_cnt = len(bits)
    if read_bits_cnt == 0:
        print("No read bits found.")
    else:
        bitinfo = i2cvisualizer.I2cBitInfo(bits, v_bus, dw_scl, dw_sda)
        fig = bitinfo.draw_plot()
        bitinfo.axis.set_title(f'SDA Bits read from 0x{ag.address:02X} ({len(bits)} wfrms)')

        read_filename = f"bits_0x{ag.address:02X}R.png"
        fig.savefig(read_filename, format="png")
        read_bitinfo = bitinfo.info()
        print(f"Eye diagram saved as '{read_filename}'")

        info["read"] = {
            "waveforms" : read_bits_cnt,
            "filename" : read_filename,
            "info" : read_bitinfo
        }

    # Bits written to devices
    print(f"Bits written to device 0x{ag.address:02X}")

    trsf = transactions.filter(ag.address, False)
    bits = trsf.get_bits(True, False, True, False)
    trsf = transactions.filter(ag.address, True) # address bits
    bits.extend(trsf.get_bits(True, False, False, False))
    write_bits_cnt = len(bits)
    
    if write_bits_cnt == 0:
        print("No write bits found.")
    else:

        bitinfo = i2cvisualizer.I2cBitInfo(bits, v_bus, dw_scl, dw_sda)
        fig = bitinfo.draw_plot()
        bitinfo.axis.set_title(f'SDA for Bits written to 0x{ag.address:02X} ({len(bits)} wfrms)')

        write_filename = f"bits_0x{ag.address:02X}W.png"
        fig.savefig(write_filename, format="png")
        write_bitinfo = bitinfo.info()
        print(f"Eye diagram saved as '{write_filename}'")

        info["write"] = {
            "waveforms" : write_bits_cnt,
            "filename" : write_filename,
            "info" : write_bitinfo
        }

    data["bitstats"].append(info)

#region Crosstalk
print()
print("== Crosstalk ==")
xtalk_combs = [
    [ "SDA", "SCL", dw_sda, True,  dw_scl, "xtalk_sda_scl_rise.png", "Crosstalk of SDA to SCL on SDA's rising edge" ],
    [ "SDA", "SCL", dw_sda, False, dw_scl, "xtalk_sda_scl_fall.png", "Crosstalk of SDA to SCL on SDA's falling edge" ],
    [ "SCL", "SDA", dw_scl, True,  dw_sda, "xtalk_scl_sda_rise.png", "Crosstalk of SCL to SDA on SCL's rising edge" ],
    [ "SCL", "SDA", dw_scl, False, dw_sda, "xtalk_scl_sda_fall.png", "Crosstalk of SCL to SDA on SCL's falling edge" ],
]

for item in xtalk_combs:
    xtalk = i2cvisualizer.I2cCrosstalk(item[2], item[3], item[4], v_bus, item[6])
    fig = xtalk.draw_plot()
    filename = item[5]
    
    fig.savefig(filename, format="png")
    print(f"Crosstalk diagram saved as '{filename}'")

    data["crosstalk"].append({
        "aggressor" : item[0],
        "victim" : item[1],
        "edge" : item[3],
        "title" : item[6],
        "filename" : filename
    })

#region Transition times
print()
print("== SCL Transition times ==")
ttgroups = i2cvisualizer.I2cTransitiontime(transactions, True)
filename = f"trtime_scl.png"
fig = ttgroups.draw_plot()
fig.savefig(filename, format="png")
print(f"Transition time diagram saved as '{filename}'")

stats_rise = Simplestats(ttgroups.data_all["rise"])
stats_fall = Simplestats(ttgroups.data_all["fall"])

print("All:")
print(f"  Rise [ns]: min={stats_rise.min:.0f} avg={stats_rise.avg:.0f} mode={stats_rise.mode:.0f} median={stats_rise.median:.0f} max={stats_rise.max:.0f}")
print(f"  Fall [ns]: min={stats_fall.min:.0f} avg={stats_fall.avg:.0f} mode={stats_fall.mode:.0f} median={stats_fall.median:.0f} max={stats_fall.max:.0f}")

#FIXME: don't use objects, use an array instead
data["transitiontimes"]["scl"] = {
    "signal" : "SCL",
    "filename" : filename,
    "rise" : stats_rise.serialize(),
    "fall" : stats_fall.serialize(),
    "devices" : []
}

for ttgroup in ttgroups.data:
    fig = ttgroups.draw_plot()
    print(f"For 0x{ag.address:02X}:")

    stats_rise = Simplestats(ttgroup["rise"])
    stats_fall = Simplestats(ttgroup["fall"])
    print(f"  Rise [ns]: min={stats_rise.min:.0f} avg={stats_rise.avg:.0f} mode={stats_rise.mode:.0f} median={stats_rise.median:.0f} max={stats_rise.max:.0f}")
    print(f"  Fall [ns]: min={stats_fall.min:.0f} avg={stats_fall.avg:.0f} mode={stats_fall.mode:.0f} median={stats_fall.median:.0f} max={stats_fall.max:.0f}")

    data["transitiontimes"]["scl"]["devices"].append({
        "address" : ttgroup["address"],
        "rise" : stats_rise.serialize(),
        "fall" : stats_fall.serialize(),
    })


print()
print("== SDA Transition times ==")
ttgroups = i2cvisualizer.I2cTransitiontime(transactions, False)
filename = f"trtime_sda.png"
fig = ttgroups.draw_plot()
fig.savefig(filename, format="png")
print(f"Transition time diagram saved as '{filename}'")

stats_rise = Simplestats(ttgroups.data_all["rise"])
stats_fall = Simplestats(ttgroups.data_all["fall"])

#TODO: Add warnings for rise/fall time violations
print("All:")
print(f"  Rise [ns]: min={stats_rise.min:.0f} avg={stats_rise.avg:.0f} mode={stats_rise.mode:.0f} median={stats_rise.median:.0f} max={stats_rise.max:.0f}")
print(f"  Fall [ns]: min={stats_fall.min:.0f} avg={stats_fall.avg:.0f} mode={stats_fall.mode:.0f} median={stats_fall.median:.0f} max={stats_fall.max:.0f}")

data["transitiontimes"]["sda"] = {
    "signal" : "SDA",
    "filename" : filename,
    "rise" : stats_rise.serialize(),
    "fall" : stats_fall.serialize(),
    "devices" : []
}

for ttgroup in ttgroups.data:
    fig = ttgroups.draw_plot()
    print(f"For 0x{ag.address:02X}:")

    stats_rise = Simplestats(ttgroup["rise"])
    stats_fall = Simplestats(ttgroup["fall"])
    print(f"  Rise [ns]: min={stats_rise.min:.0f} avg={stats_rise.avg:.0f} mode={stats_rise.mode:.0f} median={stats_rise.median:.0f} max={stats_rise.max:.0f}")
    print(f"  Fall [ns]: min={stats_fall.min:.0f} avg={stats_fall.avg:.0f} mode={stats_fall.mode:.0f} median={stats_fall.median:.0f} max={stats_fall.max:.0f}")

    data["transitiontimes"]["sda"]["devices"].append({
        "address" : ttgroup["address"],
        "rise" : stats_rise.serialize(),
        "fall" : stats_fall.serialize(),
    })

with open("report.json", "w") as fp:
    json.dump(data, fp)

with open("report.jsonc", "w") as fp:
    fp.write("report(")
    json.dump(data, fp)
    fp.write(");")