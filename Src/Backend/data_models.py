from PyQt5.QtCore import *
from PyQt5.QtCore import QAbstractListModel, Qt, QModelIndex, QAbstractTableModel, QTimer, QObject, pyqtSlot

#Dev
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget, QScrollArea, QMdiSubWindow, QFrame, QAbstractScrollArea, QMdiArea, QMainWindow, QApplication 
from PyQt5.uic import loadUi

from collections import defaultdict, deque
import random
from multiprocessing import Queue
import numpy as np
import time
from pathlib import Path
import json
import sys

#our libraries
from Nodes import *





class Bus_list_model(QAbstractListModel):
    def __init__(self, *args, bus_list=None, **kwargs):
        super(Bus_list_model, self).__init__(*args, **kwargs)
        self.bus_list = bus_list or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.bus_list[index.row()]
            return text

    def rowCount(self, index):
        return len(self.bus_list)
    



class Channels_list_model(QAbstractListModel):
    def __init__(self, *args, channel_names=None, **kwargs):
        super(Channels_list_model, self).__init__(*args, **kwargs)
        self.channel_names = channel_names or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.channel_names[index.row()]
            return text
        
    def rowCount(self, index):
        return len(self.channel_names)
    










######################################################################################


class Bus_debug_list_model(QAbstractListModel):
    def __init__(self):
        super(Bus_debug_list_model, self).__init__()
        self.id = random.random()
        self.table_data = deque(maxlen=100)
        self.chunk_size = 10
        self.max_displayed_rows = self.chunk_size * 10

    def data(self, index, role):
        if role == Qt.DisplayRole:
            text = self.table_data[index.row()]
            return str(text)
        
    def rowCount(self, index):
        return len(self.table_data)


    def add_data(self,new_data):
       # string_data_list=[x.decode('utf-8') for x in new_data]
      #  clear_data = list(map(lambda x:x.strip(),string_data_list))

        self.beginInsertRows(self.index(len(self.table_data)),len(self.table_data),len(self.table_data)-len(new_data)-1)
        self.table_data.extend(new_data)
        self.endInsertRows()
          

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        return self.id == __value.id

    def clear_list(self):
        self.table_data = np.array([])
        self.layoutChanged.emit()


######################################################################################










class Bus_trace_tabe_model_headers():
    def __init__(self) -> None:
        pass
    @staticmethod
    def get_headers(name_of_trace):
        match name_of_trace:
            case "CAN":
                to_ret = ["Time","Chn","ID","Name","Event type","Dir","DLC","DL","Data"]
            case _:
                to_ret = ["Time","Chn","DL","Data"]
        return to_ret


class Bus_trace_table_model(QAbstractTableModel):
    def __init__(self, data,headers):
        super(Bus_trace_table_model, self).__init__()
        self.table_data = data 
        self.table_headers = headers

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if len(self.table_data) == 0:
                value = ""
            else:
                value = self.table_data[index.row()][index.column()]
            return str(value)

    def rowCount(self, index):
        if len(self.table_data) == 0:
            return 1
        else:
            return len(self.table_data)

    def columnCount(self, index):
            return len(self.table_headers)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if len(self.table_headers) == 0:
                    return ""
                else:
                    return str(self.table_headers[section])



    #Need to change those functions
    ######################################################################
    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginInsertRows(parent, row, row+count-1)
        default_row = ['x']*len(self.table_headers)  
        for i in range(count):
            self.table_data.insert(row, default_row)
        self.endInsertRows()
        self.layoutChanged.emit()
        return True
    
    def removeRows(self, position, rows, QModelIndex):
        self.beginRemoveRows(QModelIndex, position, position+rows-1)
        for i in range(rows):
            del(self.table_data[position])
        self.endRemoveRows()
        self.layoutChanged.emit()
        return True
    ######################################################################




class data_models():
    def __init__(self):
        self.busses_list = []
        self.bus_ChannelList_dict = {}
        self.broker_queue_pointer = []

        self.BusListModel = None
        self.Bus_ChannelListModel_dict = {}
        self.Bus_Channel_TableModel_dict = {}
        self.Bus_Channel_ListModel_dict = {}

    ########################################
    def set_bus_list(self,bus_list:list):
        self.busses_list = bus_list
        self.BusListModel = Bus_list_model(bus_list=self.busses_list)

        for bus in self.busses_list:
            self.bus_ChannelList_dict[bus] = []
        
        for bus in self.busses_list:
            self.Bus_ChannelListModel_dict[bus] = Channels_list_model(channel_names=[])

    def update_bus_ChannelList_dict(self,bus_channel_dict:dict):
        self.bus_ChannelList_dict = bus_channel_dict

        for bus,channelList in self.bus_ChannelList_dict.items():
                if self.Bus_ChannelListModel_dict.get(bus):
                    self.Bus_ChannelListModel_dict[bus].channel_names = channelList
                    self.Bus_ChannelListModel_dict[bus].layoutChanged.emit()
        
        for bus,channelList in self.bus_ChannelList_dict.items():
            if self.Bus_ChannelListModel_dict.get(bus):
                self.Bus_Channel_TableModel_dict[bus] = {}
                for channel in channelList:
                    self.Bus_Channel_TableModel_dict[bus][channel] = Bus_trace_table_model([],Bus_trace_tabe_model_headers.get_headers(bus))

        for bus,channelList in self.bus_ChannelList_dict.items():
            if self.Bus_ChannelListModel_dict.get(bus):
                self.Bus_Channel_ListModel_dict[bus] = {}
                for channel in channelList:
                    self.Bus_Channel_ListModel_dict[bus][channel] = Bus_debug_list_model()
    


class topic_que_dict_class():
    def __init__(self):
        self.topic_que_dict = {}

                
    def add_sub(self,topic_queue_dict:dict):
        topic = list(topic_queue_dict.keys())[0]
        queue_obj = list(topic_queue_dict.values())[0]
        if topic in self.topic_que_dict:
            if queue_obj in self.topic_que_dict[topic]:
                pass
            else:
                self.topic_que_dict[topic].append(queue_obj)
        else:
            self.topic_que_dict[topic] = [queue_obj]


    def del_sub(self,topic_queue_dict:dict):
        topic = list(topic_queue_dict.keys())[0]
        queue_obj = list(topic_queue_dict.values())[0]

        if topic in self.topic_que_dict:
            if queue_obj in self.topic_que_dict[topic]:
                self.topic_que_dict[topic].remove(queue_obj)

    def clear_sub(self):
        self.topic_que_dict.clear()




