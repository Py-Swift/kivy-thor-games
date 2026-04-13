import math

import pymunk
from thorvg_cython import Shape, Scene, RadialGradient, ColorStop, Matrix

from .constants import CT_BALL, COL_BALL, COL_BALL_GLOW, Layout
from .physics import Physics


class Ball:
    """Game ball — owns a pymunk Circle body and a thorvg circle Shape."""

    def __init__(self, scene: Scene, physics: Physics, layout: Layout):
        self._scene = scene
        self._physics = physics
        self._glow = Shape()
        self._shape = Shape()
        self.launched = False
        self._hit_pulse = 0.0  # remaining pulse time (seconds)
        scene.add(self._glow)
        scene.add(self._shape)
        self._build(layout)

    # ── build / teardown ──────────────────────────────────────────────────────

    def _build(self, lo: Layout):
        self._r = lo.ball_r
        self._glow_r = lo.ball_glow_r
        self._speed = lo.ball_speed
        self._w = lo.w
        self._h = lo.h

        # pymunk
        self._body = pymunk.Body(mass=1, moment=float('inf'))
        self._pm_shape = pymunk.Circle(self._body, self._r)
        self._pm_shape.elasticity = 1.0
        self._pm_shape.friction = 0.0
        self._pm_shape.collision_type = CT_BALL
        self._physics.add(self._body, self._pm_shape)

        # thorvg — draw once, reposition via transform
        self._draw_visual()

    def _draw_visual(self):
        r = self._r
        gr = self._glow_r

        # Glow — large soft transparent circle
        self._glow.reset()
        self._glow.append_circle(0, 0, gr, gr)
        rg_glow = RadialGradient()
        rg_glow.set(0, 0, gr)
        rg_glow.set_color_stops([
            ColorStop(0.0, *COL_BALL_GLOW, 100),
            ColorStop(0.5, *COL_BALL_GLOW, 40),
            ColorStop(1.0, *COL_BALL_GLOW, 0),
        ])
        self._glow.set_gradient(rg_glow)

        # Main ball — bright with specular highlight
        self._shape.reset()
        self._shape.append_circle(0, 0, r, r)
        rg = RadialGradient()
        rg.set(-r * 0.3, -r * 0.3, r)
        rg.set_color_stops([
            ColorStop(0.0, 255, 255, 255, 255),
            ColorStop(0.5, *COL_BALL, 255),
            ColorStop(1.0, 180, 185, 210, 255),
        ])
        self._shape.set_gradient(rg)

    def _teardown_physics(self):
        self._physics.remove(self._pm_shape, self._body)

    def rebuild(self, layout: Layout):
        self._teardown_physics()
        self._build(layout)
        self.reset(layout)

    # ── game actions ──────────────────────────────────────────────────────────

    def reset(self, layout: Layout):
        """Place ball above paddle, stationary."""
        self._body.position = (layout.w / 2, layout.paddle_y - layout.paddle_h - self._r - 2)
        self._body.velocity = (0, 0)
        self.launched = False
        self.sync()

    def stick_to_paddle(self, paddle, layout):
        """Keep ball centred above paddle (before launch)."""
        if self.launched:
            return
        self._body.position = (paddle.x, layout.paddle_y - layout.paddle_h - self._r - 2)
        self._body.velocity = (0, 0)

    def launch(self):
        """Give the ball an initial upward velocity at a slight angle."""
        if self.launched:
            return
        self.launched = True
        angle = math.radians(-75)  # mostly upward, slight rightward
        self._body.velocity = (
            math.cos(angle) * self._speed,
            math.sin(angle) * self._speed,
        )

    HIT_PULSE_DUR = 0.25

    def flash(self):
        """Trigger a glow pulse (call on collision)."""
        self._hit_pulse = self.HIT_PULSE_DUR

    def sync(self, dt: float = 0.0):
        """Read pymunk position → update thorvg transform + normalize velocity."""
        x, y = self._body.position

        # ball shape — always 1:1
        m = Matrix()
        m.e13 = x
        m.e23 = y
        self._shape.set_transform(m)

        # glow — pulse scale on hit, then decay
        if self._hit_pulse > 0.0:
            self._hit_pulse = max(0.0, self._hit_pulse - dt)
            t = self._hit_pulse / self.HIT_PULSE_DUR
            glow_scale = 1.0 + 0.8 * t  # 1.8x → 1.0x
        else:
            glow_scale = 1.0
        mg = Matrix()
        mg.e11 = glow_scale
        mg.e22 = glow_scale
        mg.e13 = x
        mg.e23 = y
        self._glow.set_transform(mg)

        if self.launched:
            vx, vy = self._body.velocity
            mag = math.hypot(vx, vy)
            if mag > 0:
                scale = self._speed / mag
                self._body.velocity = (vx * scale, vy * scale)
