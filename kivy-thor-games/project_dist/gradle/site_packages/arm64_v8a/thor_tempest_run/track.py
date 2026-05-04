"""
TrackRenderer — neon wireframe cylindrical tunnel.

Draws:
  • N longitudinal lane-edge lines (along +Z, for LANE_COUNT lanes)
  • Rings of cross-section lines every ring_step units ahead of the camera

Three Shape objects (bloom / glow / core) hold all track lines as subpaths.
"""
from __future__ import annotations

import math

from thorvg_cython import Scene, Shape

from .constants import LANE_COUNT, TRACK_COLORS, TRACK_COLOR_DIST, Layout
from .projection import Camera3D, ring_point


def _pick_color(z: float) -> tuple[int, int, int]:
    idx = int(z / TRACK_COLOR_DIST) % len(TRACK_COLORS)
    return TRACK_COLORS[idx]


class TrackRenderer(Scene):
    """Renders the neon cylinder tunnel."""

    def __init__(self, layout: Layout) -> None:
        super().__init__()
        self._lo = layout
        self._bloom = Shape()
        self._glow  = Shape()
        self._core  = Shape()
        self.add(self._bloom)
        self.add(self._glow)
        self.add(self._core)

    def sync(self, camera: Camera3D, player_z: float) -> None:
        lo = self._lo
        w, h = lo.w, lo.h
        n = LANE_COUNT
        rot = camera.rotation
        z_near = player_z
        z_far  = player_z + lo.track_depth
        r, g, b = _pick_color(player_z)

        for shp, sw, a in (
            (self._bloom, lo.stroke_bloom, 38),
            (self._glow,  lo.stroke_glow,  178),
            (self._core,  lo.stroke_core,  255),
        ):
            shp.reset()

            # longitudinal lines (lane edges running forward)
            for lane in range(n):
                p1 = camera.project(*ring_point(lane, n, lo.track_radius, z_near, rot), w, h)
                p2 = camera.project(*ring_point(lane, n, lo.track_radius, z_far,  rot), w, h)
                if p1 is not None and p2 is not None:
                    shp.move_to(p1[0], p1[1])
                    shp.line_to(p2[0], p2[1])

            # ring lines (cross-section circles)
            ring_z = math.ceil(z_near / lo.ring_step) * lo.ring_step
            while ring_z <= z_far:
                for lane in range(n):
                    rp1 = camera.project(*ring_point(lane,     n, lo.track_radius, ring_z, rot), w, h)
                    rp2 = camera.project(*ring_point(lane + 1, n, lo.track_radius, ring_z, rot), w, h)
                    if rp1 is not None and rp2 is not None:
                        shp.move_to(rp1[0], rp1[1])
                        shp.line_to(rp2[0], rp2[1])
                ring_z += lo.ring_step

            shp.set_stroke_width(sw)
            shp.set_stroke_color(r, g, b, a)

    def rebuild(self, layout: Layout) -> None:
        self._lo = layout
