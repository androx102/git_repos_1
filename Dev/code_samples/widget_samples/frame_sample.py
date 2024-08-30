
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame
from PyQt5.QtGui import QColor
 
 
class Example(QMainWindow):
 
    def __init__(self):
        super().__init__()
 
        self.initUI()
 
    def initUI(self):
        # create a frame and set its properties
        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("QWidget { background-color: %s }" % QColor(0, 0, 0).name())
        frame.setGeometry(50, 50, 200, 200)
 
        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Frame Example')
        self.show()
 
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())