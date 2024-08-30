import serial
import sys
import time

port_ = "COM8"
ser = serial.Serial(port_, 9600, timeout=1)


msg = "dupa"
mg = msg.encode()

while True:
    print("sending data")
    ser.write(msg)
    time.sleep(2)
