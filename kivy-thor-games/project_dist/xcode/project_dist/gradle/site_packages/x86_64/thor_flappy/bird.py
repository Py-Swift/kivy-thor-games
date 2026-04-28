import math

from thorvg_cython import Scene, Shape, RadialGradient, ColorStop

from .constants import GRAVITY, JUMP_VEL, rot


class Bird(Scene):
    RADIUS = 20

    def __init__(self, canvas):
        super().__init__()
        self.x      = 0.0
        self.y      = 0.0
        self.vy     = 0.0
        self._wing  = Shape(); self.add(self._wing)
        self._body  = Shape(); self.add(self._body)
        self._eye_w = Shape(); self.add(self._eye_w)
        self._eye_p = Shape(); self.add(self._eye_p)
        self._beak  = Shape(); self.add(self._beak)
        canvas.add(self)

    def jump(self):
        self.vy = JUMP_VEL

    def apply_gravity(self, dt):
        self.vy += GRAVITY * dt
        self.y  += self.vy * dt

    def angle(self):
        return max(-28.0, min(90.0, self.vy * 0.05))

    def hits_ceiling_or_ground(self, ground_y, r=15):
        return self.y - r <= 0 or self.y + r >= ground_y

    def draw(self, angle_deg=None):
        if angle_deg is None:
            angle_deg = self.angle()
        m = rot(math.radians(angle_deg), self.x, self.y)
        R = self.RADIUS

        self._wing.reset()
        self._wing.append_circle(-8, 10, 14, 9)
        self._wing.set_fill_color(235, 170, 15, 210)
        self._wing.set_transform(m)

        self._body.reset()
        self._body.append_circle(0, 0, R, R)
        rg = RadialGradient()
        rg.set(-6, -6, R)
        rg.set_color_stops([
            ColorStop(0.0,  255, 242,  80, 255),
            ColorStop(0.55, 252, 192,  22, 255),
            ColorStop(1.0,  215, 135,   0, 255),
        ])
        self._body.set_gradient(rg)
        self._body.set_transform(m)

        self._eye_w.reset()
        self._eye_w.append_circle(9, -7, 8, 8)
        self._eye_w.set_fill_color(255, 255, 255, 255)
        self._eye_w.set_transform(m)

        self._eye_p.reset()
        self._eye_p.append_circle(12, -6, 4, 4)
        self._eye_p.set_fill_color(15, 15, 15, 255)
        self._eye_p.set_transform(m)

        self._beak.reset()
        self._beak.append_rect(14, -6, 18, 12, rx=4, ry=4)
        self._beak.set_fill_color(255, 135, 0, 255)
        self._beak.set_transform(m)
