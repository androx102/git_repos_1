from backend import *




#config
script_execution = "Host_based"
data_output = "File_logging"
control_type = "shell"


back = PT_Backend()
back.backend_init()
back.start_simulation_execution()

while True:
    time.sleep(1)