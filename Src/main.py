from Backend.backend import *



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.initUI()
        self.init_backend()

    def initUI(self):
        loadUi(((Path(__file__).resolve().parent) / "GUI/resources/main_window.ui"),self)
        self.main_menu = main_menu_widget(self)
        self.top_panel = top_panel_widget(self)
        self.bottom_panel = bottom_panel_widget(self)
        self.setMenuBar(self.main_menu)
        self.centralWidget().layout().addWidget(self.top_panel)
        self.centralWidget().layout().addWidget(self.bottom_panel)


    def init_backend(self):
        self.backend = Backend(self.bottom_panel,self.top_panel,self.main_menu)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()