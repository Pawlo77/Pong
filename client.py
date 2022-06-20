import socket
import json
from _thread import *
import time
from tkinter import SE

from settings import *
from widgets import ErrorPopup


class Client:
    def __init__(self):
        self.reset(True)

    def create(self, client_name):
        self.client_name = client_name
        self.scanning = True
        start_new_thread(self.listen, ())

    def reset(self, initial=False):
        Settings.inform(f"Client resetting.")
        if not initial and self.socket_ is not None:
            self.shutdown(self.socket_)
            Settings.inform(f"Connection to {self.port} closed.")
        self.socket_ = None
        self.port = None
        self.waiting = None
        self.rooms = {}
        self.game = False
        self.scanning = False
        self.client_name = None

    def shutdown(self, obj):
        try:
            obj.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            Settings.handle_error(e)

    def get_socket_(self, port):
        try:
            socket_ = socket.socket()
            socket_.settimeout(Settings.server_timeout)
            socket_.connect((Settings.host, port))
        except Exception as e:
            Settings.handle_error(e)
            return None
        return socket_

    def request_game(self, port, root):
        socket_ = self.get_socket_(port)
        if socket_:
            data = REQUEST_GAME.copy()
            data["client_name"] = self.client_name

            if self.send(socket_, data):
                data = self.recive(socket_)

                if data == REQUEST_RECIVED:
                    self.socket_ = socket_
                    self.port = port
                    self.waiting = True
                    start_new_thread(self.wait_for_game, (root, ))
                    return True
        return False

    def abandon(self):
        self.send(self.socket_, ABORT_WAITING)
        self.waiting = False

    def wait_for_game(self, root):
        t0 = time.time()
        while self.waiting:
            time.sleep(Settings.client_frequency)
            t1 = time.time()
            if self.send(self.socket_, REQUEST_GAME):
                data = self.recive(self.socket_)

                if data == REQEST_ACCEPTED:
                    self.waiting = False
                    self.scanning = False
                    root.during_waiting.back_up()
                    Settings.inform(f"Server {self.port} accepted a game.")
                    self.game = True

                elif data == REQUEST_RECIVED:
                    t0 = t1
                    Settings.inform(f"Waiting for game from {self.port}.")

                elif data == REQUEST_DENIED:
                    self.shutdown(self.socket_) 
                    self.waiting = False
                    root.during_waiting.back_up()
                    ErrorPopup("Server busy", "Server started another game.").open()
                    Settings.inform(f"Server {self.port} started anorher game")
                            
            if t1 - t0 > 10:
                self.shutdown(self.socket_)
                self.waiting = False
                print(root)
                root.during_waiting.back_up()
                ErrorPopup("Server error", "Server lost.").open()
                Settings.inform("Server {self.port} lost.")

    def send(self, socket_, data):
        data = json.dumps(data).encode(Settings.encoding)
        
        try:
            socket_.send(data)
        except Exception as e:
            Settings.handle_error(e)
            return False
        return True

    def recive(self, socket_):
        try:
            data = socket_.recv(Settings.conn_data_limit).decode(Settings.encoding)

            if data:
                return json.loads(data)
        except Exception as e:
            Settings.handle_error(e)
        return {}

    def listen(self):
        while self.scanning:
            time.sleep(Settings.client_frequency)

            port = Settings.default_port
            while port < Settings.default_port + Settings.max_rooms_num:
                Settings.inform(f"Scanning at port {port}.")
                connection = False
                
                socket_ = self.get_socket_(port)
                if socket_:
                    if self.send(socket_, ALIVE):
                        data = self.recive(socket_)

                        if "server_name" in data:  # if it is telling us about itself
                            server_name = data["server_name"]
                            del data["server_name"]

                            if data == all: # if rest of the flags are correct
                                connection = True
                    self.shutdown(socket_)

                if connection and port not in self.rooms: # if new connection found
                    self.rooms[port] = server_name
                    Settings.inform(f"Server found at {port}.")
                elif not connection and port in self.rooms: # if old connection lost
                    del self.rooms[port]
                    Settings.inform(f"Server lost at {port}.")

                port += 1



# client = Client()
# client.thread_update()

# for i in range(10): 
#     time.sleep(5)
#     print(client.rooms)

# client.thread_.exit()