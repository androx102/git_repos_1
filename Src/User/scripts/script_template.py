# static imports - importing Device drivers ect
from DUT_drivers import * 
from device_drivers import *
from private_libraries import *

#dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock

################## USER CODE BEGINS HERE ######################