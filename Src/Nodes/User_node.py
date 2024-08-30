from Nodes.nodes_abstract import *
import csv
import time
from User.private_libraries import *

#User script 
###################################################################################
class user_script_thread(abstract_node):
    script_ended = pyqtSignal()
    def __init__(self,data_model,message_broker_queue:Queue,topic_que_dict_class,us_file_name):
        super().__init__(message_broker_queue,None)
        self.name = "User_script"
        self.data_model = data_model
        self.topic_que_dict_class = topic_que_dict_class
        self.us_file_name = us_file_name

    def create_sub_threads(self):
        self.us_buffer_handler = US_message_buffer()
        self.manipulator_thread = user_script_receiver_thread(self.own_que,self.us_buffer_handler)
        self.listener_thread = user_script_main_thread(self.data_model,self.message_broker_queue,self.name,self.own_que,self.manipulator_thread,self.topic_que_dict_class,self.us_buffer_handler,self.us_file_name)
        self.listener_thread.script_finished.connect(self.stop_process)
        self.listener_thread.update_sub.connect(self.update_sub)

    def update_sub(self,topic:str,flag:bool):
        self.add_sub.emit(topic,flag)

    def end_func(self):
        self.script_ended.emit()



class user_script_receiver_thread(abstract_node_manipulator_thread):
    def __init__(self,user_script_queue: Queue,US_message_buffer):
        super().__init__(user_script_queue)
        self.US_message_buffer = US_message_buffer

    def callback_router(self,msg):
        self.route_msg_to_buffer(msg)


    def route_msg_to_buffer(self,msg):
        if self.US_message_buffer.buffer_topic_que_dict.get(msg.topic):
            self.US_message_buffer.buffer_topic_que_dict[msg.topic].put(msg.data)




class user_script_main_thread(abstract_node_listener_thread):
    
    script_finished = pyqtSignal()
    update_sub = pyqtSignal(str,int)
    def __init__(self,data_model,message_broker_queue:Queue,name:str,queue_:Queue,us_receiver,topic_que_dict_class,us_buffer_handler,us_file_name):
        super().__init__()
        self.name = name
        self.us_queue = queue_
        self.us_receiver = us_receiver
        self.message_broker_queue = message_broker_queue
        self.data_model = data_model
        self.topic_que_dict_class = topic_que_dict_class
        self.us_buffer_handler = us_buffer_handler
        self.us_file_name = us_file_name

    #################################################################################################
    def run(self):
        try:
            import sys
            sys.path.append(str(Path(__file__).resolve().parent.parent / "User"))
            file_path = Path(__file__).resolve().parent.parent / f"User/scripts/{self.us_file_name}"
            with open(file_path) as file_handler:
                file_content = file_handler.read()
            exec(file_content,globals(),{"User_thread_mock":self})

        except Exception as e:
            print(traceback.format_exc())
        finally:
            self.script_finished.emit()
    #################################################################################################




    #API
    #################################################################################################    
    def add_sub(self,topic:str):
        self.topic_que_dict_class.add_sub({(topic):self.us_queue})
        self.us_buffer_handler.add_buffer(topic)


    def del_sub(self,topic:str):
        self.topic_que_dict_class.del_sub({(topic):self.us_queue})
        self.us_buffer_handler.del_buffer(topic)


    def send_message(self,topic:str,data,optional_params="SEND_MSG"):
        msg = message_(topic=(topic+"_Tx"),source=self.name,data=data,optional_params=optional_params)
        self.message_broker_queue.put(msg)


    def send_querry(self,topic:str,data,optional_params="SEND_MSG",time_for_timeout=None,blocking=False,data_to_search=None):
        self.clear_queue(topic=topic)
        self.send_message(topic=topic,data=data,optional_params=optional_params)
        return self.read_message(topic=topic,time_for_timeout=time_for_timeout,blocking=blocking,data_to_search=data_to_search)


    def read_message(self,topic,time_for_timeout=None,blocking=False,data_to_search=None):
        if time_for_timeout == None:
            time.sleep(0.01)
            status, response = self.read_message_from_buffer(topic=topic,blocking=blocking,data_to_search=data_to_search)
        else:
            status, response = self.response_timer(self.read_message_from_buffer,topic=topic,data_to_search=data_to_search,time_for_timeout=time_for_timeout)
        return status, response 

    #################################################################################################


    #Supporting functions
    def read_message_from_buffer(self,topic:str,blocking=False,data_to_search=None):
        if data_to_search == None:
            try:
                message = self.us_buffer_handler.buffer_topic_que_dict[topic].get(blocking)
                status = True
            except:
                status = False
                message = "Empty"
            finally:

                return status, message
        else:
            while True:
                try:
                    last_message = self.us_buffer_handler.buffer_topic_que_dict[topic].get(blocking)
                    if data_to_search in last_message:
                        return True,last_message
                except:
                    return False, "Empty"


    def response_timer(self,func_to_run,topic,data_to_search,time_for_timeout):
        class timer_thread(Thread):
            def __init__(self,func_to_run,topic,data_to_search):
                super().__init__()
                self.run_flag = [True]
                self.status = False
                self.response = "Empty"
                self.func_to_run = func_to_run
                self.topic = topic
                self.data_to_search = data_to_search

            def run(self):
                while self.run_flag[0]:
                    time.sleep(0.3)
                    self.status, self.response = self.func_to_run(topic = self.topic,data_to_search = self.data_to_search) 
                    if self.status:
                        self.run_flag[0] = False
                        break

            def toggle_flag(self):
                self.run_flag[0] = False
            
            def results(self):
                return self.status, self.response

        timer_instance = timer_thread(func_to_run,topic,data_to_search)
        timer_instance.start()
        timer_instance.join(timeout=time_for_timeout)
        timer_instance.toggle_flag()
        status, result = timer_instance.results()
        return status, result


    def clear_queue(self,topic): 
        try:
            while True:
                self.us_buffer_handler.buffer_topic_que_dict[topic].get_nowait()
        except Exception:
            pass


##################################################################################################
class US_message_buffer():
    def __init__(self):
        self.buffer_topic_que_dict = {}

    def add_buffer(self,topic):
        if not self.buffer_topic_que_dict.get(topic):
            self.buffer_topic_que_dict[topic] = Queue()
        
    def del_buffer(self,topic):
        if self.buffer_topic_que_dict.get(topic):
            self.buffer_topic_que_dict.pop(topic, None)








