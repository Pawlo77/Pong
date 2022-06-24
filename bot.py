from widgets import Paddle
from settings import settings


class Bot(Paddle):
    @staticmethod
    def move(me, root):
        _, dy = root.ball.velocity

        if dy > 0 and root.ball.center_y > me.center_y: # move up if ball's center is above our center
            new = me.top + settings.botMoveSpeed * root.height
            me.top = min(new, root.top)
        elif dy < 0 and root.ball.center_y < me.center_y: # move down if ball's center is above our center
            new = me.y - settings.botMoveSpeed * root.height
            me.y = max(new, root.y)