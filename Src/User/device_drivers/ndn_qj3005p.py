from device_drivers.priv_dependencies import *


class QJ3005P():    
    def __init__(self, UART_name, user_thread:User_thread):
        self.UART_name = UART_name
        self.user_thread = user_thread
        
    def write(self, command:str):
        message = command + '\\\\n'
        self.user_thread.send_message(self.UART_name, message)
    
    def query(self, command:str, timeout:int=10):
        message = command + '\\\\n'
        status, response=self.user_thread.send_and_wait_for_response(self.UART_name, message, blocking=True, optional_params='SEND_MSG_TXT', time_for_timeout=timeout)
        print("PowerSupply Query: " + message)
        print("PowerSupply Response: ", response)
