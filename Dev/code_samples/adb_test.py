from adb_shell.adb_device import AdbDeviceUsb, _AdbIOManager, UsbTransport, _AdbTransactionInfo

device_ID = '3d71f775'
# device = AdbDeviceUsb()
# device.connect()
transport = UsbTransport.find_adb(serial=device_ID,  port_path=None, default_transport_timeout_s=2)
AdbIOManager = _AdbIOManager(transport=transport)
device = AdbDeviceUsb()
adb_info = _AdbTransactionInfo(None, None, transport_timeout_s=2, read_timeout_s=2, timeout_s=2)
device.connect()
respone = AdbIOManager.send(msg='ls', adb_info=adb_info)
print(respone)