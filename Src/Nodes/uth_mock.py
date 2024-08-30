
class User_thread_mock():
    @staticmethod
    def add_sub(topic:str):
        print(f"Added sub on {topic}")
    
    @staticmethod
    def del_sub( topic:str):
        print(f"Removed sub from {topic}")

    @staticmethod
    def send_message(topic:str,data:str,optional_params="SEND_MSG"):
        pass
    
    @staticmethod
    def send_querry(topic:str,data:str,optional_params="SEND_MSG",time_for_timeout=None,blocking=False,data_to_search=None):
        pass

    @staticmethod
    def read_message(topic:str,time_for_timeout=None,blocking=False,data_to_search=None):
        pass