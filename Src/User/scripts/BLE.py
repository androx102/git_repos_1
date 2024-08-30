#static imports - importing Device drivers ect
from DUT_drivers import * 
from device_drivers import *
from private_libraries import *

#dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock
################## USER CODE BEGINS HERE ######################

print("Starting user script!")

self.add_sub("VIP")
self.add_sub("SOC")
self.add_sub("ADB")
self.add_sub("PowerSupply")
self.add_sub("Litepoint_IQXEL_CC")

dut = IHU("VIP", "SOC", "ADB", self)
powerSupply = QJ3005P("PowerSupply", self)
generator = LitePoint("Litepoint_IQXEL_CC", self)

# powerSupply.query("*IDN?")
generator.query("*IDN?")
# dut.send_vip("version")
dut.IHU_set_pwr_always_on()
dut.send_adb("ls")

print("User script excuted!")
