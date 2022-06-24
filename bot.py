from widgets import Paddle
from settings import Settings
from kivy.vector import Vector


class Bot(Paddle):
    @staticmethod
    def move(me, root):
        _, dy = root.ball.velocity

        moved = 0
        if dy > 0 and root.ball.center_y > me.center_y:
            new = me.top + Settings.moveSpeed * root.height
            new = min(new, root.top)
            moved = new - me.top
        elif dy < 0 and root.ball.center_y < me.center_y:
            new = me.y - Settings.moveSpeed * root.height
            new = max(new, root.y)
            moved = new - me.y
        return moved + me.y
