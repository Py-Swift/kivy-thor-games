import random

from thorvg_cython import Scene, Shape, LinearGradient, ColorStop

from .constants import (
    PIPE_SPEED, PIPE_WIDTH, PIPE_GAP, PIPE_CAP_H,
    PIPE_INTERVAL, MAX_PIPES, mat,
)


class PipeLayer(Scene):
    def __init__(self, canvas, h):
        super().__init__()
        self._slots   = []
        self._pipes   = []
        self._timer   = 0.0
        self._counter = 0
        self._h       = h
        for _ in range(MAX_PIPES):
            parts = [Shape() for _ in range(4)]
            for p in parts:
                self.add(p)
            self._slots.append(parts)
        canvas.add(self)

    def reset(self):
        self._pipes.clear()
        self._timer   = 0.0
        self._counter = 0
        for slot in self._slots:
            for s in slot:
                s.reset()

    def tick(self, dt, w, ground_y, bird_x, on_score):
        self._timer += dt
        if self._timer >= PIPE_INTERVAL:
            self._timer = 0.0
            slot = self._counter % MAX_PIPES
            self._counter += 1
            min_cy = 80 + PIPE_GAP / 2
            max_cy = ground_y - PIPE_GAP / 2 - 20
            self._pipes.append([float(w) + 10, random.uniform(min_cy, max_cy), False, slot])

        for p in self._pipes:
            p[0] -= PIPE_SPEED * dt
        self._pipes = [p for p in self._pipes if p[0] > -PIPE_WIDTH - 30]

        active = set()
        for p in self._pipes:
            if not p[2] and p[0] + PIPE_WIDTH < bird_x:
                p[2] = True
                on_score()
            self._draw(p[3], p[0], p[1], ground_y)
            active.add(p[3])
        for i in range(MAX_PIPES):
            if i not in active:
                self._clear(i)

    def check_collision(self, bird_x, bird_y, bird_r):
        for p in self._pipes:
            px, gap_cy = p[0], p[1]
            if bird_x + bird_r > px and bird_x - bird_r < px + PIPE_WIDTH:
                if (bird_y - bird_r < gap_cy - PIPE_GAP / 2 or
                        bird_y + bird_r > gap_cy + PIPE_GAP / 2):
                    return True
        return False

    def _draw(self, slot, px, gap_cy, ground_top):
        top_body, bot_body, top_cap, bot_cap = self._slots[slot]
        cap_x     = px - 8
        cap_w     = PIPE_WIDTH + 16
        top_end   = gap_cy - PIPE_GAP / 2
        bot_start = gap_cy + PIPE_GAP / 2

        top_body.reset()
        if top_end > PIPE_CAP_H:
            top_body.append_rect(px, 0, PIPE_WIDTH, top_end - PIPE_CAP_H)
            self._pipe_gradient(top_body, px, 75, 175, 55)

        top_cap.reset()
        if top_end > 0:
            top_cap.append_rect(cap_x, max(0, top_end - PIPE_CAP_H),
                                 cap_w, min(PIPE_CAP_H, top_end), rx=4, ry=4)
            self._pipe_gradient(top_cap, cap_x, 55, 155, 40)

        bot_body.reset()
        bot_top = bot_start + PIPE_CAP_H
        if bot_top < ground_top:
            bot_body.append_rect(px, bot_top, PIPE_WIDTH, ground_top - bot_top)
            self._pipe_gradient(bot_body, px, 75, 175, 55)

        bot_cap.reset()
        if bot_start < ground_top:
            bot_cap.append_rect(cap_x, bot_start, cap_w,
                                 min(PIPE_CAP_H, ground_top - bot_start), rx=4, ry=4)
            self._pipe_gradient(bot_cap, cap_x, 55, 155, 40)

    def _clear(self, slot):
        for s in self._slots[slot]:
            s.reset()

    @staticmethod
    def _pipe_gradient(shape, px, r, g, b):
        lg = LinearGradient()
        lg.set(px, 0, px + PIPE_WIDTH, 0)
        lg.set_color_stops([
            ColorStop(0.0,  max(r-20, 0), max(g-20, 0), max(b-20, 0), 255),
            ColorStop(0.30, min(r+70, 255), min(g+70, 255), min(b+70, 255), 255),
            ColorStop(0.60, r, g, b, 255),
            ColorStop(1.0,  max(r-30, 0), max(g-30, 0), max(b-30, 0), 255),
        ])
        shape.set_gradient(lg)
