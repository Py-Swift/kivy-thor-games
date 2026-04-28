from thorvg_cython import Scene, Shape, LinearGradient, ColorStop

from .constants import (
    Layout, COL_BG_TOP, COL_BG_BOT,
    ST_IDLE, ST_PLAYING, ST_GAME_OVER,
    DROP_INTERVAL_BASE, DROP_INTERVAL_MIN, SOFT_DROP_FACTOR,
    LOCK_DELAY, LOCK_MOVE_LIMIT, LINES_PER_LEVEL,
    SCORE_TABLE, TSPIN_SCORE_TABLE, SOFT_DROP_PTS, HARD_DROP_PTS,
)
from .tetromino import PieceBag, T
from .physics import Physics
from .walls import Walls
from .board import Board
from .piece import ActivePiece, GhostPiece
from .debris import Debris
from .hud import Hud


class TetrisGame(Scene):
    """Main game orchestrator.  Inherits Scene — add directly to a canvas.

    Usage from Kivy::

        game = TetrisGame(w, h)
        canvas.add(game)
        canvas.add(game.hud)
        Clock.schedule_interval(game.tick, 0)
    """

    def __init__(self, w: float, h: float):
        super().__init__()
        self._layout = Layout(w, h)

        # background
        self._bg = Shape()
        self.add(self._bg)
        self._draw_bg(self._layout)

        # subsystems
        self._physics = Physics()
        self._walls = Walls(self._physics, self._layout)

        # game scene (board + pieces + debris)
        self._game_scene = Scene()
        self.add(self._game_scene)

        self._board = Board(self._game_scene, self._layout)
        self._ghost = GhostPiece(self._game_scene, self._layout)
        self._piece = ActivePiece(self._game_scene, self._layout)
        self._debris = Debris(self._game_scene, self._physics, self._layout)

        # hud (added separately to canvas by caller)
        self._hud = Hud(self._layout)

        # state
        self._bag = PieceBag()
        self._state = ST_IDLE
        self._score = 0
        self._level = 1
        self._lines = 0
        self._drop_timer = 0.0
        self._lock_timer = 0.0
        self._lock_moves = 0
        self._is_locking = False
        self._soft_dropping = False
        self._hold_type = 0
        self._hold_used = False  # can only hold once per piece
        self._last_was_tspin = False

        self._hud.set_score(0)
        self._hud.set_level(1)
        self._hud.set_lines(0)
        self._hud.show_message('PRESS SPACE')
        self._hud.set_next(self._bag.peek())

    @property
    def hud(self):
        return self._hud

    # ── background ────────────────────────────────────────────────────────────

    def _draw_bg(self, lo: Layout):
        self._bg.reset()
        self._bg.append_rect(0, 0, lo.w, lo.h)
        lg = LinearGradient()
        lg.set(lo.w / 2, 0, lo.w / 2, lo.h)
        lg.set_color_stops([
            ColorStop(0.0, *COL_BG_TOP, 255),
            ColorStop(1.0, *COL_BG_BOT, 255),
        ])
        self._bg.set_gradient(lg)

    # ── tick ──────────────────────────────────────────────────────────────────

    def tick(self, dt: float):
        dt = min(dt, 0.05)

        self._physics.step(dt)
        self._debris.update(dt)

        if self._state != ST_PLAYING:
            return

        # drop timer
        interval = self._drop_interval()
        if self._soft_dropping:
            interval = SOFT_DROP_FACTOR

        self._drop_timer += dt
        if self._drop_timer >= interval:
            self._drop_timer = 0.0
            moved = self._piece.drop_row(self._board)
            if moved and self._soft_dropping:
                self._score += SOFT_DROP_PTS

            if self._piece.is_on_ground(self._board):
                if not self._is_locking:
                    self._is_locking = True
                    self._lock_timer = 0.0
                    self._lock_moves = 0
            else:
                self._is_locking = False

        # lock delay
        if self._is_locking:
            self._lock_timer += dt
            if self._lock_timer >= LOCK_DELAY:
                self._lock_piece()

        self._ghost.update(self._piece, self._board)

    def _drop_interval(self) -> float:
        return max(DROP_INTERVAL_MIN,
                   DROP_INTERVAL_BASE - (self._level - 1) * 0.07)

    # ── piece lifecycle ───────────────────────────────────────────────────────

    def _spawn_piece(self):
        piece_type = self._bag.next()
        ok = self._piece.spawn(piece_type, self._board)
        self._hud.set_next(self._bag.peek())
        self._hold_used = False
        self._is_locking = False
        self._drop_timer = 0.0
        self._last_was_tspin = False

        if not ok:
            self._game_over()
            return

        self._ghost.update(self._piece, self._board)

    def _lock_piece(self):
        offsets = self._piece.offsets
        self._board.lock(offsets, self._piece.row, self._piece.col, self._piece.piece_type)
        self._piece.hide()
        self._ghost.hide()
        self._is_locking = False

        # check lines
        full_rows = self._board.check_lines()
        if full_rows:
            cleared_cells = self._board.clear_lines(full_rows)
            self._debris.spawn(cleared_cells, self._layout)
            n = len(full_rows)
            self._lines += n

            # scoring
            if self._last_was_tspin:
                pts = TSPIN_SCORE_TABLE.get(n, 0)
            else:
                pts = SCORE_TABLE.get(n, 0)
            self._score += pts * self._level
            self._hud.set_score(self._score)
            self._hud.set_lines(self._lines)

            # level up
            new_level = self._lines // LINES_PER_LEVEL + 1
            if new_level != self._level:
                self._level = new_level
                self._hud.set_level(self._level)

        # check game over
        if self._board.is_blocked_out():
            self._game_over()
            return

        self._spawn_piece()

    # ── input ─────────────────────────────────────────────────────────────────

    def move_left(self):
        if self._state != ST_PLAYING:
            return
        if self._piece.move(0, -1, self._board):
            self._reset_lock_if_grounded()
            self._ghost.update(self._piece, self._board)

    def move_right(self):
        if self._state != ST_PLAYING:
            return
        if self._piece.move(0, 1, self._board):
            self._reset_lock_if_grounded()
            self._ghost.update(self._piece, self._board)

    def rotate_cw(self):
        if self._state != ST_PLAYING:
            return
        ok, is_tspin = self._piece.rotate(1, self._board)
        if ok:
            self._last_was_tspin = is_tspin
            self._reset_lock_if_grounded()
            self._ghost.update(self._piece, self._board)

    def rotate_ccw(self):
        if self._state != ST_PLAYING:
            return
        ok, is_tspin = self._piece.rotate(-1, self._board)
        if ok:
            self._last_was_tspin = is_tspin
            self._reset_lock_if_grounded()
            self._ghost.update(self._piece, self._board)

    def soft_drop(self, active: bool):
        """Start or stop soft drop."""
        self._soft_dropping = active

    def hard_drop(self):
        if self._state != ST_PLAYING:
            return
        rows = self._piece.hard_drop(self._board)
        self._score += rows * HARD_DROP_PTS
        self._hud.set_score(self._score)
        self._lock_piece()

    def hold(self):
        if self._state != ST_PLAYING:
            return
        if self._hold_used:
            return
        self._hold_used = True

        current_type = self._piece.piece_type
        self._piece.hide()
        self._ghost.hide()

        if self._hold_type == 0:
            self._hold_type = current_type
            self._hud.set_hold(self._hold_type)
            self._spawn_piece()
        else:
            old_hold = self._hold_type
            self._hold_type = current_type
            self._hud.set_hold(self._hold_type)
            ok = self._piece.spawn(old_hold, self._board)
            if not ok:
                self._game_over()
                return
            self._hud.set_next(self._bag.peek())
            self._is_locking = False
            self._drop_timer = 0.0
            self._ghost.update(self._piece, self._board)

    def action(self):
        if self._state == ST_IDLE:
            self._start()
        elif self._state == ST_GAME_OVER:
            self._restart()

    def _reset_lock_if_grounded(self):
        if self._is_locking and self._lock_moves < LOCK_MOVE_LIMIT:
            self._lock_timer = 0.0
            self._lock_moves += 1
            # if piece moved off the ground, cancel lock
            if not self._piece.is_on_ground(self._board):
                self._is_locking = False

    # ── resize ────────────────────────────────────────────────────────────────

    def resize(self, w: float, h: float):
        lo = Layout(w, h)
        self._layout = lo
        self._draw_bg(lo)
        self._walls.rebuild(lo)
        self._board.rebuild(lo)
        self._piece.rebuild(lo)
        self._ghost.rebuild(lo)
        self._debris.rebuild(lo)
        self._hud.rebuild(lo)

    # ── state transitions ─────────────────────────────────────────────────────

    def _start(self):
        self._state = ST_PLAYING
        self._hud.hide_message()
        self._spawn_piece()

    def _game_over(self):
        self._state = ST_GAME_OVER
        self._piece.hide()
        self._ghost.hide()
        self._hud.show_message('GAME OVER\nPress Space')

    def _restart(self):
        self._state = ST_IDLE
        self._score = 0
        self._level = 1
        self._lines = 0
        self._hold_type = 0
        self._hold_used = False
        self._bag = PieceBag()
        self._hud.set_score(0)
        self._hud.set_level(1)
        self._hud.set_lines(0)
        self._hud.set_hold(0)
        self._hud.set_next(self._bag.peek())
        self._hud.show_message('PRESS SPACE')
        self._board.clear_all()
        self._debris.clear()
        self._piece.hide()
        self._ghost.hide()
