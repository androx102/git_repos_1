# *********************************************************************************************************
# * Name: UWB Packet Gen
# *
# * Library description:
# *
# * Library to generate CCC (Car Connectivity Consortium) "conform" packet sequence with Litepoint IQgig
# * Due to device limitations (only 72MSamples and no fast PCIe host interface) it is not possible to
# * to realize many muliple rounds/blocks/sessions with changing data content. But a single round
# * with CCC conform packets (SP0-prepoll,SP3-poll etc.) is feasible and can be repeated multiple times
# *
# * For documentation please visist APTIV Wiki: 
# * https://confluence.asux.aptiv.com/display/VA/UWB+Python+library
# *
# * Change history [date (dd,mm,yyyy), user, comment]:
# *
# * 25.03.2024 , Reissenweber, intial version, carry over with adaptions from RF_TOOLS
# * 10.04.2024 , Reissenweber, 1st release to PY-Tools repository
# *********************************************************************************************************
from device_drivers.priv_dependencies import *
import logging
import time
import random

# Constants    
UWB_MAX_SLOT_NUMBER    = 96                        # Slots per Round = 6,8,9,12,16,18,24,32,36,48,72,96
UWB_MAX_ROUND_NUMBER   = 12                        # Number of Ranging Rounds per block
UWB_MAX_BLOCK_NUMBER   = 1                         # Number of Blocks per sessions
UWB_MAX_SESSION_NUMBER = 1                         # Number of Sessions
SUCCESS                = 1 
FAIL                   = 0

# *********************************************************************************************************
# * UWB self defined enums types                                                                                  
# *********************************************************************************************************

from enum import Enum

class UWB_STS_Type_Tag(Enum):               
    STS_IEEE = 0                                   # Litepoint will use phyHrpUwbStsVCounter,phyHrpUwbStsKey,phyHrpUwbStsVUpper96 to calculate the 4096 STS bits
    STS_USER = 1                                   # Litepoint will use STS_Data (user defined 4096 bits)
                                                   # See Litepoint SCPI command CONFigure:WAVE:STS:GENeration
class UWB_Payload_Modulation_Tag(Enum):
    BPSK = 0
    QPSK = 1

class UWB_Packet_Type_Tag(Enum):    
    NOTUSED   = 0
    SP0       = 1
    SP3       = 2  
    EMPTY     = 3
    RESPONDER = 4

# ********************************************************************************************************
# * UWB Packet definion types                                                                           
# ********************************************************************************************************
                                                
class UWB_Litepoint:

    # Constructor
    def __init__(self,user_thread:User_thread):
                 
         # instance variable unique to each instance         
         self.UWB=[]
         self.UWB.append(self.UWB_Sequence_Tag())     # CCC0                   = index 0
         self.UWB.append(self.UWB_Sequence_Tag())     # CCC1                   = index 1
         self.UWB.append(self.UWB_Sequence_Tag())     # CCC2                   = index 2
         self.UWB.append(self.UWB_Sequence_Tag())     # TESTMODE_SP0_CONF1     = index 3
         self.UWB.append(self.UWB_Sequence_Tag())     # TESTMODE_SP3_CONF1     = index 4 
         self.UWB.append(self.UWB_Sequence_Tag())     # UWB_INTERFERER_TYP     = index 5
         self.UWB.append(self.UWB_Sequence_Tag())     # UWB_INTERFERER_WORST   = index 6
         self.UWB.append(self.UWB_Sequence_Tag())     # UWB_INTERFERER_EXTREME = index 7
         self.UWB_Protocol_Number:int             
                   
         # used for instruments 
         self.user_thread = user_thread

         # logging to terminal 
         # VisualStudioCode terminal history is limited to 1000 lines. Change "terminal.integrated.scrollback" var to more lines if needed
         formatter = logging.Formatter(fmt='%(levelname)-8s || %(name)-20s || %(funcName)55s || %(message)s')
         self.logger = logging.getLogger(__name__)  # auto hierachy                               
         handler = logging.StreamHandler()
         handler.setFormatter(formatter)
         self.logger.addHandler(handler)
         self.logger.setLevel(logging.DEBUG)    

    # Nested subclass below class "UWB_Litepoint"
    class UWB_Sequence_Tag:   
        # Constructor
        def __init__(self):
            self.CenterFrequency:float
            self.Sampling_Rate:int
            self.N_Chap_Per_Slot:int                        # Number of Chaps per Slot  (3,4,6,8,9,12,24)
            self.N_Slot_Per_Round:int                       # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
            self.N_Configured_Slots_per_Round:int           # internal var, will be calculated
            self.N_Round:int                                # Number of Rounds
            self.N_Block:int                                # Number of Blocks
            self.N_Session:int                              # Number of sessions
            self.N_Rounds_per_Block:int            
            self.N_Blocks_per_Session:int
            self.N_of_Sessions:int
            self.Session=[]                                 # Define a sequence as a list of sessions
            for i in range(UWB_MAX_SESSION_NUMBER):
                self.Session.append(self.UWB_Session_Tag())  

        # Nested subclass below class "UWB_Sequence_Tag"
        class UWB_Session_Tag:
            # Constructor
            def __init__(self):
                self.Block=[]
                for i in range(UWB_MAX_BLOCK_NUMBER):          # Define a session as a list of blocks
                    self.Block.append(self.UWB_Block_Tag())

            # Nested subclass below class "UWB_Session_Tag"
            class UWB_Block_Tag:
                # Constructor
                def __init__(self):
                    self.Round = []
                    for i in range(UWB_MAX_ROUND_NUMBER):          # Define a block as a list of rounds
                        self.Round.append(self.UWB_Round_Tag())

                # Nested subclass below class "UWB_Block_Tag"
                class UWB_Round_Tag:
                    # Constructor
                    def __init__(self):
                        self.Slot = []
                        for i in range(UWB_MAX_SLOT_NUMBER):           # Define a round as a list of slots    
                            self.Slot.append(self.UWB_Slot_Tag())

                    # Nested subclass below class "UWB_Round_Tag"
                    class UWB_Slot_Tag:  
                        # Constructor
                        def __init__(self):  
                            self.Packet_Type = UWB_Packet_Type_Tag              # enum
                            self.SHR = self.UWB_SHR_Tag()                       # SHR
                            self.PAYLOAD = self.UWB_PAYLOAD_Tag()               # PHR + PSDU
                            self.STS = self.UWB_STS_Tag()                       # STS
                            self.GapTime:float                                  # internal var, will be calculated automatically during timing calc
                            self.NoOfEmptyChaps:int                             # internal var, will be calculated automatically during timing calc
                            self.WaveSegmentDataFileName:str                    # internal var, will be filled automatically
                            self.WaveSegmentEmptChapFileName:str                # internal var, will be filled automatically

                        # Nested subclass below class "UWB_Slot_Tag"
                        class UWB_PAYLOAD_Tag:                                      
                            # Constructor
                            def __init__(self):                                     # Payload (PHR + MHR + PSDU) 
                                self.Modulation = UWB_Payload_Modulation_Tag        # enum 
                                self.Data_Rate:float                                # Data Rate
                                self.Ranging_Bit:int                                # PHR Ranging bit 0,1
                                self.Payload_NoOfBytes:int                          # Payload number of bytes (max. 127)
                                self.Payload_Data=[]                                # Payload data array, 128 bytes

                        # Nested subclass below class "UWB_Slot_Tag"
                        class UWB_SHR_Tag:   
                            # Constructor
                            def __init__(self):                                     # Sync Header (SYNC + SFD)    
                                self.Preamble_Sync_Code_Index:int                   # Sync Code Index
                                self.No_Preamble_Sync_Symbols:int                   # Sync Duration / Number of Repetitons
                                self.Data_Rate:float                                # Data Rate
                                self.SFD=[0,0,0,0, 0,0,0,0]                         # Start Frame Delimiter, -1,0,1

                        # Nested subclass below class "UWB_Slot_Tag"
                        class UWB_STS_Tag:                                          
                            # Constructor
                            def __init__(self):                                     # STS
                                self.STS_NoOfBits:int                               # STS number of bits
                                self.STS_Data= []                                   # STS user defined STS data array of bytes
                                self.STS_phyHrpUwbStsVCounter = []                  # Counter   4 bytes ( 32 bit)
                                self.STS_phyHrpUwbStsKey = []                       # Key      16 bytes (128 bit)
                                self.STS_phyHrpUwbStsVUpper96 = []                  # UDATA    12 bytes ( 96 bit)
                                self.STS_Type = UWB_STS_Type_Tag                    # enum Flag to specify STS bit generation type -> see defintion


                                                         
    # Member function of class "UWB_Litepoint"
    def InitializeProtocolRFParameters(self):

        # ********************************************************************************************************
        # * Fill data structure                                                                     
        # ********************************************************************************************************    

        CCC0                   = 0
        CCC1                   = 1
        CCC2                   = 2
        TESTMODE_SP0_CONF1     = 3
        TESTMODE_SP3_CONF1     = 4
        UWB_INTERFERER_TYP     = 5    # round time 288ms, 6 responder
        UWB_INTERFERER_WORST   = 6    # round time 96ms,  6 responder
        UWB_INTERFERER_EXTREME = 7    # round time 24ms,  6 responder

        # ********************************************************************************************************
        # UWB  (Example 0)
        # ********************************************************************************************************

        self.UWB[CCC0].CenterFrequency      = 6489.6e6             # in Hz
        self.UWB[CCC0].Sampling_Rate        = 2400000000           # in Samples/sec

        self.UWB[CCC0].N_Chap_Per_Slot      = 6                    # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[CCC0].N_Slot_Per_Round     = 6                    # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[CCC0].N_Rounds_per_Block   = 1                    # Number of Rounds
        self.UWB[CCC0].N_Blocks_per_Session = 1                    # Number of Blocks
        self.UWB[CCC0].N_of_Sessions        = 1                    # Number of sessions

        # This example is taken from CCC (Car Connectivity Consortium) DK3 (Digital Key Release 3) technical specification V1.1.0
        # Table 20-1 for one vehicle (k=1)
        # N_Chap_Per_Slot = 6
        # N_Responder     = 2
        # T_Round         = 12 ms
        # From these figures we can calculate:
        # T_Slot  = 6*333.333us = 2ms
        # Packets = 1 Pre-Poll+ 1 Poll + 2 Responds + 1 Final + 1 FinalData = 6 packets
        # N_Slot_Per_Round = 6 as T_Round is 12 ms
        # As N_Slot_Per_Round is 6 and the number of packets is as well 6, all slots are used

        # **************************************
        # * SP0 PRE-POLL
        # **************************************

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0   

        # SP0 Preable (SHR)
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0,1,0,-1,1,0,0,-1]
            
        # SP0 Payload
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 3
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = [0x11, 0x12, 0x13]
        
        # **************************************
        # * SP3 POLL
        # **************************************

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3              
                
        # SP3 Preable (SHR)
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].SHR.SFD =  [0,1,0,-1,1,0,0,-1]

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE   # STS_USER or STS_IEEE
            
        # SP3 STS
        # Used if UWB_STS_Type flag is set to STS_IEEE

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                          # 4 bytes
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7")  # 16 bytes
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")          # 12 bytes

        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8        
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # ******************************************************************
        # * RESPONSE slots
        # * for 2 responder
        # * LP Analyzer is currently not supported and response is scipped
        # ******************************************************************

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[2].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[3].Packet_Type = UWB_Packet_Type_Tag.RESPONDER

        # **************************************
        # * FINAL SP3
        # **************************************

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].SHR.Data_Rate = 6.81E6
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].SHR.SFD = [0,1,0,-1,1,0,0,-1]

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE   # STS_USER or STS_IEEE

        # SP3 STS
        # Used if UWB_STS_Type flag is set to STS_IEEE
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes

        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].STS.STS_NoOfBits = 16*8          
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[4].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # **************************************
        # * FINAL DATA SP0
        # **************************************

        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].SHR.Data_Rate = 6.81E6
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].SHR.SFD = [0,1,0,-1,1,0,0,-1]

        # SP0 Payload
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].PAYLOAD.Ranging_Bit = 1
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].PAYLOAD.Payload_NoOfBytes = 3
        self.UWB[CCC0].Session[0].Block[0].Round[0].Slot[5].PAYLOAD.Payload_Data = [0x0A,0x0B,0x0C]   


        # ********************************************************************************************************
        # UWB  (Example 1)
        # ********************************************************************************************************

        self.UWB[CCC1].CenterFrequency      = 6489.6e6             # in Hz
        self.UWB[CCC1].Sampling_Rate        = 2400000000           # in Samples/sec

        self.UWB[CCC1].N_Chap_Per_Slot      = 3                    # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[CCC1].N_Slot_Per_Round     = 8                    # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[CCC1].N_Rounds_per_Block   = 1                    # Number of Rounds
        self.UWB[CCC1].N_Blocks_per_Session = 1                    # Number of Blocks
        self.UWB[CCC1].N_of_Sessions        = 1                    # Number of sessions

        # This example is taken from CCC (Car Connectivity Consortium) DK3 (Digital Key Release 3) technical specification V1.1.0
        # Table 20-1 for one vehicle (k=2)
        # N_Chap_Per_Slot = 3
        # N_Responder     = 3
        # T_Round         = 8 ms
        # From these figures we can calculate:
        # T_Slot  = 3*333.333us = 1ms
        # N_Slot_Per_Round = 8 as T_Round is 8 ms
        # Packets = 1 Pre-Poll + 1 Poll + 3 Responds + 1 Final + 1 FinalData = 7 packets
        # 7 slots are not allowed, we have to use 8 slots
        # 8 slots also corresponds to T_Round = 8 ms
        # As N_Slot_Per_Round is 8 and the number of packets is 7, the last slot will be empty (see CCC chapter 20.5.1)

        # **************************************
        # * SP0 PRE-POLL
        # **************************************
        self.UWB[1].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0,1,0,-1,1,0,0,-1]
       
        # SP0 Payload
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 3
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = [0xAA, 0xBB, 0xCC]        

        # **************************************
        # * SP3 POLL
        # **************************************
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].SHR.SFD = [0,1,0,-1,1,0,0,-1]
        

        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE   # STS_USER or STS_IEEE

        # SP3 STS
        # Used if UWB_STS_Type flag is set to "STS_IEEE"
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes

        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !       
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8   
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
   
        # ******************************************************************
        # * response slots
        # * for 3 responder
        # * LP Analyzer is currently not supported and response is scipped
        # ******************************************************************

        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[2].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[3].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[4].Packet_Type = UWB_Packet_Type_Tag.RESPONDER

        # **************************************
        # * FINAL SP3
        # **************************************
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].Packet_Type = UWB_Packet_Type_Tag.SP3
        # SP3 Preable (SHR)

        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].SHR.Data_Rate = 6.81E6
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].SHR.SFD =  [0,1,0,-1,1,0,0,-1]
        
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE   # STS_USER or STS_IEEE

        # SP3 STS
        # Used if UWB_STS_Type flag is set to "STS_IEEE"
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
        
        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].STS.STS_NoOfBits = 16*8   
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[5].STS.STS_Data  =  [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
      
        # **************************************
        # * FINAL DATA SP0
        # **************************************
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].Packet_Type = UWB_Packet_Type_Tag.SP0
        
        # SP0 Preable (SHR)
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].SHR.Data_Rate = 6.81E6
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].SHR.SFD = [0,1,0,-1,1,0,0,-1]
   
        # SP0 Payload
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].PAYLOAD.Ranging_Bit = 1
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].PAYLOAD.Payload_NoOfBytes = 3
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[6].PAYLOAD.Payload_Data = [0x2A, 0x2B, 0x2C]
         
        # **************************************
        # * Last slot
        # **************************************
        self.UWB[CCC1].Session[0].Block[0].Round[0].Slot[7].Packet_Type  = UWB_Packet_Type_Tag.EMPTY
        


        # ********************************************************************************************************
        # UWB  (Example 2)
        # ********************************************************************************************************        
        self.UWB[CCC2].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[CCC2].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[CCC2].N_Chap_Per_Slot      = 9                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[CCC2].N_Slot_Per_Round     = 96                  # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[CCC2].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[CCC2].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[CCC2].N_of_Sessions        = 1                   # Number of sessions

        # This example creates a ranging round of 288ms for 10 responder
        # N_Chap_Per_Slot  = 9 
        # N_Slot_Per_Round = 96
        # N_Responder      = 10
        # T_Round          = 288 ms
        #
        # There are only a few configurations with work with the CCC requiremnts for a round time of 288ms.
        # 
        # From this, we can calculate:
        # T_slot = N_Chap_Per_Slot*333.3us = 3ms
        # Total number of slots = T_Round/T_slot = 288ms/3ms = 96
        # Number of slots slots for modulation + resonse = 4 + 10 = 14 
        # Required slots at the end = 96-14 = 82
        # Number of Empty caps at the end = 82*9 = 738 (will be calculated automatically)
        #
        # Number of packets to be be configured
        # 4 data
        # 10 empty for the resopnder
        # 1  empty at the end
        # Total 15 packets         

        # **************************************
        # * SP0 PRE-POLL
        # **************************************
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0, 1, 0, -1, 1, 0, 0, -1]
    
        # SP0 Payload
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 3
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = [0xAA, 0xBB, 0xCC] 

        # **************************************
        # * SP3 POLL
        # **************************************
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].SHR.SFD = [0, 1, 0, -1, 1, 0, 0, -1]
   
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_USER   # STS_USER or STS_IEEE

        # SP3 STS
        # Used if UWB_STS_Type flag is set to "STS_IEEE"
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
   
        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8;   
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
  
        # ******************************************************************
        # * response slots
        # * for 10 responder
        # * LP Analyzer is currently not supported and response is scipped
        # ******************************************************************

        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[2].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[3].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[4].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[5].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[6].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[7].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[8].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[9].Packet_Type  = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[10].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[11].Packet_Type = UWB_Packet_Type_Tag.RESPONDER

        # **************************************
        # * FINAL SP3
        # **************************************
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].Packet_Type = UWB_Packet_Type_Tag.SP3
        
        # SP3 Preable (SHR)
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].SHR.Data_Rate = 6.81E6
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].SHR.SFD = [0, 1, 0, -1, 1, 0, 0, -1]
        
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].STS.STS_Type = UWB_STS_Type_Tag.STS_USER;   # STS_USER or STS_IEEE

        # SP3 STS
        # Used if UWB_STS_Type flag is set to "STS_IEEE"
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
        
        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].STS.STS_NoOfBits = 16*8;   
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[12].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
   
        # **************************************
        # * FINAL DATA SP0
        #  **************************************
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].Packet_Type = UWB_Packet_Type_Tag.SP0
        
        # SP0 Preable (SHR)
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].SHR.Data_Rate = 6.81E6
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].SHR.SFD =  [0, 1, 0, -1, 1, 0, 0, -1]
  
        # SP0 Payload
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].PAYLOAD.Ranging_Bit = 1
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].PAYLOAD.Payload_NoOfBytes = 3
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[13].PAYLOAD.Payload_Data = [0x2A, 0x2B, 0x2C]
        
        # **************************************
        # * Last slot
        # **************************************
        self.UWB[CCC2].Session[0].Block[0].Round[0].Slot[14].Packet_Type = UWB_Packet_Type_Tag.EMPTY



        # ********************************************************************************************************
        # UWB  (TESTMODE_SP0_CONF1)
        # ********************************************************************************************************   
      
        self.UWB[TESTMODE_SP0_CONF1].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[TESTMODE_SP0_CONF1].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[TESTMODE_SP0_CONF1].N_Chap_Per_Slot      = 6                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[TESTMODE_SP0_CONF1].N_Slot_Per_Round     = 1                   # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[TESTMODE_SP0_CONF1].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[TESTMODE_SP0_CONF1].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[TESTMODE_SP0_CONF1].N_of_Sessions        = 1                   # Number of sessions

        # SP0 packet only
        # Example with max payload bits
        # 
        # N_Slot_Per_Round = 2  : T_Round =  1*6*333.3us = 2ms
        # N_Slot_Per_Round = 48 : T_Round = 48*6*333.3us = 288ms   etc.
        # Any combination of N_Chap_Per_Slot and N_Slot_Per_Round will work for this single SP0 packet
    
        # **************************************
        # * SP0 
        # **************************************
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0, 1, 0, -1, 1, 0, 0, -1]
       
        # SP0 Payload        
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = bytes.fromhex("492BD9091600000000778B079DAA050069DF04010D803F32D1C2EAEB21B4EDEA19340043DA69007718A30483")
        self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = len(self.UWB[TESTMODE_SP0_CONF1].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data)
        
        # ********************************************************************************************************
        # UWB  (TESTMODE_SP3_CONF1)
        # ********************************************************************************************************         

        self.UWB[TESTMODE_SP3_CONF1].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[TESTMODE_SP3_CONF1].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[TESTMODE_SP3_CONF1].N_Chap_Per_Slot      = 6                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[TESTMODE_SP3_CONF1].N_Slot_Per_Round     = 1                   # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[TESTMODE_SP3_CONF1].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[TESTMODE_SP3_CONF1].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[TESTMODE_SP3_CONF1].N_of_Sessions        = 1                   # Number of sessions

        # SP3 packet only
        # 
        # N_Slot_Per_Round = 6  : T_Round =  1*6*333.3us = 2ms
        # N_Slot_Per_Round = 48 : T_Round = 48*6*333.3us = 288ms   etc.
        # Any combination of N_Chap_Per_Slot and N_Slot_Per_Round will work for this single SP0 packet
    
        # **************************************
        # * SP3 
        # **************************************

        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0, 1, 0, -1, 1, 0, 0, -1]
  

        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].STS.STS_Type = UWB_STS_Type_Tag.STS_USER

        # SP3 STS
        # Used if UWB_STS_Type flag is set to "STS_IEEE"
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
           
        # SP3 STS 
        # Only used if UWB_STS_Type flag is set to STS_USER
        # Prepared to be used in the future. STS bits are not processed and not spreaded
        # The bits are 1:1 visible in the IQ data
        # if there are less bits than for 64 us are provided, the bits are repeated
        # A min. number of 128 bits (16 bytes) need to be provided !
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].STS.STS_NoOfBits = 16*8
        self.UWB[TESTMODE_SP3_CONF1].Session[0].Block[0].Round[0].Slot[0].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]  
        

        # ********************************************************************************************************
        # UWB  (UWB_INTERFERER_TYP)
        # for conformance tests
        # ******************************************************************************************************** 

        self.UWB[UWB_INTERFERER_TYP].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[UWB_INTERFERER_TYP].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[UWB_INTERFERER_TYP].N_Chap_Per_Slot      = 6                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[UWB_INTERFERER_TYP].N_Slot_Per_Round     = 144                 # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[UWB_INTERFERER_TYP].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[UWB_INTERFERER_TYP].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[UWB_INTERFERER_TYP].N_of_Sessions        = 1                   # Number of sessions

        # Typical UWB interferer/blocker with 288ms ROUND duration and 6 responder
        # Speciality: Litepoint is also creating SP3 packets in the responder slots to emulate potential resonpoder
        #             6 Responder are not conform with CCC
        # 
        # N_Chap_Per_Slot    = 6 = 2ms
        # N_Slot_Per_Round   = 144
        # N_Rounds_per_Block = 1
        #
        # This means this single round is repeated every 288 ms (144 slots a 2ms)

        # **************************************
        # * SP0 PRE-POLL
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0   

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0,1,0,-1,1,0,0,-1]
            
        # SP0 Payload
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 13 # Payload = 13 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * SP3 POLL
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3              
                
        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.SFD =  [0,1,0,-1,1,0,0,-1]

        # SP3 STS
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE              
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                          # 4 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7")  # 16 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")          # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # ******************************************************************
        # * RESPONSE slots
        # * for 6 responder
        # ******************************************************************
        # These are "6 empty" slots ....
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[2].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[3].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[4].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[5].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[6].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[7].Packet_Type = UWB_Packet_Type_Tag.RESPONDER            
        
        # but in this case we want to simulate the device response SP3 packets by the Litepoint as well
        for i in range (2,8):  # runs from 2 to 7            
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].Packet_Type = UWB_Packet_Type_Tag.SP3

            # SP3 Preable (SHR)
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.Preamble_Sync_Code_Index =  9
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.No_Preamble_Sync_Symbols = 64
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.Data_Rate = 6.81E6
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.SFD = [0,1,0,-1,1,0,0,-1]

             # SP3 STS  
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
            # Only used if UWB_STS_Type flag is set to STS_USER 
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_NoOfBits = 16*8        
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # **************************************
        # * FINAL SP3
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.SFD = [0,1,0,-1,1,0,0,-1]

         # SP3 STS  
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER 
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
               
        # **************************************
        # * FINAL DATA SP0
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.SFD = [0,1,0,-1,1,0,0,-1]

        # SP0 Payload
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes = 6*13  # Final data, 6 responder, each 13 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * Last slot
        # **************************************  
        # The last slot is an empty slot at slot index 10 (11. slot)
        # Please note that "N_Slot_Per_Round" is set to 144 
        # That means, that this last EMPTY SLOT will automatically extended/repeated to meet in total a round timing of 144 slots = 288ms
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[10].Packet_Type = UWB_Packet_Type_Tag.EMPTY    
        

        # ********************************************************************************************************
        # UWB  (UWB_INTERFERER_WORST)
        # for conformance tests
        # ******************************************************************************************************** 

        self.UWB[UWB_INTERFERER_WORST].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[UWB_INTERFERER_WORST].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[UWB_INTERFERER_WORST].N_Chap_Per_Slot      = 6                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[UWB_INTERFERER_WORST].N_Slot_Per_Round     = 48                  # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[UWB_INTERFERER_WORST].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[UWB_INTERFERER_WORST].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[UWB_INTERFERER_WORST].N_of_Sessions        = 1                   # Number of sessions

        # Typical UWB interferer/blocker with 96ms BLOCK duration and 6 responder
        # Speciality: Litepoint is also creating SP3 packets in the responder slots to emulate potential resonpoder
        #             6 Responder are not conform with CCC
        # 
        # N_Chap_Per_Slot    = 6 = 2ms
        # N_Slot_Per_Round   = 48
        # N_Rounds_per_Block = 1
        #
        # This means 1 block wich is repeated every 96 ms (48 slots a 2ms)

        # **************************************
        # * SP0 PRE-POLL
        # **************************************
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0   

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0,1,0,-1,1,0,0,-1]
            
        # SP0 Payload
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 13 # Payload = 13 bytes
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * SP3 POLL
        # **************************************
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3              
                
        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].SHR.SFD =  [0,1,0,-1,1,0,0,-1]

        # SP3 STS
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE              
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                          # 4 bytes
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7")  # 16 bytes
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")          # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # ******************************************************************
        # * RESPONSE slots
        # * for 6 responder
        # ******************************************************************
        # These are "empty" slots ....
        #self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[2].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[3].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[4].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[5].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[6].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[7].Packet_Type = UWB_Packet_Type_Tag.RESPONDER            
        
        # but in this case we want to simulate the device response SP3 packets by the Litepoint as well
        for i in range (2,8):  # runs from 2 to 7
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].Packet_Type = UWB_Packet_Type_Tag.SP3

            # SP3 Preable (SHR)
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].SHR.Preamble_Sync_Code_Index =  9
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].SHR.No_Preamble_Sync_Symbols = 64
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].SHR.Data_Rate = 6.81E6
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].SHR.SFD = [0,1,0,-1,1,0,0,-1]

             # SP3 STS  
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
            # Only used if UWB_STS_Type flag is set to STS_USER 
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].STS.STS_NoOfBits = 16*8        
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[i].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]



        # **************************************
        # * FINAL SP3
        # **************************************
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].SHR.SFD = [0,1,0,-1,1,0,0,-1]

         # SP3 STS  
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER 
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[8].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
               
        # **************************************
        # * FINAL DATA SP0
        # **************************************
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].SHR.SFD = [0,1,0,-1,1,0,0,-1]

        # SP0 Payload
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes = 6*13  # Final data, 6 responder, each 13 bytes
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * Last slot
        # **************************************  
        # The last slot is an empty slot at slot index 10 (11. slot)
        # Please note that "N_Slot_Per_Round" is set to 144 
        # That means, that this last EMPTY SLOT will automatically extended/repeated to meet in total a round timing of 144 slots = 288ms
        self.UWB[UWB_INTERFERER_WORST].Session[0].Block[0].Round[0].Slot[10].Packet_Type = UWB_Packet_Type_Tag.EMPTY            

        # ********************************************************************************************************
        # UWB  (UWB_INTERFERER_TYP)
        # for conformance tests
        # ******************************************************************************************************** 

        self.UWB[UWB_INTERFERER_TYP].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[UWB_INTERFERER_TYP].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[UWB_INTERFERER_TYP].N_Chap_Per_Slot      = 6                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[UWB_INTERFERER_TYP].N_Slot_Per_Round     = 144                 # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[UWB_INTERFERER_TYP].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[UWB_INTERFERER_TYP].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[UWB_INTERFERER_TYP].N_of_Sessions        = 1                   # Number of sessions

        # Typical UWB interferer/blocker with 288ms ROUND duration and 6 responder
        # Speciality: Litepoint is also creating SP3 packets in the responder slots to emulate potential resonpoder
        #             6 Responder are not conform with CCC
        # 
        # N_Chap_Per_Slot    = 6 = 2ms
        # N_Slot_Per_Round   = 144
        # N_Rounds_per_Block = 1
        #
        # This means this single round is repeated every 288 ms (144 slots a 2ms)

        # **************************************
        # * SP0 PRE-POLL
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0   

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0,1,0,-1,1,0,0,-1]
            
        # SP0 Payload
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 13 # Payload = 13 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * SP3 POLL
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3              
                
        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].SHR.SFD =  [0,1,0,-1,1,0,0,-1]

        # SP3 STS
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE              
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                          # 4 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7")  # 16 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")          # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # ******************************************************************
        # * RESPONSE slots
        # * for 6 responder
        # ******************************************************************
        # These are "6 empty" slots ....
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[2].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[3].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[4].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[5].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[6].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[7].Packet_Type = UWB_Packet_Type_Tag.RESPONDER            
        
        # but in this case we want to simulate the device response SP3 packets by the Litepoint as well
        for i in range (2,8):  # runs from 2 to 7
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].Packet_Type = UWB_Packet_Type_Tag.SP3

            # SP3 Preable (SHR)
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.Preamble_Sync_Code_Index =  9
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.No_Preamble_Sync_Symbols = 64
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.Data_Rate = 6.81E6
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].SHR.SFD = [0,1,0,-1,1,0,0,-1]

             # SP3 STS  
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
            # Only used if UWB_STS_Type flag is set to STS_USER 
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_NoOfBits = 16*8        
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[i].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # **************************************
        # * FINAL SP3
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].SHR.SFD = [0,1,0,-1,1,0,0,-1]

         # SP3 STS  
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER 
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[8].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
               
        # **************************************
        # * FINAL DATA SP0
        # **************************************
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].SHR.SFD = [0,1,0,-1,1,0,0,-1]

        # SP0 Payload
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes = 6*13  # Final data, 6 responder, each 13 bytes
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * Last slot
        # **************************************  
        # The last slot is an empty slot at slot index 10 (11. slot)
        # Please note that "N_Slot_Per_Round" is set to 48 
        # That means, that this last EMPTY SLOT will automatically extended/repeated to meet in total a round timing of 48 slots = 96ms
        self.UWB[UWB_INTERFERER_TYP].Session[0].Block[0].Round[0].Slot[10].Packet_Type = UWB_Packet_Type_Tag.EMPTY    
        

        # ********************************************************************************************************
        # UWB  (UWB_INTERFERER_EXTREME)
        # for checks
        # ******************************************************************************************************** 

        self.UWB[UWB_INTERFERER_EXTREME].CenterFrequency      = 6489.6e6            # in Hz
        self.UWB[UWB_INTERFERER_EXTREME].Sampling_Rate        = 2400000000          # in Samples/sec

        self.UWB[UWB_INTERFERER_EXTREME].N_Chap_Per_Slot      = 6                   # Number of Chaps per Slot  (3,4,6,8,9,12,24)
        self.UWB[UWB_INTERFERER_EXTREME].N_Slot_Per_Round     = 12                  # Number of Slots per Round (6,8,9,12,16,18,24,32,36,48,72,96)
        self.UWB[UWB_INTERFERER_EXTREME].N_Rounds_per_Block   = 1                   # Number of Rounds
        self.UWB[UWB_INTERFERER_EXTREME].N_Blocks_per_Session = 1                   # Number of Blocks
        self.UWB[UWB_INTERFERER_EXTREME].N_of_Sessions        = 1                   # Number of sessions

        # Typical UWB interferer/blocker with 96ms BLOCK duration and 6 responder
        # Speciality: Litepoint is also creating SP3 packets in the responder slots to emulate potential resonpoder
        #             6 Responder are not conform with CCC
        # 
        # N_Chap_Per_Slot    = 6 = 2ms
        # N_Slot_Per_Round   = 12
        # N_Rounds_per_Block = 1
        #
        # This means 1 block wich is repeated every 24 ms (12 slots a 2ms)

        # **************************************
        # * SP0 PRE-POLL
        # **************************************
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].Packet_Type = UWB_Packet_Type_Tag.SP0   

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].SHR.SFD = [0,1,0,-1,1,0,0,-1]
            
        # SP0 Payload
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes = 13 # Payload = 13 bytes
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[0].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * SP3 POLL
        # **************************************
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].Packet_Type = UWB_Packet_Type_Tag.SP3              
                
        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].SHR.SFD =  [0,1,0,-1,1,0,0,-1]

        # SP3 STS
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].STS.STS_Type = UWB_STS_Type_Tag.STS_IEEE              
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                          # 4 bytes
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7")  # 16 bytes
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")          # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[1].STS.STS_Data = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]

        # ******************************************************************
        # * RESPONSE slots
        # * for 6 responder
        # ******************************************************************
        # These are "empty" slots ....
        #self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[2].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[3].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[4].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[5].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[6].Packet_Type = UWB_Packet_Type_Tag.RESPONDER
        #self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[7].Packet_Type = UWB_Packet_Type_Tag.RESPONDER            
        
        # but in this case we want to simulate the device response SP3 packets by the Litepoint as well
        for i in range (2,8):  # runs from 2 to 7
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].Packet_Type = UWB_Packet_Type_Tag.SP3

            # SP3 Preable (SHR)
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].SHR.Preamble_Sync_Code_Index =  9
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].SHR.No_Preamble_Sync_Symbols = 64
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].SHR.Data_Rate = 6.81E6
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].SHR.SFD = [0,1,0,-1,1,0,0,-1]

             # SP3 STS  
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
            # Only used if UWB_STS_Type flag is set to STS_USER 
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].STS.STS_NoOfBits = 16*8        
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[i].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]



        # **************************************
        # * FINAL SP3
        # **************************************
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].Packet_Type = UWB_Packet_Type_Tag.SP3

        # SP3 Preable (SHR)
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].SHR.SFD = [0,1,0,-1,1,0,0,-1]

         # SP3 STS  
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].STS.STS_Type =  UWB_STS_Type_Tag.STS_IEEE         
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVCounter = bytes.fromhex("1cdd34f8")                         # 4 bytes
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsKey      = bytes.fromhex("4578AA54D663CB5AA88070CD01C604A7") # 16 bytes
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].STS.STS_phyHrpUwbStsVUpper96 = bytes.fromhex("79e865186cbd864b9cb24fda")         # 12 bytes
        # Only used if UWB_STS_Type flag is set to STS_USER 
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].STS.STS_NoOfBits = 16*8        
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[8].STS.STS_Data = [0x00,0x0,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F]
               
        # **************************************
        # * FINAL DATA SP0
        # **************************************
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].Packet_Type = UWB_Packet_Type_Tag.SP0

        # SP0 Preable (SHR)
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].SHR.Preamble_Sync_Code_Index =  9
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].SHR.No_Preamble_Sync_Symbols = 64
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].SHR.Data_Rate = 6.81E6
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].SHR.SFD = [0,1,0,-1,1,0,0,-1]

        # SP0 Payload
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Modulation = UWB_Payload_Modulation_Tag.BPSK
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Data_Rate = 0.85E6
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Ranging_Bit = 1
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes = 6*13  # Final data, 6 responder, each 13 bytes
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data = []
        for i in range (self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_NoOfBytes):
            self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[9].PAYLOAD.Payload_Data.append(random.randint(0,0xFF))
        
        # **************************************
        # * Last slot
        # **************************************  
        # The last slot is an empty slot at slot index 10 (11. slot)
        # Please note that "N_Slot_Per_Round" is set to 12 
        # That means, that this last EMPTY SLOT will automatically extended/repeated to meet in total a round timing of 12 slots = 24ms
        self.UWB[UWB_INTERFERER_EXTREME].Session[0].Block[0].Round[0].Slot[10].Packet_Type = UWB_Packet_Type_Tag.EMPTY            




    def TriggerPacketGen(self,UWB_Protocol_Number):  
    # This function will do the whole packet configuration inside the Litepoint UWB device    
    # legacy RF-TOOLS : SetRfPhy_Litepoint_UWB_Parameters
        
        #self.UWB_LP_SCPI_write("*RST;*CLS;*WAI")
        #self.UWB_LP_SCPI_query("*IDN?")
        
        # Select sequence and save it to var
        self.UWB_Protocol_Number = UWB_Protocol_Number    
                 
        #Init 
        Session_Idx = 0
        Block_Idx   = 0
        Round_Idx   = 0
        Slot_Idx    = 0         

        # Fetch data from sequence
        CenterFrequency      = self.UWB[UWB_Protocol_Number].CenterFrequency 
        Sampling_Rate        = self.UWB[UWB_Protocol_Number].Sampling_Rate
        N_Chap_Per_Slot      = self.UWB[UWB_Protocol_Number].N_Chap_Per_Slot
        N_Slot_Per_Round     = self.UWB[UWB_Protocol_Number].N_Slot_Per_Round
        N_Rounds_per_Block   = self.UWB[UWB_Protocol_Number].N_Rounds_per_Block
        N_Blocks_per_Session = self.UWB[UWB_Protocol_Number].N_Blocks_per_Session
        N_of_Sessions        = self.UWB[UWB_Protocol_Number].N_of_Sessions

        # Logging
        self.logger.debug("Center Frequency : %.0f Hz" % (CenterFrequency))
        self.logger.debug("Sampling Rate : %d Samples/sec" % (Sampling_Rate))
        self.logger.debug("N_Chap_Per_Slot : %d" % (N_Chap_Per_Slot))
        self.logger.debug("N_Slot_Per_Round : %d" % (N_Slot_Per_Round))
        self.logger.debug("N_Rounds_per_Block : %d" % (N_Rounds_per_Block))
        self.logger.debug("N_Blocks_per_Session : %d" % (N_Blocks_per_Session))
        self.logger.debug("N_of_Sessions : %d" % (N_of_Sessions))

        # Common settings
        CMD = "VSG1;FREQ:CENT %f" % (CenterFrequency)
        self.UWB_LP_SCPI_write(CMD)

        CMD = "VSA1;SRAT %d" % (Sampling_Rate)
        self.UWB_LP_SCPI_write(CMD)

        # Get number of configured slots  
        N_Configured_Slots_per_Round = self.UWB_Calculate_TotalNum_of_Configured_Slots()        
        # and write it back to the struct
        self.UWB[UWB_Protocol_Number].N_Configured_Slots_per_Round = N_Configured_Slots_per_Round

        # Run a kind of sanity check of the configuration struct before starting anything else 
        self.SanityCheck()   

        # Session loop
        for Session_Idx in range(N_of_Sessions):            
            # Loop over rounds 
            for Block_Idx in range(N_Blocks_per_Session):
                # Loop over rounds  
                for Round_Idx in range(N_Rounds_per_Block):
                    # Loop over slots
                    for Slot_Idx in range(N_Configured_Slots_per_Round):   

                        # Logging
                        self.logger.debug("Configure : Session %d, Block %d, Round %d, Slot%d" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx))
                        
                        # get packet type
                        Packet_Type = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type

                        if Packet_Type.name == "SP0":
          
                            # Configure Preamble SYNC + SFD  
                            self.SetRfPhy_Litepoint_Sync(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)  
                            # Payload on 
                            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR ON")
                            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:PCON 0")
                            self.UWB_LP_SCPI_write("UWBP; UWBP;CONF:WAVE:NSTS 0")                            
                            # Configure Payload
                            self.SetRfPhy_Litepoint_Payload(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Calculate Gap
                            self.SetRfPhy_Litepoint_CalcGap(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Create Waveform Segment and save to a file
                            self.SetRfPhy_Litepoint_StoreWaveFile(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Create Empty Chap and save to a file
                            self.SetRfPhy_Litepoint_CreateEmptyChap(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)

                        if Packet_Type.name == "SP3":

                            # Configure Preamble SYNC + SFD  
                            self.SetRfPhy_Litepoint_Sync(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Payload off       
                            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR OFF")
                            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:PCON 3")                # tbd.
                            self.UWB_LP_SCPI_write("UWBP; UWBP;CONF:WAVE:NSTS 1")               # number of STS segments (1..4 or 0=none)
                            # Configure STS
                            self.SetRfPhy_Litepoint_STS(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Calculate Gap
                            self.SetRfPhy_Litepoint_CalcGap(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Create Waveform Segment and save to a file
                            self.SetRfPhy_Litepoint_StoreWaveFile(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Create Empty Chap and save to a file
                            self.SetRfPhy_Litepoint_CreateEmptyChap(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)

                        if ((Packet_Type.name == "EMPTY") or (Packet_Type.name == "RESPONDER")):

                            # Only do some calc
                            self.SetRfPhy_Litepoint_CalcGap(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
                            # Create Empty Chap and save to a file
                            self.SetRfPhy_Litepoint_CreateEmptyChap(Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
    
        # Configure Wavelist
        self.SetRfPhy_Litepoint_Conf_Wavelist()

    def SanityCheck(self): 
    # This function will do some sanity checks    
    # As Python is a interpreter language, checking the content and existance of variables/array entries is more important as for a compiler language
    # Not everything will be checked here from the beginning ....
    # The approach is currently to expand this function in case of particuar problems
    # legacy RF-TOOLS : no such function

        UWB_Protocol_Number = self.UWB_Protocol_Number

        #Init 
        Session_Idx = 0
        Block_Idx   = 0
        Round_Idx   = 0
        Slot_Idx    = 0         

        # Logging        
        self.logger.debug("Running sanity check on the given configuration")

        # Fetch data from sequence               
        N_Configured_Slots_per_Round = self.UWB[UWB_Protocol_Number].N_Configured_Slots_per_Round   # this number can be smaller than "N_Slot_Per_Round"
        N_Slot_Per_Round             = self.UWB[UWB_Protocol_Number].N_Slot_Per_Round               # this number can be much larger than "N_Configured_Slots_per_Round"
        N_Rounds_per_Block           = self.UWB[UWB_Protocol_Number].N_Rounds_per_Block
        N_Blocks_per_Session         = self.UWB[UWB_Protocol_Number].N_Blocks_per_Session
        N_of_Sessions                = self.UWB[UWB_Protocol_Number].N_of_Sessions

        if (N_Slot_Per_Round == N_Configured_Slots_per_Round):
            self.logger.debug("All slots are configured. No automatic gap at the end will be inserted")
        if (N_Slot_Per_Round > N_Configured_Slots_per_Round):  
            self.logger.debug("%d slots are configured, but desired number of slots is %d. Automatic gap at the end will be inserted" % (N_Configured_Slots_per_Round,N_Slot_Per_Round))
        if (N_Slot_Per_Round < N_Configured_Slots_per_Round):   
            self.logger.warning("There are more slots configured in the data array as finaly used") 
            self.logger.warning("Configured are %d slots, but N_Slot_Per_Round is set to %d" % (N_Configured_Slots_per_Round,N_Slot_Per_Round)) 

                            
        # Session loop
        for Session_Idx in range(N_of_Sessions):            
            # Loop over rounds 
            for Block_Idx in range(N_Blocks_per_Session):
                # Loop over rounds  
                for Round_Idx in range(N_Rounds_per_Block):
                    # Loop over slots
                    for Slot_Idx in range(N_Configured_Slots_per_Round):  

                        # Check if the packet type is defined for all slots
                        # Give the user some hints in case the packet type is missing
                        try:
                            Packet_Type=self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type.name
                        except:
                            self.logger.error("Packet_type is not defined for index Session=%d,Block=%d,Round=%d,Slot=%d. UWB array is probably not filled up correctly with correct packet type data" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx))                                                              
                            self.logger.error("Expected number of sessions:             %d [Index 0..%d]" % (N_of_Sessions,N_of_Sessions-1))                        
                            self.logger.error("Expected number of sessions:             %d [Index 0..%d]" % (N_of_Sessions,N_of_Sessions-1)) 
                            self.logger.error("Expected number of blocks per session:   %d [Index 0..%d]" % (N_Blocks_per_Session,N_Blocks_per_Session-1))
                            self.logger.error("Expected number of rounds per block:     %d [Index 0..%d]" % (N_Rounds_per_Block,N_Rounds_per_Block-1))
                            self.logger.error("Expected number of slots per round       %d [Index 0..%d]" % (N_Slot_Per_Round,N_Slot_Per_Round-1))
                            raise Exception("Packet_type is not defined for index Session=%d,Block=%d,Round=%d,Slot=%d. UWB array has probaly not enough data, check log for details" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx))                        

                                   
    
    def UWB_Calculate_TotalNum_of_Configured_Slots(self):
    # This function calculates the total number of used/configured slots 
    # # legacy RF-TOOLS : UWB_Calculate_TotalNum_of_Configured_Slots       

        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number
                
        # Fetch data
        N_Chap_Per_Slot      = self.UWB[UWB_Protocol_Number].N_Chap_Per_Slot
        N_Slot_Per_Round     = self.UWB[UWB_Protocol_Number].N_Slot_Per_Round
        N_Rounds_per_Block   = self.UWB[UWB_Protocol_Number].N_Rounds_per_Block
        N_Blocks_per_Session = self.UWB[UWB_Protocol_Number].N_Blocks_per_Session
        N_of_Sessions        = self.UWB[UWB_Protocol_Number].N_of_Sessions
                
        ConfiguredSlot_Counter = 0
                
        # Session loop
        for Session_Idx in range(N_of_Sessions):            
            # Loop over rounds 
            for Block_Idx in range(N_Blocks_per_Session):
                # Loop over rounds  
                for Round_Idx in range(N_Rounds_per_Block):
                    # Loop over slots
                    for Slot_Idx in range(N_Slot_Per_Round):  

                        try:                      
                            # Fetch data
                            Packet_Type = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type  

                            # Logger
                            self.logger.debug("ProtNr %d, Session_Idx %d, Block_Idx %d, Round_Idx %d, Slot_Idx %d, packet.type %s" % (UWB_Protocol_Number,Session_Idx,Block_Idx,Round_Idx,Slot_Idx,Packet_Type.name))
                                                                                                                     
                            match Packet_Type.name:
                                case "NOTUSED":
                                    # do nothing
                                    ConfiguredSlot_Counter=ConfiguredSlot_Counter
                                case "SP0":
                                    ConfiguredSlot_Counter=ConfiguredSlot_Counter+1
                                case "SP3":
                                    ConfiguredSlot_Counter=ConfiguredSlot_Counter+1
                                case "EMPTY":
                                    ConfiguredSlot_Counter=ConfiguredSlot_Counter+1
                                case "RESPONDER":
                                    ConfiguredSlot_Counter=ConfiguredSlot_Counter+1
                                case other:
                                    raise Exception("Unexpected Packet_type %s" % (Packet_Type.name))
                        except:

                            self.logger.debug("ProtNr %d, Session_Idx %d, Block_Idx %d, Round_Idx %d, Slot_Idx %d, packet.type NOT DEFINED -> packet is not counted" % (UWB_Protocol_Number,Session_Idx,Block_Idx,Round_Idx,Slot_Idx))

                            
        self.logger.debug("Total Number of configured slots : %d" % (ConfiguredSlot_Counter))
                                                        
        return(ConfiguredSlot_Counter)
    


    def SetRfPhy_Litepoint_Sync(self, Session_Idx,Block_Idx,Round_Idx,Slot_Idx):
    # This function configures preamble SYNC + SFD      
    # legacy RF-TOOLS : SetRfPhy_Litepoint_Sync
        
        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number
       
        # Fetch data
        Packet_Type              = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type
        Preamble_Sync_Code_Index = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].SHR.Preamble_Sync_Code_Index
        No_Preamble_Sync_Symbols = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].SHR.No_Preamble_Sync_Symbols
        Data_Rate                = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].SHR.Data_Rate
        SFD                      = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].SHR.SFD

        match Packet_Type.name:
            case "SP0":
                str_Packet_Type = "SP0"                
            case "SP3":
                str_Packet_Type = "SP3"
            case other:
                raise Exception("Unexpected Packet_type %s" % (Packet_Type.name))
                
        # Logging
        self.logger.debug("Packet type is %s" % (str_Packet_Type))
        self.logger.debug("Configure preamble SHR (SYNC+SFD)")    
        self.logger.debug("Preamble Sync Code Index: %d" % (Preamble_Sync_Code_Index))
        self.logger.debug("Preamble Sync Repetions: %d " % (No_Preamble_Sync_Symbols))
        self.logger.debug("Data Rate: %f " % (Data_Rate))
        self.logger.debug("SDF: [%d %d %d %d %d %d %d %d]" % (SFD[0],SFD[1],SFD[2],SFD[3],SFD[4],SFD[5],SFD[6],SFD[7]))

        # SCPI Commands for Litepoint
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PRE ON")
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:SFD:DUR HPRF8")  # tbd.  
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:SFD:TYPE USER")

        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PRE:IND %d" % (Preamble_Sync_Code_Index))
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:SYNC:DUR DUR_%d" % (No_Preamble_Sync_Symbols))  # 16,24,32,48,64,96,128,256,512,1024,4096

        if Data_Rate == 6.81E6:
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:DRATE 6P81")
        else:
            raise Exception("Data rate %f is not supported. Please add support for this data rate" % (Data_Rate))
        
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:SFD:USER (%d,%d,%d,%d,%d,%d,%d,%d)" % (SFD[0],SFD[1],SFD[2],SFD[3],SFD[4],SFD[5],SFD[6],SFD[7]))

        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
               
        if RXBuffer == "0,\"No error\"":            
            return(SUCCESS)            
        else:
            raise Exception("ERROR while configuring SYNC preable")



    def SetRfPhy_Litepoint_Payload(self, Session_Idx,Block_Idx,Round_Idx,Slot_Idx):
    # This function configures the payload      
    # legacy RF-TOOLS : SetRfPhy_Litepoint_Payload

        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number
    
        # Fetch data
        Packet_Type       = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type
        Modulation        = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].PAYLOAD.Modulation
        Ranging_Bit       = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].PAYLOAD.Ranging_Bit
        Data_Rate         = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].PAYLOAD.Data_Rate
        Payload_NoOfBytes = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].PAYLOAD.Payload_NoOfBytes
        Payload_Data      = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].PAYLOAD.Payload_Data
                                         
        match Packet_Type.name:
            case "SP0":
                str_Packet_Type = "SP0"
            case "SP3":
                str_Packet_Type = "SP3"
            case other:
                raise Exception("ERROR while configuring PAYLOAD")
            
        # Logging
        self.logger.debug("Packet type is %s" % (str_Packet_Type))            
        self.logger.debug("Configure Payload (PHR + MHR + PL)")
        self.logger.debug("Payload Num of Bytes: %d " % (Payload_NoOfBytes))
        self.logger.debug("Payload Ranging Bit: %d " % (Ranging_Bit))

        # SCPI Commands for Litepoint  
        # Pay load haeder PHR 

        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR:DRAT:TYPE USER")

        # check and apply data rate 
        if Data_Rate == 0.85E6:
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR:DRATE 0P85")
        else:
           raise Exception("Data rate %f is not supported. Please add support for this data rate" % (Data_Rate))
        
        # check and apply modulation
        match Modulation.name:
            case "BPSK":
                str_Modulation = "BPSK"
                self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR:MOD %s" % str_Modulation)                
            case other:
                raise Exception("Supported modulation is currently only BPSK. Please add new modulation type")
            
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR:RBIT %d" % (Ranging_Bit))

        # SCPI Commands for Litepoint 
        # Pay load MHR + PL + MFR

        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PSDU:DATA:TYPE USER")
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PSDU:MOD %s" % (str_Modulation))

        Payload_Hex = ""
        for i in range (len(Payload_Data)):
            Payload_Hex = Payload_Hex + ("%02X" % Payload_Data[i])            

        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PSDU:LEXT OFF")
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PSDU:DATA:BITS:HEX %s" % (Payload_Hex))

        # We do not need to specifiy the number of PSDU bytes when we apply user data in hex.

        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":    
            return(SUCCESS)
        else:
            raise Exception("ERROR while configuring payload")
        
        
    def SetRfPhy_Litepoint_CalcGap(self,Session_Idx,Block_Idx,Round_Idx,Slot_Idx):
    # This function calculates the gap      
    # legacy RF-TOOLS : SetRfPhy_Litepoint_CalcGap

        T_Chap = 1000/3;  # in us , TChap = 1/3ms

        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number
    
        # Fetch data
        Packet_Type                  =  self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type
        N_Chap_Per_Slot              =  self.UWB[UWB_Protocol_Number].N_Chap_Per_Slot
        N_Slot_Per_Round             =  self.UWB[UWB_Protocol_Number].N_Slot_Per_Round               # desired    slots per round
        N_Configured_Slots_per_Round =  self.UWB[UWB_Protocol_Number].N_Configured_Slots_per_Round   # configured slots per round
    
        # Logging
        self.logger.debug("Dynamic calculation of gap and EMPTY chaps")
        self.logger.debug("Packet type is %s" % (Packet_Type.name))

        if ((Packet_Type.name == "SP0") or (Packet_Type.name == "SP3")):

            # Create temporary waveform file with zero gap
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:GAP (0e-6,0e-6)")
            self.UWB_LP_SCPI_write("UWBP; WAVE:GEN:MMEM \'uwbp_temp.iqvsg\';*WAI")
            self.UWB_LP_SCPI_query("*WAI;*OPC?")

            # Load waveform file and ask for length
            self.UWB_LP_SCPI_write("VSG1; WAVE:LOAD \'/uwbp_temp.iqvsg\'")
            self.UWB_LP_SCPI_query("*WAI;*OPC?")            
            RXBuffer = self.UWB_LP_SCPI_query("VSG1; WAVE:LENG? \'/uwbp_temp.iqvsg\'")           
            N_Samples_Waveform_File = self.atoi(RXBuffer)

            # Delete waveform file from disk
            self.UWB_LP_SCPI_write("SYS; MMEM:DEL \'%s\'" % ("uwbp_temp.iqvsg"))
            self.UWB_LP_SCPI_query("*WAI;*OPC?")                     
            self.logger.debug("Temporary file %s has been deleted from Litepoint hard disk" % ("uwbp_temp.iqvsg")) 

            # Ask VSG for the sampling rate
            RXBuffer = self.UWB_LP_SCPI_query("VSG1; SRAT?")
            Sampling_Rate = self.atoi(RXBuffer)

            # Calculate gab
            T_Chap_Target = T_Chap;                                         # in us (!)
            T_Chap_Target = T_Chap_Target+1;                                # add additional 1 us to be on the save side. The number of samples will be 
            T_Waveform_File = (1E6*N_Samples_Waveform_File)/Sampling_Rate   # in us (!)
    
            # Check for consistency
            if T_Waveform_File < T_Chap_Target:
                T_Gap=T_Chap_Target-T_Waveform_File
                N_Empty_Chaps=N_Chap_Per_Slot-1
                # Write numbers back to global structure
                self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].GapTime=T_Gap
                self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].NoOfEmptyChaps=N_Empty_Chaps
            else:
                raise Exception("The length of the waveform is %f us, but is expeced be shorther than one chap [333us]" % (T_Waveform_File))
            
            # Logging
            self.logger.debug("Number of chaps per slot : %d " % (N_Chap_Per_Slot))
            self.logger.debug("Waveform file has : %d samples" % (N_Samples_Waveform_File))
            self.logger.debug("Sampling Rate is : %d samples/sec" % (Sampling_Rate))
            self.logger.debug("Length of waveform is %f us" % (T_Waveform_File))
            self.logger.debug("Desired Slot Time (1chap + 1us): %f us" % (T_Chap_Target))
            self.logger.debug("Gap time calulation for 1st chap: %f us" % (T_Gap))
            self.logger.debug("Number of empty chaps for slot index %d : %d chaps" % (Slot_Idx,N_Empty_Chaps))

            # Finaly check for SCPI communication errors
            RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
            if RXBuffer == "0,\"No error\"":    
                return(SUCCESS)
            else:
                raise Exception("Error during calculation of the gap")    

        if ((Packet_Type.name == "EMPTY") or (Packet_Type.name == "RESPONDER")):

            #  Write default values back to global structure
            self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].GapTime = 0
            self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].NoOfEmptyChaps = N_Chap_Per_Slot

            # check if this is the last slot
            if Slot_Idx == (N_Configured_Slots_per_Round-1):
                   
                self.logger.debug("Slot %d is the last slot",Slot_Idx)
           
                # this is the last slot          
                if N_Slot_Per_Round > N_Configured_Slots_per_Round:
                                 
                    # this is the last slot and we need to add exta gap time to fill the gap until next round starts
                    N_Missing_Slots = N_Slot_Per_Round - (N_Configured_Slots_per_Round-1)
                    N_Missing_Chaps = N_Missing_Slots * N_Chap_Per_Slot    
                    
                    self.logger.debug("We need to add an additional gap")
                    self.logger.debug("Missing slots  : %d" % (N_Missing_Slots))       
                    self.logger.debug("Misssing Chaps : %d" % (N_Missing_Chaps))
                                                      
                    #  Write to global structure
                    self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].GapTime=0
                    self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].NoOfEmptyChaps=N_Missing_Chaps
            
            # Logging
            self.logger.debug("Dynamic calculation of gap and EMPTY chaps")
            self.logger.debug("Slot %d is configured to have %d empty chaps" % (Slot_Idx, self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].NoOfEmptyChaps))
            return(SUCCESS) 
        
        raise Exception("No handler for packet type %s" % (Packet_Type.name))
    
    def SetRfPhy_Litepoint_StoreWaveFile(self, Session_Idx,Block_Idx,Round_Idx,Slot_Idx):
    # This function stores a waveform file
    # legacy RF-TOOLS : SetRfPhy_Litepoint_StoreWaveFile    

        # Logging
        self.logger.debug("Storing waveform file")

        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number

        # Fetch data
        T_Gap = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].GapTime; 

        # Construct Filename
        FileName = "uwbp_S%03d_B%03d_R%03d_S%03d_datachap.iqvsg" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx)

        # Create temporary waveform file with automatic calculated gap
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:GAP (0e-6,%fe-6)" % (T_Gap))
        self.UWB_LP_SCPI_write("UWBP; WAVE:GEN:MMEM \'%s\'" % (FileName))
        self.UWB_LP_SCPI_query("*WAI;*OPC?")

        # Debug
        self.logger.debug("Storing Waveform file of session %d, block %d, round %d, slot %d" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx))
        self.logger.debug("Filename: %s" % (FileName))

        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if (RXBuffer == "0,\"No error\""):   
            # Store FileName into stuct 
            self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentDataFileName = FileName
            # Logging
            self.logger.debug("Empty waveform (%s) file was created successfully" % (FileName))
            return(SUCCESS)
        else:
            raise Exception("Error during saving wave segment file %s" % (FileName))
        



    def SetRfPhy_Litepoint_CreateEmptyChap(self, Session_Idx,Block_Idx,Round_Idx,Slot_Idx):
    # This function creates an "empty" dummy packet
    # As it is not possible with Litepoint to create relly an empty chap witout any modulation (tbd.) some kind of WA is used
    # WA: A wavefrom file is generated with a gap of ~334us in front which will be played only for the first 333.333us (TChap,800000 samples).
    # Second WA that need to be applied:
    # It is not possible to add the same file more than one time to a WaveList.
    # For each empty chap we have to create a new file and give him unique file name.    
    # legacy RF-TOOLS : SetRfPhy_Litepoint_CreateEmptyChap
        
        # Logging 
        self.logger.debug("Creating empty chap")    

        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number
                
        # we need to initialze quite a lot of settings here as the setttings might be 
        # changed by previous packet configuration
        
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PRE:IND 1")          # dummy
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:DRATE 6P81")         # dummy
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:SYNC:DUR DUR_16")    # dummy
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:SFD:DUR SHORT")      # dummy
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PHR OFF")            # dummy
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:PSDU:NBYT 0")        # dummy
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:PCON 0")         # dummy
        self.UWB_LP_SCPI_write("UWBP; UWBP;CONF:WAVE:NSTS 0")        # dummy

        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:GAP (334e-6,0e-6)")  # 334 us gap in front

        # Construct Filename
        FileName = "uwbp_S%03d_B%03d_R%03d_S%03d_emptychap.iqvsg" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx)
        self.UWB_LP_SCPI_write("UWBP; WAVE:GEN:MMEM \'%s\'" % (FileName))
        self.UWB_LP_SCPI_query("*WAI;*OPC?")

        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":   
            # Store FileName into stuct 
            self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentEmptChapFileName = FileName
    
            self.logger.debug("Empty waveform (%s) file was created successfully" % (FileName))
            return(SUCCESS)
    
        else:
            raise Exception("Error during creation of an \'empty\' wavefrom file")




    def SetRfPhy_Litepoint_STS(self, Session_Idx,Block_Idx,Round_Idx,Slot_Idx):
    # This function creates STS packet data
    # legacy RF-TOOLS : SetRfPhy_Litepoint_STS   
        
        # Logging 
        self.logger.debug("Creating STS")  
        
        # Get protocol number
        UWB_Protocol_Number = self.UWB_Protocol_Number   

        # Fetch data
        Packet_Type               = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type
        STS_NoOfBits              = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].STS.STS_NoOfBits
        STS_Type                  = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].STS.STS_Type

        STS_Data                  = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].STS.STS_Data
        STS_phyHrpUwbStsVCounter  = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].STS.STS_phyHrpUwbStsVCounter
        STS_phyHrpUwbStsKey       = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].STS.STS_phyHrpUwbStsKey
        STS_phyHrpUwbStsVUpper96  = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].STS.STS_phyHrpUwbStsVUpper96
        
        # Logging
        self.logger.debug("Packet type is %s" % (Packet_Type.name)) 
        self.logger.debug("STS type is %s" % (STS_Type.name))  

        # send to instrument
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:AGAP:BITS OFF")
        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:AGAP:LENG 0")        
                          
        # check and apply modulation
        match STS_Type.name:
            case "STS_IEEE":   
               self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:GEN IEEE")
            case "STS_USER":
                self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:GEN USER")
            case other:
                raise Exception("%s STS type is not supported" % (STS_Type.name))
            
        if STS_Type.name == "STS_USER":       

            # The user defined STS is not fully evaluated:
            # Basically the user can specify the STS bits
            # These bits are not processed and are not spreaded
            # They are clearly visible 1:1: is the IQ data stream
            # [LSByte....MSByte] -> [STS_start...STS_End]
            # The STS sequence is normaly 64 us (tbd.)
            # If the number of given bits does not fit to the 64us....the bits are simply repeated
            
            # not sure if this is needed for USER defined STS
            #match Packet_Type.name:
            #    case "SP0":
            #        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:PCON 0")
            #    case "SP3":
            #        self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:PCON 0")    # PCON = ???
            #    case other:
            #        raise Exception("ERROR : Not supported packet type %s" % (Packet_Type.name))

            STS_NoOfBytes=STS_NoOfBits//8      # integer div
            STS_RemainingBits=STS_NoOfBits%8   # modulo rest
            
            # Logging           
            self.logger.debug("STS_USER Number of Bytes : %d",STS_NoOfBytes)
            self.logger.debug("STS_USER RemainingBits   : %d",STS_RemainingBits)

            # convert byte array to bit string
            # loop over data bytes
            BitStream = ""
            for i in range(STS_NoOfBytes):                
                DataByte=STS_Data[i]                
      
                # convert byte to bit string
                bit0 = ((DataByte & 0x01) >> 0)+48;  # LSB
                bit1 = ((DataByte & 0x02) >> 1)+48;
                bit2 = ((DataByte & 0x04) >> 2)+48;
                bit3 = ((DataByte & 0x08) >> 3)+48;
                bit4 = ((DataByte & 0x10) >> 4)+48;  
                bit5 = ((DataByte & 0x20) >> 5)+48;
                bit6 = ((DataByte & 0x40) >> 6)+48;
                bit7 = ((DataByte & 0x80) >> 7)+48;
      
                strTemp = "%c,%c,%c,%c,%c,%c,%c,%c," % (bit7,bit6,bit5,bit4, bit3,bit2,bit1,bit0) 
                #print("Data : %02X %s" % (DataByte,strTemp))
                BitStream = BitStream + strTemp
                #print("%s" % (BitStream))

            # handling of remaining bits
            if STS_RemainingBits>0:
                # handle remaining bits separately 
                DataByte = STS_Data[STS_NoOfBytes]
                #print("Last byte: 0x%02X" % (DataByte))
                BitMask = 0b10000000 # MSB
                #print("Mask: 0x%02X" % (BitMask))

                for i in range(8,STS_RemainingBits,-1):    
                    masked_byte =  DataByte & BitMask                               
                    bit         =  (masked_byte >> (i-1)) + 48  # LSB
                    #print("i: %d mask 0x%02X mbyte 0x%02X bit 0b%c" % (i,BitMask,masked_byte,bit))
                    BitMask = BitMask >> 1
                    strTemp = "%c," % bit; 
                    BitStream = BitStream+strTemp 
        
            # remove last comma
            BitStream=BitStream[:-1]
   
            # Logging
            self.logger.debug("Configure STS")
            self.logger.debug("STS NoOfBits : %d" % (STS_NoOfBits))
            self.logger.debug("STS Data Bits : %s" % (BitStream))

            # Write bits to instument
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:BITS (%s)" % (BitStream))

            # Query for debugging only          
            self.UWB_LP_SCPI_query("*WAI;*OPC?")
            self.UWB_LP_SCPI_query("UWBP; CONF:WAVE:STS:PCON?") 
            self.UWB_LP_SCPI_query("UWBP; CONF:WAVE:NSTS?") 
            #self.UWB_LP_SCPI_query("UWBP; CONF:WAVE:STS:BITS?")  # The readback of the STS bits does not work, Litepoint seems to have a FW bug here
                         
        if STS_Type.name == "STS_IEEE":
             
            # write phyHrpUwbStsVCounter (Counter) to instrument
            strTemp = bytes(STS_phyHrpUwbStsVCounter).hex()
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:SEGM1:COUN %s" % (strTemp))

            # write phyHrpUwbStsKey (Key) to instrument
            strTemp = bytes(STS_phyHrpUwbStsKey).hex()
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:SEGM1:KEY %s" %(strTemp))
                       
            # write phyHrpUwbStsVUpper96 (UDATa) to instrument
            strTemp = bytes(STS_phyHrpUwbStsVUpper96).hex()
            self.UWB_LP_SCPI_write("UWBP; CONF:WAVE:STS:SEGM1:UDAT %s" % (strTemp))

        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":               
            return(SUCCESS)
        else:
            raise Exception("Error during configuring STS")
        

    def ResetPlusConfigureRfSwitch(self):
    # This function programms the external Litepoint RF switch IQ5631 accessory FESW (so called "Power and delay control module")
    # legacy RF-TOOLS : InstrumentInterface_Initialize

        # Logging
        self.logger.debug("Initialize intrument LP_IQGIGIF_UWB")

        # Reset 
        self.UWB_LP_SCPI_write("*RST;*CLS;*WAI")
        self.UWB_LP_SCPI_query("*IDN?")
                
        # RF routing 
        self.UWB_LP_SCPI_write("ROUT1;PORT:RES RF1A,VSA1")
        self.UWB_LP_SCPI_write("ROUT1;PORT:RES RF2A,VSG1")
  
        mode = "normal"   # loopback, normal
        
        if (mode == "loopback"):
            # FESW RF routing for loopback (probably beeing moved to another FU)
            self.logger.debug("Configure FESW for loopback")
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF1A,OFF")
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF2A,OFF")
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF3A,RF2")  # RF loop RF3A to RF2
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF4A,RF1")  # RF loop RF4A to RF1
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF5A,OFF")

        if (mode == "normal"):
            self.logger.debug("Configure FESW for normal output/input (NO LOOPBACK)")
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF1A,RF2") # RF1A is output
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF2A,RF1") # RF2A is input
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF3A,OFF")  
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF4A,OFF")  
            self.UWB_LP_SCPI_write("FESW1;PORT:RES RF5A,OFF")

  
        self.UWB_LP_SCPI_write("FESW1;GAIN RF1A,-20")
        self.UWB_LP_SCPI_write("FESW1;GAIN RF2A,-20")
        self.UWB_LP_SCPI_write("FESW1;GAIN RF3A,-20")
        self.UWB_LP_SCPI_write("FESW1;GAIN RF4A,-20")
        self.UWB_LP_SCPI_write("VSG1;POW:LEV 10");           # tbd.
        self.UWB_LP_SCPI_write("*WAI"); 
        
        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":               
            return(SUCCESS)
        else:
            raise Exception("ERROR during initialization of LP_IQGIGIF_UWB")
        
    def SetRfPhy_Litepoint_Conf_Wavelist(self):
    # This function configures the wave list
    # legacy RF-TOOLS : SetRfPhy_Litepoint_Conf_Wavelist
        
        UWB_Protocol_Number = self.UWB_Protocol_Number
        
        # Init 
        Session_Idx           = 0
        Block_Idx             = 0
        Round_Idx             = 0
        Slot_Idx              = 0
        WaveSegment_Idx       = 1  # Wave segments start with segment no 1

        # Fetch data
        N_Chap_Per_Slot              = self.UWB[UWB_Protocol_Number].N_Chap_Per_Slot
        N_Slot_Per_Round             = self.UWB[UWB_Protocol_Number].N_Slot_Per_Round
        N_Configured_Slots_per_Round = self.UWB[UWB_Protocol_Number].N_Configured_Slots_per_Round
        N_Rounds_per_Block           = self.UWB[UWB_Protocol_Number].N_Rounds_per_Block
        N_Blocks_per_Session         = self.UWB[UWB_Protocol_Number].N_Blocks_per_Session
        N_of_Sessions                = self.UWB[UWB_Protocol_Number].N_of_Sessions
        Sampling_Rate                = self.UWB[UWB_Protocol_Number].Sampling_Rate

        # Logging
        self.logger.debug("Configure Wave List")

        # Calculate number of samples of one Chap 
        # At 2.4 GS/sec this should be 800 000 samples
        Samples_Of_One_Chap = ((Sampling_Rate/1E3)/3)

        # Logging
        self.logger.debug("Calculated samples_Of_One_Chap : %d" % (Samples_Of_One_Chap))

        # Calculate Index of last WaveSegment
        N_WaveSegments_Total = self.SetRfPhy_Litepoint_Calculate_TotalNum_of_WaveSegments()

        self.UWB_LP_SCPI_write("VSG; WAVE:DEL:ALL")
        self.UWB_LP_SCPI_write("VSG; WLIS:CAT:DEL:ALL")
        self.UWB_LP_SCPI_query("*WAI;*OPC?")

        # Session loop
        for Session_Idx in range(N_of_Sessions):            
            # Loop over rounds 
            for Block_Idx in range(N_Blocks_per_Session):
                # Loop over rounds  
                for Round_Idx in range(N_Rounds_per_Block):
                    # Loop over slots
                    for Slot_Idx in range( N_Configured_Slots_per_Round): 

                        # Logging
                        self.logger.debug("Configure: Session %d, Block %d, Round %d, Slot %d" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx))

                        # Fetch data    
                        Packet_Type        = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type
                        N_Empty_Chaps      = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].NoOfEmptyChaps

                        if ((Packet_Type.name == "SP0") or (Packet_Type.name == "SP3")):
                            FileName_Data = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentDataFileName
                        else:
                            FileName_Data = "no file required"

                        FileName_EmptyChap = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentEmptChapFileName
                                                    
                        # Debug
                        self.logger.debug("Packet: %s, Data File %s" % (Packet_Type.name,FileName_Data))
                        self.logger.debug("Packet: %s, Empty Chap File %s" % (Packet_Type.name,FileName_EmptyChap))
                        self.logger.debug("NoOfEmptyChaps : %d" % (N_Empty_Chaps))
                        self.logger.debug("Sampling Rate : %d" % (Sampling_Rate))
                        self.logger.debug("Num of samples of one chap : %d" % (Samples_Of_One_Chap))

                        if ((Packet_Type.name == "SP0") or (Packet_Type.name == "SP3")):

                            # ***************************************
                            # Packet with data samples (1chap)
                            # ***************************************

                            # Start Sample
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:START 0" % (WaveSegment_Idx))
        
                            # Length
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:LENGTH %d" % (WaveSegment_Idx,Samples_Of_One_Chap))
        
                            # Repetitons
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:REP 0" % (WaveSegment_Idx))
        
                            # Pointer to Next WSEG
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:NEXT %d" % (WaveSegment_Idx,WaveSegment_Idx+1))
        
                            # Load File
                            self.UWB_LP_SCPI_write("VSG; WAVE:LOAD:ADD \'%s\',WSEG%d" % (FileName_Data,WaveSegment_Idx))

                            # Save Wave segment
                            self.UWB_LP_SCPI_write("VSG; WLIS:SEGM:SAVE 'WSEG%d'" % (WaveSegment_Idx))
        
                            # Increment WaveSegement index
                            WaveSegment_Idx = WaveSegment_Idx + 1

                            # ***************************************
                            # Append Empty chaps to get one slot
                            # ***************************************
          
                            # Start Sample
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:START 0" % (WaveSegment_Idx))

                            # Length
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:LENGTH %d" % (WaveSegment_Idx,Samples_Of_One_Chap))

                            # Repetitons
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:REP %d" % (WaveSegment_Idx,N_Empty_Chaps-1))


                            # Pointer to Next WSEG
                            if (WaveSegment_Idx == N_WaveSegments_Total):
                                # this is the last wave segment
                                self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:NEXT %d" % (WaveSegment_Idx,0))
                            else:          
                                self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:NEXT %d" % (WaveSegment_Idx,WaveSegment_Idx+1))
          
                            # Load File
                            self.UWB_LP_SCPI_write("VSG; WAVE:LOAD:ADD \'%s\',WSEG%d" % (FileName_EmptyChap,WaveSegment_Idx))
        
                            # Save Wave segment
                            self.UWB_LP_SCPI_write("VSG; WLIS:SEGM:SAVE 'WSEG%d'" % (WaveSegment_Idx))

                            # Increment WaveSegement index
                            WaveSegment_Idx = WaveSegment_Idx + 1

                        if ((Packet_Type.name == "EMPTY") or (Packet_Type.name == "RESPONDER")):

                            self.logger.debug("Packet type is %s, adding Empty chap(s)" % (Packet_Type.name))
                       
                            # Start Sample
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:START 0" % (WaveSegment_Idx))

                            # Length
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:LENGTH %d" % (WaveSegment_Idx,Samples_Of_One_Chap))

                            # Repetitons                                                                               
                            self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:REP %d" % (WaveSegment_Idx,N_Empty_Chaps-1))

                            # Pointer to Next WSEG
                            if (WaveSegment_Idx == N_WaveSegments_Total):
                                # this is the last wave segment
                                self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:NEXT %d" % (WaveSegment_Idx,0))          
                            else:
                                self.UWB_LP_SCPI_write("VSG; WLIS:WSEG%d:NEXT %d" % (WaveSegment_Idx,WaveSegment_Idx+1))
          
                            # Load File
                            self.UWB_LP_SCPI_write("VSG; WAVE:LOAD:ADD \'%s\',WSEG%d" % (FileName_EmptyChap,WaveSegment_Idx))

                            # Save Wave segment
                            self.UWB_LP_SCPI_write("VSG; WLIS:SEGM:SAVE 'WSEG%d'" % (WaveSegment_Idx))
        
                            # Increment WaveSegement index
                            WaveSegment_Idx = WaveSegment_Idx + 1

        # Check for SCPI Errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer != "0,\"No error\"":               
            raise Exception("Error during generation of the wave list")

        # Check number of segments in the WaveList 
        RXBuffer=self.UWB_LP_SCPI_query("VSG; WLISt:SEGMent:LIST:COUNt?")
        Readback_NoOfSegments =  self.atoi(RXBuffer)

        if (N_WaveSegments_Total != Readback_NoOfSegments):
            raise Exception("ERROR : WaveList has %d segments. Expecting %d segments" % (Readback_NoOfSegments,N_WaveSegments_Total))
   
        return(SUCCESS)



    def SetRfPhy_Litepoint_Calculate_TotalNum_of_WaveSegments(self):
    # This function calcualtes the number of wave segments
    # legacy RF-TOOLS : SetRfPhy_Litepoint_Calculate_TotalNum_of_WaveSegments

        UWB_Protocol_Number = self.UWB_Protocol_Number

        # Fetch data
        N_Chap_Per_Slot              = self.UWB[UWB_Protocol_Number].N_Chap_Per_Slot
        N_Slot_Per_Round             = self.UWB[UWB_Protocol_Number].N_Slot_Per_Round
        N_Configured_Slots_per_Round = self.UWB[UWB_Protocol_Number].N_Configured_Slots_per_Round
        N_Rounds_per_Block           = self.UWB[UWB_Protocol_Number].N_Rounds_per_Block
        N_Blocks_per_Session         = self.UWB[UWB_Protocol_Number].N_Blocks_per_Session
        N_of_Sessions                = self.UWB[UWB_Protocol_Number].N_of_Sessions

        # Logging
        self.logger.debug("Calculate total number of WaveSegments")


        WaveSegment_Counter = 0     # Info: Litepoint supports max. 250 wave segments

        # Session loop
        for Session_Idx in range(N_of_Sessions):            
            # Loop over rounds 
            for Block_Idx in range(N_Blocks_per_Session):
                # Loop over rounds  
                for Round_Idx in range(N_Rounds_per_Block):
                    # Loop over slots
                    for Slot_Idx in range(N_Configured_Slots_per_Round): 

                        # Logging
                        self.logger.debug("Session %d; Block %d; Round %d; Slot %d" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx))
                                                
                        # Fetch data
                        Packet_Type     = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type
                        N_Empty_Chaps   = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].NoOfEmptyChaps

                        # Logging
                        self.logger.debug("Session %d; Block %d; Round %d; Slot %d -> NoOfEmptyChaps %d" % (Session_Idx,Block_Idx,Round_Idx,Slot_Idx,N_Empty_Chaps))

                        if ((Packet_Type.name == "SP0") or (Packet_Type.name == "SP3")):
                           WaveSegment_Counter = WaveSegment_Counter + 2                # SP0/3 + 1 Empty

                        if ((Packet_Type.name == "EMPTY") or (Packet_Type.name == "RESPONDER")):
                           WaveSegment_Counter = WaveSegment_Counter + 1                # 1 Empty

        # Logging
        self.logger.debug("Total Number of WaveSements : %d" % (WaveSegment_Counter))

        return(WaveSegment_Counter)


                
        
    def SetRfPhy_Litepoint_Run_Wavelist(self, repetitons=1):
    # This function executes the wave list
    # Parameter "repetitons" is the number of repetions (0 = endless loop, N = [1..Inf.] Play wavelist N times )
    # legacy RF-TOOLS : SetRfPhy_Litepoint_Run_Wavelist
        
        # Logging
        self.logger.debug("Run/execute the wave list")

        # Query Wavelist
        RXBuffer=self.UWB_LP_SCPI_query("VSG; WLISt:CATalog:LIST?")
        # Logging
        self.logger.debug("WaveList: %s" % (RXBuffer))

        # Debug Info (to be removed, tbd.)
        self.SetRfPhy_Litepoint_Wavelist_Get_Info()
 
        # Configure External Trigger output (to be removed)
        self.UWB_LP_SCPI_write("BP; MARK:EXT1:SOUR SLOT1")
        self.UWB_LP_SCPI_write("BP; MARK:EXT2:SOUR OFF")
        self.UWB_LP_SCPI_write("BP; MARK:EXT3:SOUR OFF")
        self.UWB_LP_SCPI_write("BP; MARK:EXT4:SOUR OFF")
        self.UWB_LP_SCPI_write("VSG; MARK:EXT1 WSEG1")

        # VSA config for debugging (to be removed)
        self.UWB_LP_SCPI_write("VSA1;RLEV -25")
        self.UWB_LP_SCPI_write("VSA1;FREQ 6489.6e6")
        self.UWB_LP_SCPI_write("VSA1;CAPT:TIME 5e-03")   # capture time in seconds, max. is 30ms @ 2.4GS/sec for the analyzer
        self.UWB_LP_SCPI_write("VSA1;TRIG:SOUR WSEG1")

        self.UWB_LP_SCPI_write("VSA1;CHAN1")
        self.UWB_LP_SCPI_write("VSA1;INIT:NBL")
    
        self.UWB_LP_SCPI_write("VSG; WLISt:COUNt %d" % (repetitons))
        self.UWB_LP_SCPI_write("VSG; WLISt:EXEC ON,\'WSEG1\'")

        if (repetitons == 0):
            self.logger.debug("Wave list is running in endless loop")
        else:
            self.logger.debug("Wave list was executed %d times" % (repetitons))

        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":   

            RF1A = self.UWB_LP_SCPI_query("FESW1;PORT:RES? RF1A")
            RF2A = self.UWB_LP_SCPI_query("FESW1;PORT:RES? RF2A")
            RF3A = self.UWB_LP_SCPI_query("FESW1;PORT:RES? RF3A")
            RF4A = self.UWB_LP_SCPI_query("FESW1;PORT:RES? RF4A")
            RF5A = self.UWB_LP_SCPI_query("FESW1;PORT:RES? RF5A")

            VSA_RecordLength = self.UWB_LP_SCPI_query("VSA1;CAPT:TIME?")

            mode = "*  ERROR: wrong FE configuration                      *"
            if ((RF1A=="OFF") and (RF2A=="OFF") and (RF3A=="RF2") and (RF4A=="RF1") and (RF5A=="OFF")):
                mode = "*  Loopback mode                                      *"
            if ((RF1A=="RF2") and (RF2A=="RF1") and (RF3A=="OFF") and (RF4A=="OFF") and (RF5A=="OFF")):
                mode = "*  No Loopback mode                                   *"
            
            self.logger.debug("*******************************************************")
            self.logger.debug("* Configuration of the frontend switch FESW:          *")   
            self.logger.debug("*                                                     *")   
            self.logger.debug(mode)
            self.logger.debug("*                                                     *")                     
            self.logger.debug("*  RF1A: %3s                                          *" % (RF1A))
            self.logger.debug("*  RF2A: %3s                                          *" % (RF2A)) 
            self.logger.debug("*  RF3A: %3s                                          *" % (RF3A)) 
            self.logger.debug("*  RF4A: %3s                                          *" % (RF4A)) 
            self.logger.debug("*  RF5A: %3s                                          *" % (RF5A)) 
            self.logger.debug("*                                                     *")
            self.logger.debug("* For Loopback mode:                                  *")
            self.logger.debug("*  To check timing in the VSA:                        *")
            self.logger.debug("*  Go to VSA -> Results                               *")
            self.logger.debug("*  Right mouse click on the graphs -> Clear           *")
            self.logger.debug("*  From the Results select a new graph (drag&drop)    *")
            self.logger.debug("*  The RF should have been already correctly captured *")
            self.logger.debug("*                                                     *")
            self.logger.debug("* The VSA capture time is limted to ~ 30ms @ 2.4 GS/s *")
            self.logger.debug("* Record length is set to %15s sec *" % (VSA_RecordLength))
            self.logger.debug("*                                                     *")
            if (repetitons == 0):
                self.logger.debug("* Wave list is still running in endless loop          *")
            else:
                self.logger.debug("* Wave list was executed %2d times                     *" % (repetitons))
            self.logger.debug("*******************************************************")
            

            return(SUCCESS)
        else:
            raise Exception("ERROR during execution of WaveList")
        
        

    def SetRfPhy_Litepoint_Wavelist_Get_Info(self):
    # This function collects information about the current wave list
    # legacy RF-TOOLS : SetRfPhy_Litepoint_Wavelist_Get_Info
        
        # Logging
        self.logger.debug("Get wave list information")
        
        RXBuffer=self.UWB_LP_SCPI_query("VSG; WLISt:SEGMent:LIST:COUNt?")
        Readback_NoOfSegments = self.atoi(RXBuffer)

        # Const
        MaxNoOfSegments = 20
 
        # limit the number of readouts
        #if (Readback_NoOfSegments > MaxNoOfSegments):
        #    Readback_NoOfSegments = MaxNoOfSegments

        # List of strings for later printout
        DebugStrings = []    

        for WSEG_Idx in range(1,Readback_NoOfSegments+1):
                
            # Get FileName
            RXBuffer=self.UWB_LP_SCPI_query("VSG; WLIS:WSEG%d:DATA?" % (WSEG_Idx))
            FileName = RXBuffer
      
            # Get Length
            RXBuffer=self.UWB_LP_SCPI_query("VSG; WLIS:WSEG%d:LENGTH?" % (WSEG_Idx))
            Length=self.atoi(RXBuffer)

            # Get Start
            RXBuffer=self.UWB_LP_SCPI_query("VSG; WLIS:WSEG%d:STAR?" % (WSEG_Idx))
            StartSample=self.atoi(RXBuffer)

            # Get No of Repetitions
            RXBuffer=self.UWB_LP_SCPI_query("VSG; WLIS:WSEG%d:REP?" % (WSEG_Idx))
            Repetitions=self.atoi(RXBuffer)

            # TODO read out all other params
    
            # Save debug string into the list
            DebugStrings.append("WSEG%2d : FILE %50s : Length %7d : Start %7d : Rep %3d" % (WSEG_Idx,FileName,Length,StartSample,Repetitions))


        # Logging
        for i in range(len(DebugStrings)):
            self.logger.debug(DebugStrings[i])

        return(SUCCESS)
    
    def SetRfPhy_Litepoint_DeleteWaveFiles(self):
    # This function deletes the created waveform files from the harddisk on the litepoint instrument
    # legacy RF-TOOLS : SetRfPhy_Litepoint_DeleteWaveFiles
        
        UWB_Protocol_Number = self.UWB_Protocol_Number
               
        # Fetch data
        N_Chap_Per_Slot              = self.UWB[UWB_Protocol_Number].N_Chap_Per_Slot
        N_Slot_Per_Round             = self.UWB[UWB_Protocol_Number].N_Slot_Per_Round
        N_Configured_Slots_per_Round = self.UWB[UWB_Protocol_Number].N_Configured_Slots_per_Round
        N_Rounds_per_Block           = self.UWB[UWB_Protocol_Number].N_Rounds_per_Block
        N_Blocks_per_Session         = self.UWB[UWB_Protocol_Number].N_Blocks_per_Session
        N_of_Sessions                = self.UWB[UWB_Protocol_Number].N_of_Sessions
    
        # Logging
        self.logger.debug("Deleting Waveform files from Litepoint HD")
        
        WaveSegment_Counter = 0
    
        # Session loop
        for Session_Idx in range(N_of_Sessions):            
            # Loop over rounds 
            for Block_Idx in range(N_Blocks_per_Session):
                # Loop over rounds  
                for Round_Idx in range(N_Rounds_per_Block):
                    # Loop over slots
                    for Slot_Idx in range( N_Configured_Slots_per_Round): 

                        # Fetch data
                        Packet_Type = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].Packet_Type

                        if ((Packet_Type.name == "SP0") or (Packet_Type.name == "SP3")):
                   
                            # Delete Data file
                            FileName = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentDataFileName
                            self.UWB_LP_SCPI_write("SYS; MMEM:DEL \'%s\'" % (FileName))
                            self.UWB_LP_SCPI_query("*WAI;*OPC?")
                            self.logger.debug("Deleting %s" % (FileName)) # Logging

                            # Delete Empty Chap file
                            FileName = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentEmptChapFileName
                            self.UWB_LP_SCPI_write("SYS; MMEM:DEL \'%s\'" % (FileName))
                            self.UWB_LP_SCPI_query("*WAI;*OPC?")                     
                            self.logger.debug("Deleting %s" % (FileName)) # Logging

                        if ((Packet_Type.name == "EMPTY") or (Packet_Type.name == "RESPONDER")):
                  
                            # Delete Empty Chap file
                            FileName = self.UWB[UWB_Protocol_Number].Session[Session_Idx].Block[Block_Idx].Round[Round_Idx].Slot[Slot_Idx].WaveSegmentEmptChapFileName
                            self.UWB_LP_SCPI_write("SYS; MMEM:DEL \'%s\'" % (FileName))
                            self.UWB_LP_SCPI_query("*WAI;*OPC?")                     
                            self.logger.debug("Deleting %s" % (FileName)) # Logging

        self.logger.debug("Total Number of WaveSements : %d" % (WaveSegment_Counter))
    
        # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":   
            self.logger.debug("All file have been correly deleted from Litepoint HD")            
            return(SUCCESS)
        else:
            raise Exception("Error during deleting waveform files from Litepoint hard disk")
        

    def SetRfPhy_Litepoint_VSG_OutputPower(self,Power_in_dBm):
    # This function programms the output power of the Litepoint VSG
    # legacy RF-TOOLS : no such function

        self.logger.debug("Setting output power of VSG to %d dBm" % (Power_in_dBm))
        self.UWB_LP_SCPI_write("VSG1;POW:LEV %d" % (Power_in_dBm))

         # Finaly check for SCPI communication errors
        RXBuffer=self.UWB_LP_SCPI_query("SYSTem:ERRor:ALL?")    
        if RXBuffer == "0,\"No error\"":   
            #self.logger.debug("Output power has been successfully set")            
            return(SUCCESS)
        else:
            raise Exception("Error during setting output power to %d dBm,. Valid range is -120..+10 dBm" % (Power_in_dBm))
    
    def SetRfPhy_Litepoint_VSG_StopWaveList(self):
    # This function programms stops the execution of the WaveList
    # legacy RF-TOOLS : no such function

        self.logger.debug("Stopping execution of WaveList")
        self.UWB_LP_SCPI_write("VSG1;WAVE:EXEC OFF")




    def UWB_LP_SCPI_query(self,str_command): 
    # Wrapper function to query SCPI commands from Litepoint UWB device      
        #time.sleep(0.3)   
        device = "Litepoint_UWB"         
        # Send Query command
        status, ret = self.user_thread.send_and_wait_for_response(device,str_command+"\n", blocking=True, time_for_timeout=5)
        # remove termination char
        ret = ret[:-1]
        # Logger        
        self.logger.debug("%s -->%s<--" % (str_command,ret))                   
        return(ret)
    
    
    def UWB_LP_SCPI_write(self,str_command):
    # Wrapper function to send SCPI commands to Litepoint UWB device 
        #time.sleep(0.2)         
        device = "Litepoint_UWB"                   
        # Send command 
        self.user_thread.send_message(device,str_command+"\n")
        # Logger        
        self.logger.debug("%s" % (str_command))

    def atoi(self, str):
    # Conversion from string to number
        resultant = 0
        for i in range(len(str)):
            resultant = resultant * 10 + (ord(str[i]) - ord('0'))        # ASCII substraction 
        return resultant        










    
