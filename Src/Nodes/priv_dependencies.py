#Modules import
from PyQt5.QtCore import QThread, pyqtSignal,QTimer
from multiprocessing import Queue
from threading import Thread
import time
from can import interface
import json
import http.client as http
import ssl
import socket
from serial import Serial
import sys
import debugpy
import traceback
import pyvisa
import os
from pathlib import Path
from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
