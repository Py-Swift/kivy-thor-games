import pymunk


class Physics:
    """Thin wrapper around pymunk.Space — gravity-driven debris only."""

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 1200)

    def add(self, *objs):
        self.space.add(*objs)

    def remove(self, *objs):
        for o in objs:
            if o in self.space.shapes or o in self.space.bodies:
                self.space.remove(o)

    def step(self, dt: float):
        self.space.step(dt)
