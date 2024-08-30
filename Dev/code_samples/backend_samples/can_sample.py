from typing import Any
import can
import time



#create bus connection
######################################
bus1 = can.interface.Bus(bustype='vector', channel=0, bitrate=500000, app_name='pycan')
print_listener = can.Printer()
#######################################



#sample custom listener
########################################
class TestCallback(can.Listener):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.msg_to_search = ""

    def on_message_received (self,msg):
        #print("Received message !")
        pass
########################################


#notifier setup
#test_listener = TestCallback(listen_to = "x")
    
#can.Notifier(bus1, [print_listener,test_listener])
can.Notifier(bus1, [print_listener])


#IBCM specified
enter_diag = can.Message(data=[2,16,2,0,0,0,0,0],arbitration_id=0x18DA40F1)
hold_in_diag = can.Message(data=[2,62,0,0,0,0,0,0],arbitration_id=0x18DA40F1)
print(enter_diag.data)
print(hold_in_diag.data)

print(f"Sending: {str(enter_diag)}")
bus1.send(enter_diag,timeout=1)

while True:
    time.sleep(2)
    bus1.recv(1)
    #print(f"Sending: {str(hold_in_diag)}")
    #bus1.send(hold_in_diag)
    




