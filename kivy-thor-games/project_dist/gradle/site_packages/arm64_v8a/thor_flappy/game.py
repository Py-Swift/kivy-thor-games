import math

from thorvg_cython import Scene

from .constants import GRAVITY, GROUND_H, DESIGN_H, IDLE, PLAYING, DEAD, mat
from .sky import Sky
from .clouds import BgCloudLayer, CloudLayer
from .trees import TreeLayer
from .bushes import BushLayer
from .pipes import PipeLayer
from .ground import Ground
from .bird import Bird
from .hud import Hud


class FlappyScene(Scene):
    """Self-contained Flappy Bird game. Inherits Scene — add directly to a canvas.

    Usage::

        scene = FlappyScene(font='Roboto-Regular', font_bold='Roboto-Bold')
        canvas.add(scene)          # scene IS the root
        canvas.add(scene.hud)     # HUD is separate (not scaled)

        # each frame:
        scene.tick(dt)

        # on tap / click / spacebar:
        scene.tap()

        # on resize:
        scene.resize(screen_w, screen_h)
    """

    def __init__(self, font='Roboto-Regular', font_bold='Roboto-Bold'):
        super().__init__()
        self._state      = IDLE
        self._t          = 0.0
        self._dead_timer = 0.0
        self._score      = 0
        self._scale      = 1.0
        self._logical_w  = DESIGN_H

        self._sky       = Sky(self, DESIGN_H, DESIGN_H)
        self._bg_clouds = BgCloudLayer(self, DESIGN_H, DESIGN_H)
        self._clouds    = CloudLayer(self, DESIGN_H, DESIGN_H)
        self._trees     = TreeLayer(self, DESIGN_H, DESIGN_H)
        self._bushes    = BushLayer(self, DESIGN_H, DESIGN_H)
        self._pipes     = PipeLayer(self, DESIGN_H)
        self._ground    = Ground(self, DESIGN_H, DESIGN_H)
        self._bird      = Bird(self)
        self._bird.x    = DESIGN_H * 0.25
        self._bird.y    = (DESIGN_H - GROUND_H) * 0.42
        self._bird.draw(0.0)

        self._hud = Hud(0, 0, font=font, font_bold=font_bold)
        self._hud.set_score(0)
        self._hud.show_message('TAP TO PLAY')

    @property
    def hud(self):
        """HUD scene — add to canvas separately (it uses screen-pixel coords, not scaled)."""
        return self._hud

    # ── input ─────────────────────────────────────────────────────────────────

    def tap(self):
        if self._state == IDLE:
            self._state = PLAYING
            self._hud.hide_message()
            self._bird.jump()
        elif self._state == PLAYING:
            self._bird.jump()
        elif self._state == DEAD and self._dead_timer > 0.9:
            self._state = IDLE
            self._reset()

    # ── resize ────────────────────────────────────────────────────────────────

    def resize(self, screen_w: float, screen_h: float):
        if screen_w == 0 or screen_h == 0:
            return
        self._scale     = screen_h / DESIGN_H
        self._logical_w = screen_w / self._scale

        self.set_transform(mat(e11=self._scale, e22=self._scale))
        self._sky.resize(self._logical_w, DESIGN_H)
        self._ground.resize(self._logical_w, DESIGN_H)
        self._hud.resize(screen_w, screen_h)

    # ── tick ──────────────────────────────────────────────────────────────────

    def tick(self, dt: float):
        dt = min(dt, 0.05)
        self._t  += dt
        lw        = self._logical_w
        ground_y  = DESIGN_H - GROUND_H

        if self._state == PLAYING:
            self._bg_clouds.update(dt, lw)
            self._clouds.update(dt, lw)
            self._trees.update(dt, lw)
            self._bushes.update(dt, lw)

        if self._state == IDLE:
            self._bird.y = ground_y * 0.42 + math.sin(self._t * 3.2) * 12
            self._bird.draw(math.sin(self._t * 3.2) * 8)
            return

        if self._state == DEAD:
            self._dead_timer += dt
            self._bird.vy    += GRAVITY * dt
            self._bird.y     += self._bird.vy * dt
            self._bird.draw(min(90.0, self._bird.vy * 0.05))
            return

        self._bird.apply_gravity(dt)
        self._bird.draw()
        self._pipes.tick(dt, lw, ground_y, self._bird.x, self._on_score)

        if self._bird.hits_ceiling_or_ground(ground_y):
            self._die()
        elif self._pipes.check_collision(self._bird.x, self._bird.y, 15):
            self._die()

    # ── internal ──────────────────────────────────────────────────────────────

    def _reset(self):
        self._bird.y  = (DESIGN_H - GROUND_H) * 0.42
        self._bird.vy = 0.0
        self._pipes.reset()
        self._score = 0
        self._hud.set_score(0)
        self._hud.show_message('TAP TO PLAY')

    def _die(self):
        self._state      = DEAD
        self._dead_timer = 0.0
        self._hud.show_message('GAME OVER\nTap to restart')

    def _on_score(self):
        self._score += 1
        self._hud.set_score(self._score)
