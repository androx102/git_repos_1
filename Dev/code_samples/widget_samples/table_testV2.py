import sys

import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QWidget, QGridLayout, QPushButton


class TableModel(QAbstractTableModel):
    def __init__(self, table_data,headers, parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self.table_headers = headers

    def rowCount(self, parent=None) -> int:
        return len(self.table_data)

    def columnCount(self, parent=None) -> int:
        return len(self.table_data[0])

    def data(self, index: QModelIndex, role: int = ...):
        if role == Qt.DisplayRole:
            return self.table_data[index.row()][index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.table_headers[section])



##################################################################################################
    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginInsertRows(parent, row, row+count-1)
        default_row = ['x']*len(self.table_data[0])  # or _headers if you have that defined.
        for i in range(count):
            self.table_data.insert(row, default_row)
        self.endInsertRows()
        self.layoutChanged.emit()
        return True
##################################################################################################



if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QMainWindow()
    widget = QWidget()
    layout = QGridLayout()
    widget.setLayout(layout)



    data = [
          [4, 9, 2],
          [1, 0, 0],
          [3, 5, 0],
          [3, 3, 2],
          [7, 8, 9],
        ]
    headers = ["Time","Channel","Data"]
    model = TableModel(table_data=data,headers=headers)
    table = QTableView()


    table.setModel(model)
    layout.addWidget(table)

    def insert_row():
        index = table.currentIndex()
        model.insertRows(index.row(), 1)

    button = QPushButton("add row")
    button.clicked.connect(insert_row)
    layout.addWidget(button)



    win.setCentralWidget(widget)

    win.show()
    app.exec()

    