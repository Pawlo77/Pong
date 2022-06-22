from audioop import add
import socket
import json

from settings import *

class Internet:
    def get_socket_(self, port):
        try:
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket.settimeout(0.1)
            address = (Settings.host, port)
            # socket_.connect(address)
        except Exception as e:
            Settings.handle_error(e)
            return None, None
        return socket_, address

    def send(self, socket_, data, address):
        data = {**data, **all}
        data = json.dumps(data).encode(Settings.encoding)
        
        try:
            print(data, address)
            socket_.sendto(data, address)
        except Exception as e:
            Settings.handle_error(e)
            return False
        return True

    def recive(self, socket_):
        try:
            data, address = socket_.recvfrom(Settings.conn_data_limit)
            data = data.decode(Settings.encoding)
            print(data, address)
            if data:
                data = json.loads(data)
                if "key" in data.keys():
                    if data["key"] == Settings.key:
                        del data["key"]
                        return data, address         
        except Exception as e:
            Settings.handle_error(e)
        return {}, None

    def shutdown(self, obj):
        try:
            obj.close()
        except Exception as e:
            Settings.handle_error(e)
    

