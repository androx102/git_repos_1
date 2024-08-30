# importing libraries 
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys 




    

#################################################################################


class Window(QMainWindow): 

    def __init__(self): 
        super().__init__() 
        self.setWindowTitle("Python test ") 
        self.setGeometry(100, 100, 650, 400) 
        self.initUi() 
        self.show() 

        
	# method for components 
    def initUi(self): 
        self.central_wid = QWidget(self)
        self.ver_layout = QVBoxLayout()
        self.central_wid.setLayout(self.ver_layout)

        self.dummy_plaintext = QPlainTextEdit(self.central_wid)
        self.dummy_plaintext

        self.ver_layout.addWidget(self.dummy_plaintext)
        self.ver_layout.addWidget(self.dummy_plaintext)


        self.setCentralWidget(self.central_wid)
        

    def append_test(self):
        pass


if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = Window() 
    sys.exit(App.exec()) 
