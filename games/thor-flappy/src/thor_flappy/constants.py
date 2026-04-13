import math

from thorvg_cython import Matrix

GRAVITY       = 500.0
JUMP_VEL      = -240.0
PIPE_SPEED    = 200.0
PIPE_WIDTH    = 72
PIPE_GAP      = 165
PIPE_CAP_H    = 26
GROUND_H      = 70
PIPE_INTERVAL = 1.55
MAX_PIPES     = 5

IDLE    = 0
PLAYING = 1
DEAD    = 2

DESIGN_H = 600.0

BUSH_SPEED = PIPE_SPEED * 0.55
TREE_SPEED = PIPE_SPEED * 0.32


def mat(e11=1.0, e12=0.0, e13=0.0, e21=0.0, e22=1.0, e23=0.0):
    m = Matrix()
    m.e11 = e11; m.e12 = e12; m.e13 = e13
    m.e21 = e21; m.e22 = e22; m.e23 = e23
    m.e31 = 0.0; m.e32 = 0.0; m.e33 = 1.0
    return m


def rot(angle_rad, tx, ty):
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return mat(c, -s, tx, s, c, ty)
