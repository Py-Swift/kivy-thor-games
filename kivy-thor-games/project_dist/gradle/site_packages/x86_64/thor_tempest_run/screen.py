"""
TempestRunScreen — Kivy Screen wrapper.
"""
from __future__ import annotations

from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window

from .game import TempestRunGame


_KEY_LEFT  = 276
_KEY_RIGHT = 275
_KEY_UP    = 273
_KEY_DOWN  = 274
_KEY_SPACE = 32
_KEY_ESC   = 27
_KEY_P     = 112
_KEY_W     = 119
_KEY_A     = 97
_KEY_S     = 115
_KEY_D     = 100


class TempestRunScreen(Screen):

    def __init__(self, canvas_widget, **kwargs) -> None:
        super().__init__(**kwargs)
        w, h = Window.size
        self._game = TempestRunGame(canvas_widget.canvas, float(w), float(h))
        self._canvas_widget = canvas_widget
        self.add_widget(canvas_widget)

        self._held_jump  = False
        self._held_slide = False

        self._clock_event = Clock.schedule_interval(self._tick, 0)
        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        self.bind(size=self._on_size)

    def _tick(self, dt: float) -> None:
        self._game.tick(dt)
        self._canvas_widget.canvas.update()

    def _on_size(self, _widget, size) -> None:
        self._game.resize(float(size[0]), float(size[1]))

    def _on_key_down(self, _window, keycode, _scancode, _text, _mods) -> bool:
        g = self._game
        if keycode in (_KEY_LEFT, _KEY_A):
            g.move_left()
        elif keycode in (_KEY_RIGHT, _KEY_D):
            g.move_right()
        elif keycode in (_KEY_UP, _KEY_W):
            if not self._held_jump:
                g.jump()
                self._held_jump = True
        elif keycode in (_KEY_DOWN, _KEY_S):
            if not self._held_slide:
                g.slide()
                self._held_slide = True
        elif keycode == _KEY_SPACE:
            g.action()
        elif keycode in (_KEY_ESC, _KEY_P):
            g.pause()
        return False

    def _on_key_up(self, _window, keycode, *_args) -> bool:
        if keycode in (_KEY_UP, _KEY_W):
            self._held_jump = False
            self._game.release_jump()
        elif keycode in (_KEY_DOWN, _KEY_S):
            self._held_slide = False
            self._game.release_slide()
        return False

    def on_leave(self, *_args) -> None:
        self._clock_event.cancel()
        Window.unbind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
