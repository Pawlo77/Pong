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
    host = "localhost"
    rooms_num = 20
    conn_data_limit = 1024

    connection_timeout = 10
    accept_timeout = 10
    waiting_timeout = 180
    joining_timeout = 180

    conn_frequency = 3
    server_frequency = 1
    encoding = "utf-8"
    conn_key = "7fZmv`UXa75@K7e$3+g@"

    debug = False
    verbose = True

    def handle_error(e): 
        if Settings.debug:
            print(e)

    def inform(msg):
        if Settings.verbose:
            print(msg)


all = {
    "conn_key": Settings.conn_key
}

ALIVE = {
    "free": None,
    **all
}
REQUEST_GAME = {
    "ok": True,
    **all
}

REQUEST_RECIVED = {
    "understood": True,
    **all
}

WAITING = {
    "waiting": True,
    **all
}

ABORT = {
    "bye": True,
    **all
}

REQUEST_ACCEPTED = {
    "allowed": True,
    **all
}

BUSY = {
    "allowed": False,
    **all
}