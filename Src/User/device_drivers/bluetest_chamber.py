from device_drivers.priv_dependencies import *


class bluetest_chamber():
    def __init__(self,eth_node_name:str,user_thread:User_thread):
        self.eth_node_name = eth_node_name
        self.user_thread = user_thread
        self.sessionID = None
        self.counter = 1

    def login(self,login: str,password:str,timeout=10):
        if timeout != None:
            blocking = True
        else:
            blocking = False
        auth_method = {
            "jsonrpc": "2.0",
            "method": "System.Users.Authenticate",
            "params": {
                "userID": login,
                "password": password
            },
            "id": 3000
        }
        status, response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,auth_method,blocking=blocking,time_for_timeout=timeout)
        if status:
            try:
                self.sessionID = response_from_chamber["result"]["sessionID"]
                print(response_from_chamber)
                print("SessionID: "+self.sessionID)
                return True, "Auth possitive"
            except:
                to_return = response_from_chamber["error"]["message"]
                return False, "Auth failed"
        else:
            print(response_from_chamber)
            return False, response_from_chamber
            

        
    def Stirring_Stepped_NextPos(self,timeout=10):
        if timeout != None:
            blocking = True
        else:
            blocking = False
        message = {
            "jsonrpc": "2.0",
            "method": "CEM.ExecuteCommand",
            "params": {
                "arguments":{},
                "command":"STEPPED_MODE_STIRRING_NEXT_POS",
                "sessionID": self.sessionID
            },
            "id":3001
        }
        status, response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,message,blocking=blocking,time_for_timeout=timeout)
        if status:
            try:
                #print(response_from_chamber["result"])
                print(response_from_chamber)
                return True, response_from_chamber["result"]
            except:
                print(response_from_chamber["error"]["message"])
                print(response_from_chamber)
                return False, response_from_chamber["error"]["message"]
                
        else:
            print(response_from_chamber)
            return False, response_from_chamber


    def Stirring_Stepped_Configure(self,timeout=1, positions=24):
        if timeout != None:
            blocking = True
        else:
            blocking = False
        message = {
            "jsonrpc": "2.0",
            "method": "CEM.ExecuteCommand",
            "params": {
                "arguments":{
                    "algorithm_stepped_settings":"",
                    "number_of_mode_positions":positions,
                    "enable_antenna_switching":False
                },
                "command":"METHOD",
                "sessionID": self.sessionID
            },
            "id":3002
        }

        status, response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,message,blocking=blocking,time_for_timeout=timeout)
        if status:
            try:
                print(response_from_chamber["result"])
                return True, response_from_chamber["result"]
            except:
                print(response_from_chamber["error"]["message"])
                return False, response_from_chamber["error"]["message"]
                
        else:
            print(response_from_chamber)
            return False, response_from_chamber
        

    def Stirring_Stepped_Init(self,timeout=1):
        if timeout != None:
            blocking = True
        else:
            blocking = False
        message = {
            "jsonrpc": "2.0",
            "method": "CEM.ExecuteCommand",
            "params": {
                "arguments":{},
                "command":"STEPPED_MODE_STIRRING_INIT",
                "sessionID": self.sessionID
            },
            "id":3003
        }
        
        status, response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,message,blocking=blocking,time_for_timeout=timeout)
        if status:
            try:
                print(response_from_chamber["result"])
                return True, response_from_chamber["result"]
            except:
                print(response_from_chamber["error"]["message"])
                return False, response_from_chamber["error"]["message"]
                
        else:
            print(response_from_chamber)
            return False, response_from_chamber
        

    def GetPositionStirrer(self,timeout=1):
        if timeout != None:
            blocking = True
        else:
            blocking = False
        message = {
            "jsonrpc": "2.0",
            "method": "CEM.ExecuteCommand",
            "params": {
                "arguments":{
                    "address":0
                },
                "command":"MANUAL_MODE_STIRRING_GET_POS_M",
                "sessionID": self.sessionID
            },  
            "id":3004
        }

        status, response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,message,blocking=blocking,time_for_timeout=timeout)
        if status:
            try:
                print(response_from_chamber["result"])
                position = response_from_chamber["result"]["arguments"]["position"]
                step = response_from_chamber["result"]["arguments"]["step"]
                return True, position, step
            except:
                print(response_from_chamber["error"]["message"])
                return False, "NA", "NA" #response_from_chamber["error"]["message"]
                
        else:
            print(response_from_chamber)
            return False, "NA", "NA" #response_from_chamber

    def GetPositionTurntable(self,timeout=1):
        if timeout != None:
            blocking = True
        else:
            blocking = False
        message = {
            "jsonrpc": "2.0",
            "method": "CEM.ExecuteCommand",
            "params": {
                "arguments":{
                    "address":1
                },
                "command":"MANUAL_MODE_STIRRING_GET_POS_M",
                "sessionID": self.sessionID
            },
            "id":3005
        }

        status, response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,message,blocking=blocking,time_for_timeout=timeout)
        if status:
            try:
                print(response_from_chamber["result"])
                position = response_from_chamber["result"]["arguments"]["position"]
                step = response_from_chamber["result"]["arguments"]["step"]
                return True, position, step
            except:
                print(response_from_chamber["error"]["message"])
                return False, "NA", "NA" #response_from_chamber["error"]["message"]
                
        else:
            print(response_from_chamber)
            return False, "NA", "NA"        
            
    
    def get_api_version(self,timeout):
        is_logged, blocking = self.init_message(timeout=timeout)
        if is_logged == False:
            return False, "user not logged"
        message = {"jsonrpc": "2.0",
                "method": "JSONRPC.Version",
                "params": {},
                "id": 1}
        response_from_chamber = self.user_thread.send_and_wait_for_response(self.eth_node_name,message,blocking=blocking,time_for_timeout=timeout)
        return self.return_results(response_from_chamber)

        
    def init_message(self,timeout):
        if self.sessionID == None:
            to_ret_1 = False
        else:
            to_ret_1 = True
        if timeout != None:
            to_ret_2 = True
        else:
            to_ret_2 = False

        return to_ret_1,to_ret_2


        
