# ****************************************************************************
# * Test sequence for DHU WLAN TIS
# ****************************************************************************


#static imports - importing Device drivers ect
from DUT_drivers import * 
from device_drivers import *
from private_libraries import *
import csv

#dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock

################## USER CODE BEGINS HERE ######################


# auxiliary function ******************************************

def insert_results_to_dict(data_to_log: dict, meas_result: str):
    data_to_log_keys_list = list(data_to_log.keys())
    meas_result_dict_keys = data_to_log_keys_list[data_to_log_keys_list.index("Validity"):data_to_log_keys_list.index("Packets Sent")+1]
    meas_result_dict_values = meas_result.split(";")
    meas_result_dict = dict(zip(meas_result_dict_keys,meas_result_dict_values))
    data_to_log.update(meas_result_dict)
    return data_to_log

print("User script started")

# assign devices to nodes *************************************
self.add_sub("Anritsu"         )
self.add_sub("Bluetest_chamber")
self.add_sub("HKP"             )
self.add_sub("SCP"             )

# create dict for logged data *********************************
data_to_log = {
    "Stirrer Step"      : str,
    "Stirrer Position"  : str,
    "Turntable Step"    : str,
    "Turntable Position": str,
    "Power Level"       : str,
    "Validity"          : str,
    "PER"               : str,
    "ACKs Received"     : str,
    "Packets Sent"      : str,
    "Measurement Status": str
}

# set test parameters *****************************************
POS_COMBINATIONS = 4
MAX_PER         = 95.0

# create instruments objects **********************************
anritsu  = AnritsuMT8862AWLAN("Anritsu", self)
bluetest = bluetest_chamber("Bluetest_chamber", self)
dhu      = DHU("SCP", "HKP", self)
          
# initialize instruments **************************************

# Anritsu
# loading conf file to the Anritsu is done manually 

# Bluetest
bluetest.login("root", "aptiv", 10)     
bluetest.Stirring_Stepped_Configure(timeout=10, positions=POS_COMBINATIONS)
print("Setting Bluetest turntable to HOME position")
bluetest.Stirring_Stepped_Init(timeout=20)
print("Turntable reached HOME position")

# DHU
# TODO

# create csv file for logging *********************************

# TODO
filename = "DHU_WLAN_TIS_Hybrid_BT_CH40"+"_"+str(time.strftime("%Y%m%d%H%M%S"))+".csv"
csvfile = open(filename, mode='a', newline='')
print("Created file: "+filename)
csvwriter = csv.writer(csvfile, delimiter=';',
    quotechar='"', quoting=csv.QUOTE_MINIMAL)
csvwriter.writerow(list(data_to_log.keys())) # write column headers

# test sequence main loop *************************************
for pos in range(POS_COMBINATIONS):

    # log Bluetest position
    while True:
        stirrer_status, stirrer_position, stirrer_step = bluetest.GetPositionStirrer(timeout=4)
        print(stirrer_status)
        if(True == stirrer_status):
            break; 
        time.sleep(0.1) #0.5
    # while end
    data_to_log["Stirrer Position"] = str(stirrer_position).replace(".",",")
    data_to_log["Stirrer Step"] = stirrer_step
    #time.sleep(0.1)
    while True:
        turntable_status, turntable_position, turntable_step = bluetest.GetPositionTurntable(timeout=4)
        print(turntable_status)
        if(True == turntable_status):
            break; 
        time.sleep(0.1) #0.5
    # while end
    data_to_log["Turntable Position"] = str(turntable_position).replace(".",",")
    data_to_log["Turntable Step"] = turntable_step

    # initialize variables
    wlan_power_level = 0.0
    meas_end_flag    = 0
    last_PER         = 0.0

    # perform sensitivity measurement in Anritsu
    while last_PER < MAX_PER:
    
        # set WLAN power level
        anritsu.set_out_level(wlan_power_level)
        data_to_log["Power Level"] = str(wlan_power_level).replace(".",",")

        # trigger measurement
        anritsu.start_measurement()
        print(f"Sensitivity measurement started for {wlan_power_level} dBm")
        meas_start_time = time.time()
        while(meas_end_flag == 0):
            progress = anritsu.query_measurement_progress(5)
            print(f"Measurement progress: {progress}")
            if progress == "MEASUREMENT END":
                print(f"Sensitivity measurement finished for {wlan_power_level} dBm")
                meas_end_flag = 1
            else:
                meas_time = time.time()-meas_start_time
                if meas_time > 60:
                    print(f"Sensitivity measurement aborted for {wlan_power_level} dBm due to timeout")
                    meas_end_flag = 1 
            time.sleep(0.5) #0.5     
        # while end

        # log sensitivity measurement results
        meas_status = anritsu.query_measurement_status(timeout=5)
        print(f"Sensitivity measurement status: {meas_status}")
        data_to_log["Measurement Status"] = meas_status
        meas_result = anritsu.query_meas_PER(timeout=5)
        meas_result = meas_result.replace(",",";")
        meas_result = meas_result.replace(".",",")
        data_to_log = insert_results_to_dict(data_to_log, meas_result)
        csvwriter.writerow(list(data_to_log.values()))

        # update variables
        last_PER = float(data_to_log["PER"].replace(",","."))
        print(f"last_PER: {last_PER}")
        wlan_power_level = wlan_power_level - 1.0
        meas_end_flag = 0
    # while end
       
    # set next Bluetest position
    if (stirrer_step) < ((POS_COMBINATIONS)-1):
        index = 0
        while True:
            chamber_status, chamber_result = bluetest.Stirring_Stepped_NextPos(20) #important timeout -> it is blocking function and it takes as long as rotation lasts
            index = index+1
            print("index = "+str(index))
            while True:
                stirrer_status, stirrer_position, stirrer_step = bluetest.GetPositionStirrer(timeout=4)
                print(stirrer_status)
                if(True == stirrer_status):
                    break; 
                time.sleep(0.5)
            if(True == chamber_status):
                #i = stirrer_step
                print("True == chamber_status")
                break; 
            elif(False == chamber_status and stirrer_step == (turntable_step+1)):
                #i = stirrer_step
                print("False == chamber_status and stirrer_step == (turntable_step+1)")
                break; 
            elif(False == chamber_status and index>=10):
                i=0
                print("Reinit test")
                bluetest.Stirring_Stepped_Init(timeout=60)
                break; 
            time.sleep(0.5)
    else:
        break  
# for end

# close csv file **********************************************

csvfile.close()

print("User script finished")