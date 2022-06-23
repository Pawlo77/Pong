class EventManager: # suitable only with game Screen

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
