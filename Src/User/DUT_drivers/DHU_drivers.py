
class DHU():
    def __init__(self, SCP_name, HKP_name, user_thread):
        self.SCP_name = SCP_name
        self.HKP_name = HKP_name
        self.user_thread = user_thread

    def send_message(self):
        pass

    def HKP_set_pwr_always_on(self, value=1, time_for_timeout=2):
        data_to_send = f"pwr always_on {value}"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.HKP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"HKP pwr always_on set to 1"

    def SCP_dut_enable(self, value="on", time_for_timeout=2):
        data_to_send = f"eecmd WLAN_RF dut_enable {value}"
        response = "command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"
        
    def SCP_antenna_config_set(self, config=0, time_for_timeout=2):
        """
        Set antenna config.

        Parameters:
            mode:
                0 - chain1,
                1 - chain 1,
                3 - 2x2,
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF antenna_config_set {str(config)}"
        response = "eecmd antenna_config_set command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"
        
    def SCP_band_set(self, band=0, time_for_timeout=2):
        """
        Set band.

        Parameters:
            band:
                0 - 5GHz,
                1 - 2.4GHz,
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF band_set {str(band)}"
        response = "eecmd band_set command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"
        
    def SCP_channel_set(self, frequency: int, time_for_timeout=2):
        """
        Set channel.

        Parameters:
            frequency - channel frequency in MHz
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF channel_set {str(frequency)}"
        response = "eecmd channel_set command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"
        
    def SCP_modul_set(self, mode: int, time_for_timeout=2):
        """
        Set modulation.

        Parameters:
            mode:
                1 - TCMD_WLAN_MODE_HT20 (802.11n)
                2 - TCMD_WLAN_MODE_HT40PLUS (802.11n)
                5 - TCMD_WLAN_MODE_VHT20 (802.11ac)
                6 - TCMD_WLAN_MODE_VHT40PLUS (802.11ac)
                8 - TCMD_WLAN_MODE_VHT80_0 (802.11ac)
                9 - TCMD_WLAN_MODE_HE20 (802.11ax)
                10 - TCMD_WLAN_MODE_HE40 (802.11ax)
                11 - TCMD_WLAN_MODE_HE80 (802.11ax)
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF modul_set {str(mode)}"
        response = "eecmd modul_set command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"
        
    def SCP_datarate_set(self, datarate: int, time_for_timeout=2):
        """
        Set datarate.

        Parameters:
            mode:
               15 = MCS0
               26 = MCS11
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF datarate_set {str(datarate)}"
        response = "eecmd datarate_set command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"

    def SCP_tx_output_set(self, power: int, time_for_timeout=2):
        """
        Set TX output power.

        Parameters:
            power:
                8 - 8dBm
                12 - 12dBm
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF tx_output_set {str(power)}"
        response = "eecmd tx_output_set command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"
        
    def SCP_continuous(self, mode: str="on", time_for_timeout=2):
        """
        Set continuous output mode (do not confuse with CW mode).

        Parameters:
            mode:
                "on" - continuous mode on
                "off" - continuous mode off
            time_for_timeout - in seconds

        Details:
            None
        """
        data_to_send = f"eecmd WLAN_RF continous {mode}"
        response = "command successful"
        status, msg = self.user_thread.send_and_wait_for_response(
            self.SCP_name, data_to_send, "SEND_MSG_TXT", time_for_timeout)
        if status != True:
            raise Exception(f"Error during: {data_to_send}")
        else:
            return status, f"Response positive for {data_to_send}"