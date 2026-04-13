import math
import random

import pymunk
from thorvg_cython import Shape, Scene, LinearGradient, ColorStop, Matrix

from .constants import (
    CT_BRICK, BRICK_ROW_COLORS, Layout,
)
from .physics import Physics


def _clamp(v):
    return max(0, min(255, int(v)))


def _brighten(col, amt=60):
    return (_clamp(col[0] + amt), _clamp(col[1] + amt), _clamp(col[2] + amt))


def _darken(col, amt=60):
    return (_clamp(col[0] - amt), _clamp(col[1] - amt), _clamp(col[2] - amt))


class Brick:
    """Single brick — 3D gem-cut look with beveled polygon facets."""

    def __init__(self, scene: Scene, physics: Physics,
                 cx: float, cy: float, w: float, h: float,
                 health: int, row: int):
        self._scene = scene
        self._physics = physics
        self._w = w
        self._h = h
        self._row = row
        self._cx = cx
        self._cy = cy
        self.health = health
        self._max_health = health
        self.alive = True
        self._dissolving = False
        self._dissolve_t = 0.0
        self._glow_phase = random.random() * math.tau  # random start offset
        self._hit_flash = 0.0  # remaining hit-glow time

        # pymunk
        self._body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self._body.position = (cx, cy)
        self._pm_shape = pymunk.Poly.create_box(self._body, (w, h))
        self._pm_shape.elasticity = 1.0
        self._pm_shape.friction = 0.0
        self._pm_shape.collision_type = CT_BRICK
        physics.add(self._body, self._pm_shape)

        # 6 shapes: dark, left facet, right facet, top face, specular, hit-glow
        self._shp_dark = Shape()
        self._shp_left = Shape()
        self._shp_right = Shape()
        self._shp_face = Shape()
        self._shp_spec = Shape()
        self._shp_hit = Shape()
        self._draw(cx, cy)
        scene.add(self._shp_dark)
        scene.add(self._shp_left)
        scene.add(self._shp_right)
        scene.add(self._shp_face)
        scene.add(self._shp_spec)
        scene.add(self._shp_hit)

    @property
    def pm_shape(self):
        return self._pm_shape

    def _base_color(self):
        return BRICK_ROW_COLORS[self._row % len(BRICK_ROW_COLORS)]

    def _draw(self, cx: float, cy: float):
        w, h = self._w, self._h
        hw, hh = w / 2, h / 2
        b = max(h * 0.28, 3)  # bevel depth

        base = self._base_color()
        if self.health < self._max_health:
            gray = sum(base) // 3
            base = (
                _clamp((base[0] + gray) // 2),
                _clamp((base[1] + gray) // 2),
                _clamp((base[2] + gray) // 2),
            )

        top = _brighten(base, 70)
        hi = _brighten(base, 35)
        lo = _darken(base, 50)
        dark = _darken(base, 90)

        m = Matrix()
        m.e13 = cx
        m.e23 = cy

        # 1. Full dark rect (bottom-right shadow base)
        self._shp_dark.reset()
        self._shp_dark.append_rect(-hw, -hh, w, h)
        self._shp_dark.set_fill_color(*dark, 255)
        self._shp_dark.set_transform(m)

        # 2. Left facet trapezoid: bright left bevel
        #    outer-TL → inner-TL → inner-BL → outer-BL
        self._shp_left.reset()
        self._shp_left.move_to(-hw, -hh)
        self._shp_left.line_to(-hw + b, -hh + b)
        self._shp_left.line_to(-hw + b, hh - b)
        self._shp_left.line_to(-hw, hh)
        self._shp_left.close()
        self._shp_left.set_fill_color(*hi, 255)
        self._shp_left.set_transform(m)

        # 3. Right facet trapezoid: darker right bevel
        #    outer-TR → outer-BR → inner-BR → inner-TR
        self._shp_right.reset()
        self._shp_right.move_to(hw, -hh)
        self._shp_right.line_to(hw, hh)
        self._shp_right.line_to(hw - b, hh - b)
        self._shp_right.line_to(hw - b, -hh + b)
        self._shp_right.close()
        self._shp_right.set_fill_color(*lo, 255)
        self._shp_right.set_transform(m)

        # 4. Top face (inner inset rect) with gradient
        self._shp_face.reset()
        self._shp_face.append_rect(-hw + b, -hh + b, w - 2 * b, h - 2 * b)
        lg = LinearGradient()
        lg.set(0, -hh + b, 0, hh - b)
        lg.set_color_stops([
            ColorStop(0.0, *top, 255),
            ColorStop(0.45, *base, 255),
            ColorStop(1.0, *_darken(base, 20), 255),
        ])
        self._shp_face.set_gradient(lg)
        self._shp_face.set_transform(m)

        # 5. Specular highlight — redrawn each frame with pulsing glow
        self._spec_bevel = b
        self._spec_hw = hw
        self._spec_hh = hh
        self._spec_w = w
        self._spec_h = h
        self._spec_m = m
        self._spec_base = base
        spec_h = max(b * 0.6, 2)
        self._shp_spec.reset()
        self._shp_spec.append_rect(-hw + b + 2, -hh + b + 1, w - 2 * b - 4, spec_h)
        self._shp_spec.set_fill_color(255, 255, 255, 90)
        self._shp_spec.set_transform(m)

    HIT_FLASH_DUR = 0.3

    def hit(self) -> bool:
        self.health -= 1
        self._hit_flash = self.HIT_FLASH_DUR
        if self.health <= 0:
            self.destroy()
            return True
        cx, cy = self._body.position
        self._draw(cx, cy)
        return False

    def destroy(self):
        if not self.alive:
            return
        self.alive = False
        self._physics.remove(self._pm_shape, self._body)
        # start dissolve animation
        self._dissolving = True
        self._dissolve_t = 0.0

    DISSOLVE_DUR = 0.6
    GLOW_SPEED = 2.5  # radians per second

    def update(self, dt: float) -> bool:
        """Animate specular glow (alive) or dissolve (dying)."""
        if self._dissolving:
            return self._update_dissolve(dt)
        if self.alive:
            self._glow_phase += dt * self.GLOW_SPEED
            sine = 0.5 + 0.5 * math.sin(self._glow_phase)

            b = self._spec_bevel
            hw, hh = self._spec_hw, self._spec_hh
            w, h = self._spec_w, self._spec_h

            # pulse spec height from thin strip to covering ~60% of face
            base_h = max(b * 0.6, 2)
            max_h = (h - 2 * b) * 0.6
            spec_h = base_h + (max_h - base_h) * sine
            # pulse alpha 30..120
            spec_a = int(30 + 90 * sine)

            self._shp_spec.reset()
            self._shp_spec.append_rect(-hw + b + 2, -hh + b + 1,
                                        w - 2 * b - 4, spec_h)
            self._shp_spec.set_fill_color(255, 255, 255, spec_a)
            self._shp_spec.set_transform(self._spec_m)

            # hit-glow: expanding colored outline that fades
            if self._hit_flash > 0.0:
                self._hit_flash = max(0.0, self._hit_flash - dt)
                t = self._hit_flash / self.HIT_FLASH_DUR
                expand = 4 * (1.0 - t)  # grows outward
                hit_a = int(140 * t)
                base = self._base_color()
                bright = _brighten(base, 100)
                self._shp_hit.reset()
                self._shp_hit.append_rect(
                    -hw - expand, -hh - expand,
                    w + 2 * expand, h + 2 * expand,
                )
                self._shp_hit.set_fill_color(*bright, hit_a)
                self._shp_hit.set_transform(self._spec_m)
            else:
                self._shp_hit.reset()
        return False

    def _update_dissolve(self, dt: float) -> bool:
        self._dissolve_t += dt
        t = min(self._dissolve_t / self.DISSOLVE_DUR, 1.0)

        # ease-out quad
        t2 = 1.0 - (1.0 - t) * (1.0 - t)

        opacity = int(255 * (1.0 - t2))
        scale = 1.0 - t2  # shrink to nothing

        # transform: translate to center then scale
        m = Matrix()
        m.e11 = scale
        m.e22 = scale
        m.e13 = self._cx
        m.e23 = self._cy

        for shp in (self._shp_dark, self._shp_left, self._shp_right,
                     self._shp_face, self._shp_spec):
            shp.set_transform(m)
            shp.set_opacity(opacity)

        # hit-glow: redraw expanding + shrinking with dissolve
        if self._hit_flash > 0.0:
            self._hit_flash = max(0.0, self._hit_flash - dt)
            ht = self._hit_flash / self.HIT_FLASH_DUR
            hw, hh = self._spec_hw, self._spec_hh
            w, h = self._spec_w, self._spec_h
            expand = 6 * (1.0 - ht)
            hit_a = int(160 * ht)
            base = self._base_color()
            bright = _brighten(base, 100)
            self._shp_hit.reset()
            self._shp_hit.append_rect(
                -hw - expand, -hh - expand,
                w + 2 * expand, h + 2 * expand,
            )
            self._shp_hit.set_fill_color(*bright, hit_a)
            self._shp_hit.set_transform(m)
        else:
            self._shp_hit.reset()

        if t >= 1.0:
            self._dissolving = False
            self._shp_dark.reset()
            self._shp_left.reset()
            self._shp_right.reset()
            self._shp_face.reset()
            self._shp_spec.reset()
            self._shp_hit.reset()
            return True
        return False

    def force_clear(self):
        """Immediately remove visuals (for rebuild/teardown)."""
        self._dissolving = False
        if self.alive:
            self._physics.remove(self._pm_shape, self._body)
            self.alive = False
        self._shp_dark.reset()
        self._shp_left.reset()
        self._shp_right.reset()
        self._shp_face.reset()
        self._shp_spec.reset()
        self._shp_hit.reset()


class BrickGrid:
    """Manages the full grid of bricks."""

    def __init__(self, scene: Scene, physics: Physics, layout: Layout):
        self._scene = scene
        self._physics = physics
        self._bricks: list[Brick] = []
        self._dying: list[Brick] = []
        self._lookup: dict = {}  # pymunk.Shape → Brick
        self.populate(layout)

    def populate(self, lo: Layout):
        self._clear_all()
        for row in range(lo.brick_rows):
            for col in range(lo.brick_cols):
                x = lo.brick_margin + col * (lo.brick_w + lo.brick_hgap) + lo.brick_w / 2
                y = lo.brick_top + row * (lo.brick_h + lo.brick_vgap) + lo.brick_h / 2
                hp = 2
                brick = Brick(self._scene, self._physics, x, y,
                              lo.brick_w, lo.brick_h, hp, row)
                self._bricks.append(brick)
                self._lookup[brick.pm_shape] = brick

    def update(self, dt: float):
        """Tick glow + dissolve animations. Call every frame."""
        for brick in self._bricks:
            if brick.alive:
                brick.update(dt)
        still_dying = []
        for brick in self._dying:
            if not brick.update(dt):
                still_dying.append(brick)
        self._dying = still_dying

    def on_hit(self, pm_shape) -> int:
        brick = self._lookup.get(pm_shape)
        if brick is None or not brick.alive:
            return 0
        if brick._hit_flash > 0.0:
            return 0  # already hit this cycle, skip duplicate
        destroyed = brick.hit()
        if destroyed:
            del self._lookup[pm_shape]
            self._dying.append(brick)
            return 10
        return 5

    def is_clear(self) -> bool:
        return all(not b.alive for b in self._bricks)

    def rebuild(self, layout: Layout):
        self._clear_all()
        self.populate(layout)

    def _clear_all(self):
        for b in self._bricks:
            b.force_clear()
        self._bricks.clear()
        self._dying.clear()
        self._lookup.clear()
