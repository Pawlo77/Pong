from _thread import *
import time
import socket

from settings import *
from internet import Internet


class Client(Internet):
    def __init__(self):
        self.type_ = "client"
        self.reset(True)

    def reset(self, initial=False):
        if initial:
            Settings.inform(f"Setting up a client.")
        else:
            Settings.inform(f"Resetting a client.")

        self.rooms = {}
        self.server_address = None
        self.client_name = ""
        self.socket_ = None
        self.working = False
        self.frequency = Settings.server_frequency

        self.screen = None
        self.listening = False
        self.playing = False
        self.waiting = False
        self.abandon_ = False

    def initialize(self, client_name, screen):
        Settings.inform("Initializing the client")
        self.screen = screen
        self.client_name = client_name
        self.listening = True

        self.socket_ = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.working = True
        start_new_thread(self.listen, ())
        start_new_thread(self.seek, ())

    def recive(self):
        data, _ = super().recive(self.socket_)
        return data

    def request_game(self, port):
        self.port = port

    def abandon(self):
        self.abandon_ = True
        
    # test if binded server is open. If yes, return its name
    def test_server(self, address): 
        if self.send(self.socket_, ALIVE, address):
            data = self.recive()
            print(data)

            if "server_name" in data:
                server_name = data["server_name"]
                del data["server_name"]

                if data == REQUEST_RECIVED: # server is open
                    return server_name
        return None

    def connection_error(self, is_server, address):
        if self.playing and is_server:
            self.screen.add_action("ERROR", ("Server lost", "Game crashed due to lost connection with a host"))
            self.leave()
            return
        if self.waiting and is_server:
            self.server_address = None
            self.waiting = False
            self.screen.add_action("STOP WAITING", ("Server Lost", "Unable to join the server."))

        self.screen.add_action("REMOVE", address)
        del self.rooms[address]
        return Settings.conn_frequency, ""

    def listen_server(self, address, t0):
        def send(data):
            return self.send(self.socket_, data, address)

        while self.listening or address == self.address:
            is_server = address == self.server_address
            t1 = time.time()
            
            if t0 is not None and t1 - t0 > Settings.connection_timeout:
                Settings.inform(f"Connection timeout ({address}).")
                refresh, server_name = self.connection_error(is_server, address)
            
            while len(self.rooms[address]):
                alive = False
                data = self.rooms[address].pop(0)

                # we have some action with that server
                if is_server:
                    if data == ABANDON:
                        Settings.inform(f"Server {address} abandoned us.")
                        if self.playing:
                            self.screen.add_action("ERROR", ("Server lost", "Game crashed due to lost connection with a host"))
                            self.leave()
                        alive = send(REQUEST_RECIVED)

                    elif data == BUSY:
                        Settings.inform(f"Server {address} started anorher game")
                        self.waiting = False
                        self.server_address = None
                        self.screen.add_action("ERROR", ("Server is busy", "Server has already started a game."))
                        alive = send(REQUEST_RECIVED)

                    if self.abandon_:
                        Settings.inform(f"Abandoned actions with {address}.")
                        if self.playing:
                            self.leave()
                            return

                        alive = send(ABANDON)
                        self.abandon_ = False
                        self.waiting = False
                        self.server_address = None
                        refresh = Settings.conn_frequency

                    elif self.playing:
                        print("tick")
                        alive = send(REQUEST_RECIVED)

                    if self.waiting and data == GAME_ACCEPTED:
                        Settings.inform(f"Starting the game with {address}")
                        alive = send(GAME_START)
                        self.waiting = False
                        self.playing = True
                        self.listening = False
                        self.screen.add_action("START", self)
                        refresh = 1. / Settings.fps

                    # request the game
                    elif not self.waiting:
                        Settings.inform(f"Requesting a game from {address}.")
                        data = {"client_name": self.client_name, **REQUEST_GAME}
                        alive = send(data)

                        response = self.recive()
                        if response == REQUEST_RECIVED:
                            self.waiting = True
                            refresh /= 4 # make things there smoother
                            Settings.inform(f"Request recived.")
                        else:
                            Settings.inform(f"Request failed.")
                    
                    # contact server that we are still waiting
                    elif response == REQUEST_RECIVED:
                        Settings.inform(f"Waiting for game from {address}.")
                        alive = send(WAITING)     

                # we know that the server exists but we don't have an action with it
                else:
                    server_name = self.test_server(address)
                    if server_name is not None:
                        Settings.inform(f"Connection to {address} is still open.")
                        alive = True

                if not alive:
                    Settings.inform(f"Unable to reach server {address}.")
                    refresh, server_name = self.connection_error(is_server, address)
                    return
            t0 = t1

    def listen(self):
        while self.working:
            data, address = super().recive(self.socket_)

            print(data)
            if Settings.allowed(address) and address in self.rooms:
                    self.rooms[address].append(data)

            time.sleep(self.frequency)

    def seek(self):
        while self.working:
            for port in range(Settings.default_port, Settings.default_port + Settings.rooms_num):
                address = (Settings.host, port)

                if address not in self.rooms:
                    server_name = self.test_server(address)
                    if server_name is not None:
                        Settings.inform(f"New connection found at {address}.")
                        self.screen.add_action("ADD", (server_name, address))
                        self.rooms[address] = [] # queue for data from that server
                        start_new_thread(self.listen_server, (address, time.time()))
                    
    def leave(self):
        self.screen.add_action("RESET", None)