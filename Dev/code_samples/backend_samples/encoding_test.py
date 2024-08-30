
import serial
import time

#msg for dut: "0101020304"


test_str = "0101020304"
test_hex_number = 0x0101020304



test_bytes = b"\x01\x01\x02\x03\x02"
reset_msg_bytes = b'\x20\x32\x05'
test_bytes_utf8 = test_str.encode("utf-16")


# str= "01 02 03" -> bytes = b"\x01\x02\x03"
result_bytes = bytes.fromhex(test_str)

my_serial = serial.Serial("COM11",115200,timeout=0)

try:
    try:
        my_serial.open()
    except:
        my_serial.close()
        my_serial.open()

        my_serial.write(reset_msg_bytes)
        print("Sending done")
        time.sleep(2)
        response_from_dut = my_serial.read(100)
        print(response_from_dut)


except:
    print(f"Failed to open port")