import asyncio
import time
import mqttools
from nodes_controller.UART_node import *
import threading

class Nodes_controller(threading.Thread):
    def __init__(self):
        super().__init__()
        self.broker_data = None
        self.nodes_config = None
        self.nodes_list = []
        self.controller_state = False

        self.avaliable_nodes = {
            "UART":UART_node_,
            "ETH_socket":2,
            "ETH_HTTP":3
        }

    #####################################
    def run(self):
        self.test_node = self.avaliable_nodes["UART"]()
        self.test_node.test()
        #self.init_nodes()
        #self.start_nodes()

    def stop_controller(self):
        self.join()
        pass
    
    def set_config(self,broker_data,nodes_config):
        self.broker_data = broker_data
        self.nodes_config = nodes_config
    #####################################

    def init_nodes(self):
        """Init of nodes according to config"""
        #print("Starting nodes controller")
        pass

    def start_nodes(self):
        """Starting of nodes"""
        pass

    def stop_nodes(self):
        pass
    
    def test_func(self):
        pass




