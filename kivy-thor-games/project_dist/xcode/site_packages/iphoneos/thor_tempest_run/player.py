"""
Player — wireframe model + jump arc.

The player's X position is lane-based (discrete snapping to lane centres on
the cylinder surface).  Y is driven by a simple numeric integrator (no
pymunk body, for simplicity and iOS compatibility) — same math as the
original pygame player2d.py.

Wireframe data adapted from assets by David Pendergast et al.
(pygame-summer-team-jam) — used as inspiration and ported to thorvg-cython.
"""
from __future__ import annotations

import math

from thorvg_cython import Scene, Shape, Matrix

from .constants import (
    LANE_COUNT, PM_RUN, PM_JUMP, PM_SLIDE,
    JUMP_FALL_RATE, JUMP_BOOST, JUMP_FAST_FALL,
    COL_PLAYER, Layout,
)
from .projection import Camera3D


# ─────────────────────────────────────────────────────────────────────────────
# Pose classes — each owns its shapes, hardcoded at construction, never rebuilt
# ─────────────────────────────────────────────────────────────────────────────

class RunShapes(Scene):
    def __init__(self, lo: Layout) -> None:
        super().__init__()
        r, g, b = COL_PLAYER
        self._bloom = Shape()
        self._glow  = Shape()
        self._core  = Shape()
        for shp, sw, a in (
            (self._bloom, lo.stroke_bloom, 38),
            (self._glow,  lo.stroke_glow,  178),
            (self._core,  lo.stroke_core,  255),
        ):
            shp.move_to(-0.0833, 1.0   )
            shp.line_to( 0.0,    1.0   )
            shp.move_to(-0.0833, 1.0   )
            shp.line_to(-0.1667, 0.9677)
            shp.move_to(-0.1667, 0.9677)
            shp.line_to(-0.1667, 0.9355)
            shp.move_to(-0.1667, 0.9355)
            shp.line_to(-0.0833, 0.9032)
            shp.move_to(-0.0833, 0.9032)
            shp.line_to(-0.3333, 0.871 )
            shp.move_to(-0.4167, 0.8065)
            shp.line_to(-0.5,    0.6774)
            shp.move_to(-0.5,    0.6774)
            shp.line_to(-0.3333, 0.6129)
            shp.move_to(-0.3333, 0.8065)
            shp.line_to(-0.4167, 0.6774)
            shp.move_to(-0.25,   0.8065)
            shp.line_to(-0.0833, 0.6774)
            shp.move_to( 0.0,    0.6452)
            shp.line_to(-0.25,   0.5806)
            shp.move_to(-0.25,   0.5806)
            shp.line_to(-0.25,   0.5161)
            shp.move_to(-0.25,   0.3226)
            shp.line_to(-0.25,   0.2581)
            shp.move_to(-0.25,   0.2581)
            shp.line_to(-0.1667, 0.0323)
            shp.move_to(-0.1667, 0.0323)
            shp.line_to(-0.3333, 0.0   )
            shp.move_to( 0.3333, 0.8387)
            shp.line_to( 0.5,    0.7742)
            shp.move_to( 0.5,    0.7742)
            shp.line_to( 0.5,    0.6774)
            shp.move_to( 0.5,    0.6774)
            shp.line_to( 0.3333, 0.6129)
            shp.move_to( 0.0,    0.5484)
            shp.line_to( 0.0,    0.5161)
            shp.move_to( 0.4167, 0.4516)
            shp.line_to( 0.4167, 0.3548)
            shp.move_to( 0.4167, 0.3548)
            shp.line_to( 0.25,   0.2581)
            shp.move_to( 0.25,   0.2581)
            shp.line_to( 0.0833, 0.2903)
            shp.move_to( 0.25,   0.3548)
            shp.line_to( 0.0,    0.3548)
            shp.move_to( 0.0,    0.3548)
            shp.line_to( 0.0833, 0.2581)
            shp.move_to( 0.0833, 0.2581)
            shp.line_to( 0.1667, 0.3548)
            shp.move_to( 0.1667, 0.8387)
            shp.line_to( 0.3333, 0.7742)
            shp.move_to(-0.25,   0.5161)
            shp.line_to(-0.1667, 0.4194)
            shp.move_to(-0.1667, 0.4194)
            shp.line_to(-0.25,   0.3226)
            shp.move_to( 0.3333, 0.5806)
            shp.line_to( 0.3333, 0.5161)
            shp.move_to( 0.3333, 0.5161)
            shp.line_to( 0.4167, 0.4516)
            shp.move_to( 0.0,    1.0   )
            shp.line_to( 0.4167, 0.9677)
            shp.set_stroke_width(sw)
            shp.set_stroke_color(r, g, b, a)
            self.add(shp)
        self.set_opacity(0)

    def place(self, sx: float, sy: float, pw: float, ph: float, jump_y: float) -> None:
        m = Matrix()
        m.e11 = pw
        m.e22 = -ph
        m.e13 = sx
        m.e23 = sy - jump_y * ph * 2.0
        self.set_transform(m)
        self.set_opacity(255)

    def hide(self) -> None:
        self.set_opacity(0)


class JumpShapes(Scene):
    def __init__(self, lo: Layout) -> None:
        super().__init__()
        r, g, b = COL_PLAYER
        self._bloom = Shape()
        self._glow  = Shape()
        self._core  = Shape()
        for shp, sw, a in (
            (self._bloom, lo.stroke_bloom, 38),
            (self._glow,  lo.stroke_glow,  178),
            (self._core,  lo.stroke_core,  255),
        ):
            shp.move_to(-0.0714, 1.0   )
            shp.line_to(-0.1429, 1.0   )
            shp.move_to(-0.1429, 1.0   )
            shp.line_to(-0.2143, 0.9565)
            shp.move_to(-0.2143, 0.9565)
            shp.line_to(-0.2143, 0.8696)
            shp.move_to(-0.2143, 0.8696)
            shp.line_to(-0.1429, 0.8696)
            shp.move_to(-0.1429, 0.8696)
            shp.line_to(-0.1429, 0.8261)
            shp.move_to(-0.1429, 0.8261)
            shp.line_to(-0.2143, 0.7826)
            shp.move_to(-0.2143, 0.7826)
            shp.line_to(-0.2857, 0.7826)
            shp.move_to(-0.2857, 0.7826)
            shp.line_to(-0.4286, 0.6957)
            shp.move_to(-0.4286, 0.6957)
            shp.line_to(-0.5,    0.7391)
            shp.move_to(-0.5,    0.7391)
            shp.line_to(-0.5,    0.7826)
            shp.move_to(-0.5,    0.7826)
            shp.line_to(-0.3571, 0.8696)
            shp.move_to(-0.0714, 1.0   )
            shp.line_to( 0.0,    0.9565)
            shp.move_to( 0.0,    0.7826)
            shp.line_to( 0.1429, 0.7826)
            shp.move_to( 0.1429, 0.7391)
            shp.line_to( 0.5,    0.7391)
            shp.move_to( 0.5,    0.7826)
            shp.line_to( 0.5,    0.7391)
            shp.move_to( 0.5,    0.7826)
            shp.line_to( 0.3571, 0.8696)
            shp.move_to(-0.2857, 0.6957)
            shp.line_to(-0.1429, 0.4348)
            shp.move_to( 0.2143, 0.6522)
            shp.line_to( 0.1429, 0.6087)
            shp.move_to( 0.1429, 0.6087)
            shp.line_to( 0.0714, 0.4348)
            shp.move_to(-0.1429, 0.4348)
            shp.line_to(-0.2857, 0.3478)
            shp.move_to(-0.2857, 0.3478)
            shp.line_to(-0.2857, 0.2174)
            shp.move_to(-0.2143, 0.2609)
            shp.line_to(-0.0714, 0.2609)
            shp.move_to(-0.0714, 0.2609)
            shp.line_to(-0.1429, 0.087 )
            shp.move_to(-0.1429, 0.087 )
            shp.line_to(-0.2857, 0.2174)
            shp.move_to( 0.0714, 0.4348)
            shp.line_to( 0.2143, 0.2174)
            shp.move_to( 0.2143, 0.2174)
            shp.line_to( 0.2143, 0.087 )
            shp.move_to( 0.2143, 0.087 )
            shp.line_to( 0.1429, 0.0435)
            shp.move_to( 0.1429, 0.0435)
            shp.line_to( 0.2143, 0.0   )
            shp.move_to( 0.2143, 0.0   )
            shp.line_to( 0.0,    0.0   )
            shp.move_to( 0.0,    0.0   )
            shp.line_to( 0.0714, 0.0435)
            shp.move_to( 0.0714, 0.0435)
            shp.line_to(-0.0714, 0.2609)
            shp.move_to(-0.1429, 0.4348)
            shp.line_to( 0.0714, 0.4348)
            shp.set_stroke_width(sw)
            shp.set_stroke_color(r, g, b, a)
            self.add(shp)
        self.set_opacity(0)

    def place(self, sx: float, sy: float, pw: float, ph: float, jump_y: float) -> None:
        m = Matrix()
        m.e11 = pw
        m.e22 = -ph
        m.e13 = sx
        m.e23 = sy - jump_y * ph * 2.0
        self.set_transform(m)
        self.set_opacity(255)

    def hide(self) -> None:
        self.set_opacity(0)


class SlideShapes(Scene):
    def __init__(self, lo: Layout) -> None:
        super().__init__()
        r, g, b = COL_PLAYER
        self._bloom = Shape()
        self._glow  = Shape()
        self._core  = Shape()
        for shp, sw, a in (
            (self._bloom, lo.stroke_bloom, 38),
            (self._glow,  lo.stroke_glow,  178),
            (self._core,  lo.stroke_core,  255),
        ):
            shp.move_to( 0.0,    1.0   )
            shp.line_to( 0.0,    0.8333)
            shp.move_to( 0.0,    0.8333)
            shp.line_to(-0.0714, 0.8333)
            shp.move_to(-0.0714, 0.8333)
            shp.line_to(-0.1429, 0.6667)
            shp.move_to(-0.1429, 0.6667)
            shp.line_to(-0.0714, 0.5   )
            shp.move_to(-0.0714, 0.5   )
            shp.line_to( 0.0,    0.5   )
            shp.move_to( 0.0,    0.5   )
            shp.line_to( 0.0,    0.3333)
            shp.move_to( 0.0,    0.3333)
            shp.line_to( 0.0,    0.5   )
            shp.move_to( 0.0,    0.5   )
            shp.line_to( 0.0714, 0.5   )
            shp.move_to( 0.0714, 0.5   )
            shp.line_to( 0.1429, 0.6667)
            shp.move_to( 0.1429, 0.6667)
            shp.line_to( 0.0714, 0.8333)
            shp.move_to( 0.0714, 0.8333)
            shp.line_to( 0.0,    0.8333)
            shp.move_to(-0.1429, 0.6667)
            shp.line_to(-0.2143, 0.5   )
            shp.move_to(-0.2143, 0.5   )
            shp.line_to(-0.3571, 0.5   )
            shp.move_to(-0.3571, 0.5   )
            shp.line_to(-0.3571, 0.1667)
            shp.move_to(-0.3571, 0.1667)
            shp.line_to(-0.2857, 0.0   )
            shp.move_to(-0.2857, 0.0   )
            shp.line_to( 0.2857, 0.0   )
            shp.move_to( 0.2857, 0.0   )
            shp.line_to( 0.3571, 0.1667)
            shp.move_to( 0.3571, 0.1667)
            shp.line_to( 0.3571, 0.5   )
            shp.move_to( 0.3571, 0.5   )
            shp.line_to( 0.2143, 0.5   )
            shp.move_to( 0.2143, 0.5   )
            shp.line_to( 0.1429, 0.6667)
            shp.move_to( 0.3571, 0.3333)
            shp.line_to( 0.4286, 0.3333)
            shp.move_to( 0.4286, 0.3333)
            shp.line_to( 0.5,    0.6667)
            shp.move_to( 0.5,    0.6667)
            shp.line_to( 0.4286, 0.8333)
            shp.move_to(-0.3571, 0.3333)
            shp.line_to(-0.4286, 0.3333)
            shp.move_to(-0.4286, 0.3333)
            shp.line_to(-0.5,    0.6667)
            shp.move_to(-0.5,    0.6667)
            shp.line_to(-0.4286, 0.8333)
            shp.move_to(-0.2857, 0.5   )
            shp.line_to(-0.2143, 0.8333)
            shp.move_to(-0.1429, 0.6667)
            shp.line_to(-0.2143, 0.8333)
            shp.move_to( 0.1429, 0.6667)
            shp.line_to( 0.2143, 0.8333)
            shp.move_to( 0.2143, 0.8333)
            shp.line_to( 0.2857, 0.5   )
            shp.set_stroke_width(sw)
            shp.set_stroke_color(r, g, b, a)
            self.add(shp)
        self.set_opacity(0)

    def place(self, sx: float, sy: float, pw: float, ph: float, jump_y: float) -> None:
        m = Matrix()
        m.e11 = pw
        m.e22 = -ph
        m.e13 = sx
        m.e23 = sy - jump_y * ph * 2.0
        self.set_transform(m)
        self.set_opacity(255)

    def hide(self) -> None:
        self.set_opacity(0)


# ─────────────────────────────────────────────────────────────────────────────

class Player:
    """Player entity — discrete lane input, numeric jump integrator, neon wireframe."""

    def __init__(self, scene: Scene, layout: Layout) -> None:
        self._lo          = layout
        self.lane: int    = 0
        self._y:   float  = 0.0
        self._dy:  float  = 0.0
        self._mode: int   = PM_RUN
        self._jump_hold: bool = False

        self._run   = RunShapes(layout)
        self._jump  = JumpShapes(layout)
        self._slide = SlideShapes(layout)
        scene.add(self._run)
        scene.add(self._jump)
        scene.add(self._slide)

    # ── public properties ─────────────────────────────────────────────────────

    @property
    def normalised_y(self) -> float:
        return self._y

    @property
    def mode(self) -> int:
        return self._mode

    # ── input ─────────────────────────────────────────────────────────────────

    def move_left(self) -> None:
        self.lane = (self.lane - 1) % LANE_COUNT

    def move_right(self) -> None:
        self.lane = (self.lane + 1) % LANE_COUNT

    def jump(self) -> None:
        if self._mode != PM_JUMP:
            self._mode = PM_JUMP
            self._dy = 5.0
            self._jump_hold = True

    def release_jump(self) -> None:
        self._jump_hold = False

    def slide(self) -> None:
        if self._mode == PM_RUN:
            self._mode = PM_SLIDE

    def run(self) -> None:
        if self._mode == PM_SLIDE:
            self._mode = PM_RUN

    # ── update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._y > 0.0 or self._dy != 0.0:
            fall = JUMP_FALL_RATE
            if self._jump_hold and self._mode == PM_JUMP:
                fall -= JUMP_BOOST
            if self._mode == PM_SLIDE:
                fall += JUMP_FAST_FALL
            self._dy -= fall * dt
        self._y += self._dy * dt
        if self._y <= 0.0:
            self._y  = 0.0
            self._dy = 0.0
            if self._mode == PM_JUMP:
                self._mode = PM_RUN

    # ── sync ──────────────────────────────────────────────────────────────────

    def sync(self, camera: Camera3D, rotation: float, player_z: float) -> None:
        lo  = self._lo
        # Use lane face-centre angle (midpoint between vertex lane-1 and lane)
        face_ang = math.radians((self.lane - 0.5) * (360.0 / LANE_COUNT) + rotation)
        sp = camera.project(
            lo.track_radius * math.cos(face_ang),
            lo.track_radius * math.sin(face_ang),
            player_z, lo.w, lo.h,
        )

        if sp is None or self._mode != PM_RUN:
            self._run.hide()
        if sp is None or self._mode != PM_JUMP:
            self._jump.hide()
        if sp is None or self._mode != PM_SLIDE:
            self._slide.hide()

        if sp is not None:
            pw, ph = lo.player_w, lo.player_h
            if self._mode == PM_RUN:
                self._run.place(sp[0], sp[1], pw, ph, self._y)
            elif self._mode == PM_JUMP:
                self._jump.place(sp[0], sp[1], pw, ph, self._y)
            else:
                self._slide.place(sp[0], sp[1], pw, ph, self._y)

    # ── rebuild (on resize) ───────────────────────────────────────────────────

    def rebuild(self, scene: Scene, layout: Layout) -> None:
        self._run.hide()
        self._jump.hide()
        self._slide.hide()
        self._lo    = layout
        self._run   = RunShapes(layout)
        self._jump  = JumpShapes(layout)
        self._slide = SlideShapes(layout)
        scene.add(self._run)
        scene.add(self._jump)
        scene.add(self._slide)
