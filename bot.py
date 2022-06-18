from widgets import Paddle
from settings import Settings


class Bot(Paddle):
    def move(self, root):
        _, dy = root.ball.velocity

        if dy > 0 and root.ball.center_y > self.center_y:
            # print("Up")
            new = self.top + Settings.botMoveSpeed * root.height
            self.top = min(new, root.top)
        elif dy < 0 and root.ball.center_y < self.center_y:
            # print("Down")
            new = self.y - Settings.botMoveSpeed * root.height
            self.y = max(new, root.y)

    # def decide(self, ball, player):
        # dx, dy = ball.velocity

        # # if ball goes up and it's higher than bot center point
        # if dy > 0 and ball.center_y > player.center_y:
        #     print("go up")
        #     player.move_direction = 1
        # # if ball goes fown and it's lower than bot center point
        # elif dy < 0 and ball.center_y < player.center_y:
        #     print("go down")
        #     player.move_direction = -1
        # else:
        #     player.direction = 0