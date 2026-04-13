import random

from thorvg_cython import Scene, Shape, LinearGradient, ColorStop, GlCanvas

from .constants import (
    Layout, COL_BG_TOP, COL_BG_BOT, COL_STAR, LIVES,
    ST_IDLE, ST_PLAYING, ST_GAME_OVER,
)
from .physics import Physics
from .walls import Walls
from .ball import Ball
from .paddle import Paddle
from .brick import BrickGrid
from .hud import Hud


class BallBreakerGame:
    """Main game orchestrator.

    Usage from Kivy::

        game = BallBreakerGame(gl_canvas, w, h)
        Clock.schedule_interval(game.tick, 0)
        # on keyboard → game.key_down(key) / game.key_up(key)
        # on resize   → game.resize(new_w, new_h)
    """

    def __init__(self, canvas: GlCanvas, w: float, h: float):
        self.canvas = canvas
        self._layout = Layout(w, h)

        # root scene (everything lives here)
        self._root = Scene()
        canvas.add(self._root)

        # background
        self._bg = Shape()
        self._root.add(self._bg)
        self._stars: list[Shape] = []
        self._draw_bg(self._layout)

        # game-object scene (layered on top of bg)
        self._game_scene = Scene()
        self._root.add(self._game_scene)

        # state (needed before physics callbacks)
        self._state = ST_IDLE
        self._lives = LIVES
        self._score = 0

        # subsystems — callbacks wired at construction
        self._physics = Physics(self._on_brick_hit, self._on_ball_lost)
        self._walls = Walls(self._physics, self._layout)

        # entities
        self._bricks = BrickGrid(self._game_scene, self._physics, self._layout)
        self._paddle = Paddle(self._game_scene, self._physics, self._layout)
        self._ball = Ball(self._game_scene, self._physics, self._layout)
        self._ball.reset(self._layout)

        # hud (on top of everything)
        self._hud_scene = Scene()
        canvas.add(self._hud_scene)
        self._hud = Hud(self._hud_scene, self._layout)
        self._hud.set_score(0)
        self._hud.set_lives(LIVES)
        self._hud.show_message('PRESS SPACE')

    # ── background ────────────────────────────────────────────────────────────

    def _draw_bg(self, lo: Layout):
        # teal gradient sky
        self._bg.reset()
        self._bg.append_rect(0, 0, lo.w, lo.h)
        lg = LinearGradient()
        lg.set(lo.w / 2, 0, lo.w / 2, lo.h)
        lg.set_color_stops([
            ColorStop(0.0, *COL_BG_TOP, 255),
            ColorStop(1.0, *COL_BG_BOT, 255),
        ])
        self._bg.set_gradient(lg)

        # remove old stars
        for s in self._stars:
            s.reset()
        self._stars.clear()

        # sprinkle random star particles
        for _ in range(lo.star_count):
            sx = random.uniform(0, lo.w)
            sy = random.uniform(0, lo.h)
            sr = random.uniform(lo.star_r * 0.3, lo.star_r)
            alpha = random.randint(40, 180)
            star = Shape()
            star.append_circle(sx, sy, sr, sr)
            star.set_fill_color(*COL_STAR, alpha)
            self._root.add(star)
            self._stars.append(star)

    # ── tick ──────────────────────────────────────────────────────────────────

    def tick(self, dt: float):
        dt = min(dt, 0.05)  # clamp to avoid physics explosion on lag

        self._physics.step(dt)
        self._bricks.update(dt)

        if self._state == ST_PLAYING:
            if self._bricks.is_clear():
                self._next_level()
        elif self._state == ST_IDLE:
            # ball follows paddle before launch
            self._ball.stick_to_paddle(self._paddle, self._layout)

        self._ball.sync(dt)

    # ── input ─────────────────────────────────────────────────────────────────

    def move_left(self):
        self._paddle.nudge(-1)

    def move_right(self):
        self._paddle.nudge(1)

    def action(self):
        if self._state == ST_IDLE:
            self._start()
        elif self._state == ST_GAME_OVER:
            self._restart()

    # ── resize ────────────────────────────────────────────────────────────────

    def resize(self, w: float, h: float):
        lo = Layout(w, h)
        self._layout = lo
        self._draw_bg(lo)
        self._walls.rebuild(lo)
        self._bricks.rebuild(lo)
        self._paddle.rebuild(lo)
        self._ball.rebuild(lo)
        self._hud.rebuild(lo)

    # ── collision callbacks ───────────────────────────────────────────────────

    def _on_brick_hit(self, arbiter, space, data):
        # figure out which shape is the brick
        shape_a, shape_b = arbiter.shapes
        if shape_a.collision_type == 2:  # CT_BRICK
            brick_shape = shape_a
        else:
            brick_shape = shape_b
        pts = self._bricks.on_hit(brick_shape)
        self._score += pts
        self._hud.set_score(self._score)
        self._ball.flash()

    def _on_ball_lost(self, arbiter, space, data):
        self._lives -= 1
        self._hud.set_lives(self._lives)
        self._ball.flash()
        if self._lives <= 0:
            self._game_over()
        else:
            self._ball.reset(self._layout)
            self._state = ST_IDLE
            self._hud.show_message('PRESS SPACE')

    # ── state transitions ─────────────────────────────────────────────────────

    def _start(self):
        self._state = ST_PLAYING
        self._hud.hide_message()
        self._ball.launch()

    def _game_over(self):
        self._state = ST_GAME_OVER
        self._hud.show_message('GAME OVER\nPress Space')

    def _restart(self):
        self._state = ST_IDLE
        self._lives = LIVES
        self._score = 0
        self._hud.set_score(0)
        self._hud.set_lives(LIVES)
        self._hud.show_message('PRESS SPACE')
        self._bricks.rebuild(self._layout)
        self._ball.reset(self._layout)

    def _next_level(self):
        self._bricks.populate(self._layout)
        self._ball.reset(self._layout)
        self._state = ST_IDLE
        self._hud.show_message('LEVEL CLEAR!\nPress Space')
