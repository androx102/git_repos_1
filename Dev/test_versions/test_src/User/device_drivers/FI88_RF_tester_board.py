from device_drivers.priv_dependencies import *

class FI88_tester():
    def __init__(self,uart_node_name:str,user_thread:User_thread):
        self.user_thread = user_thread
        self.uart_node_name = uart_node_name
        self.terminator = '\r'
        
        self.immo_auth = 'xxx'

    def send_custom_message(self):
        pass

    def peps_authenticate(self):
        mseeage = self.immo_auth + self.terminator
        return self.user_thread.send_querry(self.uart_node_name,mseeage,blocking=True,optional_params="SEND_MSG_TXT",time_for_timeout=10)


    def send_lf_wakeup(self):
        pass

