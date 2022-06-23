from kivy.properties import NumericProperty, ObjectProperty, ReferenceListProperty, BooleanProperty, StringProperty, ColorProperty, NumericProperty, ListProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

from random import randint, choice
from functools import partial
from _thread import *

from settings import Settings
from widgets import Paddle, ErrorPopup, AcceptPopup, JoinPopup
from bot import Bot
from server import Server
from client import Client
from helpers import EventManager

class MyScreen():
    def __init__(self):
        self.settings = Settings()


class MenuScreen(Screen, MyScreen):
    pass


class ConnectScreen(Screen, MyScreen):
    pass


class NameScreen(Screen, MyScreen):
    next_screen = StringProperty("")
    username = ObjectProperty(None)
    username_border_col = ColorProperty("white")

    def validate(self):
        if len(self.username.text.strip()) > 0: # if provided and doesn't consists of whitespaces
            # remove whitespaces and keep only 10 first characters
            username = self.username.text.strip()
            username = username[:10] + "..." if len(username) > 10 else username

            self.manager.transition.duration = Settings.transition_duration
            self.manager.transition.direction = "left"
            self.manager.current = self.next_screen
            self.manager.current_screen.initialize(username)
            self.reset()
        else:
            self.username_border_col = "red"

    def reset(self): 
        self.username_border_col = "white"
        self.username.text = ""


class ServerScreen(Screen, MyScreen):
    dots = NumericProperty(0) # to change number of dots on the end of screen's title 
    time = NumericProperty(Settings.waiting_timeout)
    clients_list = ListProperty([])

    def __init__(self, **kwargs):
        super(ServerScreen, self).__init__(**kwargs)
        self.reset(True)

    def reset(self, initial=False):
        if not initial:
            self.server.reset()
            if self.accept is not None:
                self.accept.back_up()
            if self.ticking is not None:
                self.ticking.cancel()
        else:
            self.server = Server()
            self.accept = None
            self.ticking = None
        self.dots = 0
        self.clients_list = []
        self.actions = [] # all must be O(1)
        self.time = Settings.waiting_timeout # shut down the server after specified time if is doesn't start a game

    def initialize(self, server_name):
        self.reset()
        self.ticking = Clock.schedule_interval(self.tick, 1)# administrates all actions
        self.server.initialize(server_name, self)
        if not self.server.working:
            self.manager.current = "connect"
            ErrorPopup("Server error", "Unable to create server, try again later.").open()
            self.reset()

    def add_action(self, name, data):
        self.actions.append((name, data))

    def remove_client(self, address): # remove client from list if it is present
        for idx, entry in enumerate(self.clients_list):
            if entry["address"] == address:
                self.clients_list.pop(idx)
                return

    def add_client(self, client_name, client_address):
        self.clients_list.append({
            "text": client_name, "address": client_address, "root": self
        })

    def tick(self, *dt):
        self.time -= 1
        self.dots = (self.dots + 1) % 4

        if self.time <= 0:
            self.manager.current = "connect"
            ErrorPopup("Server closed", "Your server was closed bacause you exceeded connection time.").open()
            self.reset()

        while len(self.actions):
            name, data = self.actions.pop(0)
            match name:
                case "REMOVE":
                    self.remove_client(data)
                case "ADD":
                    self.add_client(*data)
                case "ERROR":
                    if self.accept is not None: # if accept popup is active or might be active
                        self.accept.back_up()
                    ErrorPopup(*data).open()
                case "START":
                    self.ticking.cancel() # we can't reset here, server will be lost
                    self.accept.back_up()
                    self.manager.transition.duration = Settings.transition_duration
                    self.manager.transition.direction = "up"
                    self.manager.current = "game"
                    self.manager.current_screen.set_up("server", data)

    def handler(self, client_name, client_address):
        self.accept = AcceptPopup(client_name, client_address, self)
        self.accept.open()


class ClientScreen(Screen, MyScreen):
    servers_list = ListProperty([])
    dots = NumericProperty(0) # to change number of dots on the end of screen's title 

    def __init__(self, **kwargs):
        super(ClientScreen, self).__init__(**kwargs)
        self.reset(True)

    def reset(self, initial=False):
        if not initial and self.ticking is not None:
            self.ticking.cancel()
        else:
            self.ticking = None
        if not initial:
            self.client.reset()
            if self.join is not None:
                self.join.dismiss()
        else:
            self.client = Client()
            self.join = None
        self.dots = 0
        self.servers_list = []
        self.actions = [] # each action must be O(1)

    def initialize(self, client_name):
        self.reset()
        self.client.initialize(client_name, self)
        self.ticking = Clock.schedule_interval(self.tick, 1)

    def add_action(self, name, data):
        self.actions.append((name, data))

    def add_server(self, server_name, server_address):
        self.servers_list.append({
            "text": server_name, "address": server_address, "root": self
        })

    def remove_server(self, server_address): # remove server from the list if present
        for idx, entry in enumerate(self.servers_list):
            if entry["address"] == server_address:
                self.servers_list.pop(idx)
                return

    def tick(self, *dt):
        self.dots = (self.dots + 1) % 4

        while len(self.actions):
            name, data = self.actions.pop(0)
            match name:
                case "REMOVE":
                    self.remove_server(data)
                case "ADD":
                    self.add_server(*data)
                case "STOP WAITING": # server we wait for is unavailable
                    self.join.back_up(False)
                    ErrorPopup(*data).open()
                case "START":
                    self.ticking.cancel() # we can't reset here, client will be lost
                    self.join.back_up(False) # back up but don't abandon the server
                    self.manager.transition.duration = Settings.transition_duration
                    self.manager.transition.direction = "up"
                    self.manager.current = "game"
                    self.manager.current_screen.set_up("client", data)

    def handler(self, server_name, server_address):
        self.client.request_game(server_address) # send request to a server
        self.join = JoinPopup(server_name, self) 
        self.join.open()
        

class StatsScreen(Screen, MyScreen):
    pass


class PauseScreen(Screen, MyScreen):
    def abort(self):
        game = self.manager.get_screen("game")

        if game.internet is not None:
            game.internet.abandon = True
    
    def unpause(self):
        self.manager.transition.duration = 0
        self.manager.current = "game"
        game = self.manager.current_screen
        game.add_action("COUNTDOWN", (("UNPAUSE", None), 3))


class GameScreen(Screen, MyScreen, EventManager):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    players = ReferenceListProperty(player1, player2)
    streak = NumericProperty(0)
    cc = BooleanProperty(False)
    gg = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.reset(True)

    def reset(self, initial=False):
        Settings.inform(f"Resetting the game ({initial}).")
        if initial:
            self.keyboard = Window.request_keyboard(None, self)
            self.ticking = None
            self.playing = None
            self.reseting_players = None
            self.counting = None
            self.serving = None
            self.internet = None # client or server handling connections 
            self.events = [self.ticking, self.playing, self.counting, self.serving, self.reseting_players]
        else:
            for player in self.players: 
                player.score = 0
            for event in self.events:
                if event is not None:
                    event.cancel()
            self.reset_players()
            self.keyboard.unbind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.started = False
        self.cc = self.gg = False # marks if countdown or turn is active
        self.cache_streak = 0
        self.actions = [] # all must be O(1)

    def reset_players(self, *dt): # set all players in starting positions and set their color to white
        for player in self.players:
            player.reset(self)

    def set_up(self, opt, internet=None):
        self.opt = opt
        self.internet = internet
        Settings.inform(f"Setting up a game: {opt}")

        match opt:
            case "solo":
                self.player1.move = Bot.move
                self.player1.initialize("Bot", 1)
                self.player2.initialize("You", 2)
            case "offline":
                self.player1.initialize("Player 1", 1)
                self.player2.initialize("Player 2", 2)
            case "server":
                self.internet.screen = self
                self.player1.initialize(internet.client_name, 1)
                self.player2.initialize(internet.server_name, 2)
            case "client":
                self.internet.screen = self
                self.player1.initialize(internet.server_name, 2)
                self.player2.initialize(internet.client_name, 1)

        if opt in ["solo", "offline", "server"]: # for client this action will be send by server
            self.add_action("COUNTDOWN", (("START", None), 5))

        self.player2.move = Paddle.move # this will always be moved by an user
        self.keyboard.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        self.ticking = Clock.schedule_interval(self.tick, 1. / Settings.fps) # administrates all game dependencies

        # object in case of internet connection, they are reversed from client paddles
        self.objects = (
            "ball",
            "player1",
            "client",
            "player2",
            "streak", 
        ) 

    def add_action(self, name, data, *dt):
        if self.opt == "server": # send data to a client
            self.internet.event_dispatcher(name, data)

        if self.opt == "client" and name in ["PAUSE", "ERROR", "RESET"]: # send  data to server
            self.internet.event_dispatcher(name, data)
            self.actions.append((name, data))

        elif self.opt != "client" and name != "UPDATE": # UPDATE is only relevant for event_dispatcher
            self.actions.append((name, data))

    def tick(self, *dt):
        while len(self.actions):
            name, data = self.actions.pop(0)
            print(name, data)

            match name:
                case "ERROR": # connection to second player lost or he left
                    ErrorPopup(*data).open()
                case "RESET":
                    self.manager.current = "menu"
                    self.manager.get_screen(self.internet.type_).reset()
                    self.reset()
                case "COUNTDOWN":
                    target, self.streak = data
                    self.cc = True # mark countdown started
                    self.counting = Clock.schedule_interval(partial(self.countdown, target), 1)
                case "PAUSE":
                    if self.gg: # if during round
                        self.gg = False
                        self.playing.cancel()
                        self.cache_streak = self.streak # save current streak, it will be overwrite by countdown
                    elif self.cc: # if during countdown
                        self.cc = False
                        self.counting.cancel()
                    elif self.serving is not None:
                        self.serving.cancel()
                case "UNPAUSE":
                    if self.started: # if game was already started 
                        self.streak = self.cache_streak
                        self.cache_streak = 0
                        self.gg = True # mark turn started
                        self.playing = self.schedule_game()
                    else:
                        self.add_action("START", None)
                case "TURN END":
                    winner_id_, direction = data
                    if winner_id_ == self.player1.id_:
                        self.player1.reward()
                    else:
                        self.player2.reward()
                    self.ball.center = self.center # pause now won't take twice the same turn end
                    self.playing.cancel() # stop update()
                    self.streak = 0 # reset streak
                    self.gg = False # mark turn end
                    self.reseting_players = Clock.schedule_once(self.reset_players, 1) # reset players after 1 s so player could prepare
                    self.serving = Clock.schedule_once(partial(self.add_action, "SERVE BALL", (direction, 60)), 1) # start next turn after 1 s so player could prepare
                case "PLAY":
                    self.playing = self.schedule_game()
                case "START":
                    self.started = True # mark that game was started
                    self.add_action("SERVE BALL", (choice([-1, 1]), 60))  

                # this action wont be fired for client
                case "SERVE BALL":
                    direction, rotate_range = data
                    self.ball.center = self.center
                    self.ball.velocity = Vector(direction * self.height * Settings.speed, 0).rotate(randint(-rotate_range, rotate_range))
                    self.gg = True # mark turn started
                    self.add_action("PLAY", None)

                # this will be fired only for server and client
                case "UPDATE":
                    for name, value in data.items:
                        print(name, value)
                        match name:
                            case "ball":
                                self.ball.center = value
                            case "player1": # players for client are revered from server's
                                self.player2.center = value
                            case "player2" | "client": # players for client are revered from server's
                                self.player1.center = value
                            case "streak":
                                self.streak = value

    def schedule_game(self):
        return Clock.schedule_interval(self.update, 1.0 / Settings.fps)  # set up a clock to call update()

    def countdown(self, callback, *dt):
        if self.streak == 0: # countdown timeout
            self.counting.cancel()
            self.cc = False # mark countdown as finished
            self.add_action(*callback)
        else:
            self.streak -= 1

    def update(self, *dt):
        if self.opt in ["client", "server", "offline", "solo"]: # if user is a player
            self.player2.move(self.player2, self)

        if self.opt in ["offline", "solo"]: # if opponent is bot or physically with us
            self.player1.move(self.player1, self)

        if self.opt in ["server", "offline", "solo"]: # if game is beeing calculated by that computer
            self.ball.move()

            # bounce off top and bottom
            if self.ball.y < 0 or self.ball.top > self.height:
                self.ball.velocity_y *= -1
            # bounce off the paddles
            p1 = self.player1.bounce_ball(self.ball)
            p2 = self.player2.bounce_ball(self.ball)
            if p1 or p2:
                self.streak += 1

            # went off the side - turn ends
            if self.ball.x < self.x:
                self.turn_end(self.player2, 1)
            elif self.ball.right > self.width:
                self.turn_end(self.player1, -1)
            
        if self.opt == "server": # send updated position of all objects to a client
            for name, value in (
                ("ball", self.ball.center),
                ("player1", self.player1.center),
                ("player2", self.player2.center),
                ("streak", self.streak)
            ):
                self.internet.event_dispatcher("UPDATE", (name, value))

        if self.opt == "client": # self new positon of client's paddle to the server
            self.internet.event_dispatcher("UPDATE", ("client", self.player2.center))                

    def turn_end(self, winner, direction):
        self.add_action("TURN END", (winner.id_, direction))

