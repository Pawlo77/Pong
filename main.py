import kivy

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder

from screens import *
from widgets import *

kivy.require("2.1.0")
Builder.load_file("style.kv")

class PongApp(App):

    def build(self): 
        sm = ScreenManager()
        
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(ConnectScreen(name="connect"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(StatsScreen(name="stats"))
        sm.add_widget(PauseScreen(name="pause"))

        return sm


if __name__ == '__main__':
    PongApp().run()