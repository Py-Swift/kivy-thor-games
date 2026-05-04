from thorvg_cython import Scene, Shape, LinearGradient, ColorStop

from .constants import mat


class Sky(Scene):
    def __init__(self, canvas, w, h):
        super().__init__()
        self._shape = Shape()
        self._paint(w, h)
        self.add(self._shape)
        canvas.add(self)

    def _paint(self, w, h):
        self._shape.reset()
        self._shape.append_rect(0, 0, w, h)
        lg = LinearGradient()
        lg.set(w / 2, 0, w / 2, h)
        lg.set_color_stops([
            ColorStop(0.0,  65, 140, 210, 255),
            ColorStop(0.7, 130, 195, 230, 255),
            ColorStop(1.0, 170, 215, 185, 255),
        ])
        self._shape.set_gradient(lg)

    def resize(self, w, h):
        self._paint(w, h)
