from kivy.clock import Clock
from kivy.core.window import Window

from kivy_thor.thor_screen import ThorScreen
from thor_tetris import TetrisGame


class TetrisScreen(ThorScreen):

    # ── size ──────────────────────────────────────────────────────────────────

    def on_size(self, instance, size):
        w, h = int(size[0]), int(size[1])
        if w == 0 or h == 0:
            return
        self.t_layer.set_size((w, h))
        try:
            self._game.resize(w, h)
        except AttributeError:
            self._game = TetrisGame(w, h)
            self.gl_canvas.add(self._game)
            self.gl_canvas.add(self._game.hud)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self, **kwargs):
        self.frame_delay = kwargs.pop("frame_delay", 0)
        super().__init__(**kwargs)

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
        self.canvas.ask_update()

    # ── keyboard ──────────────────────────────────────────────────────────────

    def _on_key_down(self, window, keycode, *args):
        if keycode == 276:        # left arrow
            self._game.move_left()
            return True
        if keycode == 275:        # right arrow
            self._game.move_right()
            return True
        if keycode == 274:        # down arrow → soft drop
            self._game.soft_drop(True)
            return True
        if keycode == 273:        # up arrow → rotate CW
            self._game.rotate_cw()
            return True
        if keycode == 32:         # space → hard drop or action
            from thor_tetris.constants import ST_PLAYING
            if self._game._state == ST_PLAYING:
                self._game.hard_drop()
            else:
                self._game.action()
            return True
        if keycode == 99:         # 'c' → hold
            self._game.hold()
            return True
        if keycode == 122:        # 'z' → rotate CCW
            self._game.rotate_ccw()
            return True
        if keycode == 13:         # enter → action (start/restart)
            self._game.action()
            return True

    def _on_key_up(self, window, keycode, *args):
        if keycode == 274:        # down arrow released → stop soft drop
            self._game.soft_drop(False)
            return True
