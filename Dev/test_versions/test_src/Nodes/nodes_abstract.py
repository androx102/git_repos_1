from Nodes.priv_dependencies import *


class message_():
    def __init__(self,topic:str=None,source:str=None,data=None,optional_params=None):
        self.topic = topic
        self.data = data
        self.source = source
        self.optional_params = optional_params



class abstract_node(QThread):
    script_finished = pyqtSignal()
    def __init__(self, message_broker_queue:Queue, config: dict):
        super().__init__()
        self.own_que = Queue()
        self.message_broker_queue = message_broker_queue
        self.manipulator_thread = None
        self.listener_thread = None
        self.config = config
        self.init_status = self.init_configuration()

    def run(self):
        self.create_sub_threads()
        self.start_sub_threads()

    #Override this with init configuration of node eg. open uart port 
    def init_configuration(self):
        return True
    
    #Define manipulator and listener
    def create_sub_threads(self):
        pass
   
    #override quit behaviour of node eg. close all ports
    def end_func(self):
        pass

    def start_sub_threads(self):
        self.manipulator_thread.start()
        self.listener_thread.start()

    def close_sub_threads(self):
        self.manipulator_thread.stop_process()
        self.listener_thread.stop_process()
        self.manipulator_thread.terminate()
        self.listener_thread.terminate()
        try:
            self.end_func()
        except Exception as e:
            pass

    def stop_process(self):
        self.close_sub_threads()
        self.quit()
        self.terminate()


class abstract_node_listener_thread(QThread):
    def __init__(self):
        super().__init__()
        self.control_flag = [True]
        
    def run(self):
        while True:
            if self.control_flag[0]:
                try:
                    self.main_func()
                except Exception as e:
                    pass
            else:
                break

    #override -> main communication spefific func
    def main_func(self):
        pass

    def stop_process(self):
        self.control_flag[0] = False
        self.quit()


class abstract_node_manipulator_thread(QThread):
    def __init__(self,node_queue:Queue):
        super().__init__()
        self.node_queue = node_queue
        self.control_flag = [True]

    def run(self):
        while self.control_flag[0]:
            try:
                if self.node_queue.empty():
                    time.sleep(0.001)
                else:
                    try:
                        self.callback_router(self.node_queue.get())
                    except Exception as e:
                        pass
            except Exception as e:
                pass

    #Override for different options in sending data out
    def callback_router(self,msg):
        pass

    def stop_process(self):
        self.control_flag[0] = False
        self.quit()