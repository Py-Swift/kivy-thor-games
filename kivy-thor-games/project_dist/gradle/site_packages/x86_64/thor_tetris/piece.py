from thorvg_cython import Scene, Shape, LinearGradient, ColorStop

from .constants import (
    COLS, ROWS, SPAWN_ROWS, TOTAL_ROWS, GHOST_ALPHA, PIECE_COLORS, Layout,
)
from .tetromino import SHAPES, KICK_TABLE, T, T_CORNERS, T_FRONT_CORNERS
from .board import Board, _brighten, _darken


class ActivePiece(Scene):
    """The currently falling tetromino — 4 Shapes in a Scene."""

    def __init__(self, canvas: Scene, layout: Layout):
        super().__init__()
        canvas.add(self)
        self._shapes = [Shape() for _ in range(4)]
        for s in self._shapes:
            self.add(s)
        self._layout = layout
        self.piece_type = 0
        self.rotation = 0
        self.row = 0
        self.col = 0

    def spawn(self, piece_type: int, board: Board) -> bool:
        """Place piece at spawn position. Returns False if blocked (game over)."""
        self.piece_type = piece_type
        self.rotation = 0
        self.row = SPAWN_ROWS - 1  # just above visible area
        self.col = COLS // 2 - 1

        offsets = SHAPES[piece_type][0]
        if not board.can_place(offsets, self.row, self.col):
            return False
        self._draw(self._layout)
        return True

    @property
    def offsets(self):
        return SHAPES[self.piece_type][self.rotation]

    # ── movement ──────────────────────────────────────────────────────────────

    def move(self, dr: int, dc: int, board: Board) -> bool:
        """Try to move piece by (dr, dc). Returns True if successful."""
        new_r = self.row + dr
        new_c = self.col + dc
        if board.can_place(self.offsets, new_r, new_c):
            self.row = new_r
            self.col = new_c
            self._draw(self._layout)
            return True
        return False

    def rotate(self, direction: int, board: Board) -> tuple[bool, bool]:
        """Rotate piece with SRS wall kicks.

        direction: +1 for CW, -1 for CCW.
        Returns (success, is_tspin).
        """
        if self.piece_type == 2:  # O doesn't rotate
            return False, False

        old_rot = self.rotation
        new_rot = (self.rotation + direction) % 4
        new_offsets = SHAPES[self.piece_type][new_rot]

        kicks = KICK_TABLE[self.piece_type].get((old_rot, new_rot), ((0, 0),))
        for dcol, drow in kicks:
            new_r = self.row + drow
            new_c = self.col + dcol
            if board.can_place(new_offsets, new_r, new_c):
                self.rotation = new_rot
                self.row = new_r
                self.col = new_c

                # T-spin detection
                is_tspin = False
                if self.piece_type == T:
                    is_tspin = self._check_tspin(board)

                self._draw(self._layout)
                return True, is_tspin

        return False, False

    def _check_tspin(self, board: Board) -> bool:
        """3-corner rule: at least 3 of 4 diagonal corners occupied."""
        filled = 0
        for dr, dc in T_CORNERS:
            r, c = self.row + dr, self.col + dc
            if r < 0 or r >= TOTAL_ROWS or c < 0 or c >= COLS:
                filled += 1  # walls count as filled
            elif board._grid[r][c] != 0:
                filled += 1
        return filled >= 3

    def drop_row(self, board: Board) -> bool:
        """Move piece down one row. Returns True if successful."""
        return self.move(1, 0, board)

    def hard_drop(self, board: Board) -> int:
        """Drop to lowest valid position. Returns number of rows dropped."""
        rows = 0
        while self.move(1, 0, board):
            rows += 1
        return rows

    def ghost_row(self, board: Board) -> int:
        """Compute the lowest valid row for this piece (for ghost display)."""
        r = self.row
        while board.can_place(self.offsets, r + 1, self.col):
            r += 1
        return r

    def is_on_ground(self, board: Board) -> bool:
        """Check if piece can't move down."""
        return not board.can_place(self.offsets, self.row + 1, self.col)

    # ── visual ────────────────────────────────────────────────────────────────

    def _draw(self, lo: Layout):
        offsets = self.offsets
        base = PIECE_COLORS.get(self.piece_type, (200, 200, 200))
        hi = _brighten(base, 60)
        dk = _darken(base, 40)
        cell = lo.cell
        pad = cell * 0.06
        rx = cell * 0.12

        for i, (dr, dc) in enumerate(offsets):
            r = self.row + dr
            c = self.col + dc
            visible_r = r - SPAWN_ROWS
            x = lo.board_x + c * cell
            y = lo.board_y + visible_r * cell

            shp = self._shapes[i]
            shp.reset()

            # hide cells above visible area
            if visible_r < 0:
                continue

            shp.append_rect(x + pad, y + pad, cell - 2 * pad, cell - 2 * pad, rx=rx, ry=rx)
            lg = LinearGradient()
            lg.set(x, y, x, y + cell)
            lg.set_color_stops([
                ColorStop(0.0, *hi, 255),
                ColorStop(0.4, *base, 255),
                ColorStop(1.0, *dk, 255),
            ])
            shp.set_gradient(lg)

    def hide(self):
        for s in self._shapes:
            s.reset()

    def rebuild(self, layout: Layout):
        self._layout = layout
        if self.piece_type:
            self._draw(layout)


class GhostPiece(Scene):
    """Semi-transparent preview of where the piece will land."""

    def __init__(self, canvas: Scene, layout: Layout):
        super().__init__()
        canvas.add(self)
        self._shapes = [Shape() for _ in range(4)]
        for s in self._shapes:
            self.add(s)
        self._layout = layout

    def update(self, active: ActivePiece, board: Board):
        """Sync ghost to the active piece's hard-drop position."""
        if not active.piece_type:
            self.hide()
            return

        ghost_r = active.ghost_row(board)
        offsets = active.offsets
        base = PIECE_COLORS.get(active.piece_type, (200, 200, 200))
        lo = self._layout
        cell = lo.cell
        pad = cell * 0.06
        rx = cell * 0.12

        for i, (dr, dc) in enumerate(offsets):
            r = ghost_r + dr
            c = active.col + dc
            visible_r = r - SPAWN_ROWS
            x = lo.board_x + c * cell
            y = lo.board_y + visible_r * cell

            shp = self._shapes[i]
            shp.reset()

            if visible_r < 0:
                continue

            shp.append_rect(x + pad, y + pad, cell - 2 * pad, cell - 2 * pad, rx=rx, ry=rx)
            shp.set_fill_color(*base, GHOST_ALPHA)

    def hide(self):
        for s in self._shapes:
            s.reset()

    def rebuild(self, layout: Layout):
        self._layout = layout
