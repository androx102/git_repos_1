from mqtt_controller import *
from nodes_controller import *

class PT_Backend():
    def __init__(self):
        self.mqtt_broker_controller = None
        self.nodes_controller = None
        self.log_controller = None
        self.script_controller = None


    def backend_init(self):
        self.init_MQTT_controller()
        self.init_nodes_controller()
        #self.init_log_controller(0)
        #self.init_script_controller()
        
    def start_simulation_execution(self):
        self.start_MQTT_controller('localhost')
        self.start_nodes_controller(0)
        #self.start_log_controller()

    def stop_simulation_execution(self):
        self.stop_nodes_controller()
        self.stop_MQTT_controller()
        #self.stop_log_controller()

    def start_script_execution(self):
        #self.start_script_controller()
        pass

    def stop_script_execution(self):
        #self.stop_script_controller()
        pass
    
    #########################################################
    def init_MQTT_controller(self):
        """Init internal MQTT broker for communication with nodes"""
        #Config input - (ip,port) or "ip"
        self.mqtt_broker_controller = MQTT_broker_controller()

    def start_MQTT_controller(self,_config):
        if self.mqtt_broker_controller != None:
            self.mqtt_broker_controller.set_config(_config)
            self.mqtt_broker_controller.start()
        else:
            print("Mqtt broker not initialized")

    def stop_MQTT_controller(self):
        if self.mqtt_broker_controller != None:
            self.mqtt_broker_controller.stop_controller()
        else:
            print("Mqtt broker not initialized")
  


    #########################################################
    def init_nodes_controller(self):
        """Init of nodes_controller"""
        self.nodes_controller = Nodes_controller()

    def start_nodes_controller(self,_config):
        if self.nodes_controller != None:
            self.nodes_controller.set_config(_config,0)
            self.nodes_controller.start()
        else:
            print("Nodes controller not initialized")

    def stop_nodes_controller(self):
        if self.nodes_controller != None:
            self.nodes_controller.stop_controller()
        else:
            print("Nodes controller not initialized")
    

    #########################################################
    def init_script_controller(self,_config):
        """Init of script controller"""
        pass

    def start_script_controller(self):
        pass

    def stop_script_controller(self):
        pass    

    #########################################################
    def init_log_controller(self,_config):
        """Init of logg controller"""
        #
        pass

    def start_log_controller(self):
        pass

    def stop_log_controller(self):
        pass