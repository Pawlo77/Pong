from kivy.properties import NumericProperty, ObjectProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

from random import randint, choice
from functools import partial

from settings import Settings
from widgets import Ball, Paddle
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
    # player1 = ObjectProperty(None)
    # name_1 = ObjectProperty(None)
    # score_1 = ObjectProperty(None)
    # player2 = ObjectProperty(None)
    # name_2 = ObjectProperty(None)
    # score_2 = ObjectProperty(None)
    # players = ReferenceListProperty(player1, player2)
    streak = NumericProperty(0)

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

        self.keyboard = Window.request_keyboard(None, self)
        if self.keyboard:
            self.keyboard.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        self.on_enter = self.set_up

        self.game = False
        self.started = False
        self.cache_streak = 0
        self.events = {}
    
    def set_up(self):
        # self.player2 = Paddle(root=self, center_y=self.center_y, right=1650, size_hint=(.02, .33))

        paddle_kw = {"center_y": self.center_y, "x": 0, "size_hint": (.02, .33)}
        if self.opt == "solo":
            self.player1 = Bot(**paddle_kw)
            self.name_1.text = self.player1.name = "Bot"
            self.name_2.text = self.player2.name = "You"
        elif self.opt == "offline":
            self.player1 = Paddle(**paddle_kw)
            self.name_1.text = self.player1.name = "Player 1"
            self.name_2.text = self.player2.name = "Player 2"
        else:
            pass
            # self.player1_name.text = self.player1.name[:10] + "..." if len(self.player1.name) > 10 else self.player1.name

        self.player1.bind_update(self)
        self.players = [self.player1, self.player2]
        self.add_widget(self.player1)
        self.update_player(self.player1)
        self.start_countdown(self.start)

    def update_player(self, player, *dt):
        if player == self.player1: 
            self.name_1.color = self.score_1.color = self.player1.color
            self.score_1.text = str(self.player1.score)
        elif player == self.player2:
            self.name_2.color = self.score_2.color = self.player2.color
            self.score_2.text = str(self.player2.score)
            
    def start(self):
        self.started = True
        self.ball = Ball( size=(self.height / 20, self.height / 20))
        self.bind(size = self.ball.resize)
        self.add_widget(self.ball)

        direction = choice([-1, 1])
        self.serve_ball(direction)
        self.events["main_clock"] = Clock.schedule_interval(self.update, 1.0 / Settings.fps)

    def start_countdown(self, target, duration=3):  
        self.streak = duration
        self.events["countdown"] = Clock.schedule_interval(partial(self.countdown, target), 1)

    def countdown(self, callback, *dt):
        print(self.size, self.width, self.height)
        if self.streak == 0:
            self.events["countdown"].cancel()
            del self.events["countdown"]
            callback()
        else:
            self.streak -= 1

    def pause(self):
        self.game = False
        if "countdown" in self.events:
            self.events["countdown"].cancel()
            del self.events["countdown"]
        self.cache_streak = self.streak

    def unpause(self):
        if self.started:
            self.streak = self.cache_streak
            self.game = True
        else:
            self.streak = 0
            self.start()

    def serve_ball(self, direction, rotate=60, *dt):  
        self.ball.center = self.center
        self.ball.velocity = Vector(direction * self.height * Settings.speed, 0).rotate(randint(-rotate, rotate))
        self.game = True

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
        if self.game:
            self.ball.move()
            self.player1.move(self)
            self.player2.move(self)

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
        self.game = False
        winner.reward()
        self.streak = 0

        self.events["reset_players"] = Clock.schedule_once(self.reset_players, 1)
        self.events["serve"] = Clock.schedule_once(partial(self.serve_ball, direction, 60), 1)

    def reset(self):
        for player in self.players: 
            player.score = 0
        self.reset_players()

        for event in self.events.values():
            event.cancel()
        for player in self.players:
            self.remove_widget(player)
        self.events = {}
        if self.ball is not None:
            self.unbind(size = self.ball.resize)
            self.remove_widget(self.ball)

    def reset_players(self, *dt):
        for player in self.players:
            player.reset(self)
