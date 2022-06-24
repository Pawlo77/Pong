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
            settings.inform(f"Setting up a server.")
        else:
            settings.inform(f"Resetting a server {self.address}")
            if self.socket_ is not None:
                self.shutdown(self.socket_)

        self.clients = set()
        self.client_address = None
        self.client_name = ""
        self.server_name = ""
        self.address = None
        self.socket_ = None
        self.working = False
        self.accept = False
        self.reset_internet(initial)

    def initialize(self, server_name, screen):
        settings.inform(f"Initializing a server.")
        self.server_name = server_name
        self.screen = screen

        port = settings.default_port
        socket_ = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        while port < settings.default_port + settings.rooms_num:
            try:
                address = (settings.host, port)
                socket_.bind(address)
            except Exception as e:
                settings.handle_error(e)
            else:
                self.socket_ = socket_
                self.address = address
                self.working = True
                start_new_thread(self.listen, ())             
                settings.inform(f"Server created at {address}.")
                break

            port += 1

    def accept_game(self, address):
        self.accept = True
        self.client_address = address

    def connection_error(self, is_client, address, socket_):
        if not self.working: # planned exit
            self.send(socket_, LEAVE, address)
        else:
            self.screen.add_action("REMOVE", address)
            self.clients.remove(address)
            
            if self.playing and is_client:
                self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))
                self.screen.add_action("LEAVE", None)

            elif self.accept and is_client:
                self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))

                if self.screen.accept is not None and self.screen.accept.client_address == address: # if accept popup is open
                    self.screen.add_action("ERROR", ("Connection lost", "Connection to that client has been lost."))
                    self.screen.accept.back_up()
        self.shutdown(socket_)

    def listen_client(self, socket_, address, t0):
        def send(data):
            self.send(socket_, data, address)
        
        refresh = settings.server_frequency
        while self.working: 
            is_client = self.client_address == address
            t1 = time.time()

            if t1 - t0 > settings.connection_timeout:
                settings.inform(f"Connection timeout ({address}).")
                break # will call connecion_error
                     
            data = self.data_recive(socket_)

            if data == LEAVE:
                settings.inform(f"Client left.")
                break # will call connecion_error

            elif data == ABANDON:
                settings.inform(f"Client {address} aborted.")
                self.screen.add_action("REMOVE", address)
                send(REQUEST_RECIVED)
                
                if self.playing and is_client:
                    self.screen.add_action("ERROR", ("Client lost", "Player left the game."))
                    self.screen.add_action("LEAVE", None)
                elif self.screen.accept is not None and self.screen.accept.client_address == address: # if accept popup to that client was open
                    self.screen.add_action("ERROR", ("Client resigned", "That user is not longer interested."))
                    self.client_address = None

            elif self.abandon_ and self.playing and is_client:
                settings.inform(f"Abandoning the game with {address}.")
                send(ABANDON)
                self.screen.add_action("LEAVE", None)
                return

            elif self.playing and is_client:
                self.internet_action(data, send)
            
            elif self.playing and not is_client: # send him bey bey
                send(BUSY)
                # at this point we are playing, no need to delete anything
                return

            elif data == ALIVE: # he tells us that he is still here
                settings.inform(f"Connection with client {address} renewed.")
                send({"server_name": self.server_name, **REQUEST_RECIVED})

            elif data == WAITING:
                if self.accept and is_client: # accepting the game
                    settings.inform(f"Game with {address} started.")
                    send(GAME_ACCEPTED)
                else: # renew connection
                    settings.inform(f"Client {address} is still waiting to join.")
                    send(REQUEST_RECIVED)
   
            elif self.accept and data == GAME_START: # client is ready for a game
                settings.inform(f"Starting the game with {address}")
                self.client_name = client_name
                refresh = settings.server_time_refresh
                self.playing = True
                self.accept = False
                self.screen.add_action("START", self)
                
            elif "client_name" in data:
                client_name = data.pop("client_name")

                if data == REQUEST_GAME:
                    settings.inform(f"Client {address} wants to join a game.")
                    send(REQUEST_RECIVED)
                    self.screen.add_action("ADD", (client_name, address))

            if data:  # there was an interaction with client, reset timer
                t0 = t1
            time.sleep(refresh)

        self.connection_error(is_client, address, socket_)

    def get_new_socket(self): # get first free socket on this pc
        port = 1
        socket_ = self.get_empty_socket()

        while True:
            address = (settings.host, port)

            if not settings.allowed(address): # if it is not port used by our main servers 
                try:
                    socket_.bind(address)
                except Exception as e:
                    settings.handle_error(e)
                    port += 1
                else:
                    return socket_, address

    def listen(self):
        while self.working:
            data, address = self.recive(self.socket_)

            if data == ALIVE and address not in self.clients: # if we found new connection from identified client
                new_socket_, new_address = self.get_new_socket()
                
                response = {
                    "server_name": self.server_name,
                    "address": new_address,
                    **REQUEST_RECIVED
                }
                self.send(self.socket_, response, address)
                settings.inform(f"New connection from {address[1]}.")
                self.clients.add(address)
                start_new_thread(self.listen_client, (new_socket_, address, time.time()))

            time.sleep(settings.server_frequency)
