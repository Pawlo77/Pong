from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, ListProperty
from kivy.vector import Vector
from kivy.core.window import Window

from random import randint

from settings import Settings


class Pong(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    streak = NumericProperty(0)
    settings = Settings()

    def __init__(self, **kwargs):
        super(Pong, self).__init__(**kwargs)

        self.keyboard = Window.request_keyboard(None, self)
        if self.keyboard:
            self.keyboard.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        self.players = [self.player1, self.player2]

    def on_key_down(self, keyboard, keycode, text, modifiers):
        val = keycode[1]

        if val == "up":
            self.player2.move_direction = 1
        elif val == "down":
            self.player2.move_direction = -1

        elif val == "w":
            self.player1.move_direction = 1
        elif val == "s":
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

        elif val == "w":
            self.player1.move_direction = 0
        elif val == "s":
            self.player1.move_direction = 0

        else:
            return False
        return True
    
    def serve_ball(self, direction, rotate=60):    
        self.ball.center = self.center
        self.ball.velocity = Vector(direction * Settings.speed, 0).rotate(randint(-rotate, rotate))

    def update(self, dt):
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
        winner.reward()
        self.streak = 0
        self.serve_ball(direction)

        for player in self.players:
            player.reset(self)


class Paddle(Widget): 
    score = NumericProperty(0)
    move_direction = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Paddle, self).__init__(**kwargs)
        self.size = (25, Settings.startPaddleSize)
    
    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            velocity_x, velocity_y = ball.velocity

            bounced = Settings.speedup * Vector(-1 * velocity_x, velocity_y)
            ball.velocity = bounced.x, bounced.y

            return True
        return False

    def move(self, root):
        if self.move_direction == 1:
            new = self.top + Settings.moveSpeed
            self.top = min(new, root.top)
        elif self.move_direction == -1:
            new = self.y - Settings.moveSpeed
            self.y = max(new, root.y)

    def reward(self):
        self.score += 1
        self.size[1] *= Settings.paddleShrink

    def reset(self, root):
        self.center_y = root.center_y
    

class Ball(Widget):
    velocity_x = NumericProperty(0)     
    velocity_y = NumericProperty(0)    
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def move(self): 
        self.pos = Vector(*self.velocity) + self.pos

