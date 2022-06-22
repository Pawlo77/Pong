from _thread import *
import time
import socket

from settings import *
from internet import Internet


class Server(Internet):
    def __init__(self):
        self.type_ = "server"
        self.reset(True)

    def reset(self, initial=False):
        if initial:
            Settings.inform(f"Setting up a server.")
        else:
            Settings.inform(f"Resetting a server {self.address}")
            if self.socket_ is not None:
                self.shutdown(self.socket_)

        self.address = None
        self.client_address = True
        self.socket_ = None
        self.server_name = ""
        self.working = False
        self.frequency = Settings.server_frequency

        self.screen = None
        self.listening = False
        self.playing = False
        self.accept = False
        self.abandon_ = False
        self.clients = {}

    def initialize(self, server_name, screen):
        Settings.inform(f"Initializing a server.")
        self.server_name = server_name
        self.screen = screen

        port = Settings.default_port
        socket_ = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        while port < Settings.default_port + Settings.rooms_num:
            try:
                address = (Settings.host, port)
                socket_.bind(address)
            except Exception as e:
                Settings.handle_error(e)
            else:
                self.socket_ = socket_
                self.address = address
                self.listening = True
                self.working = True
                start_new_thread(self.listen, ())             
                Settings.inform(f"Server created at {address}.")
                break

            port += 1

    def recive(self):
        return super().recive(self.socket_)

    def accept_game(self, address):
        self.accept = True
        self.client_address = address

    def abandon(self):
        self.abandon_ = True

    def connection_error(self, is_client, address):
        if self.playing and is_client:
            self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))
            self.leave()
        elif self.accept:
            self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))

        if self.screen.accept is not None and self.screen.accept.address == address: # if accept popup is open
            self.screen.add_action("ERROR", ("Connection lost", "Connection to that client has been lost."))
            self.screen.accept.back_up()
        
        del self.clients[address]
        self.screen.add_action("REMOVE", address)

    def listen_client(self, address, t0):
        def send(data):
            return self.send(self.socket, data, address)
            
        while self.listening or address == self.client_address: 
            is_client = self.client_address == address
            t1 = time.time()

            if t1 - t0 > Settings.connection_timeout:
                Settings.inform(f"Connection timeout ({address}).")
                self.connection_error(is_client, address)
                return
                     
            while len(self.clients[address]):
                alive = False
                data = self.clients[address].pop(0)

                if self.abandon_ and self.playing and is_client:
                    Settings.inform(f"Abandoning the game with {address}.")
                    alive = send(ABANDON)
                    self.leave()
                    return
                elif self.playing and is_client:
                    print("tick")
                    alive = send(REQUEST_RECIVED)

                if data == ABANDON:
                    Settings.inform(f"Client {address} aborted.")
                    
                    if self.playing and is_client:
                        self.screen.add_action("ERROR", ("Player left", "Player left the game."))
                        self.leave()
                        return
                    if self.screen.accept is not None and self.screen.accept.address == address: # if accept popup to that client was open
                        self.screen.add_action("ERROR", ("Client resigned", "That user is not longer interested."))
                        self.client_address = None
                        self.frequency = Settings.server_frequency
                    alive = send(REQUEST_RECIVED)

                elif data == ALIVE:
                    Settings.inform(f"Connection with client {address} renewed.")
                    alive = send({"server_name": self.server_name, **REQUEST_RECIVED})

                elif data == WAITING:
                    if self.accept and is_client: # accepting the game
                        Settings.inform(f"Game with {address} started.")
                        alive = send(GAME_ACCEPTED)
                    else: # renew connection
                        Settings.inform(f"Client {address} is still waiting to join.")
                        alive = send(REQUEST_RECIVED)

                elif self.accept and data == GAME_START:
                    Settings.inform(f"Starting the game with {address}")
                    self.playing = True
                    self.accept = False
                    self.screen.add_action("START", self)
                    self.frequency = 1. / Settings.fps
                    alive = True

                elif "client_name" in data:
                    client_name = data["client_name"]
                    del data["client_name"]

                    if data == REQUEST_GAME:
                        Settings.inform(f"Client {address} wants to join a game.")
                        alive = send(REQUEST_RECIVED)
                        self.screen.add_action("ADD", (client_name, address))
                        self.frequency /= 5 # make things smoother

                if not alive:
                    Settings.inform(f"Unable to reach client ({address}).")
                    self.connection_error(is_client, address)
                    return
            t0 = t1

    def listen(self):
        while self.working:
            data, address = self.recive()
            print(data)

            if address in self.clients:
                self.clients[address].append(data)

            elif data == ALIVE:
                response = {"server_name": self.server_name, **REQUEST_RECIVED}

                if self.send(self.socket_, response, address):
                    Settings.inform(f"New connection from {address[1]}.")
                    self.clients[address] = [] # queue with data from clients
                    start_new_thread(self.listen_client, (address, time.time()))

    def leave(self):
        self.screen.add_action("RESET", None)

# import psutil
# conns = psutil.net_connections()

