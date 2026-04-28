# ── collision types ────────────────────────────────────────────────────────────
CT_BALL   = 1
CT_BRICK  = 2
CT_PADDLE = 3
CT_WALL   = 4
CT_BOTTOM = 5

# ── lives ─────────────────────────────────────────────────────────────────────
LIVES = 3

# ── game states ───────────────────────────────────────────────────────────────
ST_IDLE      = 0
ST_PLAYING   = 1
ST_GAME_OVER = 2

# ── proportional constants (fractions of w or h) ─────────────────────────────

# ball
BALL_R_FRAC     = 0.013   # radius as fraction of h
BALL_SPEED_FRAC = 0.5     # speed as fraction of h per second

# paddle
PADDLE_W_FRAC     = 0.17  # width as fraction of w
PADDLE_H_FRAC     = 0.018 # height as fraction of h
PADDLE_Y_FRAC     = 0.94  # y-center as fraction of h (from top)
PADDLE_SPEED_FRAC = 0.8   # paddle speed as fraction of w per second

# ball glow
BALL_GLOW_FRAC    = 2.8   # glow radius = ball_r * this

# bricks
BRICK_COLS       = 9
BRICK_ROWS       = 8
BRICK_HGAP_FRAC  = 0.012  # horizontal gap as fraction of w
BRICK_VGAP_FRAC  = 0.008  # vertical gap as fraction of h
BRICK_TOP_FRAC   = 0.08   # top-row y as fraction of h
BRICK_MARGIN_FRAC = 0.03  # left/right margin as fraction of w
BRICK_H_FRAC     = 0.025  # brick height as fraction of h

# starfield
STAR_COUNT       = 80     # number of background star particles
STAR_R_FRAC      = 0.002  # max star radius as fraction of h

# hud
HUD_FONT_FRAC   = 0.028   # font size as fraction of h
HUD_MSG_FRAC    = 0.045   # message font size as fraction of h
HUD_PAD_FRAC    = 0.015   # padding as fraction of w / h

# ── colors ────────────────────────────────────────────────────────────────────
COL_BG_TOP      = (8, 50, 58)       # deep teal (top)
COL_BG_BOT      = (12, 72, 78)      # lighter teal (bottom)
COL_BALL        = (240, 240, 255)
COL_BALL_GLOW   = (180, 210, 255)   # soft blue glow around ball
COL_PADDLE_BODY = (200, 215, 235)   # silver/chrome main bar
COL_PADDLE_HI   = (245, 250, 255)   # bright top edge
COL_PADDLE_GLOW = (120, 200, 255)   # blue glow strip on top
COL_TEXT        = (255, 255, 255)
COL_TEXT_MSG    = (255, 255, 80)
COL_STAR        = (255, 255, 255)   # star particles

# Brick row palette — each row gets a distinct hue (like the reference image).
# Indexed by (row % len(BRICK_ROW_COLORS)).
# Each entry is (R, G, B) for the base face colour.
BRICK_ROW_COLORS = [
    (176,  28,  28),   # red
    (198,  99,  11),   # orange
    (198, 170,  17),   # yellow
    (33,  160,  44),   # green
    (17,  143, 182),   # cyan
    (39,   66, 182),   # blue
    (116,  33, 165),   # purple
    (182,  39, 127),   # pink
]


class Layout:
    """Computes absolute pixel values from fractional constants for a given (w, h)."""

    __slots__ = (
        'w', 'h',
        'ball_r', 'ball_speed', 'ball_glow_r',
        'paddle_w', 'paddle_h', 'paddle_y', 'paddle_speed',
        'brick_cols', 'brick_rows', 'brick_w', 'brick_h',
        'brick_hgap', 'brick_vgap', 'brick_top', 'brick_margin',
        'star_count', 'star_r',
        'hud_font', 'hud_msg_font', 'hud_pad',
    )

    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

        # ball
        self.ball_r      = h * BALL_R_FRAC
        self.ball_speed  = h * BALL_SPEED_FRAC
        self.ball_glow_r = self.ball_r * BALL_GLOW_FRAC

        # paddle
        self.paddle_w     = w * PADDLE_W_FRAC
        self.paddle_h     = h * PADDLE_H_FRAC
        self.paddle_y     = h * PADDLE_Y_FRAC
        self.paddle_speed = w * PADDLE_SPEED_FRAC

        # bricks
        self.brick_cols   = BRICK_COLS
        self.brick_rows   = BRICK_ROWS
        self.brick_margin = w * BRICK_MARGIN_FRAC
        self.brick_hgap   = w * BRICK_HGAP_FRAC
        self.brick_vgap   = h * BRICK_VGAP_FRAC
        self.brick_top    = h * BRICK_TOP_FRAC
        self.brick_h      = h * BRICK_H_FRAC
        # brick_w is derived: fill remaining space between margins and gaps
        usable_w = w - 2 * self.brick_margin - (BRICK_COLS - 1) * self.brick_hgap
        self.brick_w = usable_w / BRICK_COLS

        # starfield
        self.star_count = STAR_COUNT
        self.star_r     = h * STAR_R_FRAC

        # hud
        self.hud_font     = h * HUD_FONT_FRAC
        self.hud_msg_font = h * HUD_MSG_FRAC
        self.hud_pad      = max(w, h) * HUD_PAD_FRAC
