import os

from thorvg_cython import Scene, Text, Matrix

from .constants import COL_TEXT, COL_TEXT_MSG, Layout

# ── font loading (best-effort) ────────────────────────────────────────────────
_FONT_LOADED = False
_FONT_NAME = 'Roboto-Bold'

def _ensure_font():
    global _FONT_LOADED
    if _FONT_LOADED:
        return
    _FONT_LOADED = True
    try:
        import kivy as _kivy
        path = os.path.join(os.path.dirname(_kivy.__file__), 'data', 'fonts', 'Roboto-Bold.ttf')
        Text.font_load(path)
    except Exception:
        pass  # font won't render but game still works


class Hud(Scene):
    """Score, lives, and centre message — pure thorvg Text objects."""

    def __init__(self, layout: Layout):
        _ensure_font()
        super().__init__()

        self._score_text = Text()
        self._lives_text = Text()
        self._msg_text = Text()

        self.add(self._score_text)
        self.add(self._lives_text)
        self.add(self._msg_text)

        self._score = 0
        self._lives = 0
        self._build(layout)

    def _build(self, lo: Layout):
        self._lo = lo
        pad = lo.hud_pad

        # score — top left
        self._score_text.set_font(_FONT_NAME)
        self._score_text.set_size(lo.hud_font)
        self._score_text.set_color(*COL_TEXT)
        self._score_text.layout(lo.w * 0.4, lo.hud_font * 1.5)
        m = Matrix()
        m.e13 = pad
        m.e23 = pad
        self._score_text.set_transform(m)

        # lives — top right
        self._lives_text.set_font(_FONT_NAME)
        self._lives_text.set_size(lo.hud_font)
        self._lives_text.set_color(*COL_TEXT)
        self._lives_text.layout(lo.w * 0.4, lo.hud_font * 1.5)
        m2 = Matrix()
        m2.e13 = lo.w - lo.w * 0.4 - pad
        m2.e23 = pad
        self._lives_text.set_transform(m2)

        # centre message
        self._msg_text.set_font(_FONT_NAME)
        self._msg_text.set_size(lo.hud_msg_font)
        self._msg_text.set_color(*COL_TEXT_MSG)
        msg_w = lo.w * 0.8
        msg_h = lo.hud_msg_font * 2.5
        self._msg_text.layout(msg_w, msg_h)
        self._msg_text.align(0.5, 0.5)
        m3 = Matrix()
        m3.e13 = (lo.w - msg_w) / 2
        m3.e23 = lo.h * 0.45
        self._msg_text.set_transform(m3)

        # refresh displayed values
        self.set_score(self._score)
        self.set_lives(self._lives)

    def rebuild(self, layout: Layout):
        self._build(layout)

    def set_score(self, n: int):
        self._score = n
        self._score_text.set_text(f'Score: {n}')

    def set_lives(self, n: int):
        self._lives = n
        self._lives_text.set_text(f'Lives: {n}')

    def show_message(self, text: str):
        self._msg_text.set_text(text)
        self._msg_text.set_opacity(255)

    def hide_message(self):
        self._msg_text.set_opacity(0)
