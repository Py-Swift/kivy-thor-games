"""
TempestRunGame — main orchestrator.

Inspired by and adapted from:
  pygame-summer-team-jam  (David Pendergast et al.)
  https://github.com/davidpendergast/pygame-summer-team-jam
  Original pygame/OpenCV implementation; ported to thorvg-cython.
"""
from __future__ import annotations

import math

from thorvg_cython import Scene, GlCanvas

from .constants import (
    ST_IDLE, ST_PLAYING, ST_DEAD, ST_PAUSE,
    PM_JUMP, PM_SLIDE, PM_RUN,
    LANE_COUNT, JUMP_CLEARANCE, CELL_LENGTH,
    COL_BG, Layout,
)
from .projection import Camera3D
from .track import TrackRenderer
from .player import Player
from .obstacle import ObstacleField, get_speed
from .debris import Debris
from .hud import Hud

_DEAD_FREEZE  = 0.18   # seconds of freeze-frame on death before debris
_RESTART_WAIT = 1.5    # seconds after death before input re-enables restart


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class TempestRunGame:
    """Top-level game object.  call tick(dt) from Kivy Clock."""

    def __init__(self, canvas: GlCanvas, w: float, h: float) -> None:
        lo = Layout(w, h)
        self._lo     = lo
        self._canvas = canvas
        self._state  = ST_IDLE

        # Scenes
        self._scene     = Scene()
        self._hud_scene = Scene()
        canvas.add(self._scene)
        canvas.add(self._hud_scene)

        # Camera starts behind the origin, slightly below the cylinder axis
        self._camera         = Camera3D()
        self._camera.pos_z   = -lo.camera_z_offset
        self._camera.pos_y   = lo.camera_y
        self._rotation = -90.0 + 0.5 * (360.0 / LANE_COUNT)   # lane 0 at bottom

        # Sub-systems
        self._track   = TrackRenderer(lo)
        self._player  = Player(self._scene, lo)
        self._field   = ObstacleField(self._scene, lo)
        self._debris  = Debris(lo)
        self._scene.add(self._track)
        self._scene.add(self._debris)
        self._hud     = Hud(self._hud_scene, lo)

        # State
        self._player_z   = 0.0
        self._score      = 0
        self._dead_timer = 0.0
        self._msg_timer  = 0.0

        self._hud.show_message('tap / space to start')

    # ── public API ────────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        dt = min(dt, 0.05)  # clamp spikes

        if self._state == ST_IDLE:
            self._sync_visuals()
            return

        if self._state == ST_PAUSE:
            return

        if self._state == ST_DEAD:
            self._dead_timer += dt
            if self._dead_timer >= _DEAD_FREEZE:
                self._debris.sync(dt)
            return

        # ── ST_PLAYING ────────────────────────────────────────────────────────
        speed = get_speed(self._player_z)
        self._player_z   += speed * dt
        self._camera.pos_z = self._player_z - self._lo.camera_z_offset

        self._player.update(dt)
        self._check_collisions(speed)
        if self._state != ST_DEAD:
            self._score = int(self._player_z / 10) * 10

        if self._msg_timer > 0.0:
            self._msg_timer -= dt
            if self._msg_timer <= 0.0:
                self._hud.hide_message()

        self._sync_visuals()
        self._hud.set_score(self._score)
        self._hud.set_speed(speed)

    def resize(self, w: float, h: float) -> None:
        lo = Layout(w, h)
        self._lo = lo
        self._camera.pos_z = self._player_z - lo.camera_z_offset
        self._camera.pos_y = lo.camera_y
        self._track.rebuild(lo)
        self._player.rebuild(self._scene, lo)
        self._field.rebuild(lo)
        self._debris.rebuild(lo)
        self._hud.rebuild(lo)

    # ── input ─────────────────────────────────────────────────────────────────

    def action(self) -> None:
        """Space / tap — start, restart, or release from idle/dead."""
        if self._state == ST_IDLE:
            self._start()
        elif self._state == ST_DEAD and self._dead_timer >= _RESTART_WAIT:
            self._restart()

    def move_left(self) -> None:
        if self._state == ST_PLAYING:
            self._player.move_left()

    def move_right(self) -> None:
        if self._state == ST_PLAYING:
            self._player.move_right()

    def jump(self) -> None:
        if self._state == ST_PLAYING:
            self._player.jump()

    def release_jump(self) -> None:
        self._player.release_jump()

    def slide(self) -> None:
        if self._state == ST_PLAYING:
            self._player.slide()

    def release_slide(self) -> None:
        if self._state == ST_PLAYING:
            self._player.run()

    def pause(self) -> None:
        if self._state == ST_PLAYING:
            self._state = ST_PAUSE
            self._hud.show_message('paused — press P to resume')
        elif self._state == ST_PAUSE:
            self._state = ST_PLAYING
            self._hud.hide_message()

    # ── internals ─────────────────────────────────────────────────────────────

    def _start(self) -> None:
        self._state = ST_PLAYING
        self._hud.hide_message()

    def _restart(self) -> None:
        self._player_z   = 0.0
        self._score      = 0
        self._dead_timer = 0.0
        self._rotation   = -90.0 + 0.5 * (360.0 / LANE_COUNT)
        self._player.lane = 0
        self._debris.clear()
        self._state      = ST_PLAYING
        self._hud.hide_message()

    def _check_collisions(self, speed: float) -> None:
        p = self._player
        lane   = p.lane
        py     = p.normalised_y
        mode   = p.mode
        z      = self._player_z
        half   = CELL_LENGTH * 0.5

        for obs in self._field.obstacles_in_range(lane, z - half, z + half):
            if not obs.alive:
                continue

            if mode == PM_SLIDE and obs.can_slide_through():
                obs.kill()
                continue

            if mode == PM_JUMP and obs.can_jump_over() and py >= obs.JUMP_CLEAR:
                continue

            # Hit
            self._die(obs.DEATH_MSG)
            return

    def _die(self, msg: str) -> None:
        self._state = ST_DEAD
        self._dead_timer = 0.0
        lo = self._lo
        # project player to screen centre for debris burst
        face_ang = math.radians((self._player.lane - 0.5) * (360.0 / LANE_COUNT) + self._rotation)
        bx   = lo.track_radius * math.cos(face_ang)
        by   = lo.track_radius * math.sin(face_ang)
        sp   = self._camera.project(bx, by, self._player_z, lo.w, lo.h)
        cx, cy = sp if sp else (lo.w / 2, lo.h / 2)
        self._debris.burst(cx, cy)
        self._hud.show_message(f'you died — {msg}\ntap / space to restart')

    def _sync_visuals(self) -> None:
        lo  = self._lo
        cam = self._camera

        # Rotate cylinder so player's lane face is at screen bottom (-90 deg)
        lane_centre_unrot = (self._player.lane - 0.5) * (360.0 / LANE_COUNT)
        target_rot = -90.0 - lane_centre_unrot
        diff = ((target_rot - self._rotation + 180.0) % 360.0) - 180.0
        self._rotation = _lerp(self._rotation, self._rotation + diff, 0.07)

        cam.rotation = self._rotation
        self._track.sync(cam, self._player_z)
        self._player.sync(cam, self._rotation, self._player_z)

        if self._state != ST_DEAD:
            self._field.update_and_sync(cam, self._rotation, self._player_z)
        else:
            self._debris.sync(0.0)  # already ticked in tick(); just reposition
