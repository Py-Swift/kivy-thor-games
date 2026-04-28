import pymunk
from thorvg_cython import Shape, Scene, LinearGradient, ColorStop, Matrix

from .constants import (
    CT_PADDLE, COL_PADDLE_BODY, COL_PADDLE_HI,
    COL_PADDLE_GLOW, Layout,
)
from .physics import Physics


class Paddle(Scene):
    """Player-controlled paddle — pymunk kinematic Segment + thorvg visual."""

    def __init__(self, canvas: Scene, physics: Physics, layout: Layout):
        super().__init__()
        self._physics = physics
        self._shp_glow = Shape()
        self._shp_body = Shape()
        self.add(self._shp_glow)
        self.add(self._shp_body)
        canvas.add(self)
        self._build(layout)
        self.sync()

    # ── build / teardown ──────────────────────────────────────────────────────

    def _build(self, lo: Layout):
        self._pw = lo.paddle_w
        self._ph = lo.paddle_h
        self._py = lo.paddle_y
        self._speed = lo.paddle_speed
        self._lo_w = lo.w

        self._body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self._body.position = (lo.w / 2, self._py)
        half = self._pw / 2
        self._pm_shape = pymunk.Segment(self._body, (-half, 0), (half, 0), self._ph / 2)
        self._pm_shape.elasticity = 1.0
        self._pm_shape.friction = 0.0
        self._pm_shape.collision_type = CT_PADDLE
        self._physics.add(self._body, self._pm_shape)

        self._draw_visual()

    def _draw_visual(self):
        w, h = self._pw, self._ph
        half_w = w / 2
        half_h = h / 2
        rx = min(h * 0.4, w * 0.05)

        # Blue glow strip above paddle
        glow_h = h * 1.8
        self._shp_glow.reset()
        self._shp_glow.append_rect(-half_w * 0.85, -half_h - glow_h * 0.6, w * 0.85, glow_h,
                                    rx=glow_h / 2, ry=glow_h / 2)
        lg_g = LinearGradient()
        lg_g.set(-half_w, 0, half_w, 0)
        lg_g.set_color_stops([
            ColorStop(0.0, *COL_PADDLE_GLOW, 0),
            ColorStop(0.2, *COL_PADDLE_GLOW, 60),
            ColorStop(0.5, *COL_PADDLE_GLOW, 100),
            ColorStop(0.8, *COL_PADDLE_GLOW, 60),
            ColorStop(1.0, *COL_PADDLE_GLOW, 0),
        ])
        self._shp_glow.set_gradient(lg_g)

        # Main chrome body
        self._shp_body.reset()
        self._shp_body.append_rect(-half_w, -half_h, w, h, rx=rx, ry=rx)
        lg = LinearGradient()
        lg.set(0, -half_h, 0, half_h)
        lg.set_color_stops([
            ColorStop(0.0, *COL_PADDLE_HI, 255),
            ColorStop(0.4, *COL_PADDLE_BODY, 255),
            ColorStop(0.6, 160, 170, 190, 255),
            ColorStop(1.0, 120, 130, 150, 255),
        ])
        self._shp_body.set_gradient(lg)

    def _teardown_physics(self):
        self._physics.remove(self._pm_shape, self._body)

    def rebuild(self, layout: Layout):
        self._teardown_physics()
        self._build(layout)
        self.sync()

    # ── game actions ──────────────────────────────────────────────────────────

    @property
    def x(self):
        return self._body.position[0]

    def move_left(self):
        self._body.velocity = (-self._speed, 0)

    def move_right(self):
        self._body.velocity = (self._speed, 0)

    def move_stop(self):
        self._body.velocity = (0, 0)

    def sync(self):
        x, y = self._body.position
        half = self._pw / 2
        if x < half:
            x = half
            self._body.position = (x, y)
            self._body.velocity = (0, 0)
        elif x > self._lo_w - half:
            x = self._lo_w - half
            self._body.position = (x, y)
            self._body.velocity = (0, 0)

        m = Matrix()
        m.e13 = x
        m.e23 = y
        self.set_transform(m)