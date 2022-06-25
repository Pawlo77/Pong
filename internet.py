import socket
import json
import os
import platform

from settings import settings, REQUEST_RECIVED, all


class Internet:
    def __init__(self):
        self.reset_internet(True)

    def reset_internet(self, initial): # data used by both server and client
        self.data = []
        self.update_data = tuple()
        self.screen = None
        self.playing = False
        self.abandon_ = False

    def abandon(self): # will trigger and abandon call on server / client thread
        self.abandon_ = True

    def get_empty_socket(self):
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_.settimeout(settings.socket_timeout)
        return socket_

    def send(self, socket_, data, address):
        data = {**data, **all}
        data = json.dumps(data).encode(settings.encoding)
        
        try:
            socket_.sendto(data, address)
        except Exception as e:
            settings.handle_error(e)

    def recive(self, socket_): # returns both data and sender address
        try:
            data, address = socket_.recvfrom(settings.conn_data_limit)
            data = data.decode(settings.encoding)
            if data:
                data = json.loads(data)
                if "key" in data.keys():
                    if data["key"] == settings.key:
                        del data["key"]
                        return data, address         
        except Exception as e:
            settings.handle_error(e)
        return {}, None
 
    def data_recive(self, socket_): # returns only data
        return self.recive(socket_)[0]

    def shutdown(self, obj): # shuts down socket / connection if it was on
        try:
            obj.close()
        except Exception as e:
            settings.handle_error(e)
    
    def event_dispatcher(self, key, value): # adds data to be send as a game content
        self.data.append((key, value))

    def internet_action(self, data, send):
        if self.data or self.update_data: # if we have data to send
            send_ = self.data + [("UPDATE", self.update_data)]
            send_ = {"GAME": send_}
            send(send_)
            self.data = []
            self.update_data = tuple()
        else: # inform him that we are still alive
            send(REQUEST_RECIVED)

        # if we have some data to recive
        if "GAME" in data and data["GAME"]:
            self.screen.actions += data["GAME"]

    def check_ip(ip, local):
        try:
            ip_ = ip.split(".")
            end = int(ip_[-1])
            start = int(ip_[0])
        except:
            pass
        else:
            if local is None:
                local = start
            if end not in [1, 255] and start == local:
                return ip, local
        return None, local

    def get_devices():
        devices = []
        data = os.popen('arp -a')
        data = data.read().split("\n\n") # splits interfaces

        system = platform.system()
        
        # comment line below to scan every interface
        data = [data[-1]] # keep only local wifi (leave apps like hamachi)

        for interface in data:
            local = None
            interface = interface.strip("\n")

            if system.lower() == "windows":
                interface = interface.split("\n")[2:] # skip headers lines

                for ip in interface:
                    ip = ip.strip().split()[0]
                    ip, local = Internet.check_ip(ip, local)
                    if ip is not None:
                        devices.append(ip)

            elif system.lower() in ["darwin", "linux"]: # macos
                interface = interface.split("\n")
            
                for ip in interface:
                    ip = ip.split()[1].strip("()")
                    ip, local = Internet.check_ip(ip, local)
                    if ip is not None:
                        devices.append(ip)
        return devices
