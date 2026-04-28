import math
import random

import pymunk
from thorvg_cython import Shape, Scene, Matrix

from .constants import (
    CT_ASTEROID, COL_ASTEROID, ASTEROID_SCORES, Layout,
)
from .physics import Physics


def _generate_polygon_points(radius: float, num_verts: int = 10):
    points = []
    for i in range(num_verts):
        angle = (math.tau / num_verts) * i
        r = radius * random.uniform(0.7, 1.0)
        points.append((math.cos(angle) * r, math.sin(angle) * r))
    return points


def _build_asteroid_path(shp: Shape, pts: list):
    shp.move_to(pts[0][0], pts[0][1])
    for px, py in pts[1:]:
        shp.line_to(px, py)
    shp.close()


class Asteroid:
    """Single asteroid — neon vector polygon outline, drifts + rotates, wraps edges."""

    def __init__(self, scene: Scene, physics: Physics,
                 x: float, y: float, size: str, layout: Layout,
                 vx: float = 0.0, vy: float = 0.0):
        self._scene = scene
        self._physics = physics
        self._size = size
        self._radius = layout.asteroid_radii[size]
        self._w = layout.w
        self._h = layout.h
        self._spin = random.uniform(-1.5, 1.5)
        self._rot = random.uniform(0, math.tau)
        self.alive = True

        num_verts = random.randint(8, 12)
        self._points = _generate_polygon_points(self._radius, num_verts)

        # pymunk
        self._body = pymunk.Body(mass=1, moment=float('inf'))
        self._body.position = (x, y)
        if vx == 0.0 and vy == 0.0:
            angle = random.uniform(0, math.tau)
            speed = layout.asteroid_base_speed * random.uniform(0.5, 1.5)
            if size == 'medium':
                speed *= 1.4
            elif size == 'small':
                speed *= 1.8
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
        self._body.velocity = (vx, vy)

        self._pm_shape = pymunk.Circle(self._body, self._radius * 0.85)
        self._pm_shape.elasticity = 0.0
        self._pm_shape.friction = 0.0
        self._pm_shape.collision_type = CT_ASTEROID
        physics.add(self._body, self._pm_shape)

        # thorvg — bloom (15%) + fill (30%) + wide stroke (70%) + core (100%)
        pts = self._points
        self._shp_bloom = Shape()
        _build_asteroid_path(self._shp_bloom, pts)
        self._shp_bloom.set_stroke_width(layout.stroke_bloom)
        self._shp_bloom.set_stroke_color(*COL_ASTEROID, 38)
        self._shp_bloom.set_stroke_join(1)

        self._shp_fill = Shape()
        _build_asteroid_path(self._shp_fill, pts)
        self._shp_fill.set_fill_color(*COL_ASTEROID, 76)

        self._shp_glow = Shape()
        _build_asteroid_path(self._shp_glow, pts)
        self._shp_glow.set_stroke_width(layout.stroke_glow)
        self._shp_glow.set_stroke_color(*COL_ASTEROID, 178)
        self._shp_glow.set_stroke_join(1)

        self._shp_core = Shape()
        _build_asteroid_path(self._shp_core, pts)
        self._shp_core.set_stroke_width(layout.stroke_core)
        self._shp_core.set_stroke_color(*COL_ASTEROID, 255)
        self._shp_core.set_stroke_join(1)

        scene.add(self._shp_bloom)
        scene.add(self._shp_fill)
        scene.add(self._shp_glow)
        scene.add(self._shp_core)

    @property
    def pm_shape(self):
        return self._pm_shape

    @property
    def size(self):
        return self._size

    @property
    def position(self):
        return self._body.position

    @property
    def score(self):
        return ASTEROID_SCORES[self._size]

    def destroy(self):
        if not self.alive:
            return
        self.alive = False
        self._physics.remove(self._pm_shape, self._body)
        self._shp_bloom.reset()
        self._shp_fill.reset()
        self._shp_glow.reset()
        self._shp_core.reset()

    def sync(self, dt: float):
        if not self.alive:
            return

        self._rot += self._spin * dt

        x, y = self._body.position
        x = x % self._w
        y = y % self._h
        self._body.position = (x, y)

        cos_a = math.cos(self._rot)
        sin_a = math.sin(self._rot)
        m = Matrix()
        m.e11 = cos_a
        m.e12 = -sin_a
        m.e21 = sin_a
        m.e22 = cos_a
        m.e13 = x
        m.e23 = y
        self._shp_bloom.set_transform(m)
        self._shp_fill.set_transform(m)
        self._shp_glow.set_transform(m)
        self._shp_core.set_transform(m)

    def split(self, scene: Scene, physics: Physics, layout: Layout) -> list:
        if self._size == 'small':
            return []
        next_size = 'medium' if self._size == 'large' else 'small'
        x, y = self._body.position
        children = []
        for _ in range(2):
            offset_angle = random.uniform(0, math.tau)
            offset = self._radius * 0.3
            nx = x + math.cos(offset_angle) * offset
            ny = y + math.sin(offset_angle) * offset
            child = Asteroid(scene, physics, nx, ny, next_size, layout)
            children.append(child)
        return children


class AsteroidField:
    """Manages all asteroids in play."""

    def __init__(self, scene: Scene, physics: Physics, layout: Layout):
        self._scene = scene
        self._physics = physics
        self._asteroids: list[Asteroid] = []
        self._lookup: dict = {}

    def spawn_wave(self, layout: Layout, count: int):
        for _ in range(count):
            edge = random.randint(0, 3)
            if edge == 0:
                x, y = random.uniform(0, layout.w), 0
            elif edge == 1:
                x, y = layout.w, random.uniform(0, layout.h)
            elif edge == 2:
                x, y = random.uniform(0, layout.w), layout.h
            else:
                x, y = 0, random.uniform(0, layout.h)
            ast = Asteroid(self._scene, self._physics, x, y, 'large', layout)
            self._asteroids.append(ast)
            self._lookup[ast.pm_shape] = ast

    def on_hit(self, pm_shape, layout: Layout) -> int:
        ast = self._lookup.get(pm_shape)
        if ast is None or not ast.alive:
            return 0
        score = ast.score
        children = ast.split(self._scene, self._physics, layout)
        ast.destroy()
        del self._lookup[pm_shape]
        for child in children:
            self._asteroids.append(child)
            self._lookup[child.pm_shape] = child
        return score

    def sync(self, dt: float):
        for ast in self._asteroids:
            ast.sync(dt)

    def is_clear(self) -> bool:
        return all(not a.alive for a in self._asteroids)

    def clear_all(self):
        for a in self._asteroids:
            if a.alive:
                a.destroy()
        self._asteroids.clear()
        self._lookup.clear()

    def rebuild(self, layout: Layout):
        self.clear_all()
