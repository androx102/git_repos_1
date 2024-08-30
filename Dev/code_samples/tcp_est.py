import socket

HOST = "192.168.110.13"  # The server's hostname or IP address
PORT = 5025  # The port used by the server

message_to_andritsu = "*IDN?" + "\r\n"
message = message_to_andritsu.encode()
#(b"SSTAT?")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    #s.sendall(b"Hello, world")
    s.sendall(message)
    print(f"Sent: {str(message)}")
    data = s.recv(1024)

print(f"Received {str(data)}")
pass