import socket 

s = socket.socket()
s.bind(("localhost", 4000))
s.close()

# s.shutdown(socket.SHUT_RDWR)

print(s)