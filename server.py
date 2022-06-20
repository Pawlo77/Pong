from _thread import *
import time
import socket

from settings import *
from internet import Internet


class Server(Internet):
    def __init__(self):
        self.reset(True)

    def reset(self, initial=False):
        if initial:
            Settings.inform(f"Setting up a server.")
        else:
            Settings.inform(f"Resetting a server ({self.port}).")

            if self.socket_ is not None:
                self.shutdown(self.socket_)

        self.screen = None
        self.socket_ = None
        self.listening = False
        self.playing = False
        self.port = None
        self.server_name = ""
        self.clients = []

    def initialize(self, server_name, screen):
        Settings.inform(f"Initializing a server.")
        self.server_name = server_name
        self.screen = screen
        port = Settings.default_port
        socket_ = None

        socket_ = socket.socket()
        while port < Settings.default_port + Settings.rooms_num:
            try:
                socket_.bind((Settings.host, port))
            except Exception as e:
                Settings.handle_error(e)
            else:
                socket_.listen(1)
                self.socket_ = socket_
                self.port = port
                self.listening = True
                start_new_thread(self.listen, ())         
                start_new_thread(self.listen_clients, ())         
                Settings.inform(f"Server created at {port}.")
                break

            port += 1

    def shutdown(self, obj):
        try:
            obj.close()
        except Exception as e:
            Settings.handle_error(e)

    def accept(self, conn, port):
        if self.send(conn, REQUEST_ACCEPTED):
            Settings.inform("Game from {port} accepted.")
            self.playing = True
            self.listening = False

    def get_client(self, client_port):
        for (conn, port, lastConn) in self.server.clients:
            if port == client_port: 
                return conn, port, lastConn
        return None

    def remove(self, conn, idx, port):
        self.shutdown(conn)
        self.clients.pop(idx)
        self.screen.remove_client(port)

    def listen_clients(self):
        while self.listening:
            for idx, (conn, port, lastConn) in enumerate(self.clients):
                t = time.time()
                if t - lastConn > Settings.connection_timeout:
                    self.remove(conn, idx, port)
                    Settings.inform(f"Connection with {port} lost.")
                    continue

                data = self.recive(conn)
                if data == ALIVE:
                    if self.send(conn, REQUEST_RECIVED):
                        self.clients[idx] = [conn, port, t]
                        Settings.inform(f"Connection with client {port} renewed.")
                        continue

                elif data == WAITING:
                    if self.send(conn, REQUEST_RECIVED):
                        self.clients[idx] = [conn, port, t]
                        Settings.inform(f"Client {port} is still waiting to join.")
                        continue
  
                elif data == ABORT_WAITING:
                    if self.send(conn, REQUEST_RECIVED):
                        self.remove(conn, idx, port)
                        self.clients[idx] = [conn, port, t]
                        Settings.inform(f"Client {port} aborted.")
                        continue
                
                elif "client_name" in data:
                    client_name = data["client_name"]
                    del data["client_name"]

                    if data == REQUEST_GAME:
                        if self.send(conn, REQUEST_RECIVED):
                            self.clients[idx] = [conn, port, t]
                            self.screen.add_client(client_name, port)
                            Settings.inform(f"Client {port} wants to join a game.")
                            continue

                self.remove(conn, idx, port)
                Settings.inform(f"Connection with {port} lost.")   
                time.sleep(Settings.server_frequency)

    def listen(self):
        while self.listening:
            conn, address = self.socket_.accept()
            data = self.recive(conn)

            if data == ALIVE:
                data = {"server_name": self.server_name, **all}
                if self.send(conn, data):
                    Settings.inform(f"New connection from {address[1]}.")
                    self.clients.append([conn, address[1], time.time()])
                    continue

            self.shutdown(conn)
            time.sleep(Settings.server_frequency)


# import psutil
# conns = psutil.net_connections()

