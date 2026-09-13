"""
ed_stage.py - the shared 3-D stage for the Engineering Drawing series.

One source of truth for the two principal planes, the reference line, the
quadrant wedges and the camera framing, so every episode opens on the same
set. Episodes import from here; only the episode-specific geometry lives in
the episode file.

Axis convention used throughout the series:

    +x  along the reference line, to the right
    -y  IN FRONT OF the VP  (towards the observer)
    +y  BEHIND the VP
    +z  ABOVE the HP
    -z  BELOW the HP

so the VP is the plane y = 0 and the HP is the plane z = 0.
"""

from __future__ import annotations

import numpy as np
from manim import *

from ed_common import (
    CORAL,
    VIOLET,
    SLATE,
    chip,
    GOLD,
    INK,
    MUTED,
    NAVY,
    TEAL,
    billboard,
    hud,
    mono,
    title_bar,
)

HALF_X = 3.5
HALF_Z = 2.2
HALF_Y = 2.2

# Colour carries meaning across the whole series:
#     coral  = the VERTICAL plane and everything that lives on it
#              (the front view, and the projector that lands there)
#     teal   = the HORIZONTAL plane and everything that lives on it
#     gold   = the object itself, out in space
# so a student can tell at a glance which plane a projection belongs to.
VP_COLOR = CORAL
HP_COLOR = TEAL
OBJ_COLOR = GOLD

# Which half of each plane is visible for a given dihedral angle. Showing only
# the quadrant in use is what makes the picture readable - with both halves of
# both planes drawn transparent you cannot tell which side of anything you are
# looking at.
QUADRANT_PARTS = {
    1: ("upper", "front"),
    2: ("upper", "back"),
    3: ("lower", "back"),
    4: ("lower", "front"),
}
# A plane is drawn SOLID when the object lies on the observer's side of it -
# you genuinely cannot see through a sheet of paper - and TRANSPARENT when the
# object is on the far side, which is exactly the glass-box assumption third
# angle projection is built on. So opacity is not decoration here: it is the
# difference between the two projection systems.
#                 VP solid?              HP solid?
QUADRANT_SOLID = {
    1: (True, True),      # in front of the VP, above the HP
    2: (False, True),     # behind the VP  -> the VP cannot hide the object
    3: (False, False),    # behind and below -> both planes are glass
    4: (True, False),     # in front but below the HP
}

QUADRANT_WORDS = {
    1: "1st angle · above the HP, in front of the VP",
    2: "2nd angle · above the HP, behind the VP",
    3: "3rd angle · below the HP, behind the VP",
    4: "4th angle · below the HP, in front of the VP",
}

CAM_PHI = 60 * DEGREES
CAM_THETA = -60 * DEGREES        # observer's side: in front of the VP
#
# Every 3-D scene opens here and stays on this side throughout: the viewer is
# standing where the observer stands, looking at the face of the VP that the
# front view is drawn on. Nothing is ever shown from behind the planes.
FLAT_PHI = 90 * DEGREES
FLAT_THETA = -90 * DEGREES


def _solid_fill(accent, amount=0.22):
    """A dark tint of the accent colour - reads as a surface, and a full
    strength line drawn on it still stands out."""
    return interpolate_color(ManimColor(NAVY), ManimColor(accent), amount)


def vertical_plane(part="full", solid=False, color=VP_COLOR):
    """
    The VP: the plane y = 0.
    part = "full" | "upper" (above XY) | "lower" (below XY).
    """
    z0, z1 = {
        "full": (-HALF_Z, HALF_Z),
        "upper": (0.0, HALF_Z),
        "lower": (-HALF_Z, 0.0),
    }[part]
    face = Polygon(
        np.array([-HALF_X, 0.0, z0]),
        np.array([HALF_X, 0.0, z0]),
        np.array([HALF_X, 0.0, z1]),
        np.array([-HALF_X, 0.0, z1]),
        stroke_color=color,
        stroke_width=2.6,
        fill_color=_solid_fill(color) if solid else color,
        fill_opacity=0.97 if solid else 0.16,
    )
    return VGroup(face)


def horizontal_plane(part="full", solid=False, color=HP_COLOR):
    """
    The HP: the plane z = 0.
    part = "full" | "front" (in front of the VP) | "back" (behind it).
    """
    y0, y1 = {
        "full": (-HALF_Y, HALF_Y),
        "front": (-HALF_Y, 0.0),
        "back": (0.0, HALF_Y),
    }[part]
    face = Polygon(
        np.array([-HALF_X, y0, 0.0]),
        np.array([HALF_X, y0, 0.0]),
        np.array([HALF_X, y1, 0.0]),
        np.array([-HALF_X, y1, 0.0]),
        stroke_color=color,
        stroke_width=2.6,
        fill_color=_solid_fill(color) if solid else color,
        fill_opacity=0.97 if solid else 0.16,
    )
    return VGroup(face)


WEDGE_Y = 1.8    # cross-section half-extents - kept inside the plane outlines
WEDGE_Z = 1.8


def quadrant_wedge(sign_y, sign_z, color, x=2.1, opacity=0.34):
    """
    One quarter of the cross-section at station `x`, bounded by the two planes.
    sign_y = -1 in front of the VP, +1 behind it.
    sign_z = +1 above the HP,       -1 below it.
    """
    return Polygon(
        np.array([x, 0.0, 0.0]),
        np.array([x, sign_y * WEDGE_Y, 0.0]),
        np.array([x, sign_y * WEDGE_Y, sign_z * WEDGE_Z]),
        np.array([x, 0.0, sign_z * WEDGE_Z]),
        stroke_color=color,
        stroke_width=2.0,
        fill_color=color,
        fill_opacity=opacity,
    )


def reference_line():
    return Line(
        np.array([-HALF_X - 0.5, 0, 0]),
        np.array([HALF_X + 0.5, 0, 0]),
        color=INK,
        stroke_width=4.5,
    )


def marker(point, color, radius=0.085):
    return Dot3D(point=np.array(point, dtype=float), radius=radius, color=color)


def projector(start, end, color=MUTED):
    return DashedLine(
        np.array(start, dtype=float),
        np.array(end, dtype=float),
        color=color,
        stroke_width=2.2,
        dash_length=0.11,
    )


class ProjectionScene(ThreeDScene):
    """Common setup so every 3-D scene opens on the same stage."""

    heading = ""
    subheading = ""

    quadrant = 1          # set to None to show all four (whole planes)

    def build_stage(self, with_labels=True, quadrant="inherit"):
        """
        Set the stage. By default only the quadrant named by `self.quadrant` is
        drawn - one half of each plane - so there is never any doubt about which
        side of a plane you are looking at, or which plane a projection is on.
        Pass quadrant=None for the whole-space picture (all four angles).
        """
        q = self.quadrant if quadrant == "inherit" else quadrant

        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=CAM_PHI, theta=CAM_THETA, zoom=0.88)

        vp_part, hp_part = QUADRANT_PARTS[q] if q else ("full", "full")
        vp_solid, hp_solid = QUADRANT_SOLID[q] if q else (False, False)
        self.vp = vertical_plane(vp_part, solid=vp_solid)
        self.hp = horizontal_plane(hp_part, solid=hp_solid)
        self.xy = reference_line()

        self.bar = hud(self, title_bar(self.heading, self.subheading))

        # park each plane's name inside the half that is actually drawn
        vp_z = {"upper": 1.65, "lower": -1.65, "full": 1.8}[vp_part]
        hp_y = {"front": -1.6, "back": 1.6, "full": -1.75}[hp_part]
        vp_tag = mono("VP", color=VP_COLOR, size=26).move_to([-2.7, 0, vp_z])
        hp_tag = mono("HP", color=HP_COLOR, size=26).move_to([-2.7, hp_y, 0])
        xy_tag = mono("X", color=INK, size=24).move_to([-HALF_X - 0.95, 0, -0.28])
        yx_tag = mono("Y", color=INK, size=24).move_to([HALF_X + 0.95, 0, -0.28])
        self.tags = VGroup(vp_tag, hp_tag, xy_tag, yx_tag)
        if with_labels:
            billboard(self, vp_tag, hp_tag, xy_tag, yx_tag)

        # a standing badge saying which dihedral angle we are working in
        self.badge = None
        if q:
            colour = {1: GOLD, 2: SLATE, 3: VIOLET, 4: SLATE}[q]
            self.badge = hud(
                self,
                chip(QUADRANT_WORDS[q], color=colour, size=18).to_corner(
                    UP + RIGHT, buff=0.45
                ),
            )
            self.add(self.badge)


def unfold_camera(scene, run_time=2.6):
    """Settle the camera square on to the VP - the flat drawing sheet."""
    scene.move_camera(phi=FLAT_PHI, theta=FLAT_THETA, zoom=0.95, run_time=run_time)
