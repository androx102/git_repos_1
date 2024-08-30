#Device manuals:
#http://iq1421a0648/litepoint//HTML/doc/IQxelMUserGuideMaster.pdf
#http://iq1421a0648/litepoint//HTML/index.html

#includes
from device_drivers.priv_dependencies import *


class LitePoint():
    def __init__(self,eth_node_name:str,user_thread:User_thread):
        self.eth_node_name = eth_node_name
        self.user_thread = user_thread
        self.sessionID = None
        
    def write(self, command:str):
        message = command + "\n"
        self.user_thread.send_message(self.eth_node_name, message)
    
    def query(self, command:str, timeout:int=10):
        message = command + "\n"
        status, response = self.user_thread.send_and_wait_for_response(
            topic=self.eth_node_name, data=message, blocking=True, time_for_timeout=timeout)
        if status:
            print("LitePoint Command : ", status)
            print("LitePoint response:" + response)
            return response[:-2]
        else:
            print(f"Query failed for {command}")
            return None