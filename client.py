from _thread import *
from audioop import add
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
            settings.inform(f"Setting up a client.")
        else:
            settings.inform(f"Resetting a client.")

        self.rooms = set() # list of found servers
        self.server_address = None
        self.server_name = ""
        self.client_name = ""
        self.seeking = False # marks if we are searching for new servers or maintaining connection with one that doesn't play against us
        self.waiting = False
        self.reset_internet(initial)

    def initialize(self, client_name, screen):
        settings.inform("Initializing the client")
        self.screen = screen
        self.client_name = client_name
        self.seeking = True 

        self.socket_ = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        start_new_thread(self.seek, ())

    def request_game(self, server_address):
        self.server_address = server_address
        
    # test if binded server is open. If yes, return its name
    def test_server(self, address, socket_, initial=True): 
        self.send(socket_, ALIVE, address)
        data = self.data_recive(socket_)

        try:
            server_name = data.pop("server_name") # our servers sends their names on ALIVE request
            if initial: # new server must send its name and new address dedicated for us
                address = data.pop("address")
            else:
                address = None
        except Exception as e:
            settings.handle_error(e)
        else:
            if data == REQUEST_RECIVED:
                return server_name, address
        return None, None

    def connection_error(self, is_server, address, old_address, socket_):
        f = self.screen is not None and self.playing and self.screen.ended == True # prevents sending leave on game_end
        if not f:
            if not self.seeking and self.server_address != address: # planned exit
                    self.send(socket_, LEAVE, address)
            else:
                self.screen.add_action("REMOVE", address)
                self.rooms.remove(old_address)

                if self.playing and is_server: # if we play against this server
                    self.screen.add_action("ERROR", ("Server lost", "Game crashed due to lost connection with a host"))
                    self.screen.add_action("LEAVE", None)
                elif self.waiting and is_server: # if we wait for this server to accept us
                    self.server_address = None
                    self.waiting = False
                    self.screen.add_action("STOP WAITING", ("Server Lost", "Unable to join the server."))
        self.shutdown(socket_)

    # threaded connection with specified server
    def listen_server(self, socket_, server_name, address, old_address, t0):
        def send(data): # utility function to send data inside this function
            self.send(socket_, data, address)

        refresh = settings.server_frequency
        while self.seeking or address == self.server_address: # if we maintain connections with all servers or its our oponent
            is_server = address == self.server_address
            t1 = time.time()
            
            if t1 - t0 > settings.connection_timeout:
                settings.inform(f"Connection timeout ({address}).")
                break # will call connecion_error
            
            data = self.data_recive(socket_)

            if data == LEAVE:
                settings.inform(f"Server {address} left.")
                break # will call connecion_error

            # we have some action with that server
            elif is_server:
                if data == ABANDON: # if other side abandoned the connection
                    settings.inform(f"Server {address} abandoned us.")
                    send(REQUEST_RECIVED)
                    self.server_address = None
                    
                    if self.playing: # if we were playing against it
                        self.screen.add_action("ERROR", ("Server lost", "Player left a game"))
                        self.screen.add_action("LEAVE", None)
                        return
                    else:
                        break # will call connecion_error

                elif self.abandon_: # if we want to abandon the connection
                    settings.inform(f"Abandoned actions with {address}.")
                    send(ABANDON)
                    self.abandon_ = False
                    self.waiting = False
                    self.server_address = None

                    if self.playing: # if we are playing against it
                        self.screen.add_action("LEAVE", None)
                        return

                elif self.playing and is_server: # if we are playing with him
                    self.internet_action(data, send)

                elif data == BUSY:
                    settings.inform(f"Server {address} started anorher game")
                    self.waiting = False
                    self.server_address = None
                    self.screen.add_action("ERROR", ("Server is busy", "Server has already started a game."))
                    send(REQUEST_RECIVED)

                elif self.waiting and data == GAME_ACCEPTED: # server accepted us
                    settings.inform(f"Starting the game with {address}")
                    send(GAME_START) # send that we understood and that we are ready to play
                    self.waiting = False
                    self.playing = True
                    self.seeking = False
                    self.server_name = server_name
                    refresh = settings.server_time_refresh # set waiting to game waiting (much smaller)
                    self.screen.add_action("START", self)

                elif not self.waiting: # request the game
                    settings.inform(f"Requesting a game from {address}.")
                    data = {"client_name": self.client_name, **REQUEST_GAME}
                    send(data)
                    self.waiting = True
                
                elif data == REQUEST_RECIVED: # contact server that we are still waiting
                    settings.inform(f"Waiting for game from {address}.")
                    send(WAITING) # tell him we are here

            # we know that the server exists but we don't have an action with it
            else:
                if data == BUSY: # if server is not longer open for us
                    settings.inform(f"Connection to {address} is busy, closing it.")
                    break # will call connecion_error
                else:
                    send(ALIVE) # tell him we are here
                    server_name = data.pop("server_name", None) # check if he contacted us
                    if server_name is not None and data == REQUEST_RECIVED:
                        settings.inform(f"Connection to {address} is still open.")

            if data: # there was an interaction with server, reset timer
                t0 = t1
            time.sleep(refresh)
        
        self.connection_error(is_server, address, old_address, socket_)

    def seek(self):
        socket_ = self.get_empty_socket()

        while self.seeking: # as long as we seek connection with a new server
            for ip in Internet.get_devices():
                for port in range(settings.PORT, settings.MAX_PORT + 1):
                    address = (ip, port)

                    if address not in self.rooms: # if we aren't connected to him
                        server_name, new_address = self.test_server(address, socket_)

                        if server_name is not None: # if it is our server and it's open for us
                            new_address = tuple(new_address)
                            settings.inform(f"New connection found at {address}, redirected to {new_address}.")
                            self.screen.add_action("ADD", (server_name, new_address))
                            self.rooms.add(address)
                            start_new_thread(self.listen_server, (socket_, server_name, new_address, address, time.time()))
                            socket_ = self.get_empty_socket() # request new socket to seeking the servers
                time.sleep(settings.server_frequency)
                        