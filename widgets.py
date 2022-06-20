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
    name = StringProperty("")
    def __init__(self, root, name, port, interval, **kwargs):
        super(TickingPopup, self).__init__(**kwargs)
        self.name = name
        self.port = port
        self.root = root
        self.interval = interval
        self.countdown = Clock.schedule_interval(self.alive, 1)

    def alive(self, *dt):
        self.time -= 1

        if self.time <= 0:
            self.back_up()
        
    def back_up(self):
        self.countdown.cancel()
        self.dismiss()
        self.root.during_ticking = Clock.schedule_interval(self.root.tick, self.interval)
        

class AcceptPopup(TickingPopup):
    title = "Accept player"
    time = NumericProperty(Settings.accept_timeout)


class JoinPopup(TickingPopup):
    title = "Joining a server"
    time = NumericProperty(Settings.joining_timeout)


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

