"""
Debris — death particle burst.

On player death N small neon dots are scattered across the screen with
random outward velocities, fading to transparent over DEBRIS_TTL seconds.
Uses simple 2-D screen-space integration (no pymunk) — particles just need
to fly outward and fade.

Inspired by the Tetris debris pattern in kivy-thor-games.
"""
from __future__ import annotations

import math
import random

from thorvg_cython import Scene, Shape, Matrix

from .constants import COL_DEBRIS, DEBRIS_COUNT, DEBRIS_TTL, Layout


class _Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'ttl', 'max_ttl', 'shp')

    def __init__(self, x: float, y: float,
                 vx: float, vy: float,
                 ttl: float, shp: Shape):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ttl = ttl
        self.max_ttl = ttl
        self.shp = shp


class Debris(Scene):
    """Screen-space particle burst used for the death effect."""

    def __init__(self, layout: Layout) -> None:
        super().__init__()
        self._lo = layout
        self._particles: list[_Particle] = []

        r, g, b = COL_DEBRIS
        # Pre-allocate shape pool
        self._pool: list[Shape] = []
        for _ in range(DEBRIS_COUNT):
            shp = Shape()
            self.add(shp)
            shp.set_fill_color(r, g, b, 0)  # hidden initially
            self._pool.append(shp)

    def burst(self, cx: float, cy: float) -> None:
        """Spawn all particles at screen position (cx, cy)."""
        self._particles.clear()
        lo = self._lo
        r, g, b = COL_DEBRIS

        for i in range(min(DEBRIS_COUNT, len(self._pool))):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(lo.debris_speed * 0.3, lo.debris_speed)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            shp = self._pool[i]
            shp.reset()
            dr = lo.debris_r
            shp.append_circle(0, 0, dr, dr)
            shp.set_fill_color(r, g, b, 255)

            self._particles.append(_Particle(
                cx, cy, vx, vy,
                ttl=DEBRIS_TTL,
                shp=shp,
            ))

    def sync(self, dt: float) -> None:
        """Advance and reposition all live particles."""
        r, g, b = COL_DEBRIS
        for p in self._particles:
            if p.ttl <= 0.0:
                continue
            p.ttl -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt

            alpha = max(0, int(255 * p.ttl / p.max_ttl))
            p.shp.set_fill_color(r, g, b, alpha)
            m = Matrix()
            m.e13 = p.x
            m.e23 = p.y
            p.shp.set_transform(m)

        # Hide particles whose TTL has expired
        for p in self._particles:
            if p.ttl <= 0.0:
                p.shp.reset()

    def clear(self) -> None:
        self._particles.clear()
        for shp in self._pool:
            shp.reset()

    def rebuild(self, layout: Layout) -> None:
        self._lo = layout
        self.clear()
