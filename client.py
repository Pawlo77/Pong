from _thread import *
import time

from settings import *
from widgets import ErrorPopup
from internet import Internet


class Client(Internet):
    def __init__(self):
        self.reset(True)

    def reset(self, initial=False):
        if initial:
            Settings.inform(f"Setting up a client.")
        else:
            Settings.inform(f"Resetting a client.")
            
            if self.socket_ is not None:
                self.shutdown(self.socket_)

        self.screen = None
        self.client_name = ""
        self.socket_ = None
        self.port = None
        self.rooms = [None] * Settings.rooms_num
        self.playing = False
        self.listening = False
        self.waiting = False

    def initialize(self, client_name, screen):
        Settings.inform("Initializing the client")
        self.screen = screen
        self.client_name = client_name
        self.start_listening()

    def shutdown(self, port):
        try:
            idx = Settings.default_port - port
            self.rooms[idx].close()
        except Exception as e:
            Settings.handle_error(e)
        self.rooms[idx] = None

    def request_game(self, port):
        socket_ = self.rooms[Settings.default_port - port]

        if socket_ is not None:
            data = REQUEST_GAME.copy()
            data["client_name"] = self.client_name

            if self.send(socket_, data):
                data = self.recive(socket_)

                if data == REQUEST_RECIVED:
                    self.socket_ = socket_
                    self.port = port
                    self.waiting = True
                    self.listening = False
                    start_new_thread(self.wait_for_game, ())
                    return True
        return False

    def abandon(self):
        self.send(self.socket_, ABORT_WAITING)
        self.waiting = False
        self.start_listening()

    def wait_for_game(self):
        t0 = time.time()
        while self.waiting:
            time.sleep(Settings.client_frequency)
            t1 = time.time()
            if self.send(self.socket_, WAITING):
                data = self.recive(self.socket_)

                if data == REQUEST_ACCEPTED:
                    self.waiting = False
                    self.listening = False
                    self.playing = True
                    self.screen.joining.abort(True)
                    Settings.inform(f"Server {self.port} accepted a game.")

                elif data == REQUEST_RECIVED:
                    t0 = t1
                    Settings.inform(f"Waiting for game from {self.port}.")

                elif data == REQUEST_DENIED:
                    self.shutdown(self.socket_) 
                    self.waiting = False
                    self.screen.joining.abort()
                    ErrorPopup("Server busy", "Server started another game.").open()
                    Settings.inform(f"Server {self.port} started anorher game")
                            
            if t1 - t0 > 10:
                self.shutdown(self.socket_)
                self.waiting = False
                self.screen.joining.abort()
                ErrorPopup("Server error", "Server lost.").open()
                Settings.inform("Server {self.port} lost.")

    # test if binded server is open. If yes, return its name
    def test_socket(self, socket_): 
        if socket_ is not None:
            if self.send(socket_, ALIVE):
                data = self.recive(socket_)

                if "server_name" in data:
                    server_name = data["server_name"]
                    del data["server_name"]

                    if data == all: # server is open
                        return server_name
        return None

    def start_listening(self):
        self.listening = True 
        start_new_thread(self.listen, ())        

    def listen(self):
        while self.listening:
            for idx, socket_ in enumerate(self.rooms):
                port = Settings.default_port + idx
                if socket_ is not None:
                    server_name = self.test_socket(socket_)
                    if server_name is not None:
                        Settings.inform(f"Connection to {port} is still open.")

                    else: # server lost, 
                        self.shutdown(port) 
                        self.screen.remove_server(port)
                        Settings.inform(f"Lost connection to {port}.")

                else:
                    socket_ = self.get_socket_(port)
                    server_name = self.test_socket(socket_)
                    if server_name is not None: # new server found
                        Settings.inform(f"New connection found at {port}.")
                        self.rooms[idx] = socket_
                        self.screen.add_server(server_name, port)                                
            
            time.sleep(Settings.client_frequency)
