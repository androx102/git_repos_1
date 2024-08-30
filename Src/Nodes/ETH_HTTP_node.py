from Nodes.nodes_abstract import *


class Eth_http_node_thread(abstract_node):
    def __init__(self, message_broker_queue:Queue, config: dict):
        super().__init__(message_broker_queue,config)

    def init_configuration(self):
        self.name_of_node = self.config["node_name"]
        self.http_server_address = self.config["http_server_address"]
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        try:
            self.httpsConnection = http.HTTPSConnection(self.http_server_address,timeout=5)
            print("ETH_http node: connection to server OK!")
            return True
        except:
            print("ETH_http node: connection to server failed!")
            return False

    def create_sub_threads(self): 
        self.manipulator_thread = eth_http_node_manipulator_thread(self.own_que, self.httpsConnection)
        self.listener_thread = eth_http_node_lisener_thread(self.message_broker_queue, self.httpsConnection, self.name_of_node)

    def end_func(self):
        self.httpsConnection.close()


class eth_http_node_lisener_thread(abstract_node_listener_thread):
    def __init__(self,message_broker_queue, httpsConnection: http.HTTPSConnection, name_of_node: str): #*args
        super().__init__()
        self.message_broker_queue = message_broker_queue
        self.httpsConnection = httpsConnection
        self.name = name_of_node
        
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

    def main_func(self):
        msg_from_bus_raw = self.httpsConnection.getresponse()
        
        if msg_from_bus_raw != None:
            respData = json.loads(msg_from_bus_raw.read())
            msg_to_send = message_(topic=self.name, source=self.name, data=respData)
            self.message_broker_queue.put(msg_to_send)


class eth_http_node_manipulator_thread(abstract_node_manipulator_thread):
    def __init__(self,node_queue: Queue, httpsConnection: http.HTTPConnection):
        super().__init__(node_queue)
        self.httpsConnection = httpsConnection
                
    def callback_router(self,msg):
        self.send_message(payload_to_send=msg)

    def send_message(self,payload_to_send):
        try:
            self.httpsConnection.request('POST', '/jsonrpc', json.dumps(payload_to_send.data))
        except Exception as e:
            print(f"eth_http_node_manipulator_thread: Request Error: {e}")
