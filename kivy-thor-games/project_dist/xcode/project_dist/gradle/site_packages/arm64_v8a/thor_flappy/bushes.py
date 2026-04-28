from thorvg_cython import Scene, Shape

from .constants import BUSH_SPEED, GROUND_H, mat

_BUSH_DEFS = [
    (0.00, 10, 14, [(-12,-10,16,10),(0,-10,18,11),(12,-10,16,10),  (-8,-22,13,9),(6,-21,13,9),  (0,-32,10,8)]),
    (0.12,  8, 10, [(-10, -8,14, 9),(0, -8,15,10),(10, -8,14, 9),  (0,-20,11,8)]),
    (0.23, 12, 16, [(-14,-12,18,11),(0,-12,20,12),(14,-12,18,11),  (-9,-25,14,9),(7,-24,13,9),  (0,-36,11,8),(-6,-36,9,7)]),
    (0.34,  7,  9, [( -9, -7,12, 8),(0, -7,13, 9),( 9, -7,12, 8),  (0,-18, 9,7)]),
    (0.45, 10, 14, [(-11,-10,15,10),(0,-10,17,11),(11,-10,15,10),  (-7,-22,12,8),(5,-21,11,8),  (0,-31, 9,7)]),
    (0.57,  8, 10, [(-10, -8,13, 9),(0, -8,15,10),(10, -8,13, 9),  (0,-20,10,7),(-5,-28,8,6)]),
    (0.68,  7,  9, [( -8, -7,12, 8),(0, -7,13, 9),( 8, -7,12, 8),  (0,-18, 9,7)]),
    (0.78, 12, 15, [(-13,-11,17,11),(0,-11,19,12),(13,-11,17,11),  (-8,-24,13,9),(6,-23,12,9),  (0,-34,10,8),(-7,-33,8,6)]),
    (0.89,  8, 10, [(-10, -8,14, 9),(0, -8,15,10),(10, -8,14, 9),  (1,-20,10,7),(-4,-27,7,6)]),
]


class BushLayer(Scene):
    """Low bushy shrubs at mid-distance — scrolls at 55% of pipe speed."""

    _TRUNK_COLOR = (80,  52, 20, 220)
    _CANOPY_DARK = (34,  90, 34, 200)
    _CANOPY_MID  = (50, 120, 45, 215)

    def __init__(self, canvas, w, h):
        super().__init__()
        self._bushes = []
        ground_top   = h - GROUND_H
        for xf, tw, th, canopy in _BUSH_DEFS:
            cx = xf * w
            bs = Scene()
            self._draw_bush(bs, tw, th, canopy)
            bs.set_transform(mat(e13=cx, e23=ground_top))
            self.add(bs)
            self._bushes.append([cx, ground_top, bs])
        canvas.add(self)

    def _draw_bush(self, scene, trunk_w, trunk_h, canopy):
        trunk = Shape()
        trunk.append_rect(-trunk_w // 2, -trunk_h, trunk_w, trunk_h)
        trunk.set_fill_color(*self._TRUNK_COLOR)
        scene.add(trunk)
        for i, (ox, oy, rw, rh) in enumerate(canopy):
            s = Shape()
            s.append_circle(ox, oy, rw, rh)
            s.set_fill_color(*(self._CANOPY_MID if i % 2 == 0 else self._CANOPY_DARK))
            scene.add(s)

    def update(self, dt, w):
        for b in self._bushes:
            b[0] -= BUSH_SPEED * dt
            if b[0] < -80:
                b[0] = w + 60
            b[2].set_transform(mat(e13=b[0], e23=b[1]))
