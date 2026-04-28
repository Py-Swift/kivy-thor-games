from thorvg_cython import Scene, Shape

from .constants import GROUND_H, PIPE_SPEED, mat

_CLOUD_DEFS = [
    (0.05, 0.08, 0.18, 1.1),
    (0.25, 0.14, 0.12, 0.8),
    (0.48, 0.06, 0.22, 1.3),
    (0.65, 0.18, 0.10, 0.7),
    (0.80, 0.10, 0.20, 1.0),
    (0.90, 0.22, 0.14, 0.9),
    (0.38, 0.28, 0.08, 0.6),
]

_BG_CLOUD_DEFS = [
    (0.08, 0.04, 0.05, 0.45),
    (0.20, 0.10, 0.04, 0.35),
    (0.35, 0.03, 0.06, 0.50),
    (0.52, 0.08, 0.04, 0.38),
    (0.67, 0.05, 0.05, 0.42),
    (0.78, 0.12, 0.04, 0.32),
    (0.88, 0.02, 0.06, 0.48),
    (0.14, 0.16, 0.03, 0.30),
    (0.60, 0.14, 0.05, 0.40),
]


class BgCloudLayer(Scene):
    """Distant small clouds — scrolls slowest, rendered behind foreground clouds."""

    def __init__(self, canvas, w, h):
        super().__init__()
        self._clouds = []
        sky_h = h - GROUND_H
        for xf, yf, sf, sc in _BG_CLOUD_DEFS:
            cx    = xf * w
            cy    = yf * sky_h
            speed = sf * PIPE_SPEED
            cs    = Scene()
            self._add_blobs(cs, sc)
            cs.set_transform(mat(e13=cx, e23=cy))
            self.add(cs)
            self._clouds.append([cx, cy, speed, sc, cs])
        canvas.add(self)

    def _add_blobs(self, scene, scale):
        for ox, oy, rw, rh in [(0,0,38,20),(-28,6,26,15),(28,6,26,15),(-12,-10,22,14),(12,-10,22,14)]:
            s = Shape()
            s.append_circle(ox * scale, oy * scale, rw * scale, rh * scale)
            s.set_fill_color(240, 245, 255, 160)
            scene.add(s)

    def update(self, dt, w):
        for c in self._clouds:
            c[0] -= c[2] * dt
            if c[0] < -120 * c[3]:
                c[0] = w + 60 * c[3]
            c[4].set_transform(mat(e13=c[0], e23=c[1]))


class CloudLayer(Scene):
    def __init__(self, canvas, w, h):
        super().__init__()
        self._clouds = []
        sky_h = h - GROUND_H
        for xf, yf, sf, sc in _CLOUD_DEFS:
            cx    = xf * w
            cy    = yf * sky_h
            speed = sf * PIPE_SPEED
            cs    = Scene()
            self._add_blobs(cs, sc)
            cs.set_transform(mat(e13=cx, e23=cy))
            self.add(cs)
            self._clouds.append([cx, cy, speed, sc, cs])
        canvas.add(self)

    def _add_blobs(self, scene, scale):
        for ox, oy, rw, rh in [(0,0,40,28),(-32,10,30,22),(32,10,30,22),(-16,-12,28,22),(16,-12,28,22)]:
            s = Shape()
            s.append_circle(ox * scale, oy * scale, rw * scale, rh * scale)
            s.set_fill_color(255, 255, 255, 210)
            scene.add(s)

    def update(self, dt, w):
        for c in self._clouds:
            c[0] -= c[2] * dt
            if c[0] < -150 * c[3]:
                c[0] = w + 80 * c[3]
            c[4].set_transform(mat(e13=c[0], e23=c[1]))
