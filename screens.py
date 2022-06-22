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
        if len(self.username.text.strip()) > 0:
            self.manager.transition.duration = Settings.transition_duration
            self.manager.transition.direction = "left"
            self.manager.current = self.next_screen
            self.manager.current_screen.initialize(self.username.text.strip())
            self.reset()
        else:
            self.username_border_col = "red"

    def reset(self): 
        self.username_border_col = "white"
        self.username.text = ""


class ServerScreen(Screen, MyScreen):
    dots = NumericProperty(0)
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
        self.time = Settings.waiting_timeout

    def initialize(self, server_name):
        self.reset()
        self.ticking = Clock.schedule_interval(self.tick, 1)
        self.server.initialize(server_name, self)
        if not self.server.listening:
            self.manager.current = "connect"
            ErrorPopup("Server error", "Unable to create server, try again later.").open()
            self.reset()

    def add_action(self, name, data):
        self.actions.append((name, data))

    def remove_client(self, port):
        for idx, entry in enumerate(self.clients_list):
            if entry["port"] == port:
                self.clients_list.pop(idx)
                return

    def add_client(self, client_name, port):
        self.clients_list.append({
            "text": client_name, "port": port, "root": self
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
            if name == "REMOVE":
                self.remove_client(data)
            elif name == "ADD":
                self.add_client(*data)
            elif name == "ERROR":
                if self.accept is not None:
                    self.accept.back_up()
                ErrorPopup(*data).open()
            elif name == "START":
                self.ticking.cancel() # we can't reset here, server will be lost
                self.accept.back_up()
                self.manager.transition.duration = Settings.transition_duration
                self.manager.transition.direction = "up"
                self.manager.current = "game"
                self.manager.current_screen.set_up("server", data)

    def handler(self, client_name, client_port):
        self.accept = AcceptPopup(client_name, client_port, self)
        self.accept.open()


class ClientScreen(Screen, MyScreen):
    servers_list = ListProperty([])
    dots = NumericProperty(0)

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

    def add_server(self, server_name, port):
        self.servers_list.append({
            "text": server_name, "port": port, "root": self
        })

    def remove_server(self, port):
        for idx, entry in enumerate(self.servers_list):
            if entry["port"] == port:
                self.servers_list.pop(idx)
                return

    def tick(self, *dt):
        self.dots = (self.dots + 1) % 4

        while len(self.actions):
            name, data = self.actions.pop(0)
            if name == "REMOVE":
                self.remove_server(data)
            elif name == "ADD":
                self.add_server(*data)
            elif name == "STOP WAITING":
                self.join.back_up(False)
                ErrorPopup(*data).open()
            elif name == "ERROR":
                ErrorPopup(*data).open()
            elif name == "START":
                self.ticking.cancel() # we can't reset here, client will be lost
                self.join.back_up()
                self.manager.transition.duration = Settings.transition_duration
                self.manager.transition.direction = "up"
                self.manager.current = "game"
                self.manager.current_screen.set_up("client", data)

    def handler(self, server_name, server_port):
        self.client.request_game(server_port)
        self.join = JoinPopup(server_name, self)
        self.join.open()
        

class StatsScreen(Screen, MyScreen):
    pass


class PauseScreen(Screen, MyScreen):
    
    def unpause(self):
        self.manager.transition.duration = 0
        self.manager.current = "game"
        
        game = self.manager.current_screen
        game.add_action("COUNTDOWN", ((game.add_action, "UNPAUSE", None), 3))


class GameScreen(Screen, MyScreen):
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
            if self.internet is not None:
                self.internet.reset()
            self.reset_players()
            self.keyboard.unbind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.started = False
        self.cc = self.gg = False
        self.cache_streak = 0
        self.actions = [] # all must be O(1)

    def reset_players(self, *dt):
        for player in self.players:
            player.reset(self)

    def set_up(self, opt, internet=None):
        self.opt = opt
        self.internet = internet
        Settings.inform(f"Setting up a game: {opt}")

        if opt == "solo":
            self.player1.move = Bot.move
            self.player2.move = Paddle.move
            self.player1.name = "Bot"
            self.player2.name = "You"
        elif opt == "offline":
            self.player1.move = Paddle.move
            self.player2.move = Paddle.move
            self.player1.name = "Player 1"
            self.player2.name = "Player 2"
        elif opt == "server":
            self.internet.screen = self

        elif opt == "client":
            self.internet.screen = self

        self.keyboard.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        self.add_action("COUNTDOWN", ((self.add_action, "START", None), 5))
        self.ticking = Clock.schedule_interval(self.tick, 0.1)

    def add_action(self, name, data, *dt):
        self.actions.append((name, data))

    def tick(self, *dt):
        while len(self.actions):
            name, data = self.actions.pop(0)
            if name == "START":
                self.started = True
                self.ball.center = self.center
                self.add_action("SERVE BALL", (choice([-1, 1]), 60))
            elif name == "SERVE BALL":
                direction, rotate_range = data
                self.ball.velocity = Vector(direction * self.height * Settings.speed, 0).rotate(randint(-rotate_range, rotate_range))
                self.gg = True # mark turn started
                self.playing = self.schedule_game()
            elif name == "COUNTDOWN":
                target, self.streak = data
                self.cc = True # mark countdown started
                self.counting = Clock.schedule_interval(partial(self.countdown, target), 1)
            elif name == "PAUSE":
                if self.gg: # if during round
                    self.gg = False
                    self.playing.cancel()
                    self.cache_streak = self.streak # save current streak, it will be overwrite by countdown
                elif self.cc: # if during countdown
                    self.cc = False
                    self.counting.cancel()
                elif self.serving is not None:
                    self.serving.cancel()
            elif name == "UNPAUSE":
                if self.started: # if game was already started 
                    self.streak = self.cache_streak
                    self.cache_streak = 0
                    self.gg = True # mark turn started
                    self.playing = self.schedule_game()
                else:
                    self.add_action("START", None)

    def schedule_game(self):
        return Clock.schedule_interval(self.update, 1.0 / Settings.fps)

    def countdown(self, callback, *dt):
        if self.streak == 0:
            self.counting.cancel()
            self.cc = False
            if isinstance(callback, tuple):
                callback, data = callback[0], callback[1:]
                callback(*data)
            else:
                callback()
        else:
            self.streak -= 1

    def on_key_down(self, keyboard, keycode, text, modifiers):
        if self.gg: # if during round
            val = keycode[1]

            if val == "up":
                self.player2.move_direction = 1
            elif val == "down":
                self.player2.move_direction = -1

            elif val == "w" and self.opt == "offline":
                self.player1.move_direction = 1
            elif val == "s" and self.opt == "offline":
                self.player1.move_direction = -1

            else:
                return False
            return True
        return False

    def on_key_up(self, keyboard, keycode):
        if self.gg: # if during round
            val = keycode[1]

            if val == "up":
                self.player2.move_direction = 0
            elif val == "down":
                self.player2.move_direction = 0

            elif val == "w" and self.opt == "offline":
                self.player1.move_direction = 0
            elif val == "s" and self.opt == "offline":
                self.player1.move_direction = 0

            else:
                return False
            return True
        return False

    def update(self, *dt):
        self.ball.move()
        self.player1.move(self.player1, self)
        self.player2.move(self.player2, self)

        # bounce off top and bottom
        if self.ball.y < 0 or self.ball.top > self.height:
            self.ball.velocity_y *= -1
        
        # bounce of paddles
        p1 = self.player1.bounce_ball(self.ball)
        p2 = self.player2.bounce_ball(self.ball)
        if p1 or p2:
            self.streak += 1

        # went off the side?
        if self.ball.x < self.x:
            self.turn_end(self.player2, 1)

        elif self.ball.right > self.width:
            self.turn_end(self.player1, -1)

    def turn_end(self, winner, direction):
        self.playing.cancel()
        self.gg = False # mark turn end
        winner.reward()
        self.streak = 0
        self.ball.center = self.center # so the update in case of pause now won't take twice the same turn end

        self.reseting_players = Clock.schedule_once(self.reset_players, 1)
        self.serving = Clock.schedule_once(partial(self.add_action, "SERVE BALL", (direction, 60)), 1)

