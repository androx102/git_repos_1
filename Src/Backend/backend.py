from Backend.backend_classes import *
from Nodes import *
from configparser import ConfigParser



class Backend(QObject):
    def __init__(self,):
        super().__init__()


        #Backend flags
        ####################
        self.simulation_running = False
        self.user_script_running = False
        ####################

        #Backend nodes data
        ####################
        self.user_script = None
        self.nodes_data = []
        self.nodes_list = []
        self.topic_que_dict_class = topic_que_dict_class()
        ####################
       # self.init_backend()
        self.load_nodes_config()
        self.init_nodes()
        self.start_nodes()

        self.init_script()
        self.start_script()

    #Main
    #############################################
    def init_backend(self):
        """Init of main backned components"""
        #self.signal_center = signal_center()
        self.init_message_broker()
        pass

    def init_message_broker(self):
        self.topic_que_dict_class.clear_sub()
        self.message_broker = message_broker(self.QThread_displayer.displayer_queue,self.topic_que_dict_class)
        self.data_model.broker_queue_pointer.clear()
        self.data_model.broker_queue_pointer.append(self.message_broker.message_broker_queue)
        self.message_broker.start()



    #User script start/stop
    #########################################
    def init_script(self):
        """This func is static due to one user script at once"""
        app_cfg_path = Path(__file__).resolve().parent.parent / "app_cfg.ini"
        config_object = ConfigParser()
        config_object.read_file(open(app_cfg_path,"r"))
        us_file_name = config_object.items('Default')[1][1]
        self.user_script = user_script_thread(self.data_model,self.message_broker.message_broker_queue,self.topic_que_dict_class,us_file_name)
        self.user_script.script_ended.connect(lambda: self.set_user_script_flag(False))
        self.user_script.start()


    def start_script(self):
        pass

    def stop_user_script(self):
        self.user_script.stop_process()


        



    #Loading configs
    ##########################################


    def load_nodes_config(self):
        try:
            app_cfg_path = Path(__file__).resolve().parent.parent / "app_cfg.ini"
            config_object = ConfigParser()
            config_object.read_file(open(app_cfg_path,"r"))
            sim_cfg_name = config_object.items('Default')[0][1]

            """This func loads nodes config from ini file"""
            #####################################################
            file_path = Path(__file__).resolve().parent.parent / f"user/configs/{sim_cfg_name}"
            config_object = ConfigParser()
            config_object.read_file(open(file_path,"r"))
            dict_of_obejcts=[]
            sections=config_object.sections()

            for section in sections:
                items=config_object.items(section)
                dict_of_obejcts.append(dict(items))
            #####################################################
            self.nodes_data = dict_of_obejcts
        except Exception as e:
            print(f"Error during loading nodes data: {e}")


    def init_nodes(self):
        self.nodes_list = []
        try:
            for node_data in self.nodes_data:
                match node_data["node_type"]:
                    case "CAN":
                        new_node = Can_node_thread(self.message_broker.message_broker_queue,node_data)
                    case "UART":
                        new_node = UART_node_thread(self.message_broker.message_broker_queue,node_data)
                    case "ETH_socket":
                        new_node = Eth_socket_node_thread(self.message_broker.message_broker_queue,node_data)
                    case "ETH_http":
                        new_node = Eth_http_node_thread(self.message_broker.message_broker_queue,node_data)
                    case "GPIB":
                        new_node = gpib_node_thread(self.message_broker.message_broker_queue,node_data)
                    case "ADB":
                        new_node = ADB_node_thread(self.message_broker.message_broker_queue,node_data)
                    case _:
                        new_node = None
                
                if new_node != None:
                    self.topic_que_dict_class.add_sub({(new_node.name_of_node + "_Tx"):new_node.own_que})
                    self.nodes_list.append(new_node)

        except Exception as e:
            print(f"Error during init_of_nodes: {e}")

    def start_nodes(self):
        pass

    def stop_nodes(self):
        for node in self.nodes_obj_list:
            node.stop_process()


        






