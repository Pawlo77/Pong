from audioop import add


class Settings():
    fps = 60.
    speed = 0.01
    speedup = 1.05
    moveSpeed = 0.02
    botMoveSpeed = 0.01

    startPaddleSize = 0.3
    paddleShrink = 0.95

    font_size = 120
    transition_duration = 0

    default_port = 8000
    host = "127.0.0.1"
    rooms_num = 20
    conn_data_limit = 1024

    connection_timeout = 10
    accept_timeout = 10
    waiting_timeout = 180
    joining_timeout = 180

    server_frequency = 1
    encoding = "utf-8"
    key = "7fZmv`UXa75@K7e$3+g@"

    debug = False
    verbose = True

    def handle_error(e): 
        if Settings.debug:
            print(e)

    def inform(msg):
        if Settings.verbose:
            print(msg)

    def allowed(address):
        if address:
            return address[0] == Settings.host and Settings.default_port <= int(address[1]) <= Settings.default_port + Settings.rooms_num
        return False


all = {
    "key": Settings.key
}

ALIVE = {"free": None,}
REQUEST_GAME = {"ok": True,}
REQUEST_RECIVED = {"understood": True,}
WAITING = {"waiting": True,}
ABANDON = {"bye": True,}
BUSY = {"allowed": False,}
GAME_ACCEPTED = {"allowed": True,}
GAME_START = {"start": True,}