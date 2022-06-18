from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ColorProperty, StringProperty, BooleanProperty
from kivy.vector import Vector

from settings import Settings


class Paddle(Widget): 
    score = NumericProperty(0)
    color = ColorProperty("white")
    move_direction = NumericProperty(0)
    name = StringProperty("")
    bot = BooleanProperty(False)
    
    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            velocity_x, velocity_y = ball.velocity

            bounced = Settings.speedup * Vector(-1 * velocity_x, velocity_y)
            ball.velocity = bounced.x, bounced.y

            return True
        return False

    def reward(self):
        self.color = "green"
        self.size[1] *= Settings.paddleShrink
        self.score += 1

    def reset(self, root, *dt):
        self.color = "white"
        self.center_y = root.center_y

    @staticmethod
    def move(me, root):
        if me.move_direction == 1:
            new = me.top + Settings.moveSpeed * root.height
            me.top = min(new, root.top)
        elif me.move_direction == -1:
            new = me.y - Settings.moveSpeed * root.height
            me.y = max(new, root.y)

class Ball(Widget):
    velocity_x = NumericProperty(0)     
    velocity_y = NumericProperty(0)    
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def resize(self, _, newSize):
        r = newSize[1] / 20
        self.size = (r, r)    

    def move(self): 
        self.pos = Vector(*self.velocity) + self.pos

