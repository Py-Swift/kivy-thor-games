import os

from thorvg_cython import Scene, Text, Shape, Matrix, LinearGradient, ColorStop

from .constants import (
    COL_TEXT, COL_TEXT_MSG, COL_TEXT_DIM, PIECE_COLORS,
    PREVIEW_SIZE, HOLD_SIZE, Layout,
)
from .tetromino import SHAPES
from .board import _brighten, _darken

# ── font loading ──────────────────────────────────────────────────────────────
_FONT_LOADED = False
_FONT_NAME = 'Roboto-Bold'


def _ensure_font():
    global _FONT_LOADED
    if _FONT_LOADED:
        return
    _FONT_LOADED = True
    try:
        import kivy as _kivy
        path = os.path.join(os.path.dirname(_kivy.__file__), 'data', 'fonts', 'Roboto-Bold.ttf')
        Text.font_load(path)
    except Exception:
        pass


class Hud(Scene):
    """Score, level, lines, next preview, hold preview, centre message."""

    def __init__(self, layout: Layout):
        _ensure_font()
        super().__init__()

        # text labels
        self._score_label = Text()
        self._score_val = Text()
        self._level_label = Text()
        self._level_val = Text()
        self._lines_label = Text()
        self._lines_val = Text()
        self._next_label = Text()
        self._hold_label = Text()
        self._msg_text = Text()

        for t in (self._score_label, self._score_val,
                  self._level_label, self._level_val,
                  self._lines_label, self._lines_val,
                  self._next_label, self._hold_label, self._msg_text):
            self.add(t)

        # preview piece shapes (4 cells each)
        self._next_shapes = [Shape() for _ in range(4)]
        self._hold_shapes = [Shape() for _ in range(4)]
        for s in self._next_shapes + self._hold_shapes:
            self.add(s)

        self._score = 0
        self._level = 1
        self._lines = 0
        self._next_type = 0
        self._hold_type = 0
        self._build(layout)

    def _build(self, lo: Layout):
        self._lo = lo
        font = lo.hud_font
        vfont = lo.hud_val_font

        # ── next preview label (right of board) ──
        self._next_label.set_font(_FONT_NAME)
        self._next_label.set_size(font)
        self._next_label.set_color(*COL_TEXT_DIM)
        self._next_label.set_text('NEXT')
        self._next_label.layout(lo.cell * 5, font * 1.5)
        m = Matrix()
        m.e13 = lo.preview_x
        m.e23 = lo.preview_y - font * 1.6
        self._next_label.set_transform(m)

        # score / level / lines (below next preview, right of board)
        info_x = lo.preview_x
        info_y = lo.preview_y + PREVIEW_SIZE * lo.preview_cell + lo.cell * 1.2
        spacing = vfont * 2.5

        self._setup_label_val(self._score_label, self._score_val,
                              'SCORE', str(self._score),
                              info_x, info_y, font, vfont, lo)
        self._setup_label_val(self._level_label, self._level_val,
                              'LEVEL', str(self._level),
                              info_x, info_y + spacing, font, vfont, lo)
        self._setup_label_val(self._lines_label, self._lines_val,
                              'LINES', str(self._lines),
                              info_x, info_y + spacing * 2, font, vfont, lo)

        # ── hold preview label (left of board) ──
        self._hold_label.set_font(_FONT_NAME)
        self._hold_label.set_size(font)
        self._hold_label.set_color(*COL_TEXT_DIM)
        self._hold_label.set_text('HOLD')
        self._hold_label.layout(lo.cell * 5, font * 1.5)
        m = Matrix()
        m.e13 = lo.hold_x
        m.e23 = lo.hold_y - font * 1.6
        self._hold_label.set_transform(m)

        # ── centre message ──
        self._msg_text.set_font(_FONT_NAME)
        self._msg_text.set_size(lo.hud_msg_font)
        self._msg_text.set_color(*COL_TEXT_MSG)
        msg_w = lo.board_w * 0.8
        msg_h = lo.hud_msg_font * 2.5
        self._msg_text.layout(msg_w, msg_h)
        self._msg_text.align(0.5, 0.5)
        m = Matrix()
        m.e13 = lo.board_x + (lo.board_w - msg_w) / 2
        m.e23 = lo.board_y + lo.board_h * 0.4
        self._msg_text.set_transform(m)

        # redraw previews
        self._draw_preview(self._next_shapes, self._next_type,
                           lo.preview_x, lo.preview_y, lo.preview_cell)
        self._draw_preview(self._hold_shapes, self._hold_type,
                           lo.hold_x, lo.hold_y, lo.preview_cell)

    def _setup_label_val(self, label: Text, val: Text,
                         label_str: str, val_str: str,
                         x: float, y: float,
                         font: float, vfont: float, lo: Layout):
        label.set_font(_FONT_NAME)
        label.set_size(font)
        label.set_color(*COL_TEXT_DIM)
        label.set_text(label_str)
        label.layout(lo.cell * 6, font * 1.5)
        m = Matrix()
        m.e13 = x
        m.e23 = y
        label.set_transform(m)

        val.set_font(_FONT_NAME)
        val.set_size(vfont)
        val.set_color(*COL_TEXT)
        val.set_text(val_str)
        val.layout(lo.cell * 6, vfont * 1.5)
        m2 = Matrix()
        m2.e13 = x
        m2.e23 = y + font * 1.3
        val.set_transform(m2)

    def _draw_preview(self, shapes: list[Shape], piece_type: int,
                      px: float, py: float, cell: float):
        for s in shapes:
            s.reset()
        if piece_type == 0:
            return

        offsets = SHAPES[piece_type][0]  # spawn rotation
        base = PIECE_COLORS[piece_type]
        hi = _brighten(base, 60)
        dk = _darken(base, 40)
        pad = cell * 0.08
        rx = cell * 0.12

        # center the piece in the preview box
        min_r = min(dr for dr, dc in offsets)
        max_r = max(dr for dr, dc in offsets)
        min_c = min(dc for dr, dc in offsets)
        max_c = max(dc for dr, dc in offsets)
        piece_w = (max_c - min_c + 1) * cell
        piece_h = (max_r - min_r + 1) * cell
        box_w = PREVIEW_SIZE * cell
        box_h = PREVIEW_SIZE * cell
        off_x = px + (box_w - piece_w) / 2 - min_c * cell
        off_y = py + (box_h - piece_h) / 2 - min_r * cell

        for i, (dr, dc) in enumerate(offsets):
            x = off_x + dc * cell
            y = off_y + dr * cell
            shp = shapes[i]
            shp.append_rect(x + pad, y + pad, cell - 2 * pad, cell - 2 * pad, rx=rx, ry=rx)
            lg = LinearGradient()
            lg.set(x, y, x, y + cell)
            lg.set_color_stops([
                ColorStop(0.0, *hi, 255),
                ColorStop(0.4, *base, 255),
                ColorStop(1.0, *dk, 255),
            ])
            shp.set_gradient(lg)

    # ── public API ────────────────────────────────────────────────────────────

    def set_score(self, n: int):
        self._score = n
        self._score_val.set_text(str(n))

    def set_level(self, n: int):
        self._level = n
        self._level_val.set_text(str(n))

    def set_lines(self, n: int):
        self._lines = n
        self._lines_val.set_text(str(n))

    def set_next(self, piece_type: int):
        self._next_type = piece_type
        lo = self._lo
        self._draw_preview(self._next_shapes, piece_type,
                           lo.preview_x, lo.preview_y, lo.preview_cell)

    def set_hold(self, piece_type: int):
        self._hold_type = piece_type
        lo = self._lo
        self._draw_preview(self._hold_shapes, piece_type,
                           lo.hold_x, lo.hold_y, lo.preview_cell)

    def show_message(self, text: str):
        self._msg_text.set_text(text)
        self._msg_text.set_opacity(255)

    def hide_message(self):
        self._msg_text.set_opacity(0)

    def rebuild(self, layout: Layout):
        self._build(layout)
