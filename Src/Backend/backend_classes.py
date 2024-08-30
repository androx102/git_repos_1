from GUI.panels import *


class message_broker(QThread):
    def __init__(self,topic_que_dict_class): 
        super().__init__()
        self.control_flag = [True]
        self.message_broker_queue = Queue()


        self.topic_que_dict_class = topic_que_dict_class
    
    def run(self):
        #debugpy.debug_this_thread()
        while self.control_flag[0]:
            try:
                if self.message_broker_queue.empty():
                    time.sleep(0.001)
                else:
                    msg_ = self.message_broker_queue.get()
                    try: 
                        if self.topic_que_dict_class.topic_que_dict.get(msg_.topic):
                            for subscriber_queue in self.topic_que_dict_class.topic_que_dict[msg_.topic]:
                                subscriber_queue.put(msg_)



                    except Exception as e:
                        print(f"Msg broker, sending error: {e}")
            except Exception as e:
                print(f"Msg broker error: {e}")

    def stop_process(self):
        self.control_flag[0] = False
        self.quit()
        self.terminate()





 

class signal_center():
    def __init__(self,backend):
        self.backend = backend


    def callback_router(self,id):
        match id:
            case 11:
                self.backend.Backend_start_simulation()
            case 12:
                self.backend.stop_simulation()
            case 13:
                self.backend.start_user_script()
            case 14:
                self.backend.stop_user_script()
