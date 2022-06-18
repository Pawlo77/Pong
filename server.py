import socket 

from settings import Settings

# set up a TCP / IP server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ("localhost", Settings.default_port)
server.bind(server_address)

server.listen(1)

client = None
while Settings.server_alive:
    connection, new_client = server.accept()
    

