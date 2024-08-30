from Nodes.nodes_abstract import *

# ****************************************************************************
#
# Using pyvisa this node will replace ETH_SOCKET and ETH_HTTP nodes by merging
# their functionalities into one LAN node
#
# Author : Slezak, Maciej
#
# ****************************************************************************


class lan_node_thread(abstract_node):
    def __init__(self, message_broker_queue: Queue, config: dict):
        super().__init__(message_broker_queue, config)

    def init_configuration(self):
        # set node name used by message broker
        self.node_name = self.config["node_name"]
        # set instrument name used by resource manager.
        # It can be found as VISA Resource Name in NI MAX
        # (e.g. 'GPIB0::29::INSTR')
        self.resource_name = self.config["resource_name"]
        # open pyvisa Resource Manager
        self.rm = pyvisa.ResourceManager()
        # open connection with instrument
        self.instrument = self.rm.open_resource(self.resource_name)

    def create_sub_threads(self):
        self.manipulator_thread = lan_node_manipulator_thread(
            self.own_que, self.instrument)
        self.listener_thread = lan_node_lisener_thread(
            self.message_broker_queue, self.instrument, self.node_name)

    def end_func(self):
        # close connection with instrument
        # self.instrument.close()
        # close pyvisa Resource Manager
        # self.rm.close()
        pass


class lan_node_lisener_thread(abstract_node_listener_thread):
    def __init__(self, message_broker_queue, instrument, node_name: str):
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.instrument = instrument
        self.name = node_name

    def main_func(self):
        msg_from_bus = self.instrument.read()
        if msg_from_bus != None:
            msg_to_send = message_(
                topic=self.name, source=self.name, data=msg_from_bus)
            self.message_broker_queue.put(msg_to_send)


class lan_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self, node_queue: Queue, instrument):
        super().__init__(node_queue)
        self.instrument = instrument

    def callback_router(self, msg):
        match msg.optional_params:
            case "SEND_MSG":
                self.send_message(msg.data)
                pass
            case _:
                pass

    def send_message(self, payload_to_send):
        self.instrument.write(payload_to_send)
