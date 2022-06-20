import socket 
import json
from _thread import *
import time

from settings import *


class Server:
    def __init__(self):
        self.reset(True)

    def create(self, server_name):
        self.server_name = server_name
        while self.port < Settings.default_port + Settings.max_rooms_num:
            try:
                self.socket_.bind((Settings.host, self.port))
            except OSError:
                self.port += 1
            except Exception as e: 
                Settings.handle_error(e)
                self.port += 1
            else: 
                start_new_thread(self.listen, ())         
                self.listening = True
                Settings.inform(f"Server created at {self.port}.")
                return

    def send(self, conn, data):
        data = json.dumps(data).encode(Settings.encoding)
        
        try:
            conn.send(data)
        except Exception as e:
            Settings.handle_error(e)
            return False
        return True

    def recive(self, conn):
        try:
            data = conn.recv(Settings.conn_data_limit).decode(Settings.encoding)

            if data:
                return json.loads(data)
        except Exception as e:
            Settings.handle_error(e)
        return {}

    def shutdown(self, obj):
        try:
            obj.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            Settings.handle_error(e)

    def reset(self, initial=False):
        Settings.inform("Server resetting.")
        self.listening = False
        self.game = False
        if not initial:
            self.shutdown(self.socket_)
            Settings.inform(f"Server closed ({self.port}).")
        self.socket_ = socket.socket()
        self.server_name = ""
        self.queue = {} # users waiting for joining
        self.port = Settings.default_port

    def accept(self, port):
        if port in self.queue:
            conn, client_name = self.queue[port]
            
            if self.send(conn, REQEST_ACCEPTED):
                Settings.inform("Game from {port} accepted.")
                self.game = True
                self.listening = False
    
    def wait_for_accept(self, conn, port):
        t0 = time.time()

        while True:
            time.sleep(Settings.server_frequency)

            if self.listening:
                t1 = time.time()
                # if it haven't shown its existance for more than 10 sec without saying
                if t1 - t0 > 10:
                    if port in self.queue:
                        del self.queue[port] 
                    self.shutdown(conn)

                    Settings.inform(f"Connection with {port} lost.")
                    return
                
                # if user backs up
                data = self.recive(conn)
                if data == ABORT_WAITING:
                    if port in self.queue:
                        del self.queue[port]
                    self.shutdown(conn)

                    Settings.inform(f"Client {port} aborted.")
                    return
                
                # if he is still waiting, show him that we are alive too
                elif data == REQUEST_GAME:
                    t0 = t1
                    self.send(conn, REQUEST_RECIVED)
                    Settings.inform(f"Client {port} is still waiting.")
            else:
                break

        # if we don't wait anymore
        if port in self.queue:
            del self.queue[port]
        self.shutdown(conn)

        if self.server_name: # if it isn't our foult
            Settings.inform(f"Stopped waiting (port {port}).")

    def listen(self):
        self.socket_.listen(1)

        while True:
            time.sleep(Settings.server_frequency)

            if self.listening:
                conn, address = self.socket_.accept()
                data = self.recive(conn)

                if data == ALIVE:
                    self.send(conn, {
                        "server_name": self.server_name,
                        **all
                    })

                    Settings.inform(f"Client {address[1]} checked if server is alive.")
                    self.shutdown(conn)

                elif "client_name" in data:
                    client_name = data["client_name"]
                    del data["client_name"]

                    if data == REQUEST_GAME:
                        self.send(conn, REQUEST_RECIVED)

                        pid = start_new_thread(self.wait_for_accept, (conn, address[1]))
                        self.queue[address[1]] = (conn, client_name)
                        Settings.inform(f"Client {address[1]} requested the game.")
                    else:
                        self.shutdown(conn)
                else:  
                    self.shutdown(conn)
            else:
                return


if __name__ == "__main__":
    server = Server()
    if server.create():
        print("Server created at ", server.port)
        server.listen()

# import psutil
# conns = psutil.net_connections()

