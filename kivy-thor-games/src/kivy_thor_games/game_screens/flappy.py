import os

import kivy as _kivy
from kivy.clock import Clock
from thorvg_cython import Text

from kivy_thor.thor_screen import ThorScreen
from thor_flappy.game import FlappyScene

Text.font_load(os.path.join(os.path.dirname(_kivy.__file__), 'data', 'fonts', 'Roboto-Regular.ttf'))
Text.font_load(os.path.join(os.path.dirname(_kivy.__file__), 'data', 'fonts', 'Roboto-Bold.ttf'))


class ScreenFlappy(ThorScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scene = FlappyScene(font='Roboto-Regular', font_bold='Roboto-Bold')

        glcanvas = self.thor_fbo.gl_canvas
        glcanvas.add(self._scene)
        glcanvas.add(self._scene.hud)

    def on_enter(self, *args):
        self.clock = Clock.schedule_interval(self._tick, 0)
        return super().on_enter(*args)

    def on_leave(self, *args):
        if hasattr(self, 'clock'):
            self.clock.cancel()
        return super().on_leave(*args)

    def on_size(self, instance, size):
        w, h = int(size[0]), int(size[1])
        if w == 0 or h == 0:
            return
        self.thor_fbo.set_size((w, h))
        self._scene.resize(w, h)

    def on_touch_down(self, touch):
        self._scene.tap()
        return True

    def _tick(self, dt):
        self._scene.tick(dt)
        self.thor_fbo.refresh()
        self.canvas.ask_update()
