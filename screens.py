from kivy.properties import NumericProperty, ObjectProperty, ReferenceListProperty, BooleanProperty, StringProperty, ColorProperty, NumericProperty, ListProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

from random import randint, choice
from functools import partial
from _thread import *

from settings import settings
from widgets import ErrorPopup, AcceptPopup, JoinPopup, Paddle
from bot import Bot
from server import Server
from client import Client
from helpers import EventManager


class MyScreen():
    def __init__(self):
        self.settings = settings # all screens have access to settings, used so .kv can access them
    # convencion: every ing means threaded process / clock interval
    # ticking administrates events

    def add_action(self, name, data, *dt):
        self.actions.append((name, data))


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

            self.manager.transition.duration = settings.transition_duration
            self.manager.transition.direction = "left"
            self.manager.current = self.next_screen
            self.manager.current_screen.initialize(username)
            self.reset()
        else:
            self.username_border_col = "red" # mark that wrong data provided

    def reset(self): 
        self.username_border_col = "white"
        self.username.text = ""


class ServerScreen(Screen, MyScreen):
    dots = NumericProperty(0) # to change number of dots on the end of screen's title 
    time = NumericProperty(settings.waiting_timeout)
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
        self.time = settings.waiting_timeout # shut down the server after specified time if is doesn't start a game

    def initialize(self, server_name):
        self.reset()
        self.ticking = Clock.schedule_interval(self.tick, 1)
        self.server.initialize(server_name, self)
        if not self.server.working: # server encountered an error
            self.manager.current = "connect"
            ErrorPopup("Server error", "Unable to create server, try again later.").open()
            self.reset()

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
                    self.accept.back_up(True)
                    self.manager.transition.duration = settings.transition_duration
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

    def add_server(self, server_name, server_address): # add server name to be displayed on list
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
                    self.manager.transition.duration = settings.transition_duration
                    self.manager.transition.direction = "up"
                    self.manager.current = "game"
                    self.manager.current_screen.set_up("client", data)

    def handler(self, server_name, server_address): # called whan user wants to join a server
        self.client.request_game(server_address) # send request to a server
        self.join = JoinPopup(server_name, self) 
        self.join.open()
        

class SettingsScreen(Screen, MyScreen):
    def validate(self): # check if data provied are in correct format and range
        settings.verbose = self.log.active
        settings.debug = self.debug.active

        try:
            fps = int(self.fps.text)
            fps = min(fps, 600)
        except:
            pass
        else:
            settings.fps = fps
            self.fps.hint_text = str(fps)
        self.fps.text = ""

        fields = [self.latency, self.bot, self.user, self.ball, self.rounds]
        targets = []
        for idx in range(len(fields)):
            try:
                float_ = float(fields[idx].text)
            except:
                targets.append(None)
            else:
                targets.append(float_)

        if targets[0] is not None:
            settings.server_time_refresh = targets[0]
        if targets[1] is not None:
            settings.botMoveSpeed = targets[1]
        if targets[2] is not None:
            settings.moveSpeed = targets[2]
        if targets[3] is not None:
            settings.speed = targets[3]
        if targets[4] is not None:
            targets[4] = int(targets[4])
            settings.rounds_to_win = targets[4]
    
        for idx in range(len(fields)):
            if targets[idx] is not None:
                fields[idx].hint_text = str(targets[idx])
                fields[idx].text = ""


class PauseScreen(Screen, MyScreen):
    def abort(self):
        game = self.manager.get_screen("game")

        if game.internet is not None: # let others know we are leaving
            game.internet.abandon()
        else:
            game.add_action("LEAVE", None)

    def exit_(self):
        game = self.manager.get_screen("game")
        
        if game.internet is not None: # let others know we are leaving
            game.internet.abandon()
        Clock.schedule_once(exit, 0.5) # give the internet time to send info


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

    def reset(self, initial=False):
        settings.inform(f"Resetting the game ({initial}).")
        if initial:
            self.keyboard = Window.request_keyboard(None, self)
            self.ticking = self.counting = self.serving = None
        else:
            for player in self.players: 
                player.score = 0
            for event in [self.ticking, self.counting, self.serving]:
                if event is not None:
                    event.cancel()
            self.keyboard.unbind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.reset_players()
        self.started = self.ended = False
        self.cc = self.gg = False # marks if countdown or turn is active
        self.cache_streak = self.streak = 0
        self.internet = self.target = None # client or server handling connections 
        self.actions = [] # all must be O(1)

    def set_up(self, opt, internet=None):
        self.reset(True)
        settings.inform(f"Setting up a game: {opt}")
        self.opt = opt
        self.internet = internet

        match opt:
            case "solo":
                self.player1.move = Bot.move
                self.player1.name = "Bot"
                self.player2.name = "You"
            case "offline":
                self.player1.move = Paddle.move
                self.player1.name = "Player 1"
                self.player2.name = "Player 2"
            case "server":
                self.player1.move = Paddle.move
                self.internet.screen = self
                self.player1.name = internet.client_name
                self.player2.name = internet.server_name
            case "client":
                self.player1.move = Paddle.move
                self.internet.screen = self
                self.player1.name = internet.server_name
                self.player2.name = internet.client_name

        self.keyboard.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        self.ticking = Clock.schedule_interval(self.tick, 1. / settings.fps) # administrates all game dependencies
        if self.opt in ["server", "offline", "solo"]: # if this computer calculates game events
            self.start()

    def tick(self, *dt):
        permission = self.handle_actions() # permission will be False in case of leaving
        if permission:
            self.handle_game_action() 
            self.send_data()
        
    def start_countdown(self, callback, callback_data, duration):
        if not self.cc: # if it wasn't paused during another countdown
            self.cache_streak = self.streak
        self.cc = True
        self.streak = duration
        self.counting = Clock.schedule_interval(partial(self.countdown, callback, callback_data), 1)

    def countdown(self, callback, callback_data, *dt):
        if self.streak == 0: # countdown timeout
            self.counting.cancel()
            self.streak = self.cache_streak
            self.cc = False # mark countdown as finished
            callback(*callback_data)
        else:
            self.streak -= 1

    def start(self):
        self.ball.center = self.center
        self.start_countdown(self.serve, [choice([-1, 1])], settings.time_to_start)

    def pause(self):
        if self.gg: # if during round
            self.gg = False
        elif self.cc: # if during countdown
            self.cc = False
            self.counting.cancel()
        elif self.serving is not None: # if serving a ball might be scheduled
            self.serving.cancel()

    def unpause(self): 
        if not self.started: # if game haven't started at all, call normal entry
            self.start()
        else:
            self.start_countdown(self.unpause_helper, [], settings.time_to_unpause)

    def unpause_helper(self):
        self.streak = self.cache_streak
        self.gg = True # mark turn started
        print(self.target)
        if self.target is not None and self.target[0] == "serve":
            self.serve(*self.target[1:])
        self.target = None # reset target call
        
    def serve(self, direction, *dt):
        settings.inform(f"Serving a ball (direction -> {direction})")
        self.reset_players()
        self.started = True
        self.gg = True
        self.target = None # serve was done
        self.ball.center = self.center
        self.ball.velocity = Vector(direction * self.height * settings.speed, 0).rotate(randint(-60, 60))

    def turn_end(self, winner, direction):
        settings.inform(f"Turn ended. ({winner.name} has won)")
        self.gg = False # mark turn end
        self.streak = 0 # reset streak
        self.ball.center = self.center # pause now won't take twice the same turn end
        winner.reward()

        if self.player1.score == settings.rounds_to_win:
            self.end_game(self.player1)
            return
        elif self.player2.score == settings.rounds_to_win:
            self.end_game(self.player2)
            return

        self.target = ("serve", direction)  # during turn end mark that we need to call serve again in case of pause right now
        self.serving = Clock.schedule_once(partial(self.serve, direction), 1) # start next turn after 1 s so player could prepare

    def end_game(self, winner):
        if winner == self.player2: # we won
            if self.opt == "server": # send info to client
                self.internet.event_dispatcher("GAME END", [False, self.player2.score, self.player1.score]) # again players reversed
        else: # opponent won
            if self.opt == "server": # send info to client
                self.internet.event_dispatcher("GAME END", [True, self.player2.score, self.player1.score])
        self.end_game_helper(winner == self.player2, self.player1.score, self.player2.score)

    def end_game_helper(self, status, score1, score2, *dt):
        settings.inform(f"Game ended. ({status})")
        self.ended = True
        if status: # status True if we won, False if the opponent won
            ErrorPopup("Game ended", f"You WON against {self.player1.name} with score {score2} : {score1}.").open()
        else:
            ErrorPopup("Game ended", f"You LOST against {self.player1.name} with score {score2} : {score1}.").open()
        Clock.schedule_once(partial(self.add_action, "LEAVE", None), 0.5) # give time to send the final data

    def reset_players(self, *dt): # set all players in starting positions and set their color to white
        for player in self.players:
            player.reset(self)
