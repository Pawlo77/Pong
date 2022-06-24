from widgets import ErrorPopup
from settings import Settings


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
                case "ERROR": # connection to second player lost or he left
                    ErrorPopup(*data).open()
                case "LEAVE":
                    self.manager.current = "menu"
                    self.ticking.cancel() # to avoid next calls
                    if self.internet is not None:
                        self.manager.get_screen(self.internet.type_).reset()
                    self.reset()
                    return False
                case "START":
                    self.start()
                case "PAUSE":
                    if self.opt in ["server", "offline", "solo"]:
                        self.pause()
                        self.add_action("PAUSE_SCREEN", None)
                        if self.opt == "server": # set pause screen in client
                            self.internet.event_dispatcher("PAUSE_SCREEN", None)
                    elif self.opt == "client":
                        self.internet.event_dispatcher("PAUSE", None) # send request to the server
                case "PAUSE_SCREEN":
                    Settings.inform("Game paused.")
                    self.manager.transition.duration = 0
                    self.manager.current = "pause"
                case "UNPAUSE":
                    if self.opt in ["server", "offline", "solo"]:
                        self.unpause()
                        self.add_action("UNPAUSE_SCREEN", None)
                        if self.opt == "server": # set pause screen in client
                            self.internet.event_dispatcher("UNPAUSE_SCREEN", None)
                    elif self.opt == "client":
                        self.internet.event_dispatcher("UNPAUSE", None) # send request to the server
                case "UNPAUSE_SCREEN":
                    Settings.inform("Game unpaused.")
                    self.manager.transition.duration = 0
                    self.manager.current = "game"
                case "UPDATE":
                    # for name, val in data:
                    #     match name:
                    #         case "ball":
                    #             self.ball.center_y = val[1]
                    #             self.ball.center_x = self.right - val[0] # mirror refrection
                    #             # self.ball.center = val
                    #         case "player1":
                    #             self.player2.update(val)
                    #             if not self.gg:
                    #                 self.player2.move_direction = 0
                    #         case "player2":
                    #             self.player1.update(val)
                    #         case "client" if self.gg:
                    #             self.player1.update(val) # if turn end don't change
                    #             self.player1.move(self.player1, self) # move it
                    #         case "streak":
                    #             self.streak = val
                    #         case "cc":
                    #             self.cc = val
                    #         case "gg":
                    #             self.gg = val
                    print(data)
                    if self.opt == "server":
                        (
                            self.player1.move_direction,
                        ) = data
                    elif self.opt == "client":
                        (
                            self.gg,
                            self.cc,
                            self.streak,
                            self.ball.center,
                            self.player2.y,
                            self.player2.color,
                            self.player2.size, 
                            self.player2.score,
                            self.player1.y,
                            self.player1.color,
                            self.player1.size, 
                            self.player1.score,
                        ) = data 

        return True

    def send_data(self):
        if self.opt == "client":
            # self.internet.update_data = (
            #     ("client", {"move_direction": self.player2.move_direction}),
            # )
            self.internet.update_data = (
                self.player2.move_direction,
            )

        elif self.opt == "server":
            # self.internet.update_data = (
            #     ("gg", self.gg),
            #     ("cc", self.cc),
            #     ("streak", self.streak),
            #     ("ball", self.ball.center),
            #     ("player1", {"y": self.player1.y, "color": self.player1.color, "size": self.player1.size, "score": self.player1.score}),
            #     ("player2", {"y": self.player2.y, "color": self.player2.color, "size": self.player2.size, "score": self.player2.score}),
            # )
            self.internet.update_data = (
                self.gg,
                self.cc,
                self.streak,
                self.ball.center,
                self.player1.y,
                self.player1.color,
                self.player1.size, 
                self.player1.score,
                self.player2.y,
                self.player2.color,
                self.player2.size, 
                self.player2.score,
            )