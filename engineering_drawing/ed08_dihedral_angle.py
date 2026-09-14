"""
Engineering Drawing I - Sheet 4 / Lecture 4  (Basic Descriptive Geometry II)
Episode 08: The True Angle Between Two Planes - the dihedral angle
            + worked solution to Exercise 4 (Set A), Q.12  (Figure P4.12)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed08_dihedral_angle.py S03_Construction
    ... or use render_ed08.bat to build all four scenes in order.

Scene order (about eight minutes in all):

    S01_Dihedral      what the angle between two planes IS: the two faces are
                      folded open about their common edge in front of you, and
                      then the camera goes and looks down that edge, where the
                      hinge becomes a point and both faces become lines - which
                      is the whole method, watched rather than asserted
    S02_Strategy      the two auxiliaries, and why a line can only reach a point
                      view from a view that already shows it true length
    S03_Construction  Q.12 solved on one sheet, the camera following the chain
    S04_Recap         the method in four lines, and where it is used next

Everything is computed from the given dimensions by solve(), which asserts that
the first auxiliary really shows BC at true length, that the second really
reduces it to a point, and that the angle then read off the drawing equals the
dihedral angle computed from the space coordinates. If a number here is wrong
the render stops rather than teaching it.

No LaTeX anywhere - every glyph is Unicode Text().
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

from ed_stage import CAM_PHI, CAM_THETA, ProjectionScene, marker
from ed_common import (
    CORAL,
    GOLD,
    INK,
    MUTED,
    NAVY,
    SLATE,
    VIOLET,
    billboard,
    caption,
    card_back,
    chip,
    finish_audio,
    fly_camera,
    frame_target,
    hud,
    look_at,
    mono,
    narrate,
    pin_to_frame,
    rail_focus,
    title_bar,
)

# ==========================================================================
#  Figure P4.12, read off the given:  (x along XY, d in front of the VP,
#  h above the HP), in millimetres.
#
#  The chain along XY is 26 | 10 | 38, which fixes the four projectors at
#  0, 26, 36 and 74; the heights above XY are 44, 50, 18 and 54; the depths
#  below it are 70, 58, 48 and 12.
# ==========================================================================
SPACE = {
    "A": np.array([0.0,  70.0, 44.0]),
    "B": np.array([74.0, 58.0, 50.0]),
    "C": np.array([36.0, 48.0, 18.0]),
    "D": np.array([26.0, 12.0, 54.0]),
}
FACES = (("A", "B", "C"), ("D", "B", "C"))      # they share the edge BC
HINGE = ("B", "C")
ALL = ("A", "B", "C", "D")

# One colour per FACE, kept in every view, because the whole lesson is about
# what happens to those two faces. The hinge they share is gold - it is the
# thing every construction line on the sheet is aiming at.
F1_COL = VIOLET          # face A B C
F2_COL = CORAL           # face D B C
HINGE_COL = GOLD

GAPS = (40.0, 15.0)      # X1Y1 and X2Y2 set-backs. 40 rather than 32 for the
                         # first one: a is the deepest point in the top view and
                         # a tighter gap runs X1Y1 almost through it.

MM = 0.024               # drawing millimetre -> Manim unit (the flat sheet)
S3 = 0.029               # millimetre -> Manim unit on the 3-D stage
X_MID = 37.0             # the x that is centred on the 3-D stage


def _project(src, origin, along, normal, dist):
    """Drop each point onto the new reference line, then step off its distance."""
    return {k: origin + along * np.dot(src[k] - origin, along) + normal * dist[k]
            for k in src}


def rotate_about(v, axis, angle):
    """Rodrigues: turn `v` about a unit `axis` by `angle` radians."""
    return (v * math.cos(angle) + np.cross(axis, v) * math.sin(angle)
            + axis * float(np.dot(axis, v)) * (1.0 - math.cos(angle)))


def solve(gaps=GAPS):
    P = SPACE
    A, B, C, D = (P[k] for k in ALL)

    # ---- the true dihedral angle, straight from the geometry --------------
    # Drop each far corner onto the plane perpendicular to the hinge: the angle
    # between what is left is the angle the two faces open at.
    e = (C - B) / np.linalg.norm(C - B)
    vA = (A - B) - np.dot(A - B, e) * e
    vD = (D - B) - np.dot(D - B, e) * e
    theta = math.degrees(math.acos(np.dot(vA, vD)
                                   / (np.linalg.norm(vA) * np.linalg.norm(vD))))

    # cross-check against the two face normals - a different route to the
    # same number, so a slip in either one shows up here
    n1 = np.cross(B - A, C - A)
    n2 = np.cross(B - D, C - D)
    normals = math.degrees(math.acos(abs(np.dot(n1, n2))
                                     / (np.linalg.norm(n1) * np.linalg.norm(n2))))
    assert abs(min(theta, 180 - theta) - normals) < 1e-6, "the two routes disagree"

    # folding face 2 about the hinge by +theta lays it flat on face 1: that is
    # what "how far the book is open" means, and S01 animates exactly this
    folded = B + rotate_about(D - B, e, math.radians(theta))
    assert abs(np.dot(folded - A, n1 / np.linalg.norm(n1))) < 1e-6, \
        "folding by theta does not close the book"

    fv = {k: np.array([v[0], v[2]]) for k, v in P.items()}      # (x, height)
    tv = {k: np.array([v[0], -v[1]]) for k, v in P.items()}     # (x, -depth)

    # ---- aux 1: X1Y1 PARALLEL to the top view of BC -> BC true length ------
    u1 = tv["C"] - tv["B"]
    u1 /= np.linalg.norm(u1)
    n1d = np.array([-u1[1], u1[0]])
    if n1d[1] > 0:
        n1d = -n1d                                   # keep it below the top view
    p0 = tv["B"] + n1d * gaps[0]
    # the auxiliary goes on the FAR side of X1Y1 from the top view - offsetting
    # back towards it drops the new view straight on top of the old one
    aux1 = _project(tv, p0, u1, n1d, {k: P[k][2] for k in P})     # carry HEIGHTS

    assert abs(np.linalg.norm(aux1["C"] - aux1["B"]) - np.linalg.norm(C - B)) < 1e-6, \
        "aux 1 does not show BC at true length"

    # ---- aux 2: X2Y2 PERPENDICULAR to b1c1 -> BC becomes a point -----------
    u2 = -(aux1["C"] - aux1["B"])
    u2 /= np.linalg.norm(u2)
    w2 = np.array([-u2[1], u2[0]])
    q0 = aux1["B"] + u2 * gaps[1]
    # every distance carried in is measured from X1Y1 in the TOP view - two
    # views back - and they all lie on one side of it, so one sign serves
    steps = {k: -float(np.dot(tv[k] - p0, n1d)) for k in P}
    assert min(steps.values()) > 0, "X1Y1 has the top view on both sides of it"
    aux2 = _project(aux1, q0, w2, u2, steps)

    assert np.linalg.norm(aux2["C"] - aux2["B"]) < 1e-6, "aux 2 is not a point view of BC"
    d1, d2 = aux2["A"] - aux2["B"], aux2["D"] - aux2["B"]
    read = math.degrees(math.acos(np.dot(d1, d2)
                                  / (np.linalg.norm(d1) * np.linalg.norm(d2))))
    assert abs(read - theta) < 1e-6, "the point view does not show the true angle"

    return dict(fv=fv, tv=tv, aux1=aux1, aux2=aux2, theta=theta,
                u1=u1, n1=n1d, p0=p0, u2=u2, w2=w2, q0=q0, steps=steps,
                bc=float(np.linalg.norm(C - B)),
                # the two distances that appear in the point view, and the
                # third side of that triangle: three numbers a student can
                # check with a rule before trusting the angle
                dA=float(np.linalg.norm(vA)), dD=float(np.linalg.norm(vD)),
                ad=float(np.linalg.norm(aux2["A"] - aux2["D"])),
                # what the hinge measures where it is NOT true length
                bc_fv=float(np.linalg.norm(fv["C"] - fv["B"])),
                bc_tv=float(np.linalg.norm(tv["C"] - tv["B"])))


G = solve()


# ==========================================================================
#  The sheet: millimetre space -> Manim points, and the drawing furniture
# ==========================================================================
def P2(v2):
    """millimetre space -> Manim point"""
    return np.array([v2[0] * MM, v2[1] * MM, 0.0])


def faces_of(pts, width=3.0, fill=0.12):
    """The two triangles of one view, each keeping its own colour."""
    g = VGroup()
    for f, colour in zip(FACES, (F1_COL, F2_COL)):
        g.add(Polygon(*[P2(pts[k]) for k in f], stroke_color=colour,
                      stroke_width=width, fill_color=colour, fill_opacity=fill))
    return g


def hinge_of(pts, width=5.0):
    return Line(P2(pts["B"]), P2(pts["C"]), color=HINGE_COL, stroke_width=width)


def riser(a, b, colour, width=1.0, opacity=0.5):
    return DashedLine(P2(a), P2(b), color=colour, stroke_width=width,
                      stroke_opacity=opacity, dash_length=0.05)


def dim(p_from, p_to, text, colour, size=14, offset=0.0, gap=7.0):
    """A slim dimension, pushed `offset` mm off the line it measures
    (measured 90° anticlockwise from p_from -> p_to)."""
    a, b = P2(p_from), P2(p_to)
    d = b - a
    length = float(np.linalg.norm(d))
    n = np.array([-d[1], d[0], 0.0])
    n = n / max(float(np.linalg.norm(n)), 1e-9)
    a, b = a + n * offset * MM, b + n * offset * MM
    arrow = DoubleArrow(a, b, buff=0, color=colour, stroke_width=1.7,
                        tip_length=float(min(0.10, 0.32 * length)))
    side = 1.0 if offset >= 0 else -1.0
    lab = mono(text, color=colour, size=size).move_to((a + b) / 2 + n * side * gap * MM)
    return VGroup(arrow, lab)


def right_angle(point, d1, d2, colour=INK, size=6.0):
    """The little square that says PERPENDICULAR - step two's whole
    justification, so it earns a mark on the sheet."""
    p = P2(point)
    e1 = np.array([d1[0], d1[1], 0.0]) * size * MM
    e2 = np.array([d2[0], d2[1], 0.0]) * size * MM
    mark = VMobject(stroke_color=colour, stroke_width=1.8)
    mark.set_points_as_corners([p + e1, p + e1 + e2, p + e2])
    return mark


def par_marks(point, direction, colour, size=5.0, gap=5.0):
    """The pair of slashes that says PARALLEL - step one's justification."""
    d = np.array([direction[0], direction[1], 0.0])
    d = d / np.linalg.norm(d)
    n = np.array([-d[1], d[0], 0.0])
    g = VGroup()
    for s in (-0.5, 0.5):
        c = P2(point) + d * s * gap * MM
        arm = (n * 0.9 + d * 0.45) * size * MM
        g.add(Line(c - arm, c + arm, color=colour, stroke_width=2.4))
    return g


def ref_line(origin, direction, pts, extra=13, width=2.3):
    sp = [float(np.dot(pts[k] - origin, direction)) for k in pts]
    return Line(P2(origin + direction * (min(sp) - extra)),
                P2(origin + direction * (max(sp) + extra)),
                color=INK, stroke_width=width)


def ref_label(text, line, buff=0.26):
    """The name of a reference line, on its own axis just beyond the far end."""
    d = line.get_unit_vector()
    return mono(text, color=INK, size=14).move_to(line.get_end() + d * buff)


def outward(point, cloud):
    mid = sum(P2(cloud[j]) for j in ALL) / float(len(ALL))
    d = P2(point) - mid
    return d / max(float(np.linalg.norm(d)), 1e-9)


def step_badge(number, title, detail, colour):
    number_mob = mono(number, color=colour, size=22)
    words = VGroup(caption(title, color=INK, size=18),
                   mono(detail, color=SLATE, size=13)
                   ).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


# ==========================================================================
#  The 3-D stage: the same figure, stood up in space
# ==========================================================================
def pt3(v3):
    """(x, depth, height) in millimetres -> the 3-D stage."""
    return np.array([(v3[0] - X_MID) * S3, -v3[1] * S3, v3[2] * S3])


def space_faces(scale_fill=0.32):
    """The two faces and their hinge, standing in space."""
    pts = {k: pt3(SPACE[k]) for k in ALL}
    f1 = Polygon(*[pts[k] for k in FACES[0]], stroke_color=F1_COL, stroke_width=3.5,
                 fill_color=F1_COL, fill_opacity=scale_fill)
    f2 = Polygon(*[pts[k] for k in FACES[1]], stroke_color=F2_COL, stroke_width=3.5,
                 fill_color=F2_COL, fill_opacity=scale_fill)
    hinge = Line(pts["B"], pts["C"], color=HINGE_COL, stroke_width=7)
    return pts, f1, f2, hinge


# ==========================================================================
#  S01 - what the angle between two planes actually is
# ==========================================================================
class S01_Dihedral(ProjectionScene):
    quadrant = 1
    heading = "The True Angle Between Two Planes"
    subheading = "Sheet 4 · the dihedral angle, and how to see it"

    def construct(self):
        self.build_stage()
        self.badge.shift(DOWN * 0.62)          # the title is a long one
        # Come in on the figure - against the whole stage it is small. Zoom only:
        # a frame_center away from the origin also drags Manim's fixed-in-frame
        # mobjects across the screen, and the caption is one of those.
        self.set_camera_orientation(zoom=1.3)
        self.add(self.vp, self.hp, self.xy, *self.tags, self.bar)

        pts, f1, f2, hinge = space_faces()
        labs = VGroup(*[mono(k, color=(HINGE_COL if k in HINGE else
                                       F1_COL if k == "A" else F2_COL), size=22)
                        .move_to(pts[k] + np.array([0.0, -0.12, 0.20])) for k in ALL])
        billboard(self, *labs)

        self.begin_ambient_camera_rotation(rate=0.012)
        narrate(
            self,
            "Question twelve, standing up in space. Two triangular faces: A B C, and "
            "D B C. They are not parallel, so they meet - and they meet along the "
            "edge B C, which both of them share.",
            Create(f1), Create(f2), FadeIn(labs),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "That shared edge is a hinge, and the two faces are the covers of a book "
            "opened about it. The angle we are asked for is simply how far the book "
            "is open. It has a name: the dihedral angle.",
            Create(hinge),
        )
        self.stop_ambient_camera_rotation()

        # ---- close the book and open it again --------------------------------
        # Folding face 2 about the hinge by +theta lays it exactly on face 1 -
        # solve() asserts that - so this really is the angle, not an impression
        # of one.
        axis = pt3(SPACE["C"]) - pt3(SPACE["B"])
        axis = axis / np.linalg.norm(axis)
        pivot = pt3(SPACE["B"])
        f2.rotate(math.radians(G["theta"]), axis=axis, about_point=pivot)   # shut it
        d_lab = labs[ALL.index("D")]
        d_shut = pivot + rotate_about(pt3(SPACE["D"]) - pivot, axis,
                                      math.radians(G["theta"]))
        d_home = d_lab.get_center().copy()
        d_lab.move_to(d_shut + np.array([0.0, -0.12, 0.20]))

        narrate(
            self,
            "Watch what that means. Shut the book: the far face folds down about B C "
            "until it lies flat on the other one. There is no angle now - the two "
            "faces are one flat sheet.",
            FadeIn(f2), FadeIn(d_lab),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Now open it again, and stop where the question puts it. That swing is "
            f"the answer: {G['theta']:.1f} degrees. Everything else in this episode "
            "is about how to measure it on a flat sheet of paper, where you cannot "
            "walk round the model.",
            Rotate(f2, -math.radians(G["theta"]), axis=axis, about_point=pivot),
            d_lab.animate.move_to(d_home),
            rate_func=rate_functions.ease_in_out_sine,
        )

        # ---- go and look down the hinge --------------------------------------
        sight = VGroup(*[DashedLine(pts[k] + axis * 1.15, pts[k] - axis * 0.95,
                                    color=SLATE, stroke_width=2.2, dash_length=0.1)
                         for k in ("A", "D")])
        narrate(
            self,
            "So how would you measure it on the real model? You would put your eye at "
            "the end of the hinge and look straight down it, the way you would sight "
            "along the spine of a book.",
            Create(sight),
            lag_ratio=0.25,
        )

        # the exact collapse: everything drops onto the plane through the hinge's
        # midpoint that is square to the hinge, and stays there
        mid = (pt3(SPACE["B"]) + pt3(SPACE["C"])) / 2.0
        flat = {k: pts[k] - axis * float(np.dot(pts[k] - mid, axis)) for k in ALL}
        assert np.linalg.norm(flat["B"] - flat["C"]) < 1e-9, "the hinge did not close up"
        line_a = Line(flat["B"], flat["A"], color=F1_COL, stroke_width=7)
        line_d = Line(flat["B"], flat["D"], color=F2_COL, stroke_width=7)
        pv = marker(flat["B"], HINGE_COL, 0.085)

        cam = -axis if axis[1] > 0 else axis        # stay on the observer's side
        fly_camera(
            self,
            "So let us go and stand there.",
            # Two things go with the stage here. The planes, because from this
            # one viewpoint they are a pair of steep quadrilaterals across the
            # shot that explain nothing. And the caption - because a 3-D
            # frame_center away from the origin drags Manim's fixed-in-frame
            # mobjects with it, so anything pinned to a corner walks off the
            # screen. It comes back when the camera does.
            FadeOut(sight), FadeOut(self.vp), FadeOut(self.hp), FadeOut(self.xy),
            FadeOut(self.tags), FadeOut(self.bar), FadeOut(self.badge),
            phi=math.acos(cam[2]), theta=math.atan2(cam[1], cam[0]),
            zoom=1.5, focal_distance=60.0, frame_center=mid,
        )
        narrate(
            self,
            "And there it is. B and C are one behind the other, so the hinge has "
            "shrunk to a single point. Each face is edge on, so each face has "
            "flattened into a line out of that point.",
            FadeOut(f1), FadeOut(f2), FadeOut(hinge), FadeOut(labs),
            Create(line_a), Create(line_d), FadeIn(pv),
            lag_ratio=0.25,
        )

        # the angle, drawn in the plane square to the hinge so it reads true
        dA = (flat["A"] - flat["B"]) / np.linalg.norm(flat["A"] - flat["B"])
        dD = (flat["D"] - flat["B"]) / np.linalg.norm(flat["D"] - flat["B"])
        e1 = dA
        e2 = dD - float(np.dot(dD, e1)) * e1
        e2 = e2 / np.linalg.norm(e2)
        sweep = math.acos(float(np.clip(np.dot(dA, dD), -1.0, 1.0)))
        assert abs(math.degrees(sweep) - G["theta"]) < 1e-6, "the 3-D angle is not θ"
        arc = Arc(radius=0.5, start_angle=0.0, angle=sweep, color=HINGE_COL,
                  stroke_width=4)
        arc.apply_matrix(np.array([[e1[0], e2[0], axis[0]],
                                   [e1[1], e2[1], axis[1]],
                                   [e1[2], e2[2], axis[2]]]))
        arc.shift(flat["B"])
        bis = (dA + dD) / np.linalg.norm(dA + dD)
        arc_lab = billboard(self, mono(f"θ = {G['theta']:.1f}°", color=HINGE_COL, size=24)
                            .move_to(flat["B"] + bis * 1.15))

        narrate(
            self,
            "The angle between those two lines is the angle between the two faces - "
            f"no foreshortening left to argue with. {G['theta']:.1f} degrees.",
            Create(arc), FadeIn(arc_lab),
            lag_ratio=0.4,
        )

        note = hud(self, VGroup(
            chip("look ALONG the common edge", color=HINGE_COL, size=21),
            chip("the edge becomes a POINT · both faces become LINES",
                 color=INK, size=21),
        ).arrange(DOWN, buff=0.2).move_to(np.array([0.0, -2.6, 0.0])))
        narrate(
            self,
            "That is the whole method, and it is worth saying in one line. Get a view "
            "that looks straight along the common edge. The edge shows as a point, "
            "both faces show as lines, and the angle between those lines is the true "
            "dihedral angle.",
            FadeIn(note),
        )
        fly_camera(
            self,
            "Step off that line, even slightly, and the faces open out again and the "
            "angle starts to lie to you - exactly as it did for a single line, or a "
            "single plane. There is nothing new here except which line you have to "
            "look along.",
            FadeIn(f1), FadeIn(f2), FadeIn(hinge), FadeIn(labs),
            FadeIn(self.vp), FadeIn(self.hp), FadeIn(self.xy), FadeIn(self.tags),
            FadeIn(self.bar), FadeIn(self.badge),
            FadeOut(line_a), FadeOut(line_d), FadeOut(pv), FadeOut(arc),
            FadeOut(arc_lab),
            phi=CAM_PHI, theta=CAM_THETA, zoom=1.15, frame_center=ORIGIN,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - the two auxiliaries, and the rule underneath them
# ==========================================================================
#  A generic line, solved the same way as the exercise, so the schematic in
#  this scene is a real construction at small scale rather than a sketch of
#  one. It exists to make one point: a line reaches a POINT VIEW only from a
#  view that already shows it TRUE LENGTH.
DEMO = {"P": np.array([0.0, 8.0, 10.0]), "Q": np.array([46.0, 30.0, 34.0])}
DEMO_MM = 0.026


def line_demo():
    tv = {k: np.array([v[0], -v[1]]) for k, v in DEMO.items()}
    u = tv["Q"] - tv["P"]
    u /= np.linalg.norm(u)
    n = np.array([-u[1], u[0]])
    if n[1] > 0:
        n = -n
    p0 = tv["P"] + n * 26.0
    aux1 = _project(tv, p0, u, n, {k: DEMO[k][2] for k in DEMO})
    true_len = float(np.linalg.norm(DEMO["Q"] - DEMO["P"]))
    assert abs(np.linalg.norm(aux1["Q"] - aux1["P"]) - true_len) < 1e-6, \
        "the demo's first auxiliary is not true length"

    u2 = -(aux1["Q"] - aux1["P"])
    u2 /= np.linalg.norm(u2)
    w2 = np.array([-u2[1], u2[0]])
    q0 = aux1["P"] + u2 * 14.0
    aux2 = _project(aux1, q0, w2, u2,
                    {k: -float(np.dot(tv[k] - p0, n)) for k in DEMO})
    assert np.linalg.norm(aux2["Q"] - aux2["P"]) < 1e-6, \
        "the demo's second auxiliary is not a point view"
    return dict(tv=tv, aux1=aux1, aux2=aux2, u=u, n=n, p0=p0,
                u2=u2, w2=w2, q0=q0, true_len=true_len)


def demo_drawing():
    """The schematic, in pieces so the scene can bring it in a step at a time.

    The chain folds back on itself, so every label is pushed out along the
    line from the middle of the whole figure - left to next_to() they pile up
    on one another."""
    d = line_demo()

    def D2(v2):
        return np.array([v2[0] * DEMO_MM, v2[1] * DEMO_MM, 0.0])

    def ref(origin, direction, pts, extra=10):
        sp = [float(np.dot(pts[k] - origin, direction)) for k in pts]
        return Line(D2(origin + direction * (min(sp) - extra)),
                    D2(origin + direction * (max(sp) + extra)),
                    color=INK, stroke_width=1.8)

    tv_line = Line(D2(d["tv"]["P"]), D2(d["tv"]["Q"]), color=SLATE, stroke_width=3.4)
    x1 = ref(d["p0"], d["u"], {**d["tv"], **d["aux1"]})
    r1 = VGroup(*[DashedLine(D2(d["tv"][k]), D2(d["aux1"][k]), color=MUTED,
                             stroke_width=0.8, stroke_opacity=0.45, dash_length=0.04)
                  for k in DEMO])
    tl = Line(D2(d["aux1"]["P"]), D2(d["aux1"]["Q"]), color=HINGE_COL, stroke_width=4.5)
    x2 = ref(d["q0"], d["w2"], {**d["aux1"], **d["aux2"]})
    r2 = VGroup(*[DashedLine(D2(d["aux1"][k]), D2(d["aux2"][k]), color=MUTED,
                             stroke_width=0.8, stroke_opacity=0.45, dash_length=0.04)
                  for k in DEMO])
    dot = VGroup(Dot(D2(d["aux2"]["P"]), radius=0.07, color=HINGE_COL),
                 Circle(radius=0.16, color=HINGE_COL, stroke_width=2.4)
                 .move_to(D2(d["aux2"]["P"])))

    body = VGroup(tv_line, x1, r1, tl, x2, r2, dot)
    middle = body.get_center()

    def pushed(text, anchor, colour, size=13, push=0.5):
        v = anchor - middle
        v = v / max(float(np.linalg.norm(v)), 1e-9)
        return mono(text, color=colour, size=size).move_to(anchor + v * push)

    def at_end(text, line, colour=INK, size=12, buff=0.3):
        return mono(text, color=colour, size=size).move_to(
            line.get_end() + line.get_unit_vector() * buff)

    tv_lab = pushed("a view of the line", tv_line.get_center(), SLATE, 12, 0.42)
    x1_lab = at_end("X1Y1 ∥ it", x1)
    tl_lab = pushed("TRUE LENGTH", tl.get_center(), HINGE_COL, 13, 0.66)
    x2_lab = at_end("X2Y2 ⊥ it", x2)
    dot_lab = pushed("POINT VIEW", dot.get_center(), HINGE_COL, 13, 0.62)

    stage1 = VGroup(tv_line, tv_lab)
    stage2 = VGroup(x1, x1_lab, r1, tl, tl_lab)
    stage3 = VGroup(x2, x2_lab, r2, dot, dot_lab)
    return VGroup(stage1, stage2, stage3), stage1, stage2, stage3


class S02_Strategy(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Two Steps", "true length, then point view")
        self.add(bar)

        steps = [
            ("1", "X1Y1 PARALLEL to a view of BC",
             "carry the heights  →  BC at TRUE LENGTH", F1_COL),
            ("2", "X2Y2 PERPENDICULAR to that TL",
             "carry the distances  →  BC becomes a POINT", F2_COL),
        ]
        rows = VGroup()
        for num, headline, sub, colour in steps:
            n = mono(num, color=colour, size=28)
            text = VGroup(caption(headline, color=colour, size=21),
                          mono(sub, color=SLATE, size=15)
                          ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            rows.add(VGroup(n, text).arrange(RIGHT, buff=0.32, aligned_edge=UP))
        rows.arrange(DOWN, buff=0.5, aligned_edge=LEFT).move_to(np.array([-3.4, 1.1, 0]))

        demo, stage1, stage2, stage3 = demo_drawing()
        demo.move_to(np.array([3.5, -0.25, 0]))

        narrate(
            self,
            "Looking along the hinge is easy to say. On paper it takes two auxiliary "
            "views, and they have to come in the right order.",
            FadeIn(bar),
        )
        narrate(
            self,
            "You cannot jump straight to the point view of a line. Think about what a "
            "point view is: you are looking square down the line, so the line is "
            "parallel to nothing and perpendicular to your new plane. You can only "
            "aim that shot from a view that already shows the line at true length.",
            FadeIn(stage1),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "So step one gets the true length. Draw X one Y one parallel to one view "
            "of B C - either view will do - and project across, carrying each point's "
            "distance from the other view. A line parallel to the new plane of "
            "projection comes out at its true length.",
            FadeIn(rows[0]), Create(stage2),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Step two takes the shot. Draw X two Y two perpendicular to that true "
            "length and project once more. Now you are looking straight down the "
            "line, and it collapses to a point - and everything attached to it "
            "flattens with it.",
            FadeIn(rows[1]), Create(stage3),
            lag_ratio=0.3,
        )

        rule = VGroup(
            chip("a line reaches POINT VIEW only from a TRUE LENGTH view",
                 color=HINGE_COL, size=20),
            chip("if your point view is not a single point, X2Y2 was not square to the TL",
                 color=SLATE, size=17),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.5)
        narrate(
            self,
            "Two things to hold on to. That order is fixed - true length first, point "
            "view second. And if your point view does not come out as one single "
            "point, the mistake is almost always that X two Y two was not exactly "
            "perpendicular to the true length.",
            FadeIn(rule[0]), FadeIn(rule[1]),
            lag_ratio=0.35,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S03 - Q.12 worked on one sheet, the camera following the chain
# ==========================================================================
class S03_Construction(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        fv, tv, a1, a2 = G["fv"], G["tv"], G["aux1"], G["aux2"]
        u1, n1, p0 = G["u1"], G["n1"], G["p0"]
        u2, w2, q0 = G["u2"], G["w2"], G["q0"]
        n1d = np.array([n1[0], n1[1], 0.0])

        # ---------------- the given views -------------------------------------
        xy = Line(P2(np.array([-18.0, 0.0])), P2(np.array([92.0, 0.0])),
                  color=INK, stroke_width=2.6)
        xy_lab = VGroup(mono("X", color=INK, size=15).next_to(xy, LEFT, buff=0.1),
                        mono("Y", color=INK, size=15).next_to(xy, RIGHT, buff=0.1))
        fv_f, tv_f = faces_of(fv), faces_of(tv)
        fv_bc, tv_bc = hinge_of(fv), hinge_of(tv)
        dots = VGroup(*[Dot(P2(fv[k]), radius=0.038,
                            color=HINGE_COL if k in HINGE else
                            (F1_COL if k == "A" else F2_COL)) for k in ALL],
                      *[Dot(P2(tv[k]), radius=0.038,
                            color=HINGE_COL if k in HINGE else
                            (F1_COL if k == "A" else F2_COL)) for k in ALL])
        labs = VGroup()
        for k in ALL:
            col = HINGE_COL if k in HINGE else (F1_COL if k == "A" else F2_COL)
            labs.add(mono(f"{k.lower()}′", color=col, size=15)
                     .next_to(P2(fv[k]), outward(fv[k], fv), buff=0.07))
            labs.add(mono(k.lower(), color=col, size=15)
                     .next_to(P2(tv[k]), outward(tv[k], tv), buff=0.07))
        tag_fv = chip("FRONT VIEW", color=SLATE, size=12).move_to(P2(np.array([96.0, 44.0])))
        tag_tv = chip("TOP VIEW", color=SLATE, size=12).move_to(P2(np.array([96.0, -46.0])))
        given = VGroup(xy, xy_lab, fv_f, tv_f, fv_bc, tv_bc, dots, labs, tag_fv, tag_tv)

        # ---------------- step 1: X1Y1 parallel to bc, heights carried --------
        x1 = ref_line(p0, u1, {**tv, **a1})
        x1l = ref_label("X1Y1", x1)
        par = VGroup(par_marks((tv["B"] + tv["C"]) / 2.0, u1, HINGE_COL),
                     par_marks(p0 + u1 * float(np.dot((tv["B"] + tv["C"]) / 2.0 - p0, u1)),
                               u1, HINGE_COL))
        foot1 = {k: p0 + u1 * float(np.dot(tv[k] - p0, u1)) for k in ALL}
        rays1 = VGroup(*[riser(tv[k], a1[k], SLATE, width=1.0, opacity=0.45) for k in ALL])
        heights = VGroup(*[
            dim(np.array([fv[k][0], 0.0]), fv[k], f"{SPACE[k][2]:.0f}",
                HINGE_COL if k in HINGE else (F1_COL if k == "A" else F2_COL),
                size=13, offset=off, gap=6.0)
            for k, off in zip(ALL, (7.0, -7.0, -6.0, 6.0))])
        carried = VGroup(*[
            dim(foot1[k], a1[k], f"{SPACE[k][2]:.0f}",
                HINGE_COL if k in HINGE else (F1_COL if k == "A" else F2_COL),
                size=13, offset=off, gap=6.0)
            for k, off in zip(ALL, (5.0, -5.0, 5.0, -5.0))])
        a1_f = faces_of(a1, 2.8)
        a1_bc = hinge_of(a1, 5.5)
        a1_dim = dim(a1["B"], a1["C"], f"{G['bc']:.1f}  TRUE LENGTH", HINGE_COL,
                     size=13, offset=-8.0, gap=6.5)
        a1_labs = VGroup(*[mono(f"{k.lower()}1",
                                color=HINGE_COL if k in HINGE else
                                (F1_COL if k == "A" else F2_COL), size=13)
                           .move_to(P2(a1[k]) + n1d * 0.22) for k in ALL])
        aux1_g = VGroup(x1, x1l, par, rays1, carried, a1_f, a1_bc, a1_labs)

        # ---------------- step 2: X2Y2 square to b1c1, distances carried ------
        x2 = ref_line(q0, w2, {**a1, **a2})
        x2l = ref_label("X2Y2", x2)
        ra = right_angle(a1["B"], (a1["C"] - a1["B"]) / np.linalg.norm(a1["C"] - a1["B"]),
                         u2, colour=INK)
        foot2 = {k: q0 + w2 * float(np.dot(a1[k] - q0, w2)) for k in ALL}
        rays2 = VGroup(*[riser(a1[k], a2[k], SLATE, width=1.0, opacity=0.45) for k in ALL])
        steps_src = VGroup(*[
            dim(foot1[k], tv[k], f"{G['steps'][k]:.0f}",
                HINGE_COL if k in HINGE else (F1_COL if k == "A" else F2_COL),
                size=13, offset=off, gap=6.0)
            for k, off in zip(ALL, (-5.0, 5.0, -5.0, 5.0))])
        steps_dst = VGroup(*[
            dim(foot2[k], a2[k], f"{G['steps'][k]:.0f}",
                HINGE_COL if k in HINGE else (F1_COL if k == "A" else F2_COL),
                size=13, offset=off, gap=6.0)
            for k, off in zip(ALL, (5.0, -5.0, 5.0, -5.0))])

        # the point view: both faces out of one point, as two lines
        pv = P2(a2["B"])
        line_a = Line(pv, P2(a2["A"]), color=F1_COL, stroke_width=5)
        line_d = Line(pv, P2(a2["D"]), color=F2_COL, stroke_width=5)
        pv_ring = Circle(radius=0.12, color=HINGE_COL, stroke_width=3).move_to(pv)
        pv_lab = mono("b2 c2", color=HINGE_COL, size=14).next_to(pv_ring, DL, buff=0.06)
        a2_labs = VGroup(mono("a2", color=F1_COL, size=15).next_to(P2(a2["A"]), UR, buff=0.06),
                         mono("d2", color=F2_COL, size=15).next_to(P2(a2["D"]), UL, buff=0.06))
        pv_dims = VGroup(dim(a2["B"], a2["A"], f"{G['dA']:.1f}", F1_COL, size=12,
                             offset=6.0, gap=5.5),
                         dim(a2["B"], a2["D"], f"{G['dD']:.1f}", F2_COL, size=12,
                             offset=-6.0, gap=5.5))

        dirA = (a2["A"] - a2["B"]) / np.linalg.norm(a2["A"] - a2["B"])
        dirD = (a2["D"] - a2["B"]) / np.linalg.norm(a2["D"] - a2["B"])
        s0 = math.atan2(dirA[1], dirA[0])
        sweep = (math.atan2(dirD[1], dirD[0]) - s0 + PI) % TAU - PI
        arc = Arc(radius=0.62, start_angle=s0, angle=sweep, arc_center=pv,
                  color=HINGE_COL, stroke_width=3.2)
        alab = mono(f"θ = {G['theta']:.1f}°", color=HINGE_COL, size=18).move_to(
            pv + 1.15 * np.array([math.cos(s0 + sweep / 2.0),
                                  math.sin(s0 + sweep / 2.0), 0.0]))
        focus = Circle(radius=1.15).move_to(pv)     # never drawn: a camera target
        aux2_g = VGroup(x2, x2l, ra, rays2, steps_dst, line_a, line_d,
                        pv_ring, pv_lab, a2_labs)
        sheet = VGroup(given, aux1_g, heights, a1_dim, steps_src, aux2_g, arc, alab)

        # ---------------- furniture -------------------------------------------
        centre, W = frame_target([given])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 4 (Set A) · Q.12",
            "Figure P4.12 · the true angle between ABC and BCD")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "plot the given views", "two faces, and the hinge they share", SLATE),
            step_badge("2", "X1Y1 ∥ bc", "carry the HEIGHTS · bc comes out true length", F1_COL),
            step_badge("3", "X2Y2 ⊥ b₁c₁", "carry the DISTANCES · bc shrinks to a point", F2_COL),
            step_badge("4", "read the angle", "both faces are lines out of that point", HINGE_COL),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)

        data_rows = VGroup(
            mono("GIVEN (mm)", color=SLATE, size=15),
            mono("        above HP   in front of VP", color=SLATE, size=13),
            *[mono(f"  {k}      {SPACE[k][2]:5.0f} {SPACE[k][1]:13.0f}",
                   color=HINGE_COL if k in HINGE else
                   (F1_COL if k == "A" else F2_COL), size=15) for k in ALL],
            mono("  projectors  " + " · ".join(f"{SPACE[k][0]:.0f}" for k in "ADCB"),
                 color=SLATE, size=13),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        data = card_back(data_rows, pad=0.22, opacity=0.88)
        data.add(SurroundingRectangle(data_rows, color=SLATE, buff=0.22,
                                      corner_radius=0.1, stroke_width=1.2))
        pin_to_frame(self, data, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(data)

        # the camera roams over a sheet that has drawing above, below and either
        # side of it, so the furniture is declared foreground: it is the one
        # thing that must never end up underneath a projector
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)

        # ------------------------------ animate --------------------------------
        narrate(
            self,
            "Question twelve. Two triangular faces, A B C and B C D, given by their "
            "two views. Find the true size of the angle between them.",
            FadeIn(bar), FadeIn(data),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Transfer the question first. A is forty-four above the H P and seventy "
            "in front of the V P. B is fifty and fifty-eight. C is eighteen and "
            "forty-eight. D is fifty-four and twelve.",
            rail_focus(rail, rungs, 0),
            Create(xy), FadeIn(xy_lab), FadeIn(dots), FadeIn(tag_fv), FadeIn(tag_tv),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Join them up: face A B C in violet, face D B C in coral, in both views.",
            Create(fv_f), Create(tv_f), FadeIn(labs),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "And there is the hinge - the edge B C, which belongs to both faces. "
            "Everything from here aims at one thing: a view that looks straight along "
            "it.",
            Create(fv_bc), Create(tv_bc),
            lag_ratio=0.3,
        )

        narrate(
            self,
            "Step two. Draw X one Y one parallel to the top view b c. Parallel, "
            "because a line parallel to the new plane of projection is a line that "
            "comes out at true length.",
            rail_focus(rail, rungs, 1),
            look_at(self, [tv_f, x1, tag_tv], right=0.34),
            Create(x1), FadeIn(x1l), FadeIn(par),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Now the transfer. Each corner's height above the H P is measured in the "
            "front view: forty-four, fifty, eighteen, fifty-four.",
            look_at(self, [fv_f, heights], right=0.34),
            Create(heights),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project all four points square across X one Y one and step those same "
            "heights off on the far side. Each corner keeps its own measurement.",
            look_at(self, [tv_f, aux1_g]),
            Create(rays1),
            *[TransformFromCopy(heights[i], carried[i]) for i in range(4)],
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Join them up, and check the one thing that matters: b one c one "
            f"measures {G['bc']:.1f} millimetres, which is the true length of the "
            f"hinge. In the front view it looked {G['bc_fv']:.1f}, in the top view "
            f"{G['bc_tv']:.1f}. Both were short.",
            look_at(self, [aux1_g, a1_dim]),
            Create(a1_f), Create(a1_bc), FadeIn(a1_labs), Create(a1_dim),
            lag_ratio=0.25,
        )

        narrate(
            self,
            "Step three. Draw X two Y two perpendicular to that true length. "
            "Perpendicular, because now we want to look straight down the hinge "
            "rather than across it.",
            rail_focus(rail, rungs, 2),
            look_at(self, [aux1_g, x2]),
            FadeOut(heights), FadeOut(carried), FadeOut(a1_dim),
            Create(x2), FadeIn(x2l), Create(ra),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "The distances this time come from two views back - the top view - each "
            "one measured from X one Y one. Notice b and c are the same distance "
            f"from it, {G['steps']['B']:.0f} each, and they have to be: X one Y one "
            "was drawn parallel to b c.",
            look_at(self, [tv_f, x1, steps_src], right=0.34),
            Create(steps_src),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project across X two Y two and step them off.",
            look_at(self, [a1_f, aux2_g]),
            Create(rays2),
            *[TransformFromCopy(steps_src[i], steps_dst[i]) for i in range(4)],
            lag_ratio=0.2,
        )
        narrate(
            self,
            "And b two and c two land on top of one another. The hinge has become a "
            "point: we are looking straight down it.",
            look_at(self, [focus]),
            Create(pv_ring), FadeIn(pv_lab),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Each face has flattened into a single line out of that point - one to a "
            f"two, {G['dA']:.1f} away, one to d two, {G['dD']:.1f} away. Those are "
            "the perpendicular distances of A and D from the hinge, and they are the "
            "two arms of the angle.",
            rail_focus(rail, rungs, 3),
            Create(line_a), Create(line_d), FadeIn(a2_labs), Create(pv_dims),
            lag_ratio=0.25,
        )

        ans_rows = VGroup(
            mono(f"θ = {G['theta']:.1f}°", color=HINGE_COL, size=22),
            mono(f"  hinge BC true length {G['bc']:.1f}", color=SLATE, size=14),
            mono(f"  a2 from the point    {G['dA']:.1f}", color=F1_COL, size=14),
            mono(f"  d2 from the point    {G['dD']:.1f}", color=F2_COL, size=14),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=HINGE_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Measure between them, and that is the answer: the two faces of question "
            f"twelve open at {G['theta']:.1f} degrees.",
            FadeOut(pv_dims), Create(arc), FadeIn(alab), FadeOut(data), FadeIn(ans),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Two auxiliary views, and the whole sheet reads as one chain: the given "
            "views, the hinge at true length, the hinge as a point, the angle.",
            look_at(self, [sheet], right=0.24, top=0.12),
            FadeOut(steps_src), FadeOut(steps_dst),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Quote the angle the faces actually make with each other - the one you "
            "can see at the point view, between the two lines the faces have become. "
            f"Two planes carried on for ever cross at {G['theta']:.1f} degrees and at "
            f"{180 - G['theta']:.1f} degrees, but only one of those is the angle this "
            "pair of triangles opens at.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - recap
# ==========================================================================
class S04_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "the angle between two planes")
        self.add(bar)

        rows = VGroup(
            mono("the angle lives on the COMMON EDGE", color=HINGE_COL, size=21),
            mono("aux 1   X1Y1 ∥ one view of the edge   → TRUE LENGTH", color=F1_COL, size=20),
            mono("aux 2   X2Y2 ⊥ that true length       → POINT VIEW", color=F2_COL, size=20),
            mono("both faces are then lines · read the angle between them",
                 color=SLATE, size=18),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to(np.array([-0.25, 1.35, 0]))

        # the chain, drawn once so the order is never in doubt
        start = chip("FRONT + TOP VIEWS", color=INK, size=15)
        c1 = chip("aux 1 · BC TRUE LENGTH", color=F1_COL, size=15)
        c2 = chip("aux 2 · BC A POINT", color=F2_COL, size=15)
        ang = chip(f"θ = {G['theta']:.1f}°", color=HINGE_COL, size=17)
        chain = VGroup(start, c1, c2, ang).arrange(RIGHT, buff=1.05)
        chain.scale(0.92).move_to(np.array([0.0, -1.1, 0]))

        def link(a, b, text, colour):
            arrow = Arrow(a.get_right(), b.get_left(), buff=0.1, color=colour,
                          stroke_width=2.4, max_tip_length_to_length_ratio=0.2)
            return VGroup(arrow, mono(text, color=colour, size=12)
                          .next_to(arrow, UP, buff=0.06))

        links = VGroup(link(start, c1, "∥ bc", F1_COL),
                       link(c1, c2, "⊥ b₁c₁", F2_COL),
                       link(c2, ang, "", HINGE_COL))

        narrate(self, "The whole method in four lines.", FadeIn(bar))
        narrate(
            self,
            "The angle between two planes lives on the edge they share, and you can "
            "only see it truly by looking straight down that edge. So the job is to "
            "turn the edge into a point.",
            FadeIn(rows[0]),
        )
        narrate(
            self,
            "Which takes two auxiliaries, in this order. The first is parallel to one "
            "view of the edge and carries the heights across: the edge comes out at "
            "true length. The second is perpendicular to that true length and carries "
            "the distances from two views back: the edge shrinks to a point.",
            FadeIn(rows[1]), FadeIn(rows[2]),
            FadeIn(start), FadeIn(links[0]), FadeIn(c1), FadeIn(links[1]), FadeIn(c2),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Once you are looking down the hinge, both faces are lines and the angle "
            "is simply there, waiting to be measured.",
            FadeIn(rows[3]), FadeIn(links[2]), FadeIn(ang),
            lag_ratio=0.3,
        )

        ansc = VGroup(
            chip(f"Q.12   θ = {G['theta']:.1f}°", color=HINGE_COL, size=21),
            mono(f"check: BC true length {G['bc']:.1f} · a2 {G['dA']:.1f} · "
                 f"d2 {G['dD']:.1f} from the point", color=SLATE, size=15),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.5)
        narrate(
            self,
            f"For question twelve the answer is {G['theta']:.1f} degrees. Check "
            "yourself against three numbers on the way: the hinge should come out "
            f"{G['bc']:.1f} millimetres at true length, and in the point view the two "
            f"arms should measure {G['dA']:.1f} and {G['dD']:.1f}.",
            FadeIn(ansc[0]), FadeIn(ansc[1]),
            lag_ratio=0.35,
        )
        narrate(
            self,
            "Notice how much of this sheet is the same three moves in different "
            "orders: true length, point view, edge view. Question thirteen, the "
            "shortest distance between two skew lines, is built from the very same "
            "pair of auxiliaries you have just drawn.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme: run the file directly and it prints the answers it is about
#  to animate, so the video can be checked against a worked solution before a
#  single frame is rendered.
#
#      py -3.11 ed08_dihedral_angle.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 4 (Set A) Q.12 - Figure P4.12")
    print("  given (x along XY, in front of the VP, above the HP)")
    for k in ALL:
        print(f"    {k}   {SPACE[k][0]:5.0f} {SPACE[k][1]:6.0f} {SPACE[k][2]:6.0f}")
    print(f"  hinge BC:  front view {G['bc_fv']:6.2f}   top view {G['bc_tv']:6.2f}"
          f"   TRUE LENGTH {G['bc']:6.2f} mm")
    print("  distances carried into the second auxiliary (from X1Y1, in the top view):")
    for k in ALL:
        print(f"    {k}   {G['steps'][k]:6.2f} mm")
    print(f"  at the point view:  a2 {G['dA']:.2f} mm   d2 {G['dD']:.2f} mm"
          f"   a2-d2 {G['ad']:.2f} mm")
    print(f"  TRUE DIHEDRAL ANGLE  θ = {G['theta']:.2f}°"
          f"   ({int(G['theta'])}° {round((G['theta'] - int(G['theta'])) * 60)}')")
    print(f"  supplement {180 - G['theta']:.2f}°")
