import socket
import serial
import struct
import operator
from collections import namedtuple
from datetime import datetime, timezone

class btserial(serial.Serial):
    """Provides send and recv methods to Serial class to be consistent with
    socket classes"""
    def send(self,data):
        return self.write(data)
    def recv(self,num):
        return self.read(num)

class UM24C:
    """UM24C class provides methods for easily interfacing with the UM24C Meter"""
    # Formats, keys and instruction bytes as per https://sigrok.org/wiki/RDTech_UM_series
    fmt = ">2x2HI2HxB20I2HBx2IHIBx2HIxB2x"
    conv = struct.Struct(fmt)
    keys = (
        "V",        # Voltage (V), Originally cV
        "A",        # Amperage (A) Originally cA
        "W",        # Wattage (W) Originally mW
        "C",        # Temperature (°C)
        "F",        # Temperature (°F)
        "Group",    # Group (#)
            *( "{}{}".format(u,i)
            for i in range(10)
            for u in ("mAh", "mWh")     # Capacity (mAh), Energy (mWh)
            ),
        "Dpos",       # USB D+ Voltage (V) Originally cV
        "Dneg",       # USB D- Voltage (V) Originally cV
        "Mode",     # Charge Mode (enum)
        "mAh",      # Record Capacity (mAh)
        "mWh",      # Record Energy (mWh)
        "At",       # Record Threshold (A)
        "S",        # Record Duration (S)
        "Active",   # Recording Active (?)
        "Screensaver",  # Screen Timeout (min)
        "Backlight",    # Backlight (#)
        "Ohms",     # Resistance (Ω) Originally dΩ
        "Screen",   # Screen (#)
    )
    # Rescales particular items to standard units.
    scales = {
        0 : 0.01,   # cV to V
        1 : 0.001,  # cA to A
        2 : 0.001,  # mW to W
        26 : 0.01,  # cV to V
        27 : 0.01,  # cV to V
        31 : 0.01,  # cA to A
        36 : 0.1,   # dΩ to Ω
    }
    multipliers = lambda scales, keys: tuple(   # lambda needed for class scope
        scales[i] if i in scales else 1     # Use Scale, else 1
        for i in range(len(keys))           # For each key
    )
    multipliers = multipliers(scales,keys)  # execute the lambda to get around the scope issue with generators/comprehensions in class variables
    Reads = namedtuple("Reads", ('timestamp', *keys))
    def __init__(self, device, usesocket=True):
        """Initialise connection with the hardware.
        When 'usesocket' is True (default), 'device' should be the MAC address 
        of the Bluetooth such as '01:23:45:67:89:AB'. If False, then the name
        of the bluetooth serial port should be used for legacy mode connection
        such as '/dev/rfcomm0', or 'COM20' where this has been mapped via the
        Operating System's utilities.
        """
        self.socket = usesocket
        # Preferentially use BT Sockets, but also allow for Serial device
        if usesocket:
            self.port = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_STREAM,
                socket.BTPROTO_RFCOMM
            )
            port = self.port
            port.settimeout(5.0)    # Give more time for connection
            port.connect((device,1))
            port.settimeout(0.1)    # Flush out anything in the receive buffer
            try:
                while True:
                    if not port.recv(4096):
                        break
            except (socket.timeout, BlockingIOError):
                pass
            port.settimeout(1.0)
        else:
            self.port = btserial(
                port=device,
                baudrate=4000000,
                timeout=1,
                write_timeout=1,
            )
            self.port.reset_input_buffer()
    def __del__(self):
        self.port.close()
    def close(self):
        self.port.close()
    def reset_port(self, device):
        """Attempts to close the port and reopen with the new device which 
        must be of the same type as previous"""
        if hasattr(self, "port"):
            self.port.close()
        self.__init__(device,self.socket)
    def get_reads(self):
        '''Gets readings from the UM24C device from the given serial port'''
        port = self.port
        i = 3   # Number of attempts to make
        while True:
            try:
                buff = bytearray()
                port.send(bytes([0xF0]))    # The Get Readings instruction
                while len(buff) < 130:
                    buff += port.recv(4096)
                results = tuple(
                    map(
                        operator.mul,
                        self.multipliers,
                        self.conv.unpack(buff[-130:]),
                    )
                )
                return self.Reads(datetime.now(), *results)
                break
            except (OSError, serial.SerialException, struct.error) as err:
                print(err)
                i-=1
                port.settimeout(0.1)    # Flush out anything in the receive buffer
                try:
                    while True:
                        if not port.recv(4096):
                            break
                except (socket.timeout, BlockingIOError):
                    pass
                port.settimeout(1.0)
                if i <= 0:
                    raise
                    break
        return
    def next_screen(self):
        """Changes to the next screen mode on the device
        Equivalent of pressing the next button"""
        try:
            self.port.send(bytes([0xF1]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def rotate_screen(self):
        """Rotates the screen orientation on the device
        Equivalent of pressing and holding the top right button"""
        try:
            self.port.send(bytes([0xF2]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def next_data_group(self):
        """Changes to the next data storage group on the device
        Equivalent to pressing and holding the bottom right button on screen 1"""
        try:
            self.port.send(bytes([0xF3]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def clear_data_group(self):
        """Clears the current data storage group on the device
        Equivalent to pressing and holding the bottom left button on screen 1"""
        try:
            self.port.send(bytes([0xF4]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def set_threshold(self, threshold):
        """Sets the recording threshold to 'threshold', between 0A and 0.3A
        Equivalent to changing the settings on screen 3"""
        if 0 <= threshold <= 0.3:
            threshold = int(threshold*100)
            command = 0xB0 + threshold
            try:
                self.port.send(bytes([command]))
                print("Command Sent")
            except (OSError, serial.SerialException) as err:
                print(err)
        else:
            raise ValueError("Value must be between 0-0.3")
    def set_backlight(self, backlight):
        """Changes the backlights settings to 'backlight' between 0 and 5
        Equivalent to changing the settings on screen 7"""
        if 0 <= backlight <= 5:
            backlight = int(backlight)
            command = 0xD0 + backlight
            try:
                self.port.send(bytes([command]))
                print("Command Sent")
            except (OSError, serial.SerialException) as err:
                print(err)
        else:
            raise ValueError("Value must be between 0-5")
    def set_screensaver(self, screensaver):
        """Changes the number of minutes until the screensaver blanks the screen
        to 'screensaver' between 0 (never turn off) and up to 9 minutes.
        Equivalent to changing the settings on screen 7"""
        if 0 <= screensaver <= 9:
            screensaver = int(screensaver)
            command = 0xE0 + screensaver
            try:
                self.port.send(bytes([command]))
                print("Command Sent")
            except (OSError, serial.SerialException) as err:
                print(err)
        else:
            raise ValueError("Value must be between 0-9")