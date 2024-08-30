from DUT_drivers import * 
from device_drivers import *
from private_libraries import *
import time
import csv

#dynamic import - importing mock classes or using main thread class
if __name__ == "__main__":
   from Nodes.uth_mock import User_thread_mock
self = User_thread_mock


print("TEST STARTED")
# ----------------------------------------------------------------
# add nodes subscribers - instruments and devices to be connected 
# with #
self.add_sub("Anritsu")
self.add_sub("Bluetest_chamber")
self.add_sub("HKP")
self.add_sub("SCP")
# ----------------------------------------------------------------
# create dictionary for all data to log #
data_to_log = {
            "Stirrer Step": str,
            "Stirrer Position": str,
            "Turntable Step": str,
            "Turntable Position": str,
            "NA1": str,
            "NA2": str,
            "NA3": str,
            "Transmit Power Peak - Average": str,
            "Transmit Power Peak - Maximum": str,
            "Transmit Power Peak - Minimum": str,
            "Transmit Power Peak - SD": str,
            "Transmit Power Average - Average": str,
            "Transmit Power Average - Maximum": str,
            "Transmit Power Average - Minimum": str,
            "Transmit Power Average - SD": str,
            "Crest Factor - Average": str,
            "Crest Factor - Maximum": str,
            "Crest Factor - Minimum": str,
            "Crest Factor - SD": str,
            "NA4": str,
            "NA5": str,
            "Measurement Status": str}

# ----------------------------------------------------------------
# set test parameters
POS_COMBINATIONS = 72 # 72
BAND = 0 #1 for 2.4G, 0 for 5G
ANT_CFGS = [1,2,3] #1 - RF CHain 0, 2 - RF Chain 1, 3 - Both
CHAN_LIST = [36,40,44,48,52,56,60,64,100,104,108,112,116,120,124,128,132,136,140,144,149,153,157,161,165,169] #[chan for chan in CHANNEL_LIST[BAND] if chan in CHANNEL_LIST]
# --- automatically selected below based on above settings
CHANNEL_LIST = {
    0: [36, 48, 60, 104, 116, 128, 140, 153, 165],#36,40,44,48,52,56,60,64,100,104,108,112,116,120,124,128,132,136,140,144,149,153,157,161,165,169,
    1: [1, 6, 11]
}
MODULATION = {
    0: 9,           #eecmd WLAN_RF modul_set 5 - TCMD_WLAN_MODE_VHT20( 802.11ac) 9 = HE20
    1: 1            #eecmd WLAN_RF modul_set 1 - TCMD_WLAN_MODE_HT20( 802.11n)
}
DATARATE = 15 # 15=MCS0, 26=MSC11
BASE_CHANNEL = {0: 5180, 1: 2412}
INPUT_LEVEL = {1: -20.0, 2: -20.0, 3: -15.0} #input power depending on antenna config, +5dB for STBC

WLAN_CFG_FILE = {0: "Direct_CH36_HE20_MCS0.xml", 1: "Direct_CH1_HT20_MCS0.xml"}# AX: Direct_CH36_HE20_MCS0.xml AC: Direct_CH36_VHT20_MCS0
print(CHAN_LIST)
print("MODULATION: "+str(MODULATION[BAND]))
print("WLAN_CFG_FILE[BAND]: "+WLAN_CFG_FILE[BAND])
# ----------------------------------------------------------------
# create objects representing instruments #
anritsu = AnritsuMT8862AWLAN("Anritsu", self)
bluetest = bluetest_chamber("Bluetest_chamber", self)
dhu = DHU("SCP", "HKP", self)    
# ----------------------------------------------------------------
# initialize instruments #
# initialize Anritsu
anritsu.load_config_file(WLAN_CFG_FILE[BAND])
print("LOADING CONFIG FILE TO ANRITSU")
#time.sleep(5)
# initialize Bluetest chamber
bluetest.login("root", "aptiv", 10)     
bluetest.Stirring_Stepped_Configure(timeout=10, positions=POS_COMBINATIONS)
# initialize DUT
dhu.HKP_set_pwr_always_on()

# ----------------------------------------------------------------
# repeat test for all channels
for ch in range(len(CHAN_LIST)):
    anritsu.set_primary_channel_number(CHAN_LIST[ch])
    # repeat test for all antenna configs in each channel
    for cfg in range(len(ANT_CFGS)):
        # create csv file #
        filename = "TRP_result_CH"+str(CHAN_LIST[ch])+"_antcfg"+str(ANT_CFGS[cfg])+"_"+str(time.strftime("%Y%m%d%H%M%S"))+".csv"
        csvfile = open(filename, mode='w', newline='')
        print("Created file: "+filename)
        csvwriter = csv.writer(csvfile, delimiter=';',
            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(list(data_to_log.keys())) # write column headers
        # Set input power level expected
        anritsu.set_input_power(pwr=str(INPUT_LEVEL[ANT_CFGS[cfg]])) 
        # Set stirring and turntable to HOME position
        print("WAITING FOR BLUETEST TURNTABLE REACHES HOME POSITION")
        bluetest.Stirring_Stepped_Init(timeout=60)
        # Enable and configure DUT
        dhu.SCP_dut_enable()
        dhu.SCP_continuous(mode="off")
        dhu.SCP_antenna_config_set(config=ANT_CFGS[cfg], time_for_timeout=2)
        dhu.SCP_band_set(band=BAND)
        dhu.SCP_channel_set(frequency=(BASE_CHANNEL[BAND]+(CHAN_LIST[ch]-CHANNEL_LIST[BAND][0])*5))
        print("Channel set: "+str((BASE_CHANNEL[BAND]+(CHAN_LIST[ch]-CHANNEL_LIST[BAND][0])*5)))
        dhu.SCP_modul_set(mode=MODULATION[BAND])
        dhu.SCP_datarate_set(DATARATE)
        dhu.SCP_tx_output_set(power=8)
        dhu.SCP_continuous(mode="on")
        # repeat test for all bluestest positions in each channel and antenna config
        #for i in range(POS_COMBINATIONS):
        stirrer_step = 0
        while True:#(stirrer_step < (POS_COMBINATIONS-1)):
            # read and store Bluetest stirrer and turntable positions
            while True:
                stirrer_status, stirrer_position, stirrer_step = bluetest.GetPositionStirrer(timeout=4)
                print(stirrer_status)
                if(True == stirrer_status):
                    break; 
                time.sleep(0.5)
            data_to_log["Stirrer Position"] = str(stirrer_position).replace(".",",")
            data_to_log["Stirrer Step"] = stirrer_step
            time.sleep(0.1)
            while True:
                turntable_status, turntable_position, turntable_step = bluetest.GetPositionTurntable(timeout=4)
                print(turntable_status)
                if(True == turntable_status):
                    break; 
                time.sleep(0.5)
            data_to_log["Turntable Position"] = str(turntable_position).replace(".",",")
            data_to_log["Turntable Step"] = turntable_step
            meas_end_flag = 0
            # start measurement in Anritsu (SINGLE button press in web app)
            anritsu.start_measurement()
            # save start time
            meas_start_time = time.time()
            while(meas_end_flag == 0):
                # wait for measurement end
                progress = anritsu.query_measurement_progress(5)
                print(progress)
                if progress == "MEASUREMENT END":
                    # if measurement end = exit while loop
                    meas_end_flag = 1
                else:
                    # else measurement not end for 60 seconds - also exit while loop
                    meas_time = time.time()-meas_start_time
                    if meas_time > 60:
                        meas_end_flag = 1 
                time.sleep(0.5)
            # read and store status of the finished measurement
            meas_status = anritsu.query_measurement_status(timeout=5)
            print(f"meas_status = {meas_status}")
            data_to_log["Measurement Status"] = meas_status
            # read and store measurement results - MEAS_TP results
            meas_result = anritsu.query_transmitted_power(timeout=15)
            meas_result = meas_result.replace(",",";")
            meas_result = meas_result.replace(".",",")
            print(meas_result)
            # Update data_to_log dict with meas_result values
            data_to_log_keys_list = list(data_to_log.keys())
            meas_result_dict_keys = data_to_log_keys_list[data_to_log_keys_list.index("NA1"):data_to_log_keys_list.index("NA5")+1]
            meas_result_dict_values = meas_result.split(";")
            meas_result_dict = dict(zip(meas_result_dict_keys,meas_result_dict_values))
            data_to_log.update(meas_result_dict)
            # write all data logged from actual step into new row
            csvwriter.writerow(list(data_to_log.values()))
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
        csvfile.close()
    dhu.SCP_continuous(mode="off")
    dhu.SCP_dut_enable("off")
print("TEST FINISHED")
    ##################################################
    #pass