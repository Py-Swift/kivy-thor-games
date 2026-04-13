from thorvg_cython import Scene, Shape

from .constants import GROUND_H


class Ground(Scene):
    def __init__(self, canvas, w, h):
        super().__init__()
        self._dirt  = Shape()
        self._grass = Shape()
        self._paint(w, h)
        self.add(self._dirt)
        self.add(self._grass)
        canvas.add(self)

    def _paint(self, w, h):
        self._dirt.reset()
        self._dirt.append_rect(0, h - GROUND_H, w, GROUND_H)
        self._dirt.set_fill_color(110, 78, 36, 255)
        self._grass.reset()
        self._grass.append_rect(0, h - GROUND_H, w, 20)
        self._grass.set_fill_color(80, 165, 50, 255)

    def resize(self, w, h):
        self._paint(w, h)
