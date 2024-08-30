
import multiprocessing
import mqttools


class UART_node_(multiprocessing.Process):
    def __init__(self,config_):
        super().__init__()
        self.config_ = config_

    def run(self):
        pass

    def init_connection_with_broker(self):
        pass
    
    def init_uart(self):
        pass

    def test(self):
        print("test")