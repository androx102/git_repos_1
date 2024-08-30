
from time import time, sleep
from serial import Serial

port = 'COM6'
baudrate = 115200

bus = Serial(port=port,baudrate=baudrate,timeout=0)


max_time_between_chars = 0.1
timeout = 5


print('started')
def get_board_response( max_time_between_chars):
    buffer_data = b''
    end_time = time() + max_time_between_chars
    while True:
        if time() < end_time:
            new_data= bus.readline()
            ####
            #print(new_data)
            ####
            if new_data == b'':
               pass
                #print('no data')
            else:
                print(new_data)
                end_time = time() + max_time_between_chars
                buffer_data += new_data
        else:
            if buffer_data != b'':
                print(f'Pushing data; {buffer_data}')
                buffer_data = b''
            end_time = time() + max_time_between_chars



while True:
    get_board_response(max_time_between_chars)





