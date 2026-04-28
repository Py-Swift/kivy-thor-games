"""
Perspective projection — numpy-free, iOS-safe.

Coordinate convention (track space):
    X = horizontal (lane offset from cylinder axis)
    Y = height above ground
    Z = forward (increasing as player advances)

Camera looks along +Z.  Screen origin is top-left; Y increases downward in
screen space, so we flip Y when mapping to 2-D.
"""
from __future__ import annotations

import math


class Camera3D:
    """Minimal perspective camera.

    pos     — 3-D position in track space
    fov_deg — vertical field-of-view in degrees
    """

    def __init__(self):
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
        self.pos_z: float = 0.0
        self.fov_deg: float = 45.0
        # rotation of the track cylinder (degrees) — keeps current lane at bottom
        self.rotation: float = 0.0

    def set_pos(self, x: float, y: float, z: float) -> None:
        self.pos_x = x
        self.pos_y = y
        self.pos_z = z

    def project(self, px: float, py: float, pz: float,
                sw: float, sh: float) -> tuple[float, float] | None:
        """Project a 3-D point to screen (x, y).

        Returns None if the point is behind the camera.
        """
        # translate relative to camera
        rx = px - self.pos_x
        ry = py - self.pos_y
        rz = pz - self.pos_z

        if rz <= 0.001:
            return None

        half_fov = math.radians(self.fov_deg / 2.0)
        f = 1.0 / math.tan(half_fov)
        aspect = sw / sh

        sx = (f / aspect) * (rx / rz)
        sy = f * (ry / rz)

        # map NDC (-1..1) → screen pixels, flip Y
        screen_x = sw * (0.5 + sx * 0.5)
        screen_y = sh * (0.5 - sy * 0.5)

        return screen_x, screen_y


def rotate_xy(x: float, y: float, angle_deg: float) -> tuple[float, float]:
    """Rotate a 2-D point (x, y) around the origin by angle_deg degrees."""
    rad = math.radians(angle_deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return c * x - s * y, s * x + c * y


def lane_angle(lane: int, total_lanes: int, rotation_deg: float = 0.0) -> float:
    """Return the angle (degrees) of a lane vertex on the cylinder cross-section."""
    return lane * (360.0 / total_lanes) + rotation_deg


def ring_point(lane: int, total_lanes: int, radius: float,
               z: float, rotation_deg: float = 0.0
               ) -> tuple[float, float, float]:
    """3-D position of the lane vertex on a cylinder ring at depth z."""
    ang = math.radians(lane_angle(lane, total_lanes, rotation_deg))
    return radius * math.cos(ang), radius * math.sin(ang), z
