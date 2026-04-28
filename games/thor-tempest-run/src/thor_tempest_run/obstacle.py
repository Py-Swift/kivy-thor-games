"""
Obstacle types — Spike, Enemy, Wall — and ObstacleField (procedural grid).

Inspired by and adapted from:
  pygame-summer-team-jam  (David Pendergast et al.)
  https://github.com/davidpendergast/pygame-summer-team-jam
  Original pygame/OpenCV implementation; ported to thorvg-cython/pymunk.
"""
from __future__ import annotations

import math
import random
from typing import NamedTuple

from thorvg_cython import Scene, Shape

from .constants import (
    LANE_COUNT, CELL_LENGTH, SPEED_CURVE,
    COL_SPIKE, COL_ENEMY, COL_WALL,
    PM_RUN, PM_JUMP, PM_SLIDE,
    Layout,
)
from .projection import Camera3D, ring_point


# ── 3-D model vertices (normalised, Z = 0 = front face) ──────────────────────

def _spike_segments() -> list[tuple]:
    """Sawtooth silhouette (x, y pairs → line segments)."""
    ys = 0.2  # spike height
    pts = [
        (-1.0, 0.0), (-0.8, ys), (-0.4, 0.0),
        (0.0,  ys),  (0.4, 0.0), (0.8, ys), (1.0, 0.0),
    ]
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


def _enemy_segments() -> list[tuple]:
    """Simple rectangular ghost-like silhouette."""
    bl = (-0.5, 0.05); br = (0.5, 0.05)
    tl = (-0.5, 0.30); tr = (0.5, 0.30)
    le = ((-0.4, 0.24), (-0.1, 0.20))
    re = ((0.4,  0.24), (0.1,  0.20))
    mo = ((-0.4, 0.12), (0.4,  0.12))
    return [(bl, br), (br, tr), (tr, tl), (tl, bl), le, re, mo]


def _wall_segments() -> list[tuple]:
    """Filled rectangle with X cross."""
    h = 0.50
    l1 = (-1.0, 0.0); l2 = (-1.0, h)
    r1 = (1.0,  0.0); r2 = (1.0,  h)
    return [
        (l1, l2), (l2, r2), (r2, r1), (r1, l1),
        (l1, r2), (l2, r1),
    ]


# ── helpers ───────────────────────────────────────────────────────────────────

def _project_obstacle_lines(
    segments: list[tuple],
    lane: int, z_center: float, rotation: float,
    total_lanes: int, radius: float,
    camera: Camera3D, sw: float, sh: float,
) -> list[tuple[float, float, float, float]]:
    """Project each obstacle segment onto the lane face surface.

    Model coordinate convention (matches align_shape_to_level_surface):
      x ∈ [-1, 1] → left-to-right across the lane face
      y ∈ [0, 1]  → from the outer chord surface toward the cylinder axis

    The transform:
      world = left + horz*(right - left) + y*(axis - face_centre)
    where horz = (x + 1) / 2  and face_centre = midpoint(left, right).
    """
    lx, ly, _ = ring_point(lane - 1, total_lanes, radius, z_center, rotation)
    rx, ry, _ = ring_point(lane,     total_lanes, radius, z_center, rotation)
    bx = (lx + rx) * 0.5   # face chord centre (on the polygon face)
    by = (ly + ry) * 0.5
    # inward vector: from face chord centre toward the cylinder axis (0, 0)
    inx = -bx
    iny = -by

    out = []
    for (x1, y1), (x2, y2) in segments:
        h1 = (x1 + 1.0) * 0.5
        h2 = (x2 + 1.0) * 0.5
        wx1 = lx + h1 * (rx - lx) + y1 * inx
        wy1 = ly + h1 * (ry - ly) + y1 * iny
        wx2 = lx + h2 * (rx - lx) + y2 * inx
        wy2 = ly + h2 * (ry - ly) + y2 * iny
        p1 = camera.project(wx1, wy1, z_center, sw, sh)
        p2 = camera.project(wx2, wy2, z_center, sw, sh)
        if p1 and p2:
            out.append((p1[0], p1[1], p2[0], p2[1]))
    return out


class Obstacle(Scene):
    """Base class for all obstacles."""

    # Subclasses set these:
    _CAN_JUMP  : bool = False
    _CAN_SLIDE : bool = False
    _COLOR     : tuple[int, int, int] = (255, 255, 255)
    _SEGMENTS  : list[tuple] = []
    DEATH_MSG  : str = "avoid obstacles!"
    JUMP_CLEAR : float = 0.1  # normalised player Y that clears this obstacle

    def __init__(self, lane: int, z: float, length: float, layout: Layout) -> None:
        super().__init__()
        self.lane   = lane
        self.z      = z
        self.length = length
        self._alive = True
        self._bloom = Shape()
        self._glow  = Shape()
        self._core  = Shape()
        self.add(self._bloom)
        self.add(self._glow)
        self.add(self._core)
        self._lo    = layout

    @property
    def alive(self) -> bool:
        return self._alive

    def can_jump_over(self) -> bool:
        return self._CAN_JUMP

    def can_slide_through(self) -> bool:
        return self._CAN_SLIDE

    def kill(self) -> None:
        self._alive = False
        self.set_opacity(0)

    def sync(self, camera: Camera3D, rotation: float) -> None:
        if not self._alive:
            return
        lo = self._lo
        lines = _project_obstacle_lines(
            self._SEGMENTS, self.lane, self.z + self.length * 0.5, rotation,
            LANE_COUNT, lo.track_radius,
            camera, lo.w, lo.h,
        )
        r, g, b = self._COLOR
        for shp, sw, a in (
            (self._bloom, lo.stroke_bloom, 38),
            (self._glow,  lo.stroke_glow,  178),
            (self._core,  lo.stroke_core,  255),
        ):
            shp.reset()
            for x1, y1, x2, y2 in lines:
                shp.move_to(x1, y1)
                shp.line_to(x2, y2)
            shp.set_stroke_width(sw)
            shp.set_stroke_color(r, g, b, a)

    def remove_from(self, scene: Scene) -> None:
        self.set_opacity(0)


class Spike(Obstacle):
    _CAN_JUMP  = True
    _CAN_SLIDE = False
    _COLOR     = COL_SPIKE
    _SEGMENTS  = _spike_segments()
    DEATH_MSG  = "jump over spikes!"
    JUMP_CLEAR = 0.1


class Enemy(Obstacle):
    _CAN_JUMP  = False
    _CAN_SLIDE = True
    _COLOR     = COL_ENEMY
    _SEGMENTS  = _enemy_segments()
    DEATH_MSG  = "slide through enemies!"
    JUMP_CLEAR = 999.0  # can never jump over


class Wall(Obstacle):
    _CAN_JUMP  = False
    _CAN_SLIDE = False
    _COLOR     = COL_WALL
    _SEGMENTS  = _wall_segments()
    DEATH_MSG  = "avoid walls!"
    JUMP_CLEAR = 999.0


# ── speed curve helper ───────────────────────────────────────────────────────

def _lerp(t: float, a: float, b: float) -> float:
    return a + t * (b - a)


def get_speed(z: float) -> float:
    """Return player forward speed (track units/s) at position z."""
    if z <= SPEED_CURVE[0][0]:
        return SPEED_CURVE[0][1]
    if z >= SPEED_CURVE[-1][0]:
        return SPEED_CURVE[-1][1]
    for i in range(1, len(SPEED_CURVE)):
        z1, s1 = SPEED_CURVE[i - 1]
        z2, s2 = SPEED_CURVE[i]
        if z1 <= z <= z2:
            return _lerp((z - z1) / (z2 - z1), s1, s2)
    return SPEED_CURVE[-1][1]


# ── obstacle field ────────────────────────────────────────────────────────────

_OBSTACLE_TYPES = [Spike, Enemy, Wall]
_WEIGHTS        = [0.45,  0.40, 0.15]  # spawn probability


def _weighted_choice() -> type[Obstacle]:
    r = random.random()
    cum = 0.0
    for cls, w in zip(_OBSTACLE_TYPES, _WEIGHTS):
        cum += w
        if r < cum:
            return cls
    return Spike


class ObstacleField:
    """Procedurally generates and despawns obstacles.

    Mirrors the InfiniteGeneratingLevel cell-grid from the original pygame code.
    """

    def __init__(self, scene: Scene, layout: Layout) -> None:
        self._scene  = scene
        self._lo     = layout
        # (lane, cell_idx) → Obstacle
        self._grid: dict[tuple[int, int], Obstacle] = {}
        self._loaded_range: list[int] | None = None  # [cell_start, cell_end]

    # ── public API ────────────────────────────────────────────────────────────

    def update_and_sync(self, camera: Camera3D, rotation: float,
                        player_z: float) -> None:
        """Load/unload cells relative to player_z, then sync all visuals."""
        z_near = player_z - CELL_LENGTH
        z_far  = player_z + self._lo.track_depth + CELL_LENGTH * 2

        cell_near = int(z_near / CELL_LENGTH)
        cell_far  = int(z_far  / CELL_LENGTH) + 1

        self._load(cell_near, cell_far)
        self._unload(cell_near)

        for obs in list(self._grid.values()):
            obs.sync(camera, rotation)

    def obstacles_in_range(self, lane: int, z_start: float, z_end: float
                           ) -> list[Obstacle]:
        """Return all live obstacles in `lane` whose Z range overlaps [z_start, z_end]."""
        out = []
        for obs in self._grid.values():
            if obs.lane != lane or not obs.alive:
                continue
            if obs.z + obs.length < z_start:
                continue
            if obs.z > z_end:
                continue
            out.append(obs)
        return out

    def rebuild(self, layout: Layout) -> None:
        self._lo = layout

    # ── internals ────────────────────────────────────────────────────────────

    def _load(self, cell_near: int, cell_far: int) -> None:
        if self._loaded_range is None:
            self._loaded_range = [cell_near, cell_far]
        else:
            cell_near = min(cell_near, self._loaded_range[0])
            cell_far  = max(cell_far,  self._loaded_range[1])

        for cell_idx in range(cell_near, cell_far):
            for lane in range(LANE_COUNT):
                key = (lane, cell_idx)
                if key in self._grid:
                    continue
                obs = self._generate(lane, cell_idx)
                if obs is not None:
                    self._grid[key] = obs

        self._loaded_range = [cell_near, cell_far]

    def _unload(self, cell_near: int) -> None:
        to_del = [k for k in self._grid if k[1] < cell_near - 2]
        for k in to_del:
            self._grid[k].remove_from(self._scene)
            del self._grid[k]

    def _generate(self, lane: int, cell_idx: int) -> Obstacle | None:
        # Don't spawn anything in the first few cells so player has time to react
        if cell_idx < 3:
            return None

        rng = random.Random(cell_idx * 31337 + lane * 997)
        if rng.random() > 0.35:
            return None  # ~65% of cells are empty

        # Don't put obstacles in the same cell across all lanes simultaneously
        # (would be unavoidable); allow at most LANE_COUNT-1 lanes to be blocked.
        blocked = sum(
            1 for l in range(LANE_COUNT)
            if (l, cell_idx) in self._grid
        )
        if blocked >= LANE_COUNT - 1:
            return None

        z = cell_idx * CELL_LENGTH
        length = CELL_LENGTH * 0.7
        cls = _weighted_choice()
        obs = cls(lane, z, length, self._lo)
        self._scene.add(obs)
        return obs
