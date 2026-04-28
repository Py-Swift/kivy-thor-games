# ── grid ──────────────────────────────────────────────────────────────────────
COLS       = 10
ROWS       = 20
SPAWN_ROWS = 4   # hidden rows above visible area
TOTAL_ROWS = ROWS + SPAWN_ROWS

# ── game states ───────────────────────────────────────────────────────────────
ST_IDLE      = 0
ST_PLAYING   = 1
ST_GAME_OVER = 2

# ── collision types (pymunk, debris only) ─────────────────────────────────────
CT_WALL   = 1
CT_FLOOR  = 2
CT_DEBRIS = 3

# ── timing ────────────────────────────────────────────────────────────────────
DROP_INTERVAL_BASE = 1.0   # seconds at level 1
DROP_INTERVAL_MIN  = 0.05  # fastest drop rate
SOFT_DROP_FACTOR   = 0.05  # interval during soft drop
LOCK_DELAY         = 0.5   # seconds after piece lands
LOCK_MOVE_LIMIT    = 15    # max move/rotate resets of lock delay
LINES_PER_LEVEL    = 10

# ── scoring ───────────────────────────────────────────────────────────────────
# points[lines_cleared] × level
SCORE_TABLE = {
    1: 100,    # single
    2: 300,    # double
    3: 500,    # triple
    4: 800,    # tetris
}
TSPIN_SCORE_TABLE = {
    0: 400,    # t-spin no lines
    1: 800,    # t-spin single
    2: 1200,   # t-spin double
    3: 1600,   # t-spin triple
}
SOFT_DROP_PTS = 1   # per row
HARD_DROP_PTS = 2   # per row

# ── proportional constants (fractions of w or h) ─────────────────────────────

# board occupies ~60% of screen height, centered
BOARD_H_FRAC     = 0.85   # board height as fraction of screen h
BOARD_PAD_FRAC   = 0.02   # margin around board

# grid lines
GRID_LINE_FRAC   = 0.002  # grid line thickness as fraction of cell_size

# preview / hold box
PREVIEW_SIZE     = 4       # cells wide/tall for preview box
HOLD_SIZE        = 4

# hud
HUD_FONT_FRAC   = 0.025   # label font size as fraction of h
HUD_VAL_FRAC    = 0.035   # value font size as fraction of h
HUD_MSG_FRAC    = 0.05    # center message font
HUD_PAD_FRAC    = 0.015   # padding

# ghost
GHOST_ALPHA      = 60

# debris
DEBRIS_LIFETIME  = 1.5    # seconds
DEBRIS_IMPULSE_Y = -600   # upward impulse (negative = up in screen coords)
DEBRIS_IMPULSE_X = 300    # max sideways impulse (random ±)

# ── colors ────────────────────────────────────────────────────────────────────
COL_BG_TOP   = (15, 15, 30)
COL_BG_BOT   = (25, 25, 50)
COL_GRID     = (60, 60, 80)          # subtle grid lines
COL_BOARD_BG = (20, 20, 35, 200)     # board background with alpha
COL_TEXT     = (255, 255, 255)
COL_TEXT_MSG = (255, 255, 80)
COL_TEXT_DIM = (160, 160, 180)

# Piece colors — indexed by piece type (1=I, 2=O, 3=T, 4=S, 5=Z, 6=J, 7=L)
PIECE_COLORS = {
    1: (0, 240, 240),    # I — cyan
    2: (240, 240, 0),    # O — yellow
    3: (160, 0, 240),    # T — purple
    4: (0, 240, 0),      # S — green
    5: (240, 0, 0),      # Z — red
    6: (0, 0, 240),      # J — blue
    7: (240, 160, 0),    # L — orange
}


class Layout:
    """Computes absolute pixel values for a given (w, h)."""

    __slots__ = (
        'w', 'h',
        'cell', 'board_w', 'board_h', 'board_x', 'board_y',
        'preview_cell', 'preview_x', 'preview_y',
        'hold_x', 'hold_y',
        'hud_font', 'hud_val_font', 'hud_msg_font', 'hud_pad',
        'grid_line',
    )

    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

        # cell size derived from board height
        self.board_h = h * BOARD_H_FRAC
        self.cell = self.board_h / ROWS
        self.board_w = self.cell * COLS

        # center the board horizontally
        self.board_x = (w - self.board_w) / 2
        self.board_y = (h - self.board_h) / 2

        # grid line thickness
        self.grid_line = max(1.0, self.cell * GRID_LINE_FRAC)

        # preview box (right of board)
        self.preview_cell = self.cell * 0.7
        self.preview_x = self.board_x + self.board_w + self.cell * 1.2
        self.preview_y = self.board_y

        # hold box (left of board)
        self.hold_x = self.board_x - self.cell * 1.2 - HOLD_SIZE * self.preview_cell
        self.hold_y = self.board_y

        # hud
        self.hud_font = h * HUD_FONT_FRAC
        self.hud_val_font = h * HUD_VAL_FRAC
        self.hud_msg_font = h * HUD_MSG_FRAC
        self.hud_pad = max(w, h) * HUD_PAD_FRAC
