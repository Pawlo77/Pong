from widgets import ErrorPopup
from settings import settings
from kivy.core.window import Window

class EventManager: # helper for GameScreen

    def on_key_down(self, keyboard, keycode, text, modifiers):
        if self.gg: # if during round
            val = keycode[1]

            # if this PC plays 
            if val == "up" and self.opt in ["client", "server", "offline", "solo"]:
                self.player2.move_direction = 1
            elif val == "down" and self.opt in ["client", "server", "offline", "solo"]:
                self.player2.move_direction = -1

            # if this PC's keyboard can move second player as well
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

            # if this PC plays 
            if val == "up" and self.opt in ["client", "server", "offline", "solo"]:
                self.player2.move_direction = 0
            elif val == "down" and self.opt in ["client", "server", "offline", "solo"]:
                self.player2.move_direction = 0

            # if this PC's keyboard can move second player as well
            elif val == "w" and self.opt == "offline": 
                self.player1.move_direction = 0
            elif val == "s" and self.opt == "offline":
                self.player1.move_direction = 0

            else:
                return False
            return True
        return False

    def handle_game_action(self):
         if self.gg: # if during round
            if self.opt in ["server", "offline", "solo"]: # if user is a player
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
                    self.ball.velocity_y *= 1.1
                    self.streak += 1

                # went off the side - turn ends
                if self.ball.x < self.x:
                    self.turn_end(self.player2, 1)
                elif self.ball.right > self.width:
                    self.turn_end(self.player1, -1)

    def handle_actions(self):
        while len(self.actions):
            name, data = self.actions.pop(0)

            match name: # for all game options
                case "UPDATE" if data:
                    print(data)
                    if self.opt == "server" and self.gg:
                        (
                            self.player1.move_direction,
                        ) = data
                        self.player1.move(self.player1, self)
                    elif self.opt == "client":
                        (
                            self.gg,
                            self.cc,
                            self.streak,
                            ball_center,
                            player2_y,
                            self.player2.color,
                            self.player2.score,
                            player1_y,
                            self.player1.color,
                            self.player1.score,
                        ) = data 
                        self.player1.y = Window.size[1] * player1_y
                        self.player2.y = Window.size[1] * player2_y
                        ball_center = Window.size * ball_center
                        self.ball.center = [self.right - ball_center[0], ball_center[1]] # lient ball x coordinate is mirrorded from server's one
                        if not self.gg:
                            self.player2.move_direction = 0 # stop moving so on the turn start paddle won't "fly" in unexpected direction by itself
                case "ERROR": # connection to second player lost or he left
                    ErrorPopup(*data).open()
                case "LEAVE":
                    self.manager.current = "menu"
                    self.ticking.cancel() # to avoid next calls
                    if self.internet is not None:
                        self.manager.get_screen(self.internet.type_).reset()
                    self.reset()
                    return False # mark that other game events are redundant
                case "START":
                    self.start()
                case "PAUSE":
                    if self.opt in ["server", "offline", "solo"]: # if this PC calculates the game
                        self.pause()
                        self.add_action("PAUSE_SCREEN", None) # set pause screen 
                        if self.opt == "server": # set pause screen in client
                            self.internet.event_dispatcher("PAUSE_SCREEN", None)
                    elif self.opt == "client":
                        self.internet.event_dispatcher("PAUSE", None) # send request to the server
                case "PAUSE_SCREEN":
                    settings.inform("Game paused.")
                    self.manager.transition.duration = 0
                    self.manager.current = "pause"
                case "UNPAUSE":
                    if self.opt in ["server", "offline", "solo"]: # if this PC calculates the game# if this PC calculates the game
                        self.unpause()
                        self.add_action("UNPAUSE_SCREEN", None) # discard pause screen
                        if self.opt == "server": # discard pause screen in client
                            self.internet.event_dispatcher("UNPAUSE_SCREEN", None)
                    elif self.opt == "client":
                        self.internet.event_dispatcher("UNPAUSE", None) # send request to the server
                case "UNPAUSE_SCREEN":
                    settings.inform("Game unpaused.")
                    self.manager.transition.duration = 0
                    self.manager.current = "game"
                case "GAME END":
                    self.end_game_helper(*data)
        
        return True

    def send_data(self):
        if self.opt == "client":
            self.internet.update_data = (
                self.player2.move_direction,
            )
        elif self.opt == "server":
            self.internet.update_data = (
                self.gg,
                self.cc,
                self.streak,
                self.ball.center / Window.size,
                self.player1.y / Window.size[1],
                self.player1.color,
                self.player1.score,
                self.player2.y / Window.size[1],
                self.player2.color,
                self.player2.score,
            )