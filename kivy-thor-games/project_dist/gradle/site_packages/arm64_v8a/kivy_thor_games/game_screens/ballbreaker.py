from kivy.clock import Clock
from kivy.core.window import Window

from kivy_thor.thor_screen import ThorScreen
from thor_ballbreaker import BallBreakerGame


class BallBreakerScreen(ThorScreen):

    def __init__(self, **kwargs):
        self.frame_delay = kwargs.pop("frame_delay", 0)
        super().__init__(**kwargs)

    # ── size (fires before on_enter) ──────────────────────────────────────────

    def on_size(self, instance, size):
        w, h = int(size[0]), int(size[1])
        if w == 0 or h == 0:
            return
        self.t_layer.set_size((w, h))
        try:
            self._game.resize(w, h)
        except AttributeError:
            self._game = BallBreakerGame(w, h)
            self.gl_canvas.add(self._game)
            self.gl_canvas.add(self._game.hud)

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def on_enter(self, *args):
        Clock.schedule_interval(self._tick, self.frame_delay)
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)
        return super().on_enter(*args)

    def on_leave(self, *args):
        Clock.unschedule(self._tick)
        Window.unbind(on_key_down=self._on_key_down)
        Window.unbind(on_key_up=self._on_key_up)
        return super().on_leave(*args)

    # ── tick ──────────────────────────────────────────────────────────────────

    def _tick(self, dt):
        self._game.tick(dt)
        #self.thor_fbo.refresh()
        self.canvas.ask_update()

    # ── keyboard ──────────────────────────────────────────────────────────────

    def _on_key_down(self, window, keycode, *args):
        if keycode == 276:    # left arrow
            self._game.move_left()
            return True
        if keycode == 275:    # right arrow
            self._game.move_right()
            return True
        if keycode == 32:     # space
            self._game.action()
            return True

    def _on_key_up(self, window, keycode, *args):
        if keycode in (276, 275):  # left or right arrow released
            self._game.move_stop()
            return True
