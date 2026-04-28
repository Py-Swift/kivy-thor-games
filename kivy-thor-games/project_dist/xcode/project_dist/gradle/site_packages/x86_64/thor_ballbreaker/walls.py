import pymunk

from .constants import CT_WALL, CT_BOTTOM, Layout
from .physics import Physics


class Walls:
    """Invisible boundary walls (left, top, right) + bottom sensor."""

    def __init__(self, physics: Physics, layout: Layout):
        self._segments = []
        self._physics = physics
        self._build(layout)

    def rebuild(self, layout: Layout):
        self._teardown()
        self._build(layout)

    def _build(self, lo: Layout):
        sb = self._physics.space.static_body
        segs = [
            pymunk.Segment(sb, (0, 0), (0, lo.h), 1),           # left
            pymunk.Segment(sb, (0, 0), (lo.w, 0), 1),           # top
            pymunk.Segment(sb, (lo.w, 0), (lo.w, lo.h), 1),     # right
        ]
        for s in segs:
            s.elasticity = 1.0
            s.friction = 0.0
            s.collision_type = CT_WALL

        bottom = pymunk.Segment(sb, (0, lo.h + 40), (lo.w, lo.h + 40), 1)
        bottom.sensor = True
        bottom.collision_type = CT_BOTTOM
        segs.append(bottom)

        self._physics.add(*segs)
        self._segments = segs

    def _teardown(self):
        if self._segments:
            self._physics.remove(*self._segments)
            self._segments.clear()
