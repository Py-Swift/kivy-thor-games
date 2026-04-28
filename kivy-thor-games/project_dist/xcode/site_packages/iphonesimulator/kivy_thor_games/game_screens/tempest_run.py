from kivy.clock import Clock
from kivy.core.window import Window

from kivy_thor.thor_screen import ThorScreen
from thor_tempest_run.game import TempestRunGame

_SWIPE_THRESHOLD = 30


class TempestRunScreen(ThorScreen):

    def __init__(self, **kwargs):
        self.frame_delay = kwargs.pop("frame_delay", 0)
        super().__init__(**kwargs)

    # ── size (fires before on_enter, creates game lazily) ─────────────────────

    def on_size(self, instance, size):
        w, h = int(size[0]), int(size[1])
        if w == 0 or h == 0:
            return
        self.t_layer.set_size((w, h))
        try:
            self._game.resize(w, h)
        except AttributeError:
            self._game = TempestRunGame(self.gl_canvas, w, h)

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def on_enter(self, *args):
        Clock.schedule_interval(self._tick, self.frame_delay)
        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        return super().on_enter(*args)

    def on_leave(self, *args):
        Clock.unschedule(self._tick)
        Window.unbind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        return super().on_leave(*args)

    # ── tick ──────────────────────────────────────────────────────────────────

    def _tick(self, dt):
        self._game.tick(dt)
        self.canvas.ask_update()

    # ── touch ─────────────────────────────────────────────────────────────────

    def on_touch_down(self, touch):
        touch.ud['start_x'] = touch.x
        touch.ud['start_y'] = touch.y
        touch.ud['moved']   = False
        return True

    def on_touch_move(self, touch):
        if 'start_x' not in touch.ud:
            return True
        dx = touch.x - touch.ud['start_x']
        dy = touch.y - touch.ud['start_y']
        if not touch.ud['moved']:
            if abs(dx) > _SWIPE_THRESHOLD:
                touch.ud['moved'] = True
                if dx < 0:
                    self._game.move_left()
                else:
                    self._game.move_right()
            elif dy < -_SWIPE_THRESHOLD:
                touch.ud['moved'] = True
                self._game.slide()
        return True

    def on_touch_up(self, touch):
        if 'start_x' not in touch.ud:
            return True
        if not touch.ud['moved']:
            self._game.action()
            self._game.jump()
        self._game.release_jump()
        self._game.release_slide()
        return True

    # ── keyboard ──────────────────────────────────────────────────────────────

    def _on_key_down(self, window, keycode, *args):
        g = self._game
        if keycode in (276, 97):    # left / A
            g.move_left()
        elif keycode in (275, 100): # right / D
            g.move_right()
        elif keycode in (273, 119): # up / W
            if not getattr(self, '_held_jump', False):
                g.jump()
                self._held_jump = True
        elif keycode in (274, 115): # down / S
            if not getattr(self, '_held_slide', False):
                g.slide()
                self._held_slide = True
        elif keycode == 32:         # space
            g.action()
        elif keycode in (112, 27):  # P / Esc
            g.pause()

    def _on_key_up(self, window, keycode, *args):
        if keycode in (273, 119):   # up / W
            self._held_jump = False
            self._game.release_jump()
        elif keycode in (274, 115): # down / S
            self._held_slide = False
            self._game.release_slide()
