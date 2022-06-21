from _thread import *
from kivy.clock import Clock
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
                super().shutdown(self.socket_)

        self.screen = None
        self.client_name = ""
        self.socket_ = None
        self.port = None
        self.rooms = [None] * Settings.rooms_num
        self.playing = False
        self.listening = False
        self.waiting = False
        self.abandon = False

    def initialize(self, client_name, screen):
        Settings.inform("Initializing the client")
        self.screen = screen
        self.client_name = client_name
        self.start_listening()

    def shutdown(self, port):
        idx = Settings.default_port - port
        try:
            self.rooms[idx].close()
        except Exception as e:
            Settings.handle_error(e)
        self.rooms[idx] = None

    def request_game(self, port):
        socket_ = self.rooms[Settings.default_port - port]

        if socket_ is not None:
            data = {"client_name": self.client_name, **REQUEST_GAME}

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

    def wait_for_game(self):
        t0 = time.time()
        while self.waiting:
            t1 = time.time()

            if self.abandon:
                if self.send(self.socket_, ABORT_WAITING):
                    Settings.inform(f"Abandoned waiting for {self.port}.")
                self.waiting = False
                self.abandon = False
                self.start_listening()
                return

            if self.send(self.socket_, WAITING):
                data = self.recive(self.socket_)
                if not self.waiting: return # if we abandoned during data recive

                if data == REQUEST_ACCEPTED:
                    if self.send(self.socket_, REQUEST_RECIVED):
                        self.waiting = False
                        self.listening = False
                        self.playing = True
                        self.screen.ticking.cancel()
                        self.screen.manager.screen = "game"
                        Settings.inform(f"Server {self.port} accepted a game.")
                        return

                elif data == REQUEST_RECIVED:
                    t0 = t1
                    Settings.inform(f"Waiting for game from {self.port}.")

                elif data == REQUEST_DENIED:
                    super().shutdown(self.socket_) 
                    self.waiting = False
                    ErrorPopup("Server busy", "Server started another game.").open()
                    Settings.inform(f"Server {self.port} started anorher game")
                    return
                            
            if t1 - t0 > 10:
                super().shutdown(self.socket_)
                self.waiting = False
                self.start_listening()
                Settings.inform("Server {self.port} lost.")
                return

            time.sleep(Settings.client_frequency)

    # test if binded server is open. If yes, return its name
    def test_socket(self, socket_): 
        if socket_ is not None:
            if self.send(socket_, ALIVE):
                data = self.recive(socket_)

                if "server_name" in data:
                    server_name = data["server_name"]
                    del data["server_name"]

                    if data == REQUEST_RECIVED: # server is open
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
