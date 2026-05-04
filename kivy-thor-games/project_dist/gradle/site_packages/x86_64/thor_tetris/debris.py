import math
import random

import pymunk
from thorvg_cython import Scene, Shape, LinearGradient, ColorStop, Matrix

from .constants import (
    SPAWN_ROWS, CT_DEBRIS, PIECE_COLORS,
    DEBRIS_LIFETIME, DEBRIS_IMPULSE_Y, DEBRIS_IMPULSE_X, Layout,
)
from .physics import Physics
from .board import _brighten, _darken


class _Particle:
    __slots__ = ('body', 'pm_shape', 'shape', 'ttl')

    def __init__(self, body, pm_shape, shape, ttl):
        self.body = body
        self.pm_shape = pm_shape
        self.shape = shape
        self.ttl = ttl


class Debris(Scene):
    """Line-clear particle effects — pymunk bodies that fly apart under gravity."""

    def __init__(self, canvas: Scene, physics: Physics, layout: Layout):
        super().__init__()
        canvas.add(self)
        self._physics = physics
        self._layout = layout
        self._particles: list[_Particle] = []

    def spawn(self, cleared_cells: list[tuple[int, int, int]], layout: Layout):
        """Create debris particles for cleared cells.

        cleared_cells: list of (row, col, piece_type) tuples.
        """
        lo = layout
        cell = lo.cell
        pad = cell * 0.06
        rx = cell * 0.12
        size = cell - 2 * pad

        for r, c, pt in cleared_cells:
            visible_r = r - SPAWN_ROWS
            if visible_r < 0:
                continue

            x = lo.board_x + c * cell + cell / 2
            y = lo.board_y + visible_r * cell + cell / 2

            # pymunk body
            mass = 1.0
            moment = pymunk.moment_for_box(mass, (size, size))
            body = pymunk.Body(mass, moment)
            body.position = (x, y)
            body.angle = random.uniform(-0.3, 0.3)

            pm_shape = pymunk.Poly.create_box(body, (size, size))
            pm_shape.elasticity = 0.3
            pm_shape.friction = 0.5
            pm_shape.collision_type = CT_DEBRIS
            self._physics.add(body, pm_shape)

            # random impulse
            ix = random.uniform(-DEBRIS_IMPULSE_X, DEBRIS_IMPULSE_X)
            iy = DEBRIS_IMPULSE_Y + random.uniform(-100, 100)
            body.apply_impulse_at_local_point((ix, iy))
            body.angular_velocity = random.uniform(-8, 8)

            # thorvg shape
            base = PIECE_COLORS[pt]
            hi = _brighten(base, 60)
            dk = _darken(base, 40)

            shp = Shape()
            half = size / 2
            shp.append_rect(-half, -half, size, size, rx=rx, ry=rx)
            lg = LinearGradient()
            lg.set(0, -half, 0, half)
            lg.set_color_stops([
                ColorStop(0.0, *hi, 255),
                ColorStop(0.4, *base, 255),
                ColorStop(1.0, *dk, 255),
            ])
            shp.set_gradient(lg)
            self.add(shp)

            self._particles.append(_Particle(body, pm_shape, shp, DEBRIS_LIFETIME))

    def update(self, dt: float):
        """Tick debris — sync transforms, fade, expire."""
        alive = []
        for p in self._particles:
            p.ttl -= dt
            if p.ttl <= 0:
                p.shape.reset()
                self._physics.remove(p.pm_shape, p.body)
                continue

            # fade out in last 0.5s
            alpha = 255
            if p.ttl < 0.5:
                alpha = int(255 * (p.ttl / 0.5))

            x, y = p.body.position
            angle = p.body.angle

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            m = Matrix()
            m.e11 = cos_a
            m.e12 = -sin_a
            m.e21 = sin_a
            m.e22 = cos_a
            m.e13 = x
            m.e23 = y
            p.shape.set_transform(m)
            p.shape.set_opacity(alpha)
            alive.append(p)

        self._particles = alive

    def clear(self):
        """Remove all active debris."""
        for p in self._particles:
            p.shape.reset()
            self._physics.remove(p.pm_shape, p.body)
        self._particles.clear()

    def rebuild(self, layout: Layout):
        self._layout = layout
        # debris doesn't survive resize — just clear
        self.clear()
