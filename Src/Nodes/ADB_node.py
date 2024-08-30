from Nodes.nodes_abstract import *

class ADB_node_thread(abstract_node):
    def __init__(self,message_broker_queue:Queue,config:dict):
        super().__init__(message_broker_queue,config)

    def init_configuration(self):
        self.name_of_node = self.config["node_name"]
        self.device_ID = self.config["device_id"]
        self.adbBus = AdbDeviceUsb(serial=self.device_ID)
        try:
            try:
                self.adbBus.connect(self.device_ID)
                print(f"DUT {self.device_ID} connected via ADB!")
                return True
            except:
                self.adbBus.close()
                return True
        except:
            return False
        
    def create_sub_threads(self):
        self.manipulator_thread = ADB_node_manipulator_thread(self.own_que,self.adbBus)
        self.listener_thread = ADB_node_listener_thread(self.message_broker_queue,self.adbBus,self.name_of_node)

    def end_func(self):
        self.adbBus.close()


class ADB_node_listener_thread(abstract_node_listener_thread):
    def __init__(self,message_broker_queue, adbBus,name_of_node): #*args
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.adbBus = adbBus
        self.name = name_of_node
        self.adbBus.timeout=2
        
    def main_func(self):
        msg_from_bus = self.adbBus.read()
        # msg_from_bus = msg_from_bus.decode('utf-8').strip()
        msg_to_send = message_(topic=self.name,source="ADB",data=msg_from_bus)
        self.message_broker_queue.put(msg_to_send)

class ADB_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self,node_queue: Queue,adbBus): #*args
        super().__init__(node_queue)
        self.adbBus = adbBus
        
    def callback_router(self,msg):
        match msg.optional_params:
            case "SEND_MSG":
                self.send_message(msg.data)
            case "SEND_MSG_TXT":
                self.send_message_txt(msg.data)
            case _ :
                pass

    def send_message(self, payload_to_send):
        response=self.adbBus.shell(payload_to_send)
        # print(f"ADB Query: {payload_to_send}")
        # print(f"ADB response: \n{response}")
    
    def send_message_txt(self,payload_to_send):
        response=self.adbBus.shell(payload_to_send)
        print(f"ADB Query: {payload_to_send}")
        print(f"ADB response: \n{response}")