import pymunk

from .constants import CT_WALL, CT_FLOOR, Layout
from .physics import Physics


class Walls:
    """Invisible boundary walls around the board — contain debris briefly."""

    def __init__(self, physics: Physics, layout: Layout):
        self._segments = []
        self._physics = physics
        self._build(layout)

    def rebuild(self, layout: Layout):
        self._teardown()
        self._build(layout)

    def _build(self, lo: Layout):
        sb = self._physics.space.static_body
        bx, by = lo.board_x, lo.board_y
        bw, bh = lo.board_w, lo.board_h

        segs = [
            pymunk.Segment(sb, (bx, by), (bx, by + bh), 1),           # left
            pymunk.Segment(sb, (bx + bw, by), (bx + bw, by + bh), 1), # right
        ]
        for s in segs:
            s.elasticity = 0.3
            s.friction = 0.5
            s.collision_type = CT_WALL

        floor = pymunk.Segment(sb, (bx, by + bh), (bx + bw, by + bh), 1)
        floor.elasticity = 0.3
        floor.friction = 0.8
        floor.collision_type = CT_FLOOR
        segs.append(floor)

        self._physics.add(*segs)
        self._segments = segs

    def _teardown(self):
        if self._segments:
            self._physics.remove(*self._segments)
            self._segments.clear()
