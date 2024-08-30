from device_drivers.priv_dependencies import *

# ****************************************************************************
#
# This module contains anritsu_mt8812b_bt() class which implements functions
# to remotely control the Anritsu MT8812B (BT) Tester.
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
#   configure_ms_test() - Configure instrument to perfom 
#                         Multislot Sensitivity test.
#
# Author : Slezak, Maciej
#
# ****************************************************************************


class anritsu_mt8812b_bt():
    """
    Class anritsu_mt8812b_bt implements methods to remotely control
    the Anritsu MT8812B (BT) instrument.

    Parameters:
        gpib_node_name : Name of the GPIB node used by instrument \n
        user_thread : user thread reference
    """

    def __init__(self, gpib_node_name: str, user_thread):
        self.node_name = gpib_node_name
        self.user_thread = user_thread
        self.termination = "\n"

    def write(self, command: str):
        """
        Use write() function to send any SCPI command to the instrument.

        Parameters:
            command : SCPI message content (without termination)
        """
        # append termination chars to the command
        message = command + self.termination
        # send message
        self.user_thread.send_message(topic=self.node_name, data=message)

    def query(self, command: str, timeout: int):
        """
        Use query() function to query any SCPI command from the instrument.

        Parameters:
            command : SCPI query command content (without termination) \n
            timeout : timeout for waiting for the response in seconds
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

    def configure_ms_test(self, power: float, frequency: float,
                          packets_number: int = 10000):
        """
        Parameters:
            power : power level [dBm] at witch sensitivity will be
            measured \n
            frequency : frequency in GHz \n
            packets_number : number of packets for witch PER will be
            calculated.
        """
        command_list = [
            "*CLS",
            "SYSCFG EUTSRCE,INQUIRY",
            "SYSCFG CONFIG,RANGE,AUTO",
            "SYSCFG INQSET,NAME,ON",
            "SCPTSEL 3",
            "PATHOFF 3,OFF",
            "TXPWR 3,-30.0",
            "OPMD STEST,MS"
            "SCRIPTMODE 3,STANDARD",
            "SCPTCFG 3,ALLTSTS,OFF",
            "SCPTCFG 3,MS,ON",
            f"MSCFG 3,NUMPKTS,{packets_number}",
            f"MSCFG 3,TXPWR,{power}",
            "MSCFG 3,PKTCOUNT,TX",
            "MSCFG 3,PKTTYPE,LONG",
            "MSCFG 3,HOPPING,HOPOFF",
            "MSCFG 3,DIRTYTX,OFF",
            "MSCFG 3,LFREQSEL,OFF",
            "MSCFG 3,MFREQSEL,ON",
            "MSCFG 3,HFREQSEL,OFF",
            f"MSCFG 3,MTXFREQ,FREQ,{frequency}e+009",
            f"MSCFG 3,MRXFREQ,FREQ,{frequency}e+009"
        ]

        for command in command_list:
            status = self.query(command+";*ESR?")
            print(f"COMMAND: {command} ; STATUS: {status}")
