class Settings():
    fps = 60
    speed = 0.01 # ball speed
    speedup = 1.05 # ball speeds up every time it bounce off paddle
    moveSpeed = 0.02 # paddle move speed
    botMoveSpeed = 0.002 # bot is slower than real player
    startPaddleSize = 0.3
    rounds_to_win = 10

    font_size = 120
    transition_duration = 3

    default_port = 8000
    host = "127.0.0.1"
    rooms_num = 20
    conn_data_limit = 1024

    connection_timeout = 2
    socket_timeout = 0.1
    accept_timeout = 10 # time tha user has to accept the game in AcceptPopup
    waiting_timeout = 180 # time during after server will be closed if it hadn't started the game
    joining_timeout = 180 # time during after JoinPopup will dissapear

    server_time_refresh = 0.05 # waiting time between server loops in ms for players
    server_frequency = 1 # waiting time between server loops in ms for rest
    encoding = "utf-8"
    key = "7fZmv`UXa75@K7e$3+g@"

    debug = False
    verbose = True

    def handle_error(self, e): 
        if self.debug:
            print(e)

    def inform(self, msg):
        if self.verbose:
            print(msg)

    def allowed(self, address):
        if address:
            return address[0] == self.host and self.default_port <= int(address[1]) <= self.default_port + self.rooms_num
        return False


settings = Settings()


all = {

    "key": settings.key
}

ALIVE = {"free": None,}
LEAVE = {"left": True,}

WAITING = {"waiting": True,}
REQUEST_GAME = {"ok": True,}
REQUEST_RECIVED = {"understood": True,}
BUSY = {"allowed": False,}
ABANDON = {"bye": True,}

GAME_ACCEPTED = {"allowed": True,}
GAME_START = {"start": True,}