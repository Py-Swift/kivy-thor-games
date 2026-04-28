import pymunk

from .constants import GRAVITY


class Physics:
    """pymunk.Space wrapper — only used for the player jump arc and death debris.

    Obstacle collision is handled with pure Z-math in game.py so we don't
    need any pymunk shapes for the lane grid.
    """

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0.0, GRAVITY)

        # ground segment — keeps player body from falling through the floor
        self._ground = pymunk.Segment(
            self.space.static_body,
            (-100_000, 0), (100_000, 0),
            0,
        )
        self._ground.elasticity = 0.0
        self._ground.friction = 0.0
        self.space.add(self._ground)

    def add(self, *objs) -> None:
        self.space.add(*objs)

    def remove(self, *objs) -> None:
        for o in objs:
            if o in self.space.shapes or o in self.space.bodies:
                self.space.remove(o)

    def step(self, dt: float) -> None:
        self.space.step(dt)
