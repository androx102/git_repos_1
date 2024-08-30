from Nodes.nodes_abstract import *


class Eth_socket_node_thread(abstract_node):
    def __init__(self, message_broker_queue:Queue, config:dict):
        super().__init__(message_broker_queue,config)

    def init_configuration(self):
        self.name_of_node = self.config["node_name"]
        self.socket_server_address = self.config["socket_server_address"]
        self.socket_server_port = int(self.config["socket_server_port"])
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.socket_server_address, self.socket_server_port))
            return True
        except:
            print("ETH_socket node: connection to server failed!")
            return False

    def create_sub_threads(self): 
        self.manipulator_thread = eth_socket_node_manipulator_thread(self.own_que,self.socket)
        self.listener_thread = eth_socket_node_lisener_thread(self.message_broker_queue,self.socket,self.name_of_node)

    def end_func(self):
        print("closing use_script")
        self.socket.close()


class eth_socket_node_lisener_thread(abstract_node_listener_thread):
    def __init__(self,message_broker_queue, socket: socket, name_of_node:str): #*args
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.socket = socket
        self.name = name_of_node

    def main_func(self):
        msg_from_bus = self.socket.recv(1024).decode()
        if msg_from_bus != None:
            msg_to_send = message_(topic=self.name,source=self.name,data=msg_from_bus)
            self.message_broker_queue.put(msg_to_send)


class eth_socket_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self,node_queue: Queue, socket: socket): #*args
        super().__init__(node_queue)
        self.socket = socket

    def callback_router(self,msg):
        self.send_message(msg)

    def send_message(self,payload_to_send):
        try:
            self.socket.sendall(payload_to_send.data.encode())
        except:
            print("eth_socket_node_mainpulator_thread: sendall Error!")

