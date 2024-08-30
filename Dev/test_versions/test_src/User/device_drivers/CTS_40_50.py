from device_drivers.priv_dependencies import *




class CTS_40_50():
    def __init__(self,eth_node_name:str,user_thread:User_thread):
        self.api = user_thread
        self.node_name = eth_node_name


    def create_frame(self,command):
        return "\x02"+command+"\x03"
    
    def measuer_current_temp(self):
        message = self.create_frame("A0")
        return self.api.send_querry(self.node_name,message,time_for_timeout=5)
    
    def turn_on_chamber(self):
        message = self.create_frame("S1 1")

        return self.api.send_querry(self.node_name,message,time_for_timeout=5)
    
    def turn_off_chamber(self):
        message = self.create_frame("S1 0")
        return self.api.send_querry(self.node_name,message,time_for_timeout=5)
        pass

    def set_temperature(self,temp):
        message = self.create_frame(f"A0"+str(temp))
        print(message)
        return self.api.send_querry(self.node_name,message,time_for_timeout=5)

        return
    



    #STX/ETX
#STX = "\x02"
#ETX = "\x03"
#def create_frame(command):
 #   return STX + command + ETX