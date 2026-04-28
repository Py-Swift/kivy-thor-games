import math
import random

from thorvg_cython import Scene, Shape, Matrix, GlCanvas

from .constants import (
    Layout, COL_BG, COL_STAR, LIVES, STAR_COUNT,
    ST_IDLE, ST_PLAYING, ST_GAME_OVER,
    INITIAL_ASTEROIDS, CT_ASTEROID, CT_BULLET,
)
from .physics import Physics
from .ship import Ship
from .asteroid import AsteroidField
from .bullet import BulletPool
from .hud import Hud


class AsteroidsGame:
    """Main game orchestrator.

    Usage from Kivy::

        game = AsteroidsGame(gl_canvas, w, h)
        Clock.schedule_interval(game.tick, 0)
    """

    def __init__(self, canvas: GlCanvas, w: float, h: float):
        self.canvas = canvas
        self._layout = Layout(w, h)

        # root scene
        self._root = Scene()
        canvas.add(self._root)

        # background
        self._bg = Shape()
        self._root.add(self._bg)
        self._stars: list[Shape] = []
        self._star_data: list[list] = []  # [[x, y, vx, vy], ...]
        self._draw_bg(self._layout)

        # game scene
        self._game_scene = Scene()
        self._root.add(self._game_scene)

        # state
        self._state = ST_IDLE
        self._lives = LIVES
        self._score = 0
        self._wave = 0
        self._respawn_timer = 0.0

        # subsystems
        self._physics = Physics(self._on_bullet_hit, self._on_ship_hit)

        # entities
        self._ship = Ship(self._game_scene, self._physics, self._layout)
        self._asteroids = AsteroidField(self._game_scene, self._physics, self._layout)
        self._bullets = BulletPool(self._game_scene, self._physics)

        # hud
        self._hud_scene = Scene()
        canvas.add(self._hud_scene)
        self._hud = Hud(self._hud_scene, self._layout)
        self._hud.set_score(0)
        self._hud.set_lives(LIVES)
        self._hud.show_message('PRESS SPACE')

    # ── background ────────────────────────────────────────────────────────────

    def _draw_bg(self, lo: Layout):
        self._bg.reset()
        self._bg.append_rect(0, 0, lo.w, lo.h)
        self._bg.set_fill_color(*COL_BG, 255)

        for s in self._stars:
            s.reset()
        self._stars.clear()
        self._star_data.clear()

        for _ in range(lo.star_count):
            sx = random.uniform(0, lo.w)
            sy = random.uniform(0, lo.h)
            sr = random.uniform(lo.star_r * 0.3, lo.star_r)
            alpha = random.randint(40, 180)
            # drift speed proportional to brightness — brighter = closer = faster
            speed = (alpha / 180.0) * lo.h * 0.006
            angle = random.uniform(0, math.tau)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            star = Shape()
            star.append_circle(0, 0, sr, sr)
            star.set_fill_color(*COL_STAR, alpha)
            self._root.add(star)
            self._stars.append(star)
            self._star_data.append([sx, sy, vx, vy])

    # ── tick ──────────────────────────────────────────────────────────────────

    def tick(self, dt: float):
        dt = min(dt, 0.05)

        # drift stars
        w, h = self._layout.w, self._layout.h
        for i, star in enumerate(self._stars):
            d = self._star_data[i]
            d[0] = (d[0] + d[2] * dt) % w
            d[1] = (d[1] + d[3] * dt) % h
            m = Matrix()
            m.e13 = d[0]
            m.e23 = d[1]
            star.set_transform(m)

        self._physics.step(dt)
        self._asteroids.sync(dt)
        self._bullets.sync(dt)

        if self._state == ST_PLAYING:
            self._ship.sync(dt)

            # check if wave cleared
            if self._asteroids.is_clear():
                self._next_wave()

            # respawn timer
            if not self._ship.alive and self._lives > 0:
                self._respawn_timer -= dt
                if self._respawn_timer <= 0:
                    self._ship.respawn(self._layout)

        elif self._state == ST_IDLE:
            self._ship.sync(dt)

    # ── input ─────────────────────────────────────────────────────────────────

    def rotate_left(self):
        if self._state == ST_PLAYING and self._ship.alive:
            self._ship.rotate_left()

    def rotate_right(self):
        if self._state == ST_PLAYING and self._ship.alive:
            self._ship.rotate_right()

    def thrust(self):
        if self._state == ST_PLAYING and self._ship.alive:
            self._ship.thrust_tick()

    def fire(self):
        if self._state == ST_PLAYING and self._ship.alive:
            x, y = self._ship.position
            nose_dist = self._layout.ship_size
            angle = self._ship.angle
            bx = x + math.cos(angle) * nose_dist
            by = y + math.sin(angle) * nose_dist
            self._bullets.fire(bx, by, angle, self._layout)

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
        self._ship.rebuild(lo)
        self._asteroids.rebuild(lo)
        self._bullets.clear_all()
        self._hud.rebuild(lo)

    # ── collision callbacks ───────────────────────────────────────────────────

    def _on_bullet_hit(self, arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        if shape_a.collision_type == CT_BULLET:
            bullet_shape, asteroid_shape = shape_a, shape_b
        else:
            bullet_shape, asteroid_shape = shape_b, shape_a

        self._bullets.on_hit(bullet_shape)
        pts = self._asteroids.on_hit(asteroid_shape, self._layout)
        self._score += pts
        self._hud.set_score(self._score)

    def _on_ship_hit(self, arbiter, space, data):
        if not self._ship.alive or self._ship.invulnerable:
            return
        self._ship.die()
        self._lives -= 1
        self._hud.set_lives(self._lives)
        if self._lives <= 0:
            self._game_over()
        else:
            self._respawn_timer = 1.5

    # ── state transitions ─────────────────────────────────────────────────────

    def _start(self):
        self._state = ST_PLAYING
        self._hud.hide_message()
        self._wave = 0
        self._next_wave()

    def _next_wave(self):
        self._wave += 1
        count = INITIAL_ASTEROIDS + self._wave - 1
        self._asteroids.spawn_wave(self._layout, count)

    def _game_over(self):
        self._state = ST_GAME_OVER
        self._hud.show_message('GAME OVER\nPress Space')

    def _restart(self):
        self._state = ST_IDLE
        self._lives = LIVES
        self._score = 0
        self._wave = 0
        self._hud.set_score(0)
        self._hud.set_lives(LIVES)
        self._hud.show_message('PRESS SPACE')
        self._asteroids.clear_all()
        self._bullets.clear_all()
        self._ship.reset(self._layout)
