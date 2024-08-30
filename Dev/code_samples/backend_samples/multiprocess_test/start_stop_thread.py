import sys
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from multiprocessing import Process, Queue

import can
from time import *






####################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        #########################
       # self.test_task.moveToThread(self.test_thread) #move Qobj to thread
       # self.test_thread.started.connect(self.test_task.long_run_func) #connect "start" signal from Qthread to "start_qobject" function -> entrypoint 
        #self.test_thread.stop_task_signal.connect(self.test_task.stop_task)
        #self.test_task.worker_task_ended.connect(self.test_thread.quit) #connect "task_ended" signal from Qobject to Qthread "quit" function
        self.initUI()
        self.bind_buttons()
        self.thread_setup()
        #########################


    def initUI(self):
        ############################################
        self.main_widget = QWidget()
        self.main_widget_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_widget_layout)
        ############################################
        self.start_button = QPushButton(self)
        self.start_button.setText('Start')
        self.stop_button = QPushButton(self)
        self.stop_button.setText('Stop')
        self.stop_button.setDisabled(True)
        self.test_button = QPushButton(self)
        self.test_button.setText('test_button')
        self.text_widget = QPlainTextEdit(self)
        self.text_widget.setReadOnly(True)
        ############################################
        self.main_widget_layout.addWidget(self.text_widget)
        self.main_widget_layout.addWidget(self.start_button)
        self.main_widget_layout.addWidget(self.stop_button)
        self.main_widget_layout.addWidget(self.test_button)
        self.setCentralWidget(self.main_widget)


    def bind_buttons(self):
        self.start_button.clicked.connect(self.start_button_func)
        self.stop_button.clicked.connect(self.stop_button_func)
        self.test_button.clicked.connect(self.test)


        

    def start_button_func(self):
        #start logger process
        ########################################
        self.test_thread.start() #starts Qthread
        ########################################
        self.toggle_buttons()
        
    
    def stop_button_func(self):
        #kill logger process
        ########################################
        self.test_thread.stop_process()
        ########################################
        self.toggle_buttons()

    def toggle_buttons(self):
        self.stop_button.setDisabled(self.stop_button.isEnabled())
        self.start_button.setDisabled(self.stop_button.isEnabled())

    def test(self):
        print(f"Is thread running: {self.test_thread.isRunning()}")


  #  def start_thread(self):
   #     self.thread_setup()

    def thread_setup(self):
        self.test_thread = Custom_thread()
        self.test_thread.update_signal.connect(self.update_textbox)
        #self.test_task = object_for_thread()

    def update_textbox(self,data_to_print):
        self.text_widget.appendPlainText(data_to_print)

###############################################################################
        
class Custom_thread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self): #*args
        super(Custom_thread,self).__init__()
        print('created thread')
        self.control_list = [True]

    #main event loop overwrited
    def run(self):
        self.control_list = [True]

        #init can
        bus1 = can.interface.Bus(bustype='vector', channel=0, bitrate=500000, app_name='pycan')

        for msg in bus1:
            if self.control_list[0]:
                #print(msg)
                #print(f"{msg.arbitration_id:X}: {msg.data}")
                #print(f'Timer: {x}, Flag: {self.control_list}')
                self.update_signal.emit(str(msg))
                #sleep(1)
            else:
                #print("stopping thread")
                bus1.shutdown()
                break 

    def stop_process(self):
        print("stopping thread")
        self.control_list[0] = False
        self.exit(0)




class object_for_thread(QObject):
    worker_task_ended = pyqtSignal()

    def __init__(self):
        super(object_for_thread,self).__init__()
        self.control_list = ()

    def long_run_func(self):
        for x in range(20):

            print(x)
            sleep(1)
        self.worker_task_ended.emit()
    
    def stop_task(self):
        print('stopping task')














class Custom_abstract_worker(QRunnable):
    def __init__(self):
        QRunnable.__init__(self)
        print('created worker')

        #################
        self.finished = pyqtSignal()
        self.error = pyqtSignal(tuple)
        self.result = pyqtSignal(object)
        self.progress = pyqtSignal(int)

    def run(self):
        for x in range(20):
            print(x)
            sleep(1)



###################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())