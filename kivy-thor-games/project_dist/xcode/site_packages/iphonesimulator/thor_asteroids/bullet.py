import math

import pymunk
from thorvg_cython import Shape, Scene, RadialGradient, ColorStop, Matrix

from .constants import (
    CT_BULLET, COL_BULLET, COL_BULLET_GLOW,
    BULLET_LIFETIME, MAX_BULLETS, BULLET_COOLDOWN, Layout,
)
from .physics import Physics


class Bullet:
    """Single bullet — neon dot with radial glow, short lifetime."""

    def __init__(self, scene: Scene, physics: Physics,
                 x: float, y: float, angle: float, layout: Layout):
        self._scene = scene
        self._physics = physics
        self._r = layout.bullet_r
        self._w = layout.w
        self._h = layout.h
        self._ttl = BULLET_LIFETIME
        self.alive = True

        # pymunk
        self._body = pymunk.Body(mass=0.1, moment=float('inf'))
        self._body.position = (x, y)
        speed = layout.bullet_speed
        self._body.velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
        self._pm_shape = pymunk.Circle(self._body, self._r)
        self._pm_shape.sensor = True
        self._pm_shape.collision_type = CT_BULLET
        physics.add(self._body, self._pm_shape)

        # thorvg — bloom halo + glow halo + bright core dot
        r = self._r
        br = r * 8

        self._shp_bloom = Shape()
        self._shp_bloom.append_circle(0, 0, br, br)
        rg_bloom = RadialGradient()
        rg_bloom.set(0, 0, br)
        rg_bloom.set_color_stops([
            ColorStop(0.0, *COL_BULLET_GLOW, 100),
            ColorStop(0.3, *COL_BULLET_GLOW, 40),
            ColorStop(1.0, *COL_BULLET_GLOW, 0),
        ])
        self._shp_bloom.set_gradient(rg_bloom)

        gr = r * 4
        self._shp_glow = Shape()
        self._shp_glow.append_circle(0, 0, gr, gr)
        rg = RadialGradient()
        rg.set(0, 0, gr)
        rg.set_color_stops([
            ColorStop(0.0, *COL_BULLET_GLOW, 200),
            ColorStop(0.4, *COL_BULLET_GLOW, 80),
            ColorStop(1.0, *COL_BULLET_GLOW, 0),
        ])
        self._shp_glow.set_gradient(rg)

        self._shp_core = Shape()
        self._shp_core.append_circle(0, 0, r, r)
        self._shp_core.set_fill_color(*COL_BULLET, 255)

        scene.add(self._shp_bloom)
        scene.add(self._shp_glow)
        scene.add(self._shp_core)

    @property
    def pm_shape(self):
        return self._pm_shape

    def destroy(self):
        if not self.alive:
            return
        self.alive = False
        self._physics.remove(self._pm_shape, self._body)
        self._shp_bloom.reset()
        self._shp_glow.reset()
        self._shp_core.reset()

    def sync(self, dt: float):
        if not self.alive:
            return

        self._ttl -= dt
        if self._ttl <= 0:
            self.destroy()
            return

        x, y = self._body.position
        x = x % self._w
        y = y % self._h
        self._body.position = (x, y)

        m = Matrix()
        m.e13 = x
        m.e23 = y
        self._shp_bloom.set_transform(m)
        self._shp_glow.set_transform(m)
        self._shp_core.set_transform(m)


class BulletPool:
    """Manages all active bullets with cooldown and max count."""

    def __init__(self, scene: Scene, physics: Physics):
        self._scene = scene
        self._physics = physics
        self._bullets: list[Bullet] = []
        self._lookup: dict = {}
        self._cooldown = 0.0

    def fire(self, x: float, y: float, angle: float, layout: Layout):
        if self._cooldown > 0.0:
            return
        alive_count = sum(1 for b in self._bullets if b.alive)
        if alive_count >= MAX_BULLETS:
            return
        b = Bullet(self._scene, self._physics, x, y, angle, layout)
        self._bullets.append(b)
        self._lookup[b.pm_shape] = b
        self._cooldown = BULLET_COOLDOWN

    def on_hit(self, pm_shape):
        bullet = self._lookup.get(pm_shape)
        if bullet is None or not bullet.alive:
            return
        bullet.destroy()
        del self._lookup[pm_shape]

    def sync(self, dt: float):
        self._cooldown = max(0.0, self._cooldown - dt)
        for b in self._bullets:
            b.sync(dt)
        dead = [b for b in self._bullets if not b.alive]
        for b in dead:
            self._bullets.remove(b)
            self._lookup.pop(b.pm_shape, None)

    def clear_all(self):
        for b in self._bullets:
            if b.alive:
                b.destroy()
        self._bullets.clear()
        self._lookup.clear()
        self._cooldown = 0.0
