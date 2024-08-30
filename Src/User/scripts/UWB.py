#static imports - importing Device drivers ect
from DUT_drivers import * 
from device_drivers import *
from private_libraries import *

#dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock
################## USER CODE BEGINS HERE ######################

print("starting user script")
print("This Example will program the Litepoint UWBgig device")

self.add_sub("Litepoint_UWB")

# Create instance of the Listpoint UWB class
UWB_LP = UWB_Litepoint(self)   
                                
# Initialize parameter structure for UWB
UWB_LP.InitializeProtocolRFParameters() 

# Intrument reset and configuration of external FESW
UWB_LP.ResetPlusConfigureRfSwitch()   

# There are pre-defined sequences (index 0,1,2,3....)
# 0 = CCC0
# 1 = CCC1
# 2 = CCC2
# 3 = TESTMODE_SP0_CONF1
# 4 = TESTMODE_SP3_CONF1
# 5 = UWB_INTERFERER_TYP
# 6 = UWB_INTERFERER_WORST
# 7 = UWB_INTERFERER_EXTREME
# Check InitializeProtocolRFParameters for details            
UWB_LP.TriggerPacketGen(5)                                      
            
# Run WaveList with number of repetitions 0 = endless loop, N = [1..Inf.] Play wavelist N times
number_of_repetitions = 0                                                 
UWB_LP.SetRfPhy_Litepoint_Run_Wavelist(number_of_repetitions)   

# Set output power in dBm
for power in range (-10,10,2):
    time.sleep(2)  
    UWB_LP.SetRfPhy_Litepoint_VSG_OutputPower(power) 
	
# Stop the execution of the WaveList (only needed in case of endless loop)
UWB_LP.SetRfPhy_Litepoint_VSG_StopWaveList()	

# clean up files on Litepoint hard disk
UWB_LP.SetRfPhy_Litepoint_DeleteWaveFiles()   

print("UWB user script done")
