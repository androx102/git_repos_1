
from time import time, sleep
from serial import Serial

port = 'COM6'
baudrate = 115200

bus = Serial(port=port,baudrate=baudrate,timeout=0)


max_time_between_chars = 0.1
timeout = 5

def get_board_response(timeout, max_time_between_chars):
        end_time = time() + timeout
        last_char_ts = time()
        resp = b''
        status= False
        while time() < end_time:
            try:
                new_data= bus.readline()
            except:
                new_data = b''

            if len(new_data) > 0:
                resp += new_data
                last_char_ts = time()
            elif time() > (last_char_ts + max_time_between_chars) :
                break
            sleep(0.005)
        if resp != b'':
             status = True
        
        return status, resp.decode('utf-8').strip()



while True:
    print(get_board_response(timeout,max_time_between_chars))





