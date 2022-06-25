# python >= 3.10

import kivy

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.core.window import Window

from screens import *
from widgets import *


kivy.require("2.1.0")
Builder.load_file("style.kv")
Window.size = (800, 600)

class PongApp(App):

    def build(self): 
        sm = ScreenManager()
        
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(ConnectScreen(name="connect"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(NameScreen(name="name"))
        sm.add_widget(ServerScreen(name="server"))
        sm.add_widget(ClientScreen(name="client"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(PauseScreen(name="pause"))

        return sm


if __name__ == '__main__':
    PongApp().run()