import socket
import serial
import struct
import operator
from datetime import datetime, timezone

class btserial(serial.Serial):
    def send(self,data):
        return self.write(data)
    def recv(self,num):
        return self.read(num)

class UM24C:
    fmt = ">2x2HI2HxB20I2HBx2IHIBx2HIxB2x"
    conv = struct.Struct(fmt)
    keys = (
        "Voltage (V)",      # Originally cV
        "Amperage (A)",     # Originally cA
        "Wattage (W)",     # Originally mW
        "Temperature (°C)",
        "Temperature (°F)",
        "Group (#)",
            *( "Group {}, {}".format(i,u)
            for i in range(10)
            for u in ("Capacity (mAh)", "Energy (mWh)")
            ),
        "USB D+ Voltage (V)",  # Originally cV
        "USB D- Voltage (V)",  # Originally cV
        "Charge Mode (enum)",
        "Record Capacity (mAh)",
        "Record Energy (mWh)",
        "Record Threshold (A)",    # Originally cA
        "Record Duration (S)",
        "Recording Active (?)",
        "Screen Timeout (min)",
        "Backlight (#)",
        "Resistance (Ω)",  # Originally dΩ
        "Screen (#)",
    )
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
    multipliers = multipliers(scales,keys)  # execute the lambda to get around the scope issue with generators/comprehensions in  class variables
    def __init__(self, device, usesocket=True):
        self.socket = usesocket
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
    def ResetPort(self, device):
        if hasattr(self, "port"):
            self.port.close()
        self.__init__(device,self.socket)
    def GetReads(self, raw=False):
        '''Gets readings from the UM24C device from the given serial port'''
        port = self.port
        i = 3   # Number of attempts to make
        while True:
            try:
                buff = bytearray()
                port.send(bytes([0xF0]))
                while len(buff) < 130:
                    buff += port.recv(4096)
                results = self.conv.unpack(buff[-130:])
                if not raw:
                    results = tuple(
                        map(
                            operator.mul,
                            self.multipliers,
                            results,
                        )
                    )
                return (datetime.now(timezone.utc), *results)
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
    def NextScreen(self):
        try:
            self.port.send(bytes([0xF1]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def RotateScreen(self):
        try:
            self.port.send(bytes([0xF2]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def NextDataGroup(self):
        try:
            self.port.send(bytes([0xF3]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def ClearDataGroup(self):
        try:
            self.port.send(bytes([0xF4]))
            print("Command Sent")
        except (OSError, serial.SerialException) as err:
            print(err)
    def SetThreshold(self, threshold):
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
    def SetBacklight(self, backlight):
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
    def SetScreensaver(self, screensaver):
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