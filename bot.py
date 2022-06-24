from widgets import Paddle
from settings import Settings
from kivy.vector import Vector


class Bot(Paddle):
    @staticmethod
    def move(me, root):
        _, dy = root.ball.velocity

        if dy > 0 and root.ball.center_y > me.center_y:
            new = me.top + Settings.moveSpeed * root.height
            me.top = min(new, root.top)
        elif dy < 0 and root.ball.center_y < me.center_y:
            new = me.y - Settings.moveSpeed * root.height
            me.y = max(new, root.y)