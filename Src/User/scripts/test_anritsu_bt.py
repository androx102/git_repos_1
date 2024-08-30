# static imports - importing Device drivers ect
from DUT_drivers import *
from device_drivers import *
from private_libraries import *

# dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock

################## USER CODE BEGINS HERE ######################

# start message ***********************************************
print("USER SCRIPT STARTED")

# add subscribers here ****************************************
self.add_sub("anritsu_bt")

# put your code here ******************************************

# create Anritsu BT object
anritsu_bt = AnritsuMT8852BBT("anritsu_bt", self)

wlan = AnritsuMT8852BBT("anritsu_wlan", self)

# query IDN
# print("Query IDN:")
# print(anritsu_bt.query("*IDN?", timeout=10))

# anritsu_bt.write("SCRIPTMODE 3,STANDARD")

# anritsu_bt.configure_ms_test()

status = anritsu_bt.query("SCPTCFG 3,ALLTSTS,OFF;*ESR?")
print(f"STATUS : {status}")

# finish message **********************************************
print("USER SCRIPT FINISHED")
