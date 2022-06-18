from kivy.properties import NumericProperty, ObjectProperty, ReferenceListProperty, BooleanProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

from random import randint, choice
from functools import partial

from settings import Settings
from widgets import Paddle
from bot import Bot

class MyScreen():
    def __init__(self):
        self.settings = Settings()


class MenuScreen(Screen, MyScreen):
    pass


class ConnectScreen(Screen, MyScreen):
    pass


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

    def on_key_up(self, keyboard, keycode):
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
