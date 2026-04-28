from thorvg_cython import Scene, Text

from .constants import mat


class Hud(Scene):
    _SS = 2.0

    def __init__(self, screen_w, screen_h, font='Roboto-Regular', font_bold='Roboto-Bold'):
        super().__init__()
        S = self._SS
        self._font = font
        self._font_bold = font_bold

        inner = Scene()
        inner.set_transform(mat(e11=1/S, e22=1/S))
        self.add(inner)

        sx = (round(screen_w / 2) - 60) * S
        sy = 20 * S

        score_sh = Text()
        score_sh.set_font(font_bold)
        score_sh.set_size(42.0 * S)
        score_sh.set_text('0')
        score_sh.set_color(0, 0, 0)
        score_sh.set_opacity(128)
        score_sh.layout(120 * S, 60 * S)
        score_sh.align(0.5, 0.5)
        score_sh.set_transform(mat(e13=sx + 2 * S, e23=sy + 2 * S))
        inner.add(score_sh)

        score = Text()
        score.set_font(font_bold)
        score.set_size(42.0 * S)
        score.set_text('0')
        score.set_color(255, 255, 255)
        score.layout(120 * S, 60 * S)
        score.align(0.5, 0.5)
        score.set_transform(mat(e13=sx, e23=sy))
        inner.add(score)

        mx = (round(screen_w / 2) - 160) * S
        my = (round(screen_h / 2) - 30) * S

        msg_sh = Text()
        msg_sh.set_font(font_bold)
        msg_sh.set_size(30.0 * S)
        msg_sh.set_text('TAP TO PLAY')
        msg_sh.set_color(0, 0, 0)
        msg_sh.set_opacity(128)
        msg_sh.layout(320 * S, 60 * S)
        msg_sh.align(0.5, 0.5)
        msg_sh.set_transform(mat(e13=mx + 2 * S, e23=my + 2 * S))
        inner.add(msg_sh)

        msg = Text()
        msg.set_font(font_bold)
        msg.set_size(30.0 * S)
        msg.set_text('TAP TO PLAY')
        msg.set_color(255, 255, 38)
        msg.layout(320 * S, 60 * S)
        msg.align(0.5, 0.5)
        msg.set_transform(mat(e13=mx, e23=my))
        inner.add(msg)

        self._inner    = inner
        self._score    = score
        self._score_sh = score_sh
        self._msg      = msg
        self._msg_sh   = msg_sh

    def set_score(self, n):
        t = str(n)
        self._score.set_text(t)
        self._score_sh.set_text(t)

    def show_message(self, text):
        self._msg.set_text(text)
        self._msg_sh.set_text(text)
        self._msg.set_opacity(255)
        self._msg_sh.set_opacity(128)

    def hide_message(self):
        self._msg.set_opacity(0)
        self._msg_sh.set_opacity(0)

    def resize(self, screen_w, screen_h):
        S = self._SS
        sx = (round(screen_w / 2) - 60) * S
        sy = 20 * S
        self._score.set_transform(mat(e13=sx, e23=sy))
        self._score.layout(120 * S, 60 * S)
        self._score_sh.set_transform(mat(e13=sx + 2 * S, e23=sy + 2 * S))
        self._score_sh.layout(120 * S, 60 * S)

        mx = (round(screen_w / 2) - 160) * S
        my = (round(screen_h / 2) - 30) * S
        self._msg.set_transform(mat(e13=mx, e23=my))
        self._msg.layout(320 * S, 60 * S)
        self._msg_sh.set_transform(mat(e13=mx + 2 * S, e23=my + 2 * S))
        self._msg_sh.layout(320 * S, 60 * S)
