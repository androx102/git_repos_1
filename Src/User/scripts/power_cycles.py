#static imports - importing Device drivers ect
from DUT_drivers import * 
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
print("ahoj")

delta_name = "Delta_PW"
chamber_name = "CTS"
self.add_sub(delta_name)
self.add_sub(chamber_name)


power_supply = Delta_power("Delta_PW",self)
thermal_chamber = CTS_40_50("CTS",self)

#init of power supply
#print(f"Idenitifer querry: {power_supply.read_identifier()}")
#print("Setting remote voltage: " + str(power_supply.set_remote("CV","REM")))
#print("Truning on output: " + str(power_supply.set_output_state(1)))
#print(f"Temp: "+ str(thermal_chamber.set_temperature(30)))
print(f"Temp: "+ str(thermal_chamber.measuer_current_temp()))

#print(f"Turning on: "+ str(thermal_chamber.turn_on_chamber()))
sleep(4)



#for x in range(1,10):
 #   sleep(1.5)
  #  print(f"Setting voltage to {x}: " + str(power_supply.set_output_value("VOLT",x)))


#
print("End")
#print(self.send_and_wait_for_response("FI88","x/r",blocking=True,optional_params="SEND_MSG_TXT",time_for_timeout=10))
#print(FI88.peps_authenticate())

