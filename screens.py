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


class RoomScreen(Screen, MyScreen):
    dots = NumericProperty(0)
    time = NumericProperty(Settings.waiting_timeout)
    clients_list = ListProperty([])

    def __init__(self, **kwargs):
        super(RoomScreen, self).__init__(**kwargs)
        self.during_counting = None
        self.during_ticking = None
        self.server = Server()

    def initialize(self, server_name):
        self.during_counting = Clock.schedule_interval(self.dot_count, 1)
        self.during_ticking = Clock.schedule_interval(self.tick, 1)

        self.server.create(server_name)
        if not self.server.listening:
            self.manager.current = "connect"
            ErrorPopup("Server error", "Unable to create server, try again later.").open()
            self.reset()

    def dot_count(self, *dt):
        self.dots = (self.dots + 1) % 4

    def tick(self, *dt):
        self.time -= 1

        if self.time % Settings.server_frequency == 0:
            self.clients_list = []
            for port, data in self.server.queue.items():
                self.clients_list.append({
                    "text": data[1], "port": port, "root": self
                })
            self.clients_list.sort(key=lambda x: x["text"])

        if self.time <= 0:
            self.manager.current = "connect"
            ErrorPopup("Server closed", "Your server was closed bacause you exceeded connection time.").open()
            self.reset()

    def reset(self):
        if self.during_counting is not None: 
            self.during_counting.cancel()
        if self.during_ticking is not None:
            self.during_ticking.cancel()
        self.dots = 0
        self.clients_list = []
        self.time = Settings.waiting_timeout
        self.server.reset()

    def handler(self, client_name, client_port):
        if self.during_ticking is not None:
            self.during_ticking.cancel()
        AcceptPopup(self, client_name, client_port, 1).open()


class RoomsScreen(Screen, MyScreen):
    servers_list = ListProperty([])
    dots = NumericProperty(0)

    def __init__(self, **kwargs):
        super(RoomsScreen, self).__init__(**kwargs)
        self.during_counting = None
        self.during_scaning = None
        self.during_waiting = None
        self.waiting = None
        self.client = Client()

    def initialize(self, client_name):
        self.client.create(client_name)
        self.during_ticking = Clock.schedule_interval(self.tick, Settings.client_frequency)
        self.during_counting = Clock.schedule_interval(self.dot_count, 1)

    def dot_count(self, *dt):
        self.dots = (self.dots + 1) % 4

    def tick(self, *dt):
        self.servers_list = []
        for port, server_name in self.client.rooms.items():
            self.servers_list.append({
                "text": server_name, "port": port, "root": self
                })
        self.servers_list.sort(key=lambda x: x["text"])

    def reset(self):
        if self.during_ticking is not None:
            self.during_ticking.cancel()
        if self.during_counting is not None:
            self.during_counting.cancel()
        self.dots = 0
        self.servers_list = []
        self.client.reset()

    def handler(self, server_name, server_port):
        if self.client.request_game(server_port, self):
            if self.during_ticking is not None:
                self.during_ticking.cancel()
            self.during_waiting = JoinPopup(self, server_name, server_port, Settings.client_frequency).open()
        else:
            ErrorPopup("Server error", "Unable to connect to a server.").open()
        

class StatsScreen(Screen, MyScreen):
    pass


class PauseScreen(Screen, MyScreen):
    pass


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

        self.keyboard = Window.request_keyboard(None, self)
        if self.keyboard:
            self.keyboard.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.cache_streak = 0
        self.during_game = None
        self.during_countdown = None
        self.reseting_players = None
        self.serving = None
        self.events = [self.during_game, self.during_countdown, self.reseting_players, self.serving]
    
    def set_up(self, opt):
        self.opt = opt
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
        else:
            pass
            # self.player1_name.text = self.player1.name[:10] + "..." if len(self.player1.name) > 10 else self.player1.name

        self.start_countdown(self.start)
            
    def start(self):
        self.started = True
        direction = choice([-1, 1])
        self.serve_ball(direction)
        
    def schedule_game(self):
        return Clock.schedule_interval(self.update, 1.0 / Settings.fps)

    def start_countdown(self, target, duration=3):  
        self.streak = duration
        self.cc = True
        self.during_countdown = Clock.schedule_interval(partial(self.countdown, target), 1)

    def countdown(self, callback, *dt):
        if self.streak == 0:
            self.during_countdown.cancel()
            self.cc = False
            callback()
        else:
            self.streak -= 1

    def pause(self):
        if self.gg:
            self.gg = False
            self.during_game.cancel()
        if self.cc:
            self.cc = False
            self.during_countdown.cancel()
        self.cache_streak = self.streak

    def unpause(self):
        if self.started:
            self.streak = self.cache_streak
            self.gg = True
            self.during_game = self.schedule_game()
        else:
            self.start()

    def serve_ball(self, direction, rotate=60, *dt):  
        self.ball.center = self.center
        self.ball.velocity = Vector(direction * self.height * Settings.speed, 0).rotate(randint(-rotate, rotate))
        self.during_game = self.schedule_game()
        self.gg = True

    def on_key_down(self, keyboard, keycode, text, modifiers):
        if self.gg:
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
        if self.gg:
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
        self.during_game.cancel()
        self.gg = False
        winner.reward()
        self.streak = 0

        self.reseting_players = Clock.schedule_once(self.reset_players, 1)
        self.serving = Clock.schedule_once(partial(self.serve_ball, direction, 60), 1)

    def reset(self):
        for player in self.players: 
            player.score = 0
        self.reset_players()

        self.cc = self.gg = False
        for event in self.events:
            if event is not None:
                event.cancel()

    def reset_players(self, *dt):
        for player in self.players:
            player.reset(self)
