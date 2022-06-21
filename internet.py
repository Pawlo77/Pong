import socket
import json

from settings import Settings

class Internet:
    def get_socket_(self, port):
        try:
            socket_ = socket.socket()
            socket_.settimeout(Settings.connection_timeout)
            socket_.connect((Settings.host, port))
        except Exception as e:
            Settings.handle_error(e)
            return None
        return socket_

    def send(self, socket_, data):
        data = json.dumps(data).encode(Settings.encoding)
        
        try:
            socket_.send(data)
        except Exception as e:
            Settings.handle_error(e)
            return False
        return True

    def recive(self, socket_):
        try:
            data = socket_.recv(Settings.conn_data_limit).decode(Settings.encoding)

            if data:
                return json.loads(data)
        except Exception as e:
            Settings.handle_error(e)
        return {}

    def shutdown(self, obj):
        try:
            obj.close()
        except Exception as e:
            Settings.handle_error(e)