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

        self.clients = set()
        self.data = {}
        self.client_address = None
        self.address = None
        self.socket_ = None
        self.server_name = ""
        self.working = False

        self.screen = None
        self.playing = False
        self.accept = False
        self.abandon_ = False

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
                self.working = True
                start_new_thread(self.listen, ())             
                Settings.inform(f"Server created at {address}.")
                break

            port += 1

    def accept_game(self, address):
        self.accept = True
        self.client_address = address

    def abandon(self):
        self.abandon_ = True

    def connection_error(self, is_client, address, socket_):
        if not self.working: # planned exit
            self.send(socket_, LEAVE, address)
        else:
            self.screen.add_action("REMOVE", address)
            self.clients.remove(address)
            
            if self.playing and is_client:
                self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))
                self.leave()
            elif self.accept and is_client:
                self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))

            if self.screen.accept is not None and self.screen.accept.client_address == address: # if accept popup is open
                self.screen.add_action("ERROR", ("Connection lost", "Connection to that client has been lost."))
                self.screen.accept.back_up()
        self.shutdown(socket_)

    def listen_client(self, socket_, address, t0):
        def send(data):
            return self.send(socket_, data, address)
        
        refresh = Settings.server_frequency
        while self.working: 
            is_client = self.client_address == address
            t1 = time.time()

            if t1 - t0 > Settings.connection_timeout:
                Settings.inform(f"Connection timeout ({address}).")
                break
                     
            alive = False
            data = self.data_recive(socket_)

            if data == LEAVE:
                Settings.inform(f"Client {address} left.")
                break

            elif self.abandon_ and self.playing and is_client:
                Settings.inform(f"Abandoning the game with {address}.")
                alive = send(ABANDON)
                self.leave()
                return

            elif data == ABANDON:
                Settings.inform(f"Client {address} aborted.")
                self.screen.add_action("REMOVE", address)
                
                if self.playing and is_client:
                    self.screen.add_action("ERROR", ("Player left", "Player left the game."))
                    self.leave()
                    return
                if self.screen.accept is not None and self.screen.accept.client_address == address: # if accept popup to that client was open
                    self.screen.add_action("ERROR", ("Client resigned", "That user is not longer interested."))
                    self.client_address = None
                alive = send(REQUEST_RECIVED)

            elif self.playing and is_client:
                alive = self.internet_action(data, send)

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
                refresh = 1. / Settings.fps
                self.playing = True
                self.accept = False
                self.screen.add_action("START", self)
                

            elif "client_name" in data:
                client_name = data["client_name"]
                del data["client_name"]

                if data == REQUEST_GAME:
                    Settings.inform(f"Client {address} wants to join a game.")
                    alive = send(REQUEST_RECIVED)
                    self.screen.add_action("ADD", (client_name, address))

            if data or alive: # there was an interaction with client, reset timer
                t0 = t1
            time.sleep(refresh)

        self.connection_error(is_client, address, socket_)

    def get_new_socket(self):
        port = 1
        socket_ = self.get_empty_socket()

        while True:
            address = (Settings.host, port)

            if not Settings.allowed(address): # if it is not a default port
                try:
                    socket_.bind(address)
                except Exception as e:
                    Settings.handle_error(e)
                    port += 1
                else:
                    return socket_, address

    def listen(self):
        while self.working:
            data, address = self.recive(self.socket_)

            if data == ALIVE and address not in self.clients:
                new_socket_, new_address = self.get_new_socket()
                
                response = {
                    "server_name": self.server_name,
                    "address": new_address,
                    **REQUEST_RECIVED
                }
                if self.send(self.socket_, response, address):
                    Settings.inform(f"New connection from {address[1]}.")
                    self.clients.add(address)
                    start_new_thread(self.listen_client, (new_socket_, address, time.time()))
                else:
                    self.shutdown(new_socket_)
            time.sleep(Settings.server_frequency)

    def leave(self):
        self.screen.add_action("RESET", None)

# import psutil
# conns = psutil.net_connections()

