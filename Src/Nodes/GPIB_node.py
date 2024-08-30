from Nodes.nodes_abstract import *


class gpib_node_thread(abstract_node):
    def __init__(self,message_broker_queue:Queue,config:dict):
        super().__init__(message_broker_queue,config)

    def init_configuration(self):
        # set node name used by message broker
        self.name_of_node = self.config["node_name"]
        # set instrument name used by resource manager. Can be found as VISA Resource Name in NI MAX (e.g. 'GPIB0::29::INSTR')
        self.resource_name = self.config["resource_name"] 
        # open pyvisa Resource Manager
        self.rm = pyvisa.ResourceManager()
        # open connection with instrument
        self.instrument = self.rm.open_resource(self.resource_name)

    def create_sub_threads(self): 
        self.manipulator_thread = gpib_node_manipulator_thread(self.own_que,self.instrument)
        self.listener_thread = gpib_node_lisener_thread(self.message_broker_queue,self.instrument,self.name_of_node)

    def end_func(self):
        # close connection with instrument
        #self.instrument.close()
        # close pyvisa Resource Manager
        #self.rm.close()
        pass


class gpib_node_lisener_thread(abstract_node_listener_thread):
    def __init__(self,message_broker_queue, instrument, name_of_node:str): #*args
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.instrument = instrument
        self.name = name_of_node
    
    def main_func(self):
        msg_from_bus = self.instrument.read()
        if msg_from_bus != None:
            msg_to_send = message_(topic=self.name,source=self.name,data=msg_from_bus)
            self.message_broker_queue.put(msg_to_send)


class gpib_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self, node_queue: Queue, instrument): #*args
        super().__init__(node_queue)
        self.instrument = instrument

    def callback_router(self,msg):
        match msg.optional_params:
            case "SEND_MSG":
                self.send_message(msg.data)
                pass
            case _ :
                pass

    def send_message(self,payload_to_send):
        self.instrument.write(payload_to_send)
