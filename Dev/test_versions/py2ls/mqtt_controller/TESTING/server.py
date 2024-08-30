import asyncio
import time
import mqttools


class MQTT_broker_controller():
    def __init__(self,broker_ip,broker_port = 1883) -> None:
        """Tu narazie jest ścernisko, ale będzie... MQTT broker"""
        self.broker_port = broker_port
        self.broker_ip = broker_ip
        self.broker = None
        self.controller_state = False

    def start_controller(self):
        try:
            self.broker = mqttools.BrokerThread((self.broker_ip,self.broker_port))
            self.broker.start()
            self.controller_state = True
            print(f"MQTT broker started sucesfully on: {self.broker_ip}:{self.broker_port}")
        except Exception as e:
            print(f"Failed to start MQTT broker due to: {e}")
            self.broker = None
            self.controller_state = False

    def stop_controller(self):
        if not self.controller_state:
            print("MQTT broker not running")
        else:
            self.broker.stop()
            self.broker = None
            self.controller_state = False
            print("MQTT broker turned off")

    def run_diagnostics(self):
        pass

    def stop_diagnostics(self):
        pass



#Test of broker
if __name__ == '__main__':
    x = MQTT_broker_controller('localhost')
    x.start_controller()
    while True:
        time.sleep(10)
