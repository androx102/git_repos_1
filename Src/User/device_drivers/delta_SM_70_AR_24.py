from device_drivers.priv_dependencies import *
from enum import Enum
from time import sleep



class Delta_power():
    def __init__(self,eth_node_name:str,user_thread:User_thread):
        self.api = user_thread
        self.node_name = eth_node_name
        self.terminator = '\n'



    def read_identifier(self):
        message = "*IDN?" + self.terminator
        return self.api.send_querry(self.node_name,message,blocking=True,time_for_timeout=5)

    def set_output_state(self,output_state):
        """
        Output state:
            1 - ON
            0 - OFF
        """
        message = f"OUTP {output_state}" + self.terminator
        self.api.send_message(self.node_name,message)
        message = "OUTP?" + self.terminator
        return self.api.send_querry(self.node_name,message,blocking=True,time_for_timeout=5)
       
    def set_remote(self,_parameter,_type):
        """
        parameter:
            CV - voltage
            CC - current
        type:
            REM - remote
            LOC - local
        """
        message = f"SYST:REM:{_parameter} {_type}" + self.terminator
        self.api.send_message(self.node_name,message)
        sleep(0.5)
        message = f"SYST:REM:{_parameter}?" + self.terminator
        return self.api.send_querry(self.node_name,message,time_for_timeout=5)

 

    def set_output_value(self,_parameter,_val):
        """
        Parameter:
            VOLT - voltage
            CURR - current
        Val - float value
        """ 
        _val = _val 
        message = f"SOUR:{_parameter} " + "{:.4f}".format( _val ) + self.terminator
        self.api.send_message(self.node_name,message)
        sleep(0.5)
        message = f"SOUR:{_parameter}?" + self.terminator
        return self.api.send_querry(self.node_name,message,time_for_timeout=5)


    def measure_param(self,_param):
        """
        Param:
            VOLT - voltage
            CURR - current
        """
        message = f"MEAS:{_param}?" + self.terminator
        return self.api.send_querry(self.node_name,message,time_for_timeout=5)
