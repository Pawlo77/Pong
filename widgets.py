from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ColorProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.vector import Vector
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock

from settings import Settings


class HoverableButton(Button):
    hovered = BooleanProperty(False)
    border_point= ObjectProperty(None)

    def __init__(self, **kwargs):
        super(HoverableButton, self).__init__(**kwargs)
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return # do proceed if I'm not displayed <=> If have no parent
        pos = args[1]
        #Next line to_widget allow to compensate for relative layout
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            #We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        self.color = "red"

    def on_leave(self):
        self.color = "white"


class TickingPopup(Popup):
    exit_text = StringProperty("Back")
    title = StringProperty("Ticking Popup")
    time = NumericProperty(10)

    def alive(self, *dt):
        self.time -= 1
        if self.time <= 0:
            self.back_up()
            return

    def back_up(self):
        self.countdown.cancel()
        self.dismiss()

    def open(self, **kwargs):
        super(TickingPopup, self).open(**kwargs)
        self.countdown = Clock.schedule_interval(self.alive, 1)


class AcceptPopup(TickingPopup):
    client_name = StringProperty("")
    main_text = StringProperty("")
    minor_text = StringProperty("")
    btn_text = StringProperty("")

    def __init__(self, client_name, client_port, conn, root, **kwargs):
        super(AcceptPopup, self).__init__(**kwargs)
        self.client_name = client_name
        self.client_port = client_port
        self.conn = conn
        self.root = root
        self.title = "Accept a game"
        self.time = Settings.accept_timeout
        self.waiting = False
        self.main_text = f"Are sure you want to play against {client_name} ?"
        self.minor_text = f"Decide in {self.time} seconds..."
        self.btn_text = "Play"

    def alive(self, *dt):
        super(AcceptPopup, self).alive(*dt)
        if self.waiting and self.root.server.playing:
            print("DADADADA")
            self.root.ticking.cancel()
            self.root.manager.current = "game"
            super().back_up()
        elif self.waiting:
            self.minor_text = f"Timeout in {self.time} seconds..."
            self.btn_text = "".join(["." for _ in range(self.time % 4)])
        else:
            self.minor_text = f"Decide in {self.time} seconds..."

        if self.root.server.get_client(self.client_port) is None:
            self.back_up()
            ErrorPopup("Server error", f"Connection to {self.client_name} lost.").open()
            return
        
        f = False
        for data in self.root.clients_list:
            if data["port"] == self.client_port:
                f = True
                break
        if not f:
            ErrorPopup("Player resigned", f"{self.client_name} no longer in your lobby.").open()
            self.back_up()
            return

    def back_up(self):
        if self.waiting:
            ErrorPopup("Server error", f"Unable to connect to {self.client_name}.").open()
        super().back_up()

    def accept(self):
        self.root.server.accept(self.conn, self.client_port)
        self.root.time = max(6, self.root.time) # make sure it won't quit during waitng
        self.time = 10 # 5 seconds to establish connection
        self.main_text = f"Waiting for a connection with {self.client_name}"
        self.minor_text = f"Timeout in {self.time} seconds..."
        self.btn_text = ""


class JoinPopup(TickingPopup):
    def __init__(self, server_name, root, **kwargs):
        super(JoinPopup, self).__init__(**kwargs)
        self.root = root
        self.exit_text = "Abandon"
        self.title = f"Joining a game of {server_name}..."
        self.time = Settings.joining_timeout

    def back_up(self):
        super().back_up()
        self.root.client.abandon = True
        self.root.ticking = Clock.schedule_interval(self.root.tick, 1)

    def alive(self, *dt):
        super().alive(*dt)
        if not self.root.client.waiting:
            if not self.root.client.playing:
                self.abort()
                ErrorPopup("Server error", "Server lost.").open()
            else:
                self.abort(True)
            return

    def abort(self, positive=False):
        super().back_up()
        if not positive:
            self.root.ticking = Clock.schedule_interval(self.root.tick, 1)


class ErrorPopup(Popup):
    error = StringProperty("")

    def __init__(self, title, error, **kwargs):
        super(ErrorPopup, self).__init__(**kwargs)
        self.title = title
        self.error = error


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

