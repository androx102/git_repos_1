from Backend.data_models import *






class desktop(QScrollArea):
    update_windows_list_desktop = pyqtSignal(QMdiSubWindow,bool)
    update_sub_content_dict = pyqtSignal(str,QFrame)
    def __init__(self, parent:QWidget,*args):
        super().__init__()
        self.my_parent = parent
        self.args = args
        self.initUI()
        self.bind_slots_and_signals()


    def initUI(self):
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents) 
        self.setWidgetResizable(True)
        self.custom_desktop = desktop_mdi(self,self.args)
        self.setWidget(self.custom_desktop)

    def bind_slots_and_signals(self):
        self.horizontalScrollBar().actionTriggered.connect(self.custom_desktop.calculate_required_desktop_area)
        self.verticalScrollBar().actionTriggered.connect(self.custom_desktop.calculate_required_desktop_area)



class desktop_mdi(QMdiArea):
    udpate_subs_display = pyqtSignal()
    def __init__(self, parent:QWidget,*args):
        super().__init__()
        self.my_parent = parent
        self.args = args
        self.initUI()


    def initUI(self):
        self.setMinimumSize(self.frameGeometry().width(), self.frameGeometry().height())
        self.calculate_required_desktop_area()

    @pyqtSlot()
    def add_sub_window(self):
        sub_window = trace_window(self.args)
        self.addSubWindow(sub_window)
        sub_window.window_dragged_signal.connect(self.calculate_required_desktop_area)
        sub_window.show()

    @pyqtSlot()
    def add_debug_window(self):
        sys_dialog = debug_dialog_window(self.args)
        self.addSubWindow(sys_dialog)
        sys_dialog.window_dragged_signal.connect(self.calculate_required_desktop_area)
        sys_dialog.show()

    @pyqtSlot()
    def calculate_required_desktop_area(self):
        sub_window_y_list = []
        sub_window_x_list = []
        if len(self.subWindowList()) != 0:
            for sub_window in self.subWindowList():
                sub_window_y_list.append(sub_window.frameGeometry().bottom())
                sub_window_y_list.append(sub_window.frameGeometry().top())
                sub_window_x_list.append(sub_window.frameGeometry().right())
                sub_window_x_list.append(sub_window.frameGeometry().left())
            self.min_x_widgets = (min(sub_window_x_list))
            self.max_x_widgets = (max(sub_window_x_list))
            self.min_y_widgets = (min(sub_window_y_list))
            self.max_y_widgets = (max(sub_window_y_list))
        else:
            self.min_x_widgets = 0
            self.max_x_widgets = 0
            self.min_y_widgets = 0
            self.max_y_widgets = 0

        self.min_x_required = min(self.my_parent.horizontalScrollBar().value(),self.min_x_widgets)
        self.max_x_required = max((self.frameGeometry().width()-(self.my_parent.horizontalScrollBar().maximum()-self.my_parent.horizontalScrollBar().value())),self.max_x_widgets)
        self.min_y_required = min(self.my_parent.verticalScrollBar().value(),self.min_y_widgets)
        self.max_y_required = max((self.frameGeometry().height()-(self.my_parent.verticalScrollBar().maximum()-self.my_parent.verticalScrollBar().value())),self.max_y_widgets)


        if (self.min_x_required != 0) or ((self.frameGeometry().right() +1 + abs(self.frameGeometry().left())) != self.max_x_required):
            self.resize_desktop("x")
        if (self.min_y_required != 0) or ((self.frameGeometry().bottom() +1 + abs(self.frameGeometry().top())) != self.max_y_required):
            self.resize_desktop('y')

    def resize_desktop(self,axis):
        if axis == "x":
            self.setMinimumWidth(self.max_x_required - self.min_x_required)
            for sub_window in self.subWindowList():
                sub_window.move(sub_window.x() - self.min_x_required,sub_window.y()) 
            self.my_parent.horizontalScrollBar().setValue(self.my_parent.horizontalScrollBar().value() - self.min_x_required)
        if axis == "y":
            self.setMinimumHeight(self.max_y_required - self.min_y_required)
            for sub_window in self.subWindowList():
                sub_window.move(sub_window.x(),sub_window.y() - self.min_y_required) 
            self.my_parent.verticalScrollBar().setValue(self.my_parent.verticalScrollBar().value() - self.min_y_required)

######################################################################################################################################



#DEV
class trace_window(QMdiSubWindow):
    window_dragged_signal = pyqtSignal()
    closed_sub_widnow = pyqtSignal()
    def __init__(self,*args):
        super(trace_window,self).__init__()
        self.args = args
        self.initUI()

    def initUI(self):
        self.content = trace_window_content_frame(self.args)
        self.setWidget(self.content)

    def mouseReleaseEvent(self, event): 
        super(trace_window, self).mouseReleaseEvent(event)
        self.window_dragged_signal.emit()
    
    def closeEvent(self, event):
        super(trace_window, self).closeEvent(event)




class trace_window_content_frame(QFrame):
    def __init__(self,*args):
        super(trace_window_content_frame,self).__init__()
        self.data_model = args[0][0][0][0]
        self.current_content_widget = None
        self.current_bus = None
        self.current_channel = None
        self.initUI()
        #refresh table by changing comboBox_bus index


    def initUI(self):
        loadUi(((Path(__file__).resolve().parent) / "resources/trace_window.ui"),self)
        self.bind_slots_and_signals()
        self.comboBox_bus.setModel(self.data_model.BusListModel)
        #Toggle bus combobox

        
    def bind_slots_and_signals(self):
        self.comboBox_bus.currentIndexChanged.connect(self.change_bus)
        self.comboBox_channel.currentIndexChanged.connect(self.change_bottom_contetn)


    def change_bus(self,index:int):
        self.current_bus = self.comboBox_bus.itemText(index)
        self.comboBox_channel.setModel(self.data_model.Bus_ChannelListModel_dict[self.current_bus])
        #self.comboBox_channel.changeIndex to refresh table


    def change_bottom_contetn(self,index:int):
        self.current_channel = self.comboBox_channel.itemText(index)
        try:
            self.tableView.setModel(self.data_model.Bus_Channel_TableModel_dict[self.current_bus][self.current_channel])
        except:
            new_blank_model = Bus_trace_table_model([],Bus_trace_tabe_model_headers.get_headers(self.current_bus))
            self.tableView.setModel(new_blank_model)
      








class debug_dialog_window(QMdiSubWindow):
    window_dragged_signal = pyqtSignal()
    closed_sub_widnow = pyqtSignal()
    def __init__(self,*args):
        super(debug_dialog_window,self).__init__()
        self.args = args
        self.initUI()

    def initUI(self):
        self.content = debug_dialog_content(self.args)
        self.setWidget(self.content)

    def mouseReleaseEvent(self, event): 
        super(debug_dialog_window, self).mouseReleaseEvent(event)
        self.window_dragged_signal.emit()
    
    def closeEvent(self, event):
        super(debug_dialog_window, self).closeEvent(event)
                        


class debug_dialog_content(QFrame):
    def __init__(self,*args):
        super(debug_dialog_content,self).__init__()
        self.data_model = args[0][0][0][0] 
        self.broker_queue_pointer = self.data_model.broker_queue_pointer
        self.current_content_widget = None
        self.current_bus = None
        self.current_channel = None
        self.initUI()
        #refresh table by changing comboBox_bus index


    def initUI(self):
        loadUi(((Path(__file__).resolve().parent) / "resources/debug_window.ui"),self)
        self.bind_slots_and_signals()
        self.comboBox_bus.setModel(self.data_model.BusListModel)
        #Toggle bus combobox

    def bind_slots_and_signals(self):
        self.comboBox_bus.currentIndexChanged.connect(self.change_bus)
        self.comboBox_channel.currentIndexChanged.connect(self.change_bottom_contetn)
        self.pushButton.clicked.connect(self.send_message)
        self.pushButton_2.clicked.connect(self.clear_window)


    def change_bus(self,index:int):
        self.current_bus = self.comboBox_bus.itemText(index)
        self.comboBox_channel.setModel(self.data_model.Bus_ChannelListModel_dict[self.current_bus])
        #self.comboBox_channel.changeIndex to refresh table


    def change_bottom_contetn(self,index:int):
        self.current_channel = self.comboBox_channel.itemText(index)
        try:
            self.listView.setModel(self.data_model.Bus_Channel_ListModel_dict[self.current_bus][self.current_channel])
        except:
            new_blank_model = Channels_list_model()
            self.listView.setModel(new_blank_model)    

    def clear_window(self):
        pass

    def send_message(self):
        data = self.lineEdit.text()
        x = self.lineEdit.text()
        print("trying to send: " + data)
        msg = message_(topic=(self.current_channel+"_Tx"),source="UART",data=(data),optional_params="SEND_MSG_TXT")
        self.broker_queue_pointer[0].put(msg)






            
   
#DEV
class sys_dialog_window(QMdiSubWindow):
    window_dragged_signal = pyqtSignal()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.initUI()

    def initUI(self):
        content = loadUi(((Path(__file__).resolve().parent) / "resources/system_dialog_window.ui"))
        self.setWidget(content)


    def mouseReleaseEvent(self, event): 
        super(sys_dialog_window, self).mouseReleaseEvent(event)
        self.window_dragged_signal.emit()


