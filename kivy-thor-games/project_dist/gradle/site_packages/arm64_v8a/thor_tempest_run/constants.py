# ── game states ───────────────────────────────────────────────────────────────
ST_IDLE    = 0
ST_PLAYING = 1
ST_DEAD    = 2
ST_PAUSE   = 3

# ── player modes ──────────────────────────────────────────────────────────────
PM_RUN   = 0
PM_JUMP  = 1
PM_SLIDE = 2

# ── track ─────────────────────────────────────────────────────────────────────
LANE_COUNT = 9

# ── physics ───────────────────────────────────────────────────────────────────
GRAVITY          = -1500.0   # px/s² (screen-space)
JUMP_IMPULSE     = 5.0       # normalised units/s (scaled to track units)
JUMP_FALL_RATE   = 25.0      # normalised units/s² (fall gravity in track space)
JUMP_BOOST       = 10.0      # extra hold-down reduction
JUMP_FAST_FALL   = 30.0      # extra when slide pressed while airborne
JUMP_CLEARANCE   = 0.1       # normalised player Y that clears spikes

# ── world-unit geometry (fixed, matches original pygame game) ────────────────
FOV_DEGREES     = 45.0
TRACK_RADIUS    = 10.0   # cylinder radius (world units)
CAMERA_Z_OFFSET = 44.0   # camera sits this many world units behind player
CAMERA_Y        = -1.0   # camera Y offset below axis
TRACK_DEPTH     = 150.0  # visible tunnel depth (world units / foresight)
RING_STEP       = 20.0   # z-distance between cross-section rings (world units, = CELL_LENGTH)

# player
PLAYER_ANIM_FPS = 8      # wireframe animation frames per second
PLAYER_W_FRAC   = 0.150  # player wireframe width as fraction of screen height
PLAYER_H_FRAC   = 0.135  # player wireframe height as fraction of screen height

# speed curve  [(z, units/s), …]  — same inflection points as original
SPEED_CURVE = [
    (0,      60),
    (3000,   90),
    (10000,  120),
    (100000, 200),
]
CELL_LENGTH = 20  # obstacle grid cell length in track units

# ── neon stroke widths (fraction of view height) ─────────────────────────────
STROKE_CORE_FRAC  = 0.0022
STROKE_GLOW_FRAC  = 0.0044
STROKE_BLOOM_FRAC = 0.018

# ── colors ────────────────────────────────────────────────────────────────────
COL_BG       = (2,   4,  12)
COL_TRACK    = (0,  84, 247)    # BLUE
COL_PLAYER   = (0, 220, 255)    # CYAN
COL_SPIKE    = (231,  0,   0)   # RED
COL_ENEMY    = (123, 255,  0)   # LIME
COL_WALL     = (154,  0, 154)   # PURPLE
COL_DEBRIS   = (255, 140,  0)   # ORANGE
COL_TEXT     = (220, 220, 255)
COL_TEXT_MSG = (255, 255,   0)

# ── track color palette (cycles with distance) ───────────────────────────────
TRACK_COLORS = [
    (0,  84, 247),    # blue
    (0, 255, 255),    # cyan
    (220, 220, 255),  # white
    (251, 208, 0),    # yellow
    (255, 70, 0),     # orange
]
TRACK_COLOR_DIST = 1000  # units between color transitions

# ── hud ───────────────────────────────────────────────────────────────────────
HUD_FONT_FRAC = 0.028
HUD_MSG_FRAC  = 0.045
HUD_PAD_FRAC  = 0.015

# ── debris ────────────────────────────────────────────────────────────────────
DEBRIS_COUNT   = 18
DEBRIS_TTL     = 1.2   # seconds
DEBRIS_R_FRAC  = 0.006
DEBRIS_SPEED_FRAC = 0.5  # fraction of view height per second (impulse magnitude)


class Layout:
    """All pixel-space constants derived from window (w, h)."""

    __slots__ = (
        'w', 'h',
        'track_radius', 'track_depth', 'ring_step', 'camera_z_offset', 'camera_y',
        'player_w', 'player_h',
        'debris_r', 'debris_speed',
        'hud_font', 'hud_msg_font', 'hud_pad',
        'stroke_core', 'stroke_glow', 'stroke_bloom',
    )

    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h
        ref = min(w, h)

        # 3-D world-unit geometry (fixed, not screen-relative)
        self.track_radius    = TRACK_RADIUS
        self.camera_z_offset = CAMERA_Z_OFFSET
        self.camera_y        = CAMERA_Y
        self.track_depth     = TRACK_DEPTH
        self.ring_step       = RING_STEP

        # Player wireframe size in screen pixels
        self.player_w = h * PLAYER_W_FRAC
        self.player_h = h * PLAYER_H_FRAC

        self.debris_r     = ref * DEBRIS_R_FRAC
        self.debris_speed = ref * DEBRIS_SPEED_FRAC

        self.hud_font     = h * HUD_FONT_FRAC
        self.hud_msg_font = h * HUD_MSG_FRAC
        self.hud_pad      = max(w, h) * HUD_PAD_FRAC

        self.stroke_core  = max(1.0, h * STROKE_CORE_FRAC)
        self.stroke_glow  = max(2.0, h * STROKE_GLOW_FRAC)
        self.stroke_bloom = max(5.0, h * STROKE_BLOOM_FRAC)
