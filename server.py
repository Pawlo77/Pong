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
            Settings.inform(f"Resetting a server ({self.port}).")

            if self.socket_ is not None:
                self.shutdown(self.socket_)
            for conn in self.clients:
                super().shutdown(conn)

        self.screen = None
        self.socket_ = None
        self.listening = False
        self.playing = False
        self.port = None
        self.client_port = True
        self.accept = False
        self.server_name = ""
        self.clients = {} # to access sockets in order to force shut them down on reset

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
                Settings.inform(f"Server created at {port}.")
                break

            port += 1

    def accept_game(self, port):
        self.accept = True
        self.client_port = port

    def queue_action(self, port, inf):
        if not inf:
            self.screen.add_action("REMOVE", port)
        elif inf == "fatal":
            self.screen.add_action("REMOVE", port)
            self.screen.add_action("ERROR", ("Connection error", "Connection with client lost."))

    def listen_client(self, conn, port, t0):
        refresh = Settings.conn_frequency
        self.clients[port] = conn

        while self.listening or port == self.client_port: 
            t1 = time.time()
            alive = False
            error = ""

            if t1 - t0 > Settings.connection_timeout:
                Settings.inform(f"Connection timeout ({port}).")
                if self.accept or self.playing:
                    error = "fatal"
                self.shutdown(conn)
                self.queue_action(port, error)
                break

            data = self.recive(conn)
            basic_response = {"server_name": self.server_name, **REQUEST_RECIVED}

            if data == ALIVE:
                if self.send(conn, basic_response):
                    alive = True
                    Settings.inform(f"Connection with client {port} renewed.")

            elif data == WAITING:
                if self.accept and port == self.client_port: # accepting the game
                    if self.send(conn, REQUEST_ACCEPTED):
                        alive = True
                        self.playing = True
                        Settings.inform(f"Game with {self.client_port} started.")
                        self.screen.add_action("START", self)
                    else:
                        error = "fatal"

                elif self.send(conn, REQUEST_RECIVED):
                    alive = True
                    Settings.inform(f"Client {port} is still waiting to join.")

            elif data == ABORT:
                if self.send(conn, REQUEST_RECIVED):
                    alive = True
                if self.screen.accept is not None and self.screen.accept.client_port == port: # if accept popup to that client was open
                    self.port = None
                    self.screen.add_action("ERROR", ("Client resigned", "That user is not longer interested."))
                self.screen.add_action("REMOVE", port)
                Settings.inform(f"Client {port} aborted.")

            elif "client_name" in data:
                client_name = data["client_name"]
                del data["client_name"]

                if data == REQUEST_GAME:
                    if self.send(conn, REQUEST_RECIVED):
                        alive = True
                        self.screen.add_action("ADD", (client_name, port))
                        Settings.inform(f"Client {port} wants to join a game.")

            if not alive:
                self.shutdown(conn)
                self.queue_action(port, error)
                Settings.inform(f"Client {port} lost.")

                if self.screen.accept is not None and self.screen.accept.client_port == port: # if accept popup to that client was open
                    self.port = None
                    self.screen.add_action("ERROR", ("Server Error", "Connetion to client lost."))
                break
            else:
                t0 = t1
            time.sleep(refresh)

    def listen(self):
        while self.listening:
            conn, address = self.socket_.accept()
            data = self.recive(conn)

            if data == ALIVE:
                data = {"server_name": self.server_name, **REQUEST_RECIVED}
                if self.send(conn, data):
                    Settings.inform(f"New connection from {address[1]}.")
                    start_new_thread(self.listen_client, (conn, address[1], time.time()))
                    continue

            self.shutdown(conn)
            time.sleep(Settings.server_frequency)


# import psutil
# conns = psutil.net_connections()

