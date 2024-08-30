import sys

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine


app = QGuiApplication(sys.argv)

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('C:\\Users\\po0ml3\\wkspaces\\EPLVTS01_PY_TOOLS\\03_CodeSamples\\qml_test\\main.qml')

sys.exit(app.exec())