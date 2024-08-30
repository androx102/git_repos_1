from nodes_controller import *


x = UART_node_()
x.test()



xx = Nodes_controller()
xx.run()

time.sleep(2)
xx.join()