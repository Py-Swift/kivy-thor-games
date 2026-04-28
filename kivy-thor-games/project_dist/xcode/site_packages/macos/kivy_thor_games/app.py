import sys

from kivy.app import App

from kivy.properties import StringProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.widget import Widget

from thorvg_cython.thorvg import Engine
from kivy_thor.thorvg_egl import thorvg_load_egl


from .game_screens.flappy import FlappyScreen
from .game_screens.ballbreaker import BallBreakerScreen
from .game_screens.asteroids import AsteroidsScreen
from .game_screens.tetris import TetrisScreen
from .game_screens.tempest_run import TempestRunScreen




class SMHeader(BoxLayout):

    current = StringProperty("flappy")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 50
        self.add_widget(Button(text="Flappy", on_press=self.show_flappy))
        self.add_widget(Button(text="Breaker", on_press=self.show_breaker))
        self.add_widget(Button(text="Asteroids", on_press=self.show_asteroids))
        self.add_widget(Button(text="Tetris", on_press=self.show_tetris))
        self.add_widget(Button(text="Tempest", on_press=self.show_tempest))
    
    def show_demo(self, *args):
        self.current = "demo"

    def show_radar(self, *args):
        self.current = "radar"

    def show_flappy(self, *args):
        self.current = "flappy"

    def show_breaker(self, *args):
        self.current = "breaker"

    def show_asteroids(self, *args):
        self.current = "asteroids"

    def show_tetris(self, *args):
        self.current = "tetris"

    def show_tempest(self, *args):
        self.current = "tempest"

class DemoSM(ScreenManager):

    def __init__(self, **kwargs):
        print(f"DemoSM init with kwargs: {kwargs}")
        frame_delay = kwargs.pop("frame_delay", 0)
        super().__init__(**kwargs)
        self.add_widget(FlappyScreen(name="flappy", frame_delay=frame_delay))
        self.add_widget(BallBreakerScreen(name="breaker", frame_delay=frame_delay))
        self.add_widget(AsteroidsScreen(name="asteroids", frame_delay=frame_delay))
        self.add_widget(TetrisScreen(name="tetris", frame_delay=frame_delay))
        self.add_widget(TempestRunScreen(name="tempest", frame_delay=frame_delay))


    def on_size(self, _, size):
        print(f"[DemoSM] on_size={size}")
        for screen in self.screens:
            screen.size = size

class DemoScreens(BoxLayout):

    def __init__(self, **kwargs):
        frame_delay = kwargs.pop("frame_delay", 0)
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        screen_manager = DemoSM(frame_delay=frame_delay)
        sm_header = SMHeader()
        sm_header.bind(current=screen_manager.setter("current"))
        
        self.add_widget(screen_manager)

        self.add_widget(sm_header)
        #self.add_widget(Widget())
        
        self.sm_header = sm_header
        self.screen_manager = screen_manager

class ThorApp(App):

    def __init__(self, **kwargs):
        thorvg_load_egl(sys.platform)
        self._engine = Engine(4)
        self._engine.init(4)
        super().__init__(**kwargs)
        

    def build(self):
        frame_delay = 1 / 60.0  # Example frame delay, adjust as needed
        return DemoScreens(frame_delay=frame_delay)

    def on_stop(self):
        self._engine.term()


def main():
    
    app = ThorApp()
    app.run()
    