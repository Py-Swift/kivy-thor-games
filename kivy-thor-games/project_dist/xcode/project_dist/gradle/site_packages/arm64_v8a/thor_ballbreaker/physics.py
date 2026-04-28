import pymunk

from .constants import CT_BALL, CT_BRICK, CT_BOTTOM


class Physics:
    """Thin wrapper around pymunk.Space with collision callback routing."""

    def __init__(self, on_brick_hit, on_ball_lost):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self._on_brick_hit = on_brick_hit
        self._on_ball_lost = on_ball_lost
        self._setup_handlers()

    # ── collision handling ────────────────────────────────────────────────────

    def _setup_handlers(self):
        self.space.on_collision(
            collision_type_a=CT_BALL,
            collision_type_b=CT_BRICK,
            begin=self._ball_brick_begin,
        )
        self.space.on_collision(
            collision_type_a=CT_BALL,
            collision_type_b=CT_BOTTOM,
            begin=self._ball_bottom_begin,
        )

    def _ball_brick_begin(self, arbiter, space, data):
        self._on_brick_hit(arbiter, space, data)
        return True

    def _ball_bottom_begin(self, arbiter, space, data):
        self._on_ball_lost(arbiter, space, data)
        return False  # don't process collision physics — ball is "dead"

    # ── helpers ───────────────────────────────────────────────────────────────

    def add(self, *objs):
        self.space.add(*objs)

    def remove(self, *objs):
        for o in objs:
            if o in self.space.shapes or o in self.space.bodies:
                self.space.remove(o)

    def step(self, dt: float):
        self.space.step(dt)
