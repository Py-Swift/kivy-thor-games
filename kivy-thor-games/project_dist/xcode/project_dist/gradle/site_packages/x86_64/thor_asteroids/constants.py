# ── collision types ────────────────────────────────────────────────────────────
CT_SHIP     = 1
CT_ASTEROID = 2
CT_BULLET   = 3

# ── lives ─────────────────────────────────────────────────────────────────────
LIVES = 3

# ── game states ───────────────────────────────────────────────────────────────
ST_IDLE      = 0
ST_PLAYING   = 1
ST_GAME_OVER = 2

# ── proportional constants (fractions of w or h) ─────────────────────────────

# ship
SHIP_SIZE_FRAC    = 0.028   # ship "radius" as fraction of h
SHIP_THRUST_FRAC  = 0.35    # thrust acceleration as fraction of h/s²
SHIP_MAX_SPD_FRAC = 0.55    # max speed as fraction of h/s
SHIP_DRAG         = 0.98    # per-frame velocity damping
SHIP_ROTATE_SPEED = 4.5     # radians per second
SHIP_INVULN_DUR   = 2.5     # seconds of invulnerability after respawn

# bullets
BULLET_SPEED_FRAC = 0.7     # bullet speed as fraction of h/s
BULLET_R_FRAC     = 0.004   # bullet radius as fraction of h
BULLET_LIFETIME   = 1.2     # seconds before bullet despawns
BULLET_COOLDOWN   = 0.15    # min seconds between shots
MAX_BULLETS       = 6

# asteroids
ASTEROID_SPEED_FRAC = 0.08  # base drift speed as fraction of h/s
ASTEROID_SIZES = {
    'large':  0.06,          # radius as fraction of h
    'medium': 0.035,
    'small':  0.018,
}
ASTEROID_SCORES = {
    'large':  20,
    'medium': 50,
    'small':  100,
}
INITIAL_ASTEROIDS = 4

# starfield
STAR_COUNT   = 100
STAR_R_FRAC  = 0.002

# hud
HUD_FONT_FRAC = 0.028
HUD_MSG_FRAC  = 0.045
HUD_PAD_FRAC  = 0.015

# ── colors ────────────────────────────────────────────────────────────────────
COL_BG           = (2, 2, 8)
COL_SHIP         = (0, 220, 255)
COL_SHIP_THRUST  = (255, 80, 0)
COL_BULLET       = (255, 255, 50)
COL_BULLET_GLOW  = (255, 220, 0)
COL_ASTEROID     = (0, 255, 70)
COL_STAR         = (255, 255, 255)
COL_TEXT         = (255, 255, 255)
COL_TEXT_MSG     = (255, 255, 0)

# neon stroke widths (as fraction of h)
STROKE_CORE_FRAC  = 0.0025   # thin bright line (100% alpha)
STROKE_GLOW_FRAC  = 0.005    # medium stroke (2× core, 70% alpha)
STROKE_BLOOM_FRAC = 0.020    # wide soft bloom halo (8× core, ~15% alpha)


class Layout:
    """Computes absolute pixel values from fractional constants for a given (w, h)."""

    __slots__ = (
        'w', 'h',
        'ship_size', 'ship_thrust', 'ship_max_speed',
        'bullet_speed', 'bullet_r',
        'asteroid_radii', 'asteroid_base_speed',
        'star_count', 'star_r',
        'hud_font', 'hud_msg_font', 'hud_pad',
        'stroke_core', 'stroke_glow', 'stroke_bloom',
    )

    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

        # ship
        self.ship_size      = h * SHIP_SIZE_FRAC
        self.ship_thrust    = h * SHIP_THRUST_FRAC
        self.ship_max_speed = h * SHIP_MAX_SPD_FRAC

        # bullets
        self.bullet_speed = h * BULLET_SPEED_FRAC
        self.bullet_r     = h * BULLET_R_FRAC

        # asteroids
        self.asteroid_radii = {k: h * v for k, v in ASTEROID_SIZES.items()}
        self.asteroid_base_speed = h * ASTEROID_SPEED_FRAC

        # starfield
        self.star_count = STAR_COUNT
        self.star_r     = h * STAR_R_FRAC

        # hud
        self.hud_font     = h * HUD_FONT_FRAC
        self.hud_msg_font = h * HUD_MSG_FRAC
        self.hud_pad      = max(w, h) * HUD_PAD_FRAC

        # neon strokes
        self.stroke_core  = max(1.0, h * STROKE_CORE_FRAC)
        self.stroke_glow  = max(3.0, h * STROKE_GLOW_FRAC)
        self.stroke_bloom = max(6.0, h * STROKE_BLOOM_FRAC)
