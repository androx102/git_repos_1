from GUI.dynamic_widgets import *


class main_menu_widget(QMenuBar):
    main_menu_signal = pyqtSignal(int)
    def __init__(self, parent:QWidget, *args):
        super().__init__(parent, *args)
        self.initUI()
        self.bind_slots_and_signals()

    def initUI(self):
        #self.app_item = self.addMenu("App")
        self.start_action = self.addAction("Start sim")
        self.stop_action = self.addAction("Stop sim")
        self.stop_action.setDisabled(True)
        self.start_user_script_action = self.addAction("Start_us")
        self.start_user_script_action.setDisabled(True)
        self.stop_user_script_action = self.addAction("Stop_us")
        self.stop_user_script_action.setDisabled(True)
        #self.save_item = self.addMenu("Save")
        #self.save_as_item = self.addMenu("Save as")
        #self.load_config_item = self.addMenu("Load cfg")
        #self.options_item = self.addMenu("Options")
     
    def bind_slots_and_signals(self):
        self.start_action.triggered.connect(lambda: self.main_menu_signal.emit(11))
        self.stop_action.triggered.connect(lambda: self.main_menu_signal.emit(12))
        self.start_user_script_action.triggered.connect(lambda: self.main_menu_signal.emit(13))
        self.stop_user_script_action.triggered.connect(lambda: self.main_menu_signal.emit(14))

    def simulation_started_state(self):
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.start_user_script_action.setEnabled(True)
        self.stop_user_script_action.setEnabled(False)

    def simulation_stop_state(self):
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.start_user_script_action.setEnabled(False)
        self.stop_user_script_action.setEnabled(False)
    
    def user_script_start_state(self):
        self.start_user_script_action.setEnabled(False)
        self.stop_user_script_action.setEnabled(True)

    def user_script_stop_state(self):
        self.start_user_script_action.setEnabled(True)
        self.stop_user_script_action.setEnabled(False)



class top_panel_widget(QTabWidget):
    top_panel_signal = pyqtSignal(int)
    def __init__(self, parent:QWidget, *args):
        super().__init__(parent, *args)
        self.initUI()
        self.bind_static_buttons()

    def initUI(self):
        loadUi(((Path(__file__).resolve().parent) / "resources/top_panel.ui"),self)

    def bind_static_buttons(self):
        self.add_trace_button.clicked.connect(lambda: self.top_panel_signal.emit(21))
        self.add_debug_console.clicked.connect(lambda: self.top_panel_signal.emit(22))
        self.add_plot_button.clicked.connect(lambda: self.top_panel_signal.emit(23))


    



class bottom_panel_widget(QTabWidget):
    def __init__(self, parent:QWidget, *args):
        super().__init__(parent, *args)
        self.current_tab = None
        self.special_tab_index = 0
        self.data_model = None 
        self.initUI()
        self.bind_static_signals()

    def initUI(self):
        loadUi(((Path(__file__).resolve().parent) / "resources/bottom_panel.ui"),self)
        self.create_models()
        self.create_new_tab("Main",0)
        self.create_special_tab()
        self.curren_changed_callback()
        
    def bind_static_signals(self):
        self.tabBarClicked.connect(self.tab_bar_callback)
        self.currentChanged.connect(self.curren_changed_callback)

    def tab_bar_callback(self,clicked_tab_index):
        if clicked_tab_index == self.special_tab_index:
            print("clicked + ")
            self.create_new_tab("new tab",clicked_tab_index)
    
    def curren_changed_callback(self):
        self.current_tab = self.currentWidget()

    def create_special_tab(self):
        self.special_tab = QWidget()
        self.special_tab_index = self.addTab(self.special_tab,"+")

    def create_new_tab(self,name_of_desktop,index_of_special_tab):
        new_tab = desktop(self,(self.data_model))
        self.insertTab((index_of_special_tab),new_tab,name_of_desktop)
        self.special_tab_index +=1
            
    def create_models(self):
        #bus_list = ["CAN","ETH","UART"]
        bus_list = ["UART"]
        self.data_model = data_models()
        self.data_model.set_bus_list(bus_list)
    
    def update_list_of_models(self,bus_channel_dict:dict):
        self.data_model.update_bus_ChannelList_dict(bus_channel_dict)

    def update_msg_broker_pointer(self,pointer):
        self.data_model.broker_queue_pointer = pointer 









