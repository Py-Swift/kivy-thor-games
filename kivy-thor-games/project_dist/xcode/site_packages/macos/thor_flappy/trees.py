import os

from thorvg_cython import Picture, Scene

from .constants import GROUND_H, TREE_SPEED, mat

_SVG_DIR = os.path.join(os.path.dirname(__file__), "svgs")
_SVG_FILES = [
    "tree-svgrepo-com-6.svg",
    "tree-svgrepo-com-7.svg",
    "tree-svgrepo-com-8.svg",
    "tree-svgrepo-com-9.svg",
]

_SVG_TREE_DEFS = [
    (0.03, 110), (0.14,  90), (0.26, 120), (0.37,  95),
    (0.48, 105), (0.59,  85), (0.70, 115), (0.80,  92), (0.91, 100),
]


class TreeLayer(Scene):
    """SVG trees in background — scrolls slowest."""

    def __init__(self, canvas, w, h):
        super().__init__()
        self._trees = []
        ground_top  = h - GROUND_H
        for i, (xf, tree_h) in enumerate(_SVG_TREE_DEFS):
            svg_path = os.path.join(_SVG_DIR, _SVG_FILES[i % len(_SVG_FILES)])
            cx = xf * w
            pic = Picture()
            pic.load(svg_path)
            pic.set_size(tree_h, tree_h)
            pic.set_transform(mat(e13=cx - tree_h / 2, e23=ground_top - tree_h))
            self.add(pic)
            self._trees.append([cx, ground_top, pic, tree_h])
        canvas.add(self)

    def update(self, dt, w):
        for t in self._trees:
            t[0] -= TREE_SPEED * dt
            tree_h = t[3]
            if t[0] < -tree_h:
                t[0] = w + tree_h
            t[2].set_transform(mat(e13=t[0] - tree_h / 2, e23=t[1] - tree_h))
