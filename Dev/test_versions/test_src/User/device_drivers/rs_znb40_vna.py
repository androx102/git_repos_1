from device_drivers.priv_dependencies import *

# ****************************************************************************
#
# This module contains rs_znb40_vna() class which implements functions
# to remotely control the Rohde&Schwarz ZNB40 Vector Networ Analyzer.
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
#   N/A
#
# Author : Slezak, Maciej
#
# ****************************************************************************


class rs_znb40_vna():
    """
    Class rs_znb40_vna implements methods to remotely control
    the Rohde&Schwarz ZNB40 Vector Networ Analyzer.

    Parameters:
        lan_node_name : Name of the LAN node used by instrument \n
        user_thread : user thread reference
    """

    def __init__(self, lan_node_name: str, user_thread):
        self.node_name = lan_node_name
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
