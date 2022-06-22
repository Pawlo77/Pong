from _thread import *
import time

from settings import *
from internet import Internet


class Client(Internet):
    def __init__(self):
        self.type_ = "client"
        self.reset(True)

    def reset(self, initial=False):
        if initial:
            Settings.inform(f"Setting up a client.")
            self.rooms = [None] * Settings.rooms_num
        else:
            Settings.inform(f"Resetting a client.")
            for idx in range(Settings.rooms_num):
                self.shutdown(idx + Settings.default_port)

        self.screen = None
        self.client_name = ""
        self.port = None
        self.playing = False
        self.listening = False
        self.waiting = False
        self.abandon = False

    def initialize(self, client_name, screen):
        Settings.inform("Initializing the client")
        self.screen = screen
        self.client_name = client_name
        self.start_listening()

    def start_listening(self):
        self.listening = True
        for idx in range(Settings.rooms_num):
            start_new_thread(self.listen, (idx, ))

    def shutdown(self, port):
        idx = Settings.default_port - port
        try:
            if self.rooms[idx] is not None:
                self.rooms[idx].close()
        except Exception as e:
            Settings.handle_error(e)
        self.rooms[idx] = None

    def request_game(self, port):
        self.port = port
        
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

    def queue_action(self, port, inf):
        if not inf:
            self.screen.actions.append(("REMOVE", port))
        elif inf == "fatal":
            self.screen.actions.append(("REMOVE", port))
            self.screen.actions.append(("ERROR", ("Server error", "Unable to connect to a server.")))
        elif inf == "busy":
            self.screen.actions.append(("ERROR", ("Server is busy", "Server has already started a game.")))

    def listen(self, idx):
        port = Settings.default_port + idx
        refresh = Settings.conn_frequency
        server_name = ""

        while self.listening or port == self.port:
            socket_ = self.rooms[idx]
            alive = False
            error = ""

            # we have some action with that server
            if port == self.port:
                t1 = time.time()

                # connection to server lost
                if socket_ is None:
                    pass

                # connection timeout
                elif (self.waiting or self.playing) and t1 - t0 > Settings.connection_timeout:
                    Settings.inform(f"Connection timeout ({port}).")

                elif self.abandon and self.port == port:
                    if self.send(socket_, ABORT):
                        if self.recive(socket_) == REQUEST_RECIVED:
                            alive = True
                    self.abandon = False
                    self.waiting = False
                    self.playing = False
                    self.port = None
                    refresh = Settings.conn_frequency
                    Settings.inform(f"Abandoned actions with {port}.")

                elif self.playing:
                    alive = True

                # request the game
                elif not self.waiting:
                    data = {"client_name": self.client_name, **REQUEST_GAME}
                    Settings.inform(f"Requesting a game from {port}.")
                
                    if self.send(socket_, data):
                        response = self.recive(socket_)

                        if response == REQUEST_RECIVED:
                            alive = True
                            self.waiting = True
                            # t1 = time.time() # it will overwrite t0 at the end
                            # refresh /= 4 # make things there smoother
                            Settings.inform(f"Request recived.")

                    if not alive:
                        Settings.inform(f"Request failed.")
                    
                # contact server that we are waiting
                else:
                    if self.send(socket_, WAITING):
                        response = self.recive(socket_)

                        # server accepts a game
                        if response == REQUEST_ACCEPTED:
                            alive = True
                            refresh = 1. / Settings.fps
                            self.waiting = False
                            self.listening = False
                            self.playing = True
                            Settings.inform(f"Server {port} accepted a game.")
                            self.screen.add_action("START", self)

                        elif response == REQUEST_RECIVED:
                            alive = True
                            Settings.inform(f"Waiting for game from {port}.")

                        elif response == BUSY:
                            alive = True
                            self.waiting = False
                            self.port = None
                            error = "busy"
                            Settings.inform(f"Server {port} started anorher game")

                if alive:
                    t0 = t1 # reset timeout

            # if we know that the server exists but we don't have an action with it
            elif socket_ is not None:
                server_name = self.test_socket(socket_)
                if server_name is not None:
                    alive = True
                    Settings.inform(f"Connection to {port} is still open.")
                else:
                    error = "" # silent removal

            else:
                alive = True # don't call queue_action if server didn't existed nor was corelated to us
                socket_ = self.get_socket_(port)
                server_name = self.test_socket(socket_)

                if server_name is not None: # new server found
                    self.rooms[idx] = socket_
                    self.screen.actions.append(("ADD", (server_name, port)))
                    Settings.inform(f"New connection found at {port}.")
        
            if not alive:
                self.shutdown(port) 
                self.port = None
                if self.waiting:
                    self.screen.actions.append(("STOP WAITING", ("Server Lost", "Unable to join the server.")))
                self.waiting = False
                self.playing = False
                self.abandon = False
                refresh = Settings.conn_frequency
                server_name = ""
                self.queue_action(port, error)
                Settings.inform(f"Server {port} lost.")
            elif error:
                self.queue_action(port, error)
            time.sleep(refresh)
