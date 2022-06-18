from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ColorProperty, StringProperty
from kivy.vector import Vector
from kivy.graphics import Rectangle, Color

from functools import partial

from settings import Settings


class Paddle(Widget): 
    score = NumericProperty(0)
    color = ColorProperty("white")
    move_direction = NumericProperty(0)
    name = StringProperty("")

    def __init__(self, **kwargs):
        super(Paddle, self).__init__(**kwargs)

        # self.size_hint = (None, None)
        with self.canvas:
            Color(255, 255, 255, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos = self.update_rect, size = self.update_rect)

    def bind_update(self, root):
        data = partial(root.update_player, self)
        self.bind(color = data, score = data)

    def update_rect(self, *dt):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            velocity_x, velocity_y = ball.velocity

            bounced = Settings.speedup * Vector(-1 * velocity_x, velocity_y)
            ball.velocity = bounced.x, bounced.y

            return True
        return False

    def move(self, root):
        if self.move_direction == 1:
            new = self.top + Settings.moveSpeed * root.height
            self.top = min(new, root.top)
        elif self.move_direction == -1:
            new = self.y - Settings.moveSpeed * root.height
            self.y = max(new, root.y)

    def reward(self):
        self.color = "green"
        self.size[1] *= Settings.paddleShrink
        self.score += 1

    def reset(self, root, *dt):
        self.color = "white"
        self.center_y = root.center_y


class Ball(Widget):
    velocity_x = NumericProperty(0)     
    velocity_y = NumericProperty(0)    
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def resize(self, _, newSize):
        r = newSize[1] / 20
        self.size = (r, r)    

    def move(self): 
        self.pos = Vector(*self.velocity) + self.pos

