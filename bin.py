import socket



msgFromClient       = "Hello UDP Server"

bytesToSend         = str.encode(msgFromClient)

serverAddressPort   = ("127.0.0.1", 8000)

bufferSize          = 1024

 

# Create a UDP socket at client side

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.settimeout(2)
 

# Send to server using created UDP socket

UDPClientSocket.sendto(bytesToSend, serverAddressPort)
try:
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)
except:
    pass
print(UDPClientSocket)

exit(0)

msg = "Message from Server {}".format(msgFromServer[0])

print(msg)