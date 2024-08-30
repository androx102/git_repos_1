import asyncio
import time
import mqttools
import multiprocessing
import threading

class MQTT_broker_controller(threading.Thread):
    def __init__(self):
        super().__init__()
        """Tu narazie jest ścernisko, ale będzie... MQTT broker"""
        self.broker_port = None
        self.broker_ip = None
        self.broker = None
        self.controller_state = False

    def run(self):
        if self.broker_ip == None:
            print("Broker not configured")
            self.join()
        try:
            self.broker = mqttools.BrokerThread((self.broker_ip,self.broker_port))
            self.broker.start()
            self.controller_state = True
            print(f"MQTT broker started sucesfully on: {self.broker_ip}:{self.broker_port}")
        except Exception as e:
            print(f"Failed to start MQTT broker due to: {e}")
            self.broker = None
            self.controller_state = False

    
    def set_config(self,broker_ip,broker_port = 1883):
        self.broker_ip = broker_ip
        self.broker_port = broker_port


    def stop_controller(self):
        if not self.controller_state:
            print("MQTT broker not running")
        else:
            self.broker.stop()
            self.broker = None
            self.controller_state = False
            self.join()
            print("MQTT broker turned off")



#Test of broker
if __name__ == '__main__':
    x = MQTT_broker_controller()
    x.set_config('localhost')
    x.start()
    while True:
        time.sleep(1)
    x.join()
