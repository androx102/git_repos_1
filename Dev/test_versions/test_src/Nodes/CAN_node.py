from Nodes.nodes_abstract import *


class Can_node_thread(abstract_node):
    def __init__(self,message_broker_queue:Queue,config:dict):
        super().__init__(message_broker_queue,config)

    def init_configuration(self):
        self.name_of_node = self.config["node_name"]
        self.channel = self.config["channel"]
        self.bus = interface.Bus(bustype='vector', channel=self.channel, bitrate=500000, app_name='pycan')

    def create_sub_threads(self): 
        self.manipulator_thread = can_node_manipulator_thread(self.own_que,self.bus)
        self.listener_thread = can_node_lisener_thread(self.message_broker_queue,self.bus,self.name_of_node)

    def end_func(self):
        self.bus.shutdown()


class can_node_lisener_thread(abstract_node_listener_thread):
    def __init__(self,message_broker_queue, bus,name_of_node:str): #*args
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.bus = bus
        self.name = name_of_node
    
    def main_func(self):
        msg_from_bus = self.bus.recv(1)
        if msg_from_bus != None:
            msg_to_send = message_(topic=self.name,source="CAN",data=str(msg_from_bus))
            self.message_broker_queue.put(msg_to_send)


class can_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self,node_queue: Queue,bus): #*args
        super().__init__(node_queue)
        self.bus = bus

    def callback_router(self,msg):
        match msg.optional_params:
            case "SEND_MSG":
                self.send_message(msg.data)
                pass
            case _ :
                pass

    def send_message(self,payload_to_send):
        self.bus.send(payload_to_send)
