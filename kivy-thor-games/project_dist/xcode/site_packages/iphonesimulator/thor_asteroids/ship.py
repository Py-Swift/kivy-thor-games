import math

import pymunk
from thorvg_cython import Shape, Scene, Matrix

from .constants import (
    CT_SHIP, COL_SHIP, COL_SHIP_THRUST,
    SHIP_DRAG, SHIP_ROTATE_SPEED, SHIP_INVULN_DUR, Layout,
)
from .physics import Physics

FLAME_SHOW_DUR = 0.08  # seconds flame stays visible after a thrust tick


def _build_ship_path(shp: Shape, s: float):
    """Draw the classic asteroids ship outline."""
    shp.move_to(s, 0)
    shp.line_to(-s * 0.7, -s * 0.6)
    shp.line_to(-s * 0.4, 0)
    shp.line_to(-s * 0.7, s * 0.6)
    shp.close()


class Ship:
    """Player ship — neon vector triangle, pymunk dynamic body, discrete input."""

    def __init__(self, scene: Scene, physics: Physics, layout: Layout):
        self._scene = scene
        self._physics = physics
        self._angle = -math.pi / 2
        self._flame_timer = 0.0
        self._invuln = 0.0
        self._alive = True
        self._size = layout.ship_size
        self._thrust_acc = layout.ship_thrust
        self._max_speed = layout.ship_max_speed
        self._stroke_core = layout.stroke_core
        self._stroke_glow = layout.stroke_glow
        self._stroke_bloom = layout.stroke_bloom
        self._w = layout.w
        self._h = layout.h

        # pymunk
        self._body = pymunk.Body(mass=1, moment=float('inf'))
        self._body.position = (layout.w / 2, layout.h / 2)
        self._body.velocity = (0, 0)
        self._pm_shape = pymunk.Circle(self._body, self._size * 0.7)
        self._pm_shape.elasticity = 0.0
        self._pm_shape.friction = 0.0
        self._pm_shape.collision_type = CT_SHIP
        physics.add(self._body, self._pm_shape)

        # thorvg — bloom (15%) + fill (30%) + wide stroke (70%) + core (100%) + flame
        s = self._size
        self._shp_bloom = Shape()
        _build_ship_path(self._shp_bloom, s)
        self._shp_bloom.set_stroke_width(self._stroke_bloom)
        self._shp_bloom.set_stroke_color(*COL_SHIP, 38)
        self._shp_bloom.set_stroke_join(1)

        self._shp_fill = Shape()
        _build_ship_path(self._shp_fill, s)
        self._shp_fill.set_fill_color(*COL_SHIP, 76)

        self._shp_glow = Shape()
        _build_ship_path(self._shp_glow, s)
        self._shp_glow.set_stroke_width(self._stroke_glow)
        self._shp_glow.set_stroke_color(*COL_SHIP, 178)
        self._shp_glow.set_stroke_join(1)

        self._shp_core = Shape()
        _build_ship_path(self._shp_core, s)
        self._shp_core.set_stroke_width(self._stroke_core)
        self._shp_core.set_stroke_color(*COL_SHIP, 255)
        self._shp_core.set_stroke_join(1)

        self._shp_flame_bloom = Shape()
        self._shp_flame_fill = Shape()
        self._shp_flame_glow = Shape()
        self._shp_flame_core = Shape()

        scene.add(self._shp_bloom)
        scene.add(self._shp_fill)
        scene.add(self._shp_glow)
        scene.add(self._shp_core)
        scene.add(self._shp_flame_bloom)
        scene.add(self._shp_flame_fill)
        scene.add(self._shp_flame_glow)
        scene.add(self._shp_flame_core)

    @property
    def alive(self):
        return self._alive

    @property
    def invulnerable(self):
        return self._invuln > 0.0

    @property
    def position(self):
        return self._body.position

    @property
    def angle(self):
        return self._angle

    @property
    def pm_shape(self):
        return self._pm_shape

    def _draw_ship_shapes(self):
        s = self._size
        self._shp_bloom.reset()
        _build_ship_path(self._shp_bloom, s)
        self._shp_bloom.set_stroke_width(self._stroke_bloom)
        self._shp_bloom.set_stroke_color(*COL_SHIP, 38)
        self._shp_bloom.set_stroke_join(1)

        self._shp_fill.reset()
        _build_ship_path(self._shp_fill, s)
        self._shp_fill.set_fill_color(*COL_SHIP, 76)

        self._shp_glow.reset()
        _build_ship_path(self._shp_glow, s)
        self._shp_glow.set_stroke_width(self._stroke_glow)
        self._shp_glow.set_stroke_color(*COL_SHIP, 178)
        self._shp_glow.set_stroke_join(1)

        self._shp_core.reset()
        _build_ship_path(self._shp_core, s)
        self._shp_core.set_stroke_width(self._stroke_core)
        self._shp_core.set_stroke_color(*COL_SHIP, 255)
        self._shp_core.set_stroke_join(1)

    def _teardown_physics(self):
        self._physics.remove(self._pm_shape, self._body)

    def rebuild(self, layout: Layout):
        self._teardown_physics()
        self._size = layout.ship_size
        self._thrust_acc = layout.ship_thrust
        self._max_speed = layout.ship_max_speed
        self._stroke_core = layout.stroke_core
        self._stroke_glow = layout.stroke_glow
        self._stroke_bloom = layout.stroke_bloom
        self._w = layout.w
        self._h = layout.h

        self._body = pymunk.Body(mass=1, moment=float('inf'))
        self._body.position = (layout.w / 2, layout.h / 2)
        self._body.velocity = (0, 0)
        self._pm_shape = pymunk.Circle(self._body, self._size * 0.7)
        self._pm_shape.elasticity = 0.0
        self._pm_shape.friction = 0.0
        self._pm_shape.collision_type = CT_SHIP
        self._physics.add(self._body, self._pm_shape)

        self._draw_ship_shapes()
        self._angle = -math.pi / 2
        self.sync(0.0)

    def reset(self, layout: Layout):
        self._body.position = (layout.w / 2, layout.h / 2)
        self._body.velocity = (0, 0)
        self._angle = -math.pi / 2
        self._flame_timer = 0.0
        self._alive = True
        self._invuln = SHIP_INVULN_DUR
        self._pm_shape.collision_type = CT_SHIP
        self.sync(0.0)

    def die(self):
        self._alive = False
        self._flame_timer = 0.0
        self._shp_bloom.set_opacity(0)
        self._shp_fill.set_opacity(0)
        self._shp_core.set_opacity(0)
        self._shp_glow.set_opacity(0)
        self._shp_flame_bloom.reset()
        self._shp_flame_fill.reset()
        self._shp_flame_glow.reset()
        self._shp_flame_core.reset()

    def respawn(self, layout: Layout):
        self._alive = True
        self._invuln = SHIP_INVULN_DUR
        self._body.position = (layout.w / 2, layout.h / 2)
        self._body.velocity = (0, 0)
        self._angle = -math.pi / 2
        self._shp_bloom.set_opacity(255)
        self._shp_fill.set_opacity(255)
        self._shp_core.set_opacity(255)
        self._shp_glow.set_opacity(255)
        self._pm_shape.collision_type = CT_SHIP
        self.sync(0.0)

    # ── input (all discrete ticks) ────────────────────────────────────────────

    def rotate_left(self):
        self._angle -= SHIP_ROTATE_SPEED * 0.016

    def rotate_right(self):
        self._angle += SHIP_ROTATE_SPEED * 0.016

    def thrust_tick(self):
        dx = math.cos(self._angle) * self._thrust_acc * 0.016
        dy = math.sin(self._angle) * self._thrust_acc * 0.016
        vx, vy = self._body.velocity
        vx += dx
        vy += dy
        mag = math.hypot(vx, vy)
        if mag > self._max_speed:
            scale = self._max_speed / mag
            vx *= scale
            vy *= scale
        self._body.velocity = (vx, vy)
        self._flame_timer = FLAME_SHOW_DUR

    # ── sync visuals ──────────────────────────────────────────────────────────

    def sync(self, dt: float):
        if not self._alive:
            return

        vx, vy = self._body.velocity
        self._body.velocity = (vx * SHIP_DRAG, vy * SHIP_DRAG)

        x, y = self._body.position
        x = x % self._w
        y = y % self._h
        self._body.position = (x, y)

        if self._invuln > 0.0:
            self._invuln -= dt
            blink = int(self._invuln * 10) % 2
            vis = 200 if blink else 40
        else:
            vis = 255

        cos_a = math.cos(self._angle)
        sin_a = math.sin(self._angle)
        m = Matrix()
        m.e11 = cos_a
        m.e12 = -sin_a
        m.e21 = sin_a
        m.e22 = cos_a
        m.e13 = x
        m.e23 = y

        self._shp_bloom.set_transform(m)
        self._shp_bloom.set_opacity(vis)
        self._shp_fill.set_transform(m)
        self._shp_fill.set_opacity(vis)
        self._shp_core.set_transform(m)
        self._shp_core.set_opacity(vis)
        self._shp_glow.set_transform(m)
        self._shp_glow.set_opacity(vis)

        if self._flame_timer > 0.0:
            self._flame_timer = max(0.0, self._flame_timer - dt)
            s = self._size
            t = self._flame_timer / FLAME_SHOW_DUR
            flame_len = s * (0.5 + 0.4 * t)

            self._shp_flame_bloom.reset()
            self._shp_flame_bloom.move_to(-s * 0.4, -s * 0.2)
            self._shp_flame_bloom.line_to(-s * 0.4 - flame_len, 0)
            self._shp_flame_bloom.line_to(-s * 0.4, s * 0.2)
            self._shp_flame_bloom.set_stroke_width(self._stroke_bloom)
            self._shp_flame_bloom.set_stroke_color(*COL_SHIP_THRUST, int(38 * t))
            self._shp_flame_bloom.set_stroke_join(1)
            self._shp_flame_bloom.set_transform(m)

            self._shp_flame_fill.reset()
            self._shp_flame_fill.move_to(-s * 0.4, -s * 0.2)
            self._shp_flame_fill.line_to(-s * 0.4 - flame_len, 0)
            self._shp_flame_fill.line_to(-s * 0.4, s * 0.2)
            self._shp_flame_fill.close()
            self._shp_flame_fill.set_fill_color(*COL_SHIP_THRUST, int(76 * t))
            self._shp_flame_fill.set_transform(m)

            self._shp_flame_glow.reset()
            self._shp_flame_glow.move_to(-s * 0.4, -s * 0.2)
            self._shp_flame_glow.line_to(-s * 0.4 - flame_len, 0)
            self._shp_flame_glow.line_to(-s * 0.4, s * 0.2)
            self._shp_flame_glow.set_stroke_width(self._stroke_glow)
            self._shp_flame_glow.set_stroke_color(*COL_SHIP_THRUST, int(178 * t))
            self._shp_flame_glow.set_stroke_join(1)
            self._shp_flame_glow.set_transform(m)

            self._shp_flame_core.reset()
            self._shp_flame_core.move_to(-s * 0.4, -s * 0.2)
            self._shp_flame_core.line_to(-s * 0.4 - flame_len, 0)
            self._shp_flame_core.line_to(-s * 0.4, s * 0.2)
            self._shp_flame_core.set_stroke_width(self._stroke_core)
            self._shp_flame_core.set_stroke_color(*COL_SHIP_THRUST, int(255 * t))
            self._shp_flame_core.set_stroke_join(1)
            self._shp_flame_core.set_transform(m)
        else:
            self._shp_flame_bloom.reset()
            self._shp_flame_fill.reset()
            self._shp_flame_glow.reset()
            self._shp_flame_core.reset()
