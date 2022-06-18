from widgets import Paddle
from settings import Settings


class Bot(Paddle):
    @staticmethod
    def move(me, root):
        _, dy = root.ball.velocity


        if dy > 0 and root.ball.center_y > me.center_y:
            new = me.top + Settings.botMoveSpeed * root.height
            me.top = min(new, root.top)
        elif dy < 0 and root.ball.center_y < me.center_y:
            new = me.y - Settings.botMoveSpeed * root.height
            me.y = max(new, root.y)
