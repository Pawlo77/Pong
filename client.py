from _thread import *
from tempfile import TemporaryFile
import time
import socket
from tkinter import N

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

        self.rooms = set()
        self.data = {}
        self.server_address = None
        self.client_name = ""
        self.seeking = False

        self.screen = None
        self.playing = False
        self.waiting = False
        self.abandon_ = False

    def initialize(self, client_name, screen):
        Settings.inform("Initializing the client")
        self.screen = screen
        self.client_name = client_name
        self.seeking = True

        self.socket_ = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        start_new_thread(self.seek, ())

    def request_game(self, server_address):
        self.server_address = server_address

    def abandon(self):
        self.abandon_ = True
        
    # test if binded server is open. If yes, return its name
    def test_server(self, address, socket_, initial=True): 
        if self.send(socket_, ALIVE, address):
            data = self.data_recive(socket_)

            try:
                server_name = data.pop("server_name")
                if initial:
                    address = data.pop("address")
                else:
                    address = None
            except Exception as e:
                Settings.handle_error(e)
            else:
                if data == REQUEST_RECIVED:
                    return server_name, address
        return None, None

    def connection_error(self, is_server, address, old_address, socket_):
        if not self.seeking and self.server_address != address: # planned exit
            self.send(socket_, LEAVE, address)
        else:
            self.screen.add_action("REMOVE", address)
            self.rooms.remove(old_address)

            if self.playing and is_server:
                self.screen.add_action("ERROR", ("Server lost", "Game crashed due to lost connection with a host"))
                self.leave()
            if self.waiting and is_server:
                self.server_address = None
                self.waiting = False
                self.screen.add_action("STOP WAITING", ("Server Lost", "Unable to join the server."))
        self.shutdown(socket_)

    def listen_server(self, socket_, address, old_address, t0):
        def send(data):
            return self.send(socket_, data, address)

        refresh = Settings.server_frequency
        while self.seeking or address == self.server_address:
            is_server = address == self.server_address
            t1 = time.time()
            
            if t1 - t0 > Settings.connection_timeout:
                Settings.inform(f"Connection timeout ({address}).")
                break
            
            alive = False
            data = self.data_recive(socket_)

            if data == LEAVE:
                Settings.inform(f"Server {address} left.")
                break

            # we have some action with that server
            elif is_server:
                if data == ABANDON:
                    Settings.inform(f"Server {address} abandoned us.")
                    if self.playing:
                        self.screen.add_action("ERROR", ("Server lost", "Game crashed due to lost connection with a host"))
                        self.leave()
                    alive = send(REQUEST_RECIVED)
                    self.server_address = None

                elif self.abandon_:
                    Settings.inform(f"Abandoned actions with {address}.")
                    if self.playing:
                        self.leave()
                        return

                    alive = send(ABANDON)
                    self.abandon_ = False
                    self.waiting = False
                    self.server_address = None

                elif self.playing:
                    alive = self.internet_action(data, send)

                elif data == BUSY:
                    Settings.inform(f"Server {address} started anorher game")
                    self.waiting = False
                    self.server_address = None
                    self.screen.add_action("ERROR", ("Server is busy", "Server has already started a game."))
                    alive = send(REQUEST_RECIVED)

                elif self.waiting and data == GAME_ACCEPTED:
                    Settings.inform(f"Starting the game with {address}")
                    alive = send(GAME_START)
                    self.waiting = False
                    self.playing = True
                    self.listening = False
                    refresh = 1. / Settings.fps
                    self.screen.add_action("START", self)

                # request the game
                elif not self.waiting:
                    Settings.inform(f"Requesting a game from {address}.")
                    data = {"client_name": self.client_name, **REQUEST_GAME}
                    alive = send(data)
                    self.waiting = True
                
                # contact server that we are still waiting
                elif data == REQUEST_RECIVED:
                    Settings.inform(f"Waiting for game from {address}.")
                    alive = send(WAITING) # tell him we are here

            # we know that the server exists but we don't have an action with it
            else:
                alive = send(ALIVE) # tell him we are here
                server_name = data.pop("server_name", None) # check if he contacted us
                if server_name is not None and data == REQUEST_RECIVED:
                    Settings.inform(f"Connection to {address} is still open.")

            if data or alive: # there was an interaction with server, reset timer
                t0 = t1
            time.sleep(refresh)
        
        self.connection_error(is_server, address, old_address, socket_)

    def seek(self):
        socket_ = self.get_empty_socket()

        while self.seeking: # as long as we seek connection with a new server
            for port in range(Settings.default_port, Settings.default_port + Settings.rooms_num):
                address = (Settings.host, port)

                if address not in self.rooms:
                    server_name, new_address = self.test_server(address, socket_)

                    if server_name is not None:
                        new_address = tuple(new_address)
                        Settings.inform(f"New connection found at {address}, redirected to {new_address}.")
                        self.screen.add_action("ADD", (server_name, new_address))
                        self.rooms.add(address)
                        start_new_thread(self.listen_server, (socket_, new_address, address, time.time()))
                        socket_ = self.get_empty_socket()
            time.sleep(Settings.server_frequency)
                    
    def leave(self):
        self.screen.add_action("RESET", None)