#static imports - importing Device drivers ect
#from DUT_drivers import * 
from device_drivers import *
from private_libraries import *
#from Nodes.User_node import user_script_main_thread as User_thread
#from Nodes.uth_mock import User_thread_mock
#dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock
################## USER CODE BEGINS HERE ######################


print("Hello from US")
self.add_sub("FI88")
self.send_message("FI88",'UGA\n\r',optional_params="SEND_MSG_TXT")
#time.sleep(5)
#
FI88 = FI88_tester("FI88",self)
FI88.send_custom_message()
#print(self.send_and_wait_for_response("FI88","x/r",blocking=True,optional_params="SEND_MSG_TXT",time_for_timeout=10))
#print(FI88.peps_authenticate())

