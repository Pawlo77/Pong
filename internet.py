import socket
import json

from settings import *

class Internet:
    def abandon(self):
        self.abandon_ = True

    def get_empty_socket(self):
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_.settimeout(Settings.socket_timeout)
        return socket_

    def send(self, socket_, data, address):
        data = {**data, **all}
        data = json.dumps(data).encode(Settings.encoding)
        
        try:
            socket_.sendto(data, address)
        except Exception as e:
            Settings.handle_error(e)
            return False
        return True

    def recive(self, socket_):
        try:
            data, address = socket_.recvfrom(Settings.conn_data_limit)
            data = data.decode(Settings.encoding)
            if data:
                data = json.loads(data)
                if "key" in data.keys():
                    if data["key"] == Settings.key:
                        del data["key"]
                        return data, address         
        except Exception as e:
            Settings.handle_error(e)
        return {}, None

    def data_recive(self, socket_):
        return self.recive(socket_)[0]

    def shutdown(self, obj):
        try:
            obj.close()
        except Exception as e:
            Settings.handle_error(e)
    
    def event_dispatcher(self, key, value=None):
        match key:
            case "UPDATE":
                if "UPDATE" in self.data:
                    self.data["UPDATE"][value[0]] = value[1]
                else:
                    self.data["UPDATE"] = {value[0]: value[1]}
            case _:
                self.data[key] = value


    def internet_action(self, data, send):
        alive = False

        if self.data: # if we have data to send
            alive = send(self.data)
            self.data = {}
        else: # inform him that we are still alive
            alive = send(REQUEST_RECIVED)
        if data and data != REQUEST_RECIVED: # if recived data is significant pass it to a game
            for key, val in data.items():
                self.screen.actions.append((key, val))
        return alive

