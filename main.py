import kivy
kivy.require("2.1.0")

from kivy.app import App
from kivy.clock import Clock

from random import choice

from widgets import Pong
from settings import Settings


class PongApp(App):

    def build(self): 
        game = Pong()

        direction = choice([-1, 1])
        game.serve_ball(direction)

        Clock.schedule_interval(game.update, 1. / Settings.fps)
        return game


if __name__ == '__main__':
    PongApp().run()