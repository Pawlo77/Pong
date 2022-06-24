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
    
    def event_dispatcher(self, key, value):
        self.data.append((key, value))

    def internet_action(self, data, send):
        alive = False

        if self.data or self.update_data: # if we have data to send
            send_ = self.data + [("UPDATE", self.update_data)]
            send_ = {"GAME": send_}
            alive = send(send_)
            self.data = []
            self.update_data = tuple()
        else: # inform him that we are still alive
            alive = send(REQUEST_RECIVED)

        # if we have some data to recive
        if "GAME" in data:
            self.screen.actions += data["GAME"]
        # if data and data != REQUEST_RECIVED: # if recived data is significant pass it to a game
        #     for key, val in data.items():
        #         self.screen.actions.append((key, val))
        return alive

