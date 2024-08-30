import os

class IHU():
    def __init__(self, VIP_name, SOC_name, ADB_name, user_thread):
        self.VIP_name = VIP_name
        self.SOC_name = SOC_name
        self.ADB_name = ADB_name
        self.user_thread = user_thread

    def send_vip(self, command):
        status, msg=self.user_thread.send_and_wait_for_response(
            self.VIP_name, command, "SEND_MSG_TXT", time_for_timeout=2)
        print("VIP query: ", status)
        print("VIP response:" + msg)
    
    def send_soc(self, command):
        status, msg=self.user_thread.send_and_wait_for_response(
            self.SOC_name, command, "SEND_MSG", time_for_timeout=2)
        print("SOC query: ", status)
        print("SOC response:" + msg)
        
    def send_adb(self, command):
        status, msg=self.user_thread.send_and_wait_for_response(
            self.ADB_name, data=command, optional_params='SEND_MSG_TXT', time_for_timeout=2)
        print("ADB query: ", status)
        print("ADB response:" + msg)
        
    def IHU_set_pwr_always_on(self, value=1, time_for_timeout=2):
        data_to_send = f"pwr always_on {value}"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.VIP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"IHU pwr always_on set to 1"