import random

# ── piece type IDs (match PIECE_COLORS keys in constants.py) ─────────────────
I, O, T, S, Z, J, L = 1, 2, 3, 4, 5, 6, 7

ALL_TYPES = (I, O, T, S, Z, J, L)

# ── rotation states ──────────────────────────────────────────────────────────
# Each piece has 4 rotation states (0=spawn, 1=CW, 2=180, 3=CCW).
# Each state is a tuple of 4 (row, col) offsets from the piece origin.
# Offsets are relative to the piece's logical center.

SHAPES = {
    I: (
        ((0, -1), (0, 0), (0, 1), (0, 2)),
        ((-1, 1), (0, 1), (1, 1), (2, 1)),
        ((1, -1), (1, 0), (1, 1), (1, 2)),
        ((-1, 0), (0, 0), (1, 0), (2, 0)),
    ),
    O: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    T: (
        ((0, -1), (0, 0), (0, 1), (-1, 0)),
        ((-1, 0), (0, 0), (1, 0), (0, 1)),
        ((0, -1), (0, 0), (0, 1), (1, 0)),
        ((-1, 0), (0, 0), (1, 0), (0, -1)),
    ),
    S: (
        ((0, -1), (0, 0), (-1, 0), (-1, 1)),
        ((-1, 0), (0, 0), (0, 1), (1, 1)),
        ((1, -1), (1, 0), (0, 0), (0, 1)),
        ((-1, -1), (0, -1), (0, 0), (1, 0)),
    ),
    Z: (
        ((-1, -1), (-1, 0), (0, 0), (0, 1)),
        ((-1, 1), (0, 0), (0, 1), (1, 0)),
        ((0, -1), (0, 0), (1, 0), (1, 1)),
        ((-1, 0), (0, -1), (0, 0), (1, -1)),
    ),
    J: (
        ((-1, -1), (0, -1), (0, 0), (0, 1)),
        ((-1, 0), (-1, 1), (0, 0), (1, 0)),
        ((0, -1), (0, 0), (0, 1), (1, 1)),
        ((-1, 0), (0, 0), (1, -1), (1, 0)),
    ),
    L: (
        ((-1, 1), (0, -1), (0, 0), (0, 1)),
        ((-1, 0), (0, 0), (1, 0), (1, 1)),
        ((0, -1), (0, 0), (0, 1), (1, -1)),
        ((-1, -1), (-1, 0), (0, 0), (1, 0)),
    ),
}

# ── SRS wall kick data ───────────────────────────────────────────────────────
# kick_offsets[(from_rot, to_rot)] → tuple of (dcol, drow) offsets to try.
# Standard SRS tables for J/L/S/T/Z and a separate one for I.

_KICKS_JLSTZ = {
    (0, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (1, 0): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (1, 2): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (2, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (2, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (3, 2): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (3, 0): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (0, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
}

_KICKS_I = {
    (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (1, 0): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    (2, 1): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (2, 3): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (3, 0): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
}

KICK_TABLE = {
    I: _KICKS_I,
    O: {},  # O doesn't rotate
}
for _t in (J, L, S, T, Z):
    KICK_TABLE[_t] = _KICKS_JLSTZ

# ── T-spin corner positions ──────────────────────────────────────────────────
# The 4 diagonal corners around the T piece center.
# A T-spin is detected when at least 3 of these 4 cells are occupied,
# and the last move was a rotation.
T_CORNERS = ((-1, -1), (-1, 1), (1, 1), (1, -1))

# For each rotation state, which 2 corners are the "front" corners.
# If both front corners are filled → proper T-spin; else → T-spin mini.
T_FRONT_CORNERS = {
    0: ((-1, -1), (-1, 1)),   # top-left, top-right
    1: ((-1, 1), (1, 1)),     # top-right, bot-right
    2: ((1, 1), (1, -1)),     # bot-right, bot-left
    3: ((1, -1), (-1, -1)),   # bot-left, top-left
}


class PieceBag:
    """7-bag randomizer: shuffle all 7 piece types, deal in order, repeat."""

    def __init__(self):
        self._bag: list[int] = []

    def next(self) -> int:
        if not self._bag:
            self._bag = list(ALL_TYPES)
            random.shuffle(self._bag)
        return self._bag.pop()

    def peek(self) -> int:
        """Look at next piece without consuming it."""
        if not self._bag:
            self._bag = list(ALL_TYPES)
            random.shuffle(self._bag)
        return self._bag[-1]
