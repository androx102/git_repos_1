from Nodes.nodes_abstract import *



class UART_node_thread(abstract_node):
    def __init__(self,message_broker_queue:Queue,config:dict):
        super().__init__(message_broker_queue,config)

    def init_configuration(self):
        self.name_of_node = self.config["node_name"]
        self.port = self.config["port"]
        self.baudrate = self.config["baudrate"]
        self.bus = Serial(port=self.port,baudrate=self.baudrate,timeout=0)
        try:
            try:
                self.bus.open()
                return True
            except:
                self.bus.close()
                self.bus.open()
                return True
        except:
            return False

    
    def create_sub_threads(self):
        self.manipulator_thread = UART_node_manipulator_thread(self.own_que,self.bus)
        self.listener_thread = UART_node_listener_thread(self.message_broker_queue,self.bus,self.name_of_node)

    def end_func(self):
        self.bus.close()


class UART_node_listener_thread(abstract_node_listener_thread):
    def __init__(self,message_broker_queue, bus:Serial,name_of_node): #*args
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.bus = bus
        self.name = name_of_node
        self.bus.timeout=None
        
    def main_func(self):
        msg_from_bus = self.bus.readline()
        msg_from_bus = msg_from_bus.decode('utf-8').strip()
        print("received: " + msg_from_bus )
        msg_to_send = message_(topic=self.name,source="UART",data=msg_from_bus)
        self.message_broker_queue.put(msg_to_send)
    


class UART_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self,node_queue: Queue,bus:Serial): #*args
        super().__init__(node_queue)
        self.bus = bus

    def callback_router(self,msg):
        match msg.optional_params:
            
            case "SEND_MSG":
                self.send_message(msg.data)
            case "SEND_MSG_TXT":
                self.send_message_txt(msg.data)
            case _ :
                pass

    def send_message(self,payload_to_send):
        # str= "01 02 03" -> bytes = b"\x01\x02\x03"
        #takes hex string and converts to bytes
        result_bytes = bytes.fromhex(payload_to_send)
        self.bus.write(result_bytes)
    
    def send_message_txt(self,payload_to_send):
        result_bytes = (payload_to_send).encode()
        self.bus.write(result_bytes)
