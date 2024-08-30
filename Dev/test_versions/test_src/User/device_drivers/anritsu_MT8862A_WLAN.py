from device_drivers.priv_dependencies import *

# ****************************************************************************
#
# This module contains anritsu_mt8862a_wlan() class which implements functions
# to remotely control the Anritsu MT8862A (WLAN) Tester.
#
# Base functions implements basic exchange od SCPI commands i.e. writing
# and quering a given command.
#
# Custom functions use base functions to implement a given functionality
# of the instrument.
#
# BASE FUNCTIONS:
#
#   write() - function to send any SCPI command to the instrument.
#   query() - function to query any given SCPI command from the instrument.
#
# CUSTOM FUNCTIONS:
#
#   load_config_file()         - Load settings from file. The file must
#                                exist in the instrument's internal storage.
#   set_input_power()          - Set the input level power in dBm
#   start_measurement()        - Start measurement.
#   get_measurement_progress() - Query the measurement progress status.
#   get_measurement_status()   - Query the measurement result status.
#   set_channel_number()       - Set the channel number.
#   get_transmitted_power()    - Query the results of transmitted power
#                                measurement.
#   set_out_level()            - Set RF output level.
#   get_measured_PER()         - Query the PER calculated by instrument
#                                during measurement.
#
# Author : Slezak, Maciej
#
# ****************************************************************************


class anritsu_mt8862a_wlan():
    """
    Class anritsu_mt8862a_wlan implements methods to remotely control
    the Anritsu MT8862A (WLAN) instrument.

    Parameters:
        node_name : Name of the interface node used by instrument \n
        user_thread : user thread reference
    """

    def __init__(self, node_name: str, user_thread):
        self.node_name = node_name
        self.user_thread = user_thread
        self.termination = "\r\n"

    def write(self, command: str):
        """
        Use write() function to send any SCPI command to the instrument.

        Parameters:
            command: SCPI command content (without termination)
        """
        # append termination chars to the command
        message = command + self.termination
        # send message
        self.user_thread.send_message(topic=self.node_name, data=message)

    def query(self, command: str, timeout: int):
        """
        Use query() function to query any SCPI command from the instrument.

        Parameters:
            command : SCPI query command content (without termination), \n
            timeout : timeout for waiting for the response in seconds,

        Details:
            Function returns response content (str) if response received. 
            Otherwise returns empty string.
        """
        # set blocking mode
        blocking = True if timeout != None else False
        # Append termination chars to the command
        message = command + self.termination
        # pass query to User Node and get result
        status, response = self.user_thread.send_and_wait_for_response(
            topic=self.node_name, data=message,
            blocking=blocking, time_for_timeout=timeout, termination=self.termination)
        if status:
            # remove termination
            return response[:-len(self.termination)]
        else:
            return ""

    def load_config_file(self, filename: str):
        """
        Load settings from file. The file must exist in the Anritsu internal
        drive.

        Parameters:
            filename: config file name (with extension)
        """
        self.write("PRMRECALLNAME " + "\"" + filename + "\"")

    def set_input_power(self, pwr: str):
        """
        Set the input level power in dBm

        Parameters:
            pwr:
                input power level value in dBm
        """
        self.write("ILVL " + pwr)

    def start_measurement(self):
        """
        Start measurement.

        Parameters:
            ---

        Details:
            Starts RX measurement when in the RX measurement mode. \n
            Starts TX measurement when in the TX measurement mode. \n
            The measurement stops when it is completed or when the ABORT
            command is received.
        """
        self.write("SNGLS")

    def get_measurement_progress(self, timeout: int):
        """
        Get the measurement progress status. 

        Parameters:
            timeout : timeout for response in seconds.
        """
        response = self.query("MPSTAT?", timeout)
        match(response):
            case "0":
                return "IDLE"
            case "1":
                return "PREPARING"
            case "2":
                return "TRIGGER READY"
            case "3":
                return "MEASURING"
            case "4":
                return "MEASUREMENT END"
            case "10":
                return "AUTO LEVELING"
            case "11":
                return "AUTO LEVEL END"
            case _:
                # this will be empty string
                return response

    def get_measurement_status(self, timeout):
        """
        Get the measurement result status. 

        Parameters:
            timeout : timeout for response in seconds.
        """
        response = self.query("MSTAT?", timeout)
        match(response):
            case "0":
                return "MEASUREMENT COMPLETED SUCCESSFULLY"
            case "2":
                return "LEVEL OVER"
            case "4":
                return "HEADER INFORMATION MISMATCH"
            case "5":
                return "CAPTURE INFORMATION ERROR"
            case "9":
                return "MEASUREMENT IN PROGRESS OR NOT MEASURED"
            case "10":
                return "NOT MEASURED DUE TO CALL DISCONNECTION"
            case "12":
                return "TIMEOUT"
            case "15":
                return "CAPTURE OVER FLOW"
            case "16":
                return "SYNCHRONOUS MEASUREMENT FAILED"
            case "17":
                return "DISCONNECTED COMMUNICATIONS BETWEEN PRIMARY AND \
                        SECONDARY MT8862A DURING SYNCHRONOUS MEASUREMENT"
            case "18":
                return "LEVEL RANGE MISMATCH DURING SYNCHRONOUS RX SEARCH MEASUREMENT"
            case _:
                # this will be empty string
                return response

    def set_channel_number(self, channel_number: int):
        """
        Set the channel number. Only primary channel. 

        Parameters:
            channel: Channel number

        Details:
            See CHANNELNUM comand in manual for details regarding channels
            for different WLAN standards.
        """
        self.write("CHANNELNUM " + str(channel_number))

    def get_transmitted_power(self, timeout):
        """
        Get transmitted power [dBm] from finished TRP measurement.

        Parameters:
            timeout : timeout for response in seconds.
        """
        return self.query("MEAS_TP?", timeout)

    def set_out_level(self, level: float):
        """
        Set RF output level.

        Parameters:
            level - output power level in dBm
        """
        self.write("OLVL " + str(level))

    def get_measured_PER(self, timeout):
        """
        Get transmitted PER [%] from finished measurement.

        Parameters:
            timeout : timeout for response in seconds.
        """
        return self.query("MEAS_PER?", timeout)
