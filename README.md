# I2C Analyzer

Let's make it quick: This tool dissects analog recordings of I2C traffic and shows the following:

* Eye diagrams and some statistics of bits read from and written to devices (separated by devices)
* Cross talk between SDA and SCL (you currently need to know what you are looking for)
* Shows warnings when some I2C spec parameters are violated
* Histograms and some statistic parameters of signal transition times for SCL and SDA

Please note that this scripts is still in an early development phase (which is my lame excuse to be a lazy, sloppy, not to great developer).
This means: use it at your own risk, don't rely on anything that's shown in the report, because, like, "on the internet, nobody knows you're a dog".

## Dependencies

pipreq says:

* matplotlib==3.5.1
* numpy==1.23.5
* scipy==1.15.1

## How to use

```
report.py -h
usage: report.py [-h] [-vbus BUS_VOLTAGE] [-tl THRESHOLD_LOW] [-th THRESHOLD_HIGH] -f {saleae_bin,saleae_csv} ...

Creates a I2C analysis report

positional arguments:
  rest

options:
  -h, --help            show this help message and exit
  -vbus, --bus_voltage BUS_VOLTAGE
                        Nominal voltage of the I2C bus (default: 5)
  -tl, --threshold_low THRESHOLD_LOW
                        Threshold for low level in percent (default: 30)
  -th, --threshold_high THRESHOLD_HIGH
                        Threshold for high level in percent (default: 70)
  -f, --filetype {saleae_bin,saleae_csv}
                        File format of the analog data (options: saleae_bin, saleae_csv). For saleae_bin, 2 arguments: SCL file, SDA
                        file. For saleae_csv, 3 arguments: CSV file, SCL column, SDA column (both column numbers are 0-based).
```

As the help text already indicates, focus is currently on analog data recorded by a Saleae logic analyzer with analog capabilities.

With 400 kHz, 12.5 MHz sampling rate is good enough, with enough traffic (check the example), not too much traffic is needed.

After capturing the data, File -> Export Raw Data... -> select the analog channels for your SDA and SCL and select the binary export format.

To save space (with slim to no speed penalty), you can gzip the files. The script will autodetect the .bin.gz file extension and will decompress transparently.

with the example data provided, you can use the following command:

```report.py -vbus 5 -f saleae_bin exampledata\analog_1.bin.gz exampledata\analog_0.bin.gz```

Apart a report.json and report.jsonc, some png files will be generated in the same directory. Open index.html to see the report or use the report.json for further processing.
If you're wondering about the .jsonc-file, this is a workaround to not need a HTTP-server to view the report since all modern browsers don't allow XHRs to local files, even from a local file in the same directory. Good security measure but sometimes annoying.

## Example data

For tests (and the shown demonstration), I strapped some ready made modules to my [MCP2221 adapter](https://hobbyelektronik.org/w/index.php/MCP-USB-Bridge#USB-I.C2.B2C-Bridge_v1.1), to be precise:

* TI INA219
* Broadcom APDS-9900 (both SDA and SCL via 47 ohms resistors)
* Microchip MCP4725

Generated some traffic and recorded 2 seconds of data with a Saleae Pro 16, exported it as raw binary and imported it.

The report can be viewed in the exampledata directory.


## Known issues

* Lack of error handling, if something goes wrong, it crashes. Feel free to file issue reports (and provide your input data, best as .sal file by now)
* It's slow. The state machine to convert the analog waveforms to digital samples is inefficient. Same is true for the detection of high and low levels
* Crosstalk diagrams are somewhat misaligned, also it's not quite clear for the uninitiated where to look. Also no effort spent to generate statistics for crosstalk
* Code is bad style, spaghetti at some places, I don't know how to efficiently use numpy, or even properly organize python projects
* Report data is dumped in the current directory. Bad habits
* You better not show the report to your customers, they may get confused or will ask questions
* Author is a bit too flippant. Recalibration, proper readme, article is needed and on a loooong TODO list

## Features I'd like to add

* Setup & Hold times
* More statistics regarding SCL (eye diagrams?!)
* Bus load, bus frequency over time
* Detection and visualization of clock stretching
* Visualization of transactions
* More and better references to NXP's [UM10204](https://www.nxp.com/docs/en/user-guide/UM10204.pdf)
* Estimation of bus capacity
* Direct support for oscilloscope recordings

## License

* Something, Something, MIT, Something.
* Do whatever you want. Please consider contributing rather than complaining. Thank you :)

