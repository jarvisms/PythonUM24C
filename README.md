# PythonUM24C

This Python module provides a class and methods for interfacing with the RDTech UM24C USB Meter with Bluetooth connectivity. This library has been based on predominantly on the information provided [here](https://sigrok.org/wiki/RDTech_UM_series). This has been written in Python 3.7.2, but may work in earlier versions but this is not guaranteed.

## Prerequisites

The [`pyserial`](https://pypi.org/project/pyserial/) module is needed to allow the use of the Bluetooth Serial Port interface to connect to the device.
```
pip install pyserial
```

## Installing
There is no need to clone this repo since the module is a single file. You can simply download the ['um24c.py'](um24c.py) file to a location within the import path of your project, and then simply import it.

## Usage

Once imported, you may connect to the device in two ways;
- Using Python's built in sockets interface - this relies on the underlying operating system compatibility however and knowing the MAC Address of the device directly
- Using the legacy Bluetooth Serial Port interface - this relies on the user bonding the device and creating a Bluetooth virtual serial port via other means, such as with operating system utilities.

Using Direct Socket interface
```
from um24c import UM24C
meter  =  UM24C("01:23:45:67:89:AB")
```
OR...

Using BT VSP interface where "False" denotes that sockets should not be used.
```
from um24c import UM24C
meter  =  UM24C("COM21",False)
```

After you have created your connected instance, the various methods are then available to use - the main one being `get_reads` to read data, but others to remotely control the device.

When finished, you may simply delete the object to disconnect, such as `del meter` or call `meter.close()` which disconnects but retains the object.

If the connection seems to have been lost, you can call `meter.reset_port(device)` where `device` is the equivelent of the socket or VSP port from when it was initialised. However, in this case, the type of connection must be the same. i.e. you can use this to change from `COM21` to `COM22` for example, but not from `COM21` to `01:23:45:67:89:AB` as this would be a change of connection type.

### Getting Readings
`meter.get_reads()`
Calling this method will request readings from the meter device, scale the readings and returns them as a Named Tuple as follows:
```
Reads(
    timestamp = datetime.datetime(2019, 3, 23, 21, 33, 5, 1331),    # datetime (Python datetime.datetime naive object)
    V = 5.34,         # Voltage (V)
    A = 0.919,        # Amperage (A)
    W = 4.907,        # Wattage (W)
    C = 26,           # Temperature (°C)
    F = 79,           # Temperature (°F)
    Group = 3,        # Group Number (#)
    mAh0 = 177,       # Capacity (mAh) for Group 0
    mWh0 = 934,       # Energy (mWh) for Group 0
    ...                 # Capacity and Energy for Groups 1-9 as above
    Dpos = 1.33,      # USB D+ Voltage (V)
    Dneg = 1.33,      # USB D- Voltage (V)
    Mode = 0,         # Charge Mode (enum)
    mAh = 1501,       # Record Capacity (mAh)
    mWh = 8053,       # Record Energy (mWh)
    At = 0.0,         # Record Threshold (A)
    S = 5040,         # Record Duration (S)
    Active = 0,       # Recording Active (True/False)
    Screensaver = 9,  # Screen Timeout (min)
    Backlight = 0,    # Backlight (#)
    Ohms = 5.8,       # Resistance (Ω)
    Screen = 0        # Screen (#)
)
```
Since this is a Named Tuple, you may retrieve individual parameters directly by its attribute name, or by an index number:
```
result = meter.get_reads()
result.V    # Gives 5.34 in example above
result[2]   # Corresponds to A, and would give 0.919 in example above
```

### Device Control Functions
The UM24C can also be remotely controlled to some extent - although there's not a great deal te be controlled. They are summarised here:

`meter.next_screen()`
Changes to the next screen mode on the device. Equivalent of pressing the next button.

`meter.rotate_screen()`
Rotates the screen orientation on the device. Equivalent of pressing and holding the top right button.

`meter.next_data_group()`
Changes to the next data storage group on the device. Equivalent to pressing and holding the bottom right button on screen 1.

`meter.clear_data_group()`
Clears the current data storage group on the device. Equivalent to pressing and holding the bottom left button on screen 1.

`meter.set_threshold(f)`
Sets the recording theshold to `f`, between 0A and 0.3A. Equivalent to changing the settings on screen 3.

`meter.set_backlight(i)`
Changes the backlights settings to `i` between 0 and 5. Equivalent to changing the settings on screen 7.

`meter.set_screensaver(i)`
Changes the number of minutes until the screensaver blanks the screen to `i` between 0 (never turn off) and up to 9 minutes. Equivalent to changing the settings on screen 7.

## Author & Motivation

**Mark Jarvis** - [jarvisms](https://github.com/jarvisms)

I code in Python as a hobby and tinker with electronics. I bought one of these devices from eBay out of interest and decided to write a little library for it to allow it to be integrated into  - such as a logger.

## Contributions & Feature requests

For bugs, or feature requests, please contact me via GitHub or raise an issue.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgements

* Everything has been based on information found on [sigrok](https://sigrok.org/wiki/RDTech_UM_series)
* This site also links to another Python library called [rdumtool](https://github.com/rfinnie/rdumtool), however my implementation is not based on this as it was written entirely from scratch
