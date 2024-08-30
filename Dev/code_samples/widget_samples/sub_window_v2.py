# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class MainWindow(QMainWindow):
     def __init__(self):
         super(MainWindow, self).__init__()
         self.resize(400, 300)

         # Button
         #self.button = QPushButton(self)
         #self.button.setGeometry(0, 0, 400, 300)
         #self.button.setText('Main Window')
         #self.button.setStyleSheet('font-size:40px')

         # Sub Window
        # 
         self.main_widget = main_widget()
         self.setCentralWidget(self.main_widget)

         # Button Event
        # self.button.clicked.connect(self.sub_window.show)


class main_widget(QWidget):
     def __init__(self):
          super(main_widget, self).__init__()
          self.resize(400, 300)
          self.test_layout = QHBoxLayout()
          self.setLayout(self.test_layout)

          #test mdi_window
          self.sample_window = QMdiSubWindow(self)
          self.sample_window.show()
        

if __name__ == '__main__':
     app = QApplication([])
     window = MainWindow()
     window.show()
     sys.exit(app.exec_())