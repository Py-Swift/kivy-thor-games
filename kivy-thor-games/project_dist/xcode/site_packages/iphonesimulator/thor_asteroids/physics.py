import pymunk

from .constants import CT_SHIP, CT_ASTEROID, CT_BULLET


class Physics:
    """Thin wrapper around pymunk.Space with collision callback routing."""

    def __init__(self, on_bullet_hit_asteroid, on_ship_hit_asteroid):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self._on_bullet_hit = on_bullet_hit_asteroid
        self._on_ship_hit = on_ship_hit_asteroid
        self._setup_handlers()

    def _setup_handlers(self):
        self.space.on_collision(
            collision_type_a=CT_BULLET,
            collision_type_b=CT_ASTEROID,
            begin=self._bullet_asteroid_begin,
        )
        self.space.on_collision(
            collision_type_a=CT_SHIP,
            collision_type_b=CT_ASTEROID,
            begin=self._ship_asteroid_begin,
        )

    def _bullet_asteroid_begin(self, arbiter, space, data):
        self._on_bullet_hit(arbiter, space, data)
        return False  # don't process physics bounce

    def _ship_asteroid_begin(self, arbiter, space, data):
        self._on_ship_hit(arbiter, space, data)
        return False

    def add(self, *objs):
        self.space.add(*objs)

    def remove(self, *objs):
        for o in objs:
            if o in self.space.shapes or o in self.space.bodies:
                self.space.remove(o)

    def step(self, dt: float):
        self.space.step(dt)
