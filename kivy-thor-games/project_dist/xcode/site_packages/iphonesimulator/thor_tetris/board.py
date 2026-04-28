from thorvg_cython import Scene, Shape, LinearGradient, ColorStop, Matrix

from .constants import (
    COLS, ROWS, SPAWN_ROWS, TOTAL_ROWS,
    COL_GRID, COL_BOARD_BG, PIECE_COLORS, Layout,
)


def _clamp(v):
    return max(0, min(255, int(v)))


def _brighten(col, amt=50):
    return (_clamp(col[0] + amt), _clamp(col[1] + amt), _clamp(col[2] + amt))


def _darken(col, amt=50):
    return (_clamp(col[0] - amt), _clamp(col[1] - amt), _clamp(col[2] - amt))


class Board(Scene):
    """Visual game board — grid state + locked cell shapes.

    The grid has TOTAL_ROWS rows (SPAWN_ROWS hidden above + ROWS visible).
    Row 0 is the top of the hidden area; row SPAWN_ROWS is the first visible row.
    """

    def __init__(self, canvas: Scene, layout: Layout):
        super().__init__()
        canvas.add(self)

        # grid state: 0=empty, piece_type (1–7) = locked
        self._grid = [[0] * COLS for _ in range(TOTAL_ROWS)]
        self._cell_shapes: dict[tuple[int, int], Shape] = {}

        # board background + grid lines
        self._bg = Shape()
        self.add(self._bg)
        self._grid_scene = Scene()  # holds grid line shapes
        self.add(self._grid_scene)
        self._cells_scene = Scene()  # holds locked cell shapes
        self.add(self._cells_scene)

        self._layout = layout
        self._draw_board(layout)

    # ── visual ────────────────────────────────────────────────────────────────

    def _draw_board(self, lo: Layout):
        bx, by = lo.board_x, lo.board_y
        bw, bh = lo.board_w, lo.board_h
        cell = lo.cell

        # board background
        self._bg.reset()
        self._bg.append_rect(bx, by, bw, bh)
        self._bg.set_fill_color(*COL_BOARD_BG)

        # grid lines
        # remove old grid shapes
        self._grid_scene = Scene()
        # re-add (Scene.add replacement — we need to rebuild)
        # Actually just reset and redraw:
        # We'll store grid lines in a list and recreate
        self._rebuild_grid_lines(lo)

    def _rebuild_grid_lines(self, lo: Layout):
        bx, by = lo.board_x, lo.board_y
        bw, bh = lo.board_w, lo.board_h
        cell = lo.cell
        lw = lo.grid_line

        # vertical lines
        for c in range(1, COLS):
            x = bx + c * cell
            line = Shape()
            line.append_rect(x - lw / 2, by, lw, bh)
            line.set_fill_color(*COL_GRID, 80)
            self._grid_scene.add(line)

        # horizontal lines
        for r in range(1, ROWS):
            y = by + r * cell
            line = Shape()
            line.append_rect(bx, y - lw / 2, bw, lw)
            line.set_fill_color(*COL_GRID, 80)
            self._grid_scene.add(line)

    def _cell_to_pixel(self, r: int, c: int, lo: Layout) -> tuple[float, float]:
        """Convert grid (r, c) to pixel (x, y).  r is in total-row space."""
        visible_r = r - SPAWN_ROWS
        x = lo.board_x + c * lo.cell
        y = lo.board_y + visible_r * lo.cell
        return x, y

    def _create_cell_shape(self, r: int, c: int, piece_type: int, lo: Layout) -> Shape:
        """Create a gradient-filled rounded rect for a locked cell."""
        x, y = self._cell_to_pixel(r, c, lo)
        cell = lo.cell
        pad = cell * 0.06
        rx = cell * 0.12

        base = PIECE_COLORS[piece_type]
        hi = _brighten(base, 60)
        dk = _darken(base, 40)

        shp = Shape()
        shp.append_rect(x + pad, y + pad, cell - 2 * pad, cell - 2 * pad, rx=rx, ry=rx)
        lg = LinearGradient()
        lg.set(x, y, x, y + cell)
        lg.set_color_stops([
            ColorStop(0.0, *hi, 255),
            ColorStop(0.4, *base, 255),
            ColorStop(1.0, *dk, 255),
        ])
        shp.set_gradient(lg)
        return shp

    # ── grid logic ────────────────────────────────────────────────────────────

    def can_place(self, offsets, row: int, col: int) -> bool:
        """Check if piece offsets fit at (row, col) without collision."""
        for dr, dc in offsets:
            r, c = row + dr, col + dc
            if c < 0 or c >= COLS or r >= TOTAL_ROWS:
                return False
            if r < 0:
                continue  # above the grid is ok
            if self._grid[r][c] != 0:
                return False
        return True

    def lock(self, offsets, row: int, col: int, piece_type: int):
        """Write piece cells to grid and create visual shapes."""
        lo = self._layout
        for dr, dc in offsets:
            r, c = row + dr, col + dc
            if 0 <= r < TOTAL_ROWS and 0 <= c < COLS:
                self._grid[r][c] = piece_type
                shp = self._create_cell_shape(r, c, piece_type, lo)
                self._cells_scene.add(shp)
                self._cell_shapes[(r, c)] = shp

    def check_lines(self) -> list[int]:
        """Return sorted list of full row indices (top to bottom)."""
        full = []
        for r in range(TOTAL_ROWS):
            if all(self._grid[r][c] != 0 for c in range(COLS)):
                full.append(r)
        return full

    def clear_lines(self, rows: list[int]) -> list[tuple[int, int, int]]:
        """Remove full rows, shift above down.

        Returns list of (row, col, piece_type) for cleared cells (for debris).
        """
        cleared = []
        lo = self._layout

        # collect cleared cell data
        for r in rows:
            for c in range(COLS):
                pt = self._grid[r][c]
                if pt != 0:
                    cleared.append((r, c, pt))

        # remove rows from grid (bottom to top to keep indices valid)
        for r in sorted(rows, reverse=True):
            del self._grid[r]
        # insert empty rows at top
        for _ in range(len(rows)):
            self._grid.insert(0, [0] * COLS)

        # rebuild all cell visuals (simpler and correct after row shifts)
        self._rebuild_cell_shapes(lo)

        return cleared

    def is_blocked_out(self) -> bool:
        """Check if any cell in the spawn area is occupied (game over)."""
        for r in range(SPAWN_ROWS):
            for c in range(COLS):
                if self._grid[r][c] != 0:
                    return True
        return False

    def clear_all(self):
        """Reset the entire board."""
        self._grid = [[0] * COLS for _ in range(TOTAL_ROWS)]
        self._rebuild_cell_shapes(self._layout)

    def _rebuild_cell_shapes(self, lo: Layout):
        """Recreate all locked cell visuals from grid state."""
        # clear old shapes
        for shp in self._cell_shapes.values():
            shp.reset()
        self._cell_shapes.clear()

        # recreate
        for r in range(TOTAL_ROWS):
            for c in range(COLS):
                pt = self._grid[r][c]
                if pt != 0:
                    visible_r = r - SPAWN_ROWS
                    if visible_r >= 0:  # only draw visible cells
                        shp = self._create_cell_shape(r, c, pt, lo)
                        self._cells_scene.add(shp)
                        self._cell_shapes[(r, c)] = shp

    def rebuild(self, layout: Layout):
        """Recompute visuals after resize."""
        self._layout = layout
        self._bg.reset()
        # recreate grid_scene
        self._grid_scene = Scene()
        # re-add sub-scenes in order
        # We need to clear self and re-add everything
        # Since Scene doesn't have remove(), rebuild by re-adding
        _grid = self._grid
        _cell_shapes = self._cell_shapes

        # Reconstruct the scene hierarchy
        self._bg = Shape()
        old_grid_scene = self._grid_scene
        self._grid_scene = Scene()
        old_cells_scene = self._cells_scene
        self._cells_scene = Scene()

        # Clear old shapes
        for shp in _cell_shapes.values():
            shp.reset()
        _cell_shapes.clear()

        # Reset self and re-add children
        # Note: Scene doesn't have clear(), so we re-init shape children
        self._draw_board(layout)
        self._rebuild_cell_shapes(layout)

    def cell_to_pixel(self, r: int, c: int) -> tuple[float, float]:
        """Public helper for converting grid coords to pixel coords."""
        return self._cell_to_pixel(r, c, self._layout)
