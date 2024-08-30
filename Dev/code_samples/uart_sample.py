
from serial import *
from time import *
baudrate_ = 115200
com_port = 'COM7'
timeout_ = 1
message = 'dupa\n\r'

serial_channel = Serial(port=com_port,baudrate=baudrate_,timeout=timeout_)

try:
    serial_channel.open()
    print("open 1")
except:
    serial_channel.close()
    serial_channel.open()
    print("open 2")





for x in range(10):
    serial_channel.write(message.encode())
    sleep(0.1)

serial_channel.close()