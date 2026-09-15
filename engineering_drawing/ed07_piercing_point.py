"""
Engineering Drawing I - Sheet 4 / Lecture 4  (Basic Descriptive Geometry II)
Episode 07: Where a Line Pierces a Plane
            - the piercing point, by the cutting plane method
            - which stretch of the line is hidden, and why
            - the true angle between the line and the plane
            + worked solution to Exercise 4 (Set A), Q.11  (Figure P4.11)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed07_piercing_point.py S03_Piercing
    ... or use render_ed07.bat to build all six scenes in order.

Scene order (about thirteen minutes in all):

    S01_ThePiercingPoint  the figure standing in space: one point belongs to
                          both, and from that moment half the line is hidden -
                          demonstrated by following the projectors, not asserted
    S02_CuttingPlane      the cutting plane built in space, sliced across the
                          triangle, then looked at face on (both lines lie in
                          it, so they must cross) and finally from straight
                          above, where it collapses onto the top view of the
                          line - which is why it never has to be drawn
    S03_Piercing          Q.11 part one on the sheet: the piercing point in both
                          views, then visibility settled crossing by crossing by
                          comparing heights and depths, not by eye
    S04_TrueAngleA        Q.11 part two: why the angle needs a view with the
                          plane edge-on AND the line true length, then the first
                          two auxiliaries - edge view, true shape
    S05_TrueAngleB        the third auxiliary, taken parallel to the line's
                          image: the plane closes up again, the line comes out
                          true length, and the angle can be measured
    S06_Recap             three jobs, three tools, and the chain that links them

Everything is computed from the given dimensions by solve(), which asserts that
the piercing point lies on the plane and inside the triangle, that each
auxiliary view does what it is supposed to do, and that the angle finally read
off the drawing equals the angle computed from the plane's normal. If a number
in this file is wrong the render stops rather than teaching it.

No LaTeX anywhere - every glyph is Unicode Text().
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

from ed_stage import ProjectionScene, marker
from ed_common import (
    CORAL,
    CREAM,
    GOLD,
    INK,
    MUTED,
    NAVY,
    SLATE,
    TEAL,
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
    settle,
    title_bar,
)

# ==========================================================================
#  Figure P4.11, read off the given:  (x along XY, d in front of the VP,
#  h above the HP), in millimetres
# ==========================================================================
SPACE = {
    "A": np.array([10.0, 10.0, 55.0]),
    "B": np.array([95.0, 40.0, 70.0]),
    "C": np.array([55.0, 65.0, 15.0]),
    "D": np.array([0.0, 55.0, 30.0]),
    "E": np.array([105.0, 20.0, 60.0]),
}
TRI = ("A", "B", "C")
EDGES = (("A", "B"), ("B", "C"), ("C", "A"))
ALL = ("A", "B", "C", "D", "E")

# Colour carries meaning for the whole series:
#     coral  = the front view and everything that lives on the VP
#     teal   = the top view and everything that lives on the HP
#     violet = an auxiliary view
#     gold   = the line D E, wherever it appears, and the answers
#     cream  = the cutting plane and its trace - scaffolding, not answer
#     ink    = the piercing point itself, and the reference lines
# The plate keeps ONE colour in every view, and so does the line: a student
# following the figure from view to view is following a colour, and the view's
# identity comes from its reference line and its labels instead.
PLATE_COL = VIOLET
LINE_COL = GOLD
CUT_COL = CREAM
POINT_COL = INK

# set-backs of X1Y1, X2Y2 and X3Y3, chosen by searching for the arrangement
# that stays collision-free at the largest possible scale
GAPS = (46.0, 16.0, 16.0)

MM = 0.028      # drawing millimetre -> Manim unit (the flat sheet)
S3 = 0.029      # millimetre -> Manim unit on the 3-D stage
X_MID = 52.5    # the x that is centred on the 3-D stage


def _project(src, origin, along, normal, dist):
    """Drop each point onto the new reference line, then step off its distance."""
    return {k: origin + along * np.dot(src[k] - origin, along) + normal * dist[k]
            for k in src}


def _cross(p1, p2, q1, q2):
    """Where segment p1p2 meets segment q1q2, as (parameter on p, parameter on
    q), or None if they do not meet within both segments."""
    r, s = p2 - p1, q2 - q1
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    a = ((q1 - p1)[0] * s[1] - (q1 - p1)[1] * s[0]) / den
    b = ((q1 - p1)[0] * r[1] - (q1 - p1)[1] * r[0]) / den
    return (a, b) if -1e-9 < a < 1 + 1e-9 and -1e-9 < b < 1 + 1e-9 else None


def solve(gaps=GAPS):
    p = SPACE
    A, B, C, D, E = (p[k] for k in ALL)
    n = np.cross(B - A, C - A)

    # ---- piercing point ---------------------------------------------------
    t = -float(np.dot(n, D - A) / np.dot(n, E - D))
    P = D + t * (E - D)
    assert abs(np.dot(n, P - A)) < 1e-9, "piercing point is not on the plane"
    uv = np.linalg.lstsq(np.array([B - A, C - A]).T, P - A, rcond=None)[0]
    assert uv[0] > 0 and uv[1] > 0 and uv.sum() < 1, "piercing point misses the triangle"
    assert 0 < t < 1, "the piercing point is not between D and E"

    true_angle = math.degrees(math.asin(
        abs(np.dot(n, E - D)) / (np.linalg.norm(n) * np.linalg.norm(E - D))))

    # ---- page views -------------------------------------------------------
    fv = {k: np.array([v[0], v[2]]) for k, v in p.items()}      # (x, height)
    tv = {k: np.array([v[0], -v[1]]) for k, v in p.items()}     # (x, -depth)

    # ---- cutting plane: it shows as the line `de` itself in the top view ---
    cut = []                     # where the cutting plane meets the triangle
    for e0, e1 in EDGES:
        hit = _cross(tv["D"], tv["E"], tv[e0], tv[e1])
        if hit:
            a, b = hit
            cut.append(dict(edge=(e0, e1), t=a, s=b,
                            space=p[e0] + b * (p[e1] - p[e0])))
    assert len(cut) == 2, "the cutting plane should cross exactly two edges"
    cut.sort(key=lambda c: c["t"])

    # the whole method rests on this: the slice and the line meet at P
    span = cut[1]["space"] - cut[0]["space"]
    along = float(np.dot(P - cut[0]["space"], span) / np.dot(span, span))
    assert 0 < along < 1 and np.linalg.norm(
        cut[0]["space"] + along * span - P) < 1e-9, "P is not on the cut line"

    # ---- visibility, view by view ----------------------------------------
    # At every crossing of the two outlines the question is the same: which of
    # the two things is nearer THIS observer? The answer is read in the OTHER
    # view, where the two candidates sit on one projector at different heights
    # (for the top view) or different depths (for the front view).
    vis = {}
    for name, comp in (("front", 1), ("top", 2)):     # nearer = more depth / more height
        idx = (0, 2) if name == "front" else (0, 1)
        g = {k: np.array([v[idx[0]], v[idx[1]]]) for k, v in p.items()}
        events = []
        for e0, e1 in EDGES:
            hit = _cross(g["D"], g["E"], g[e0], g[e1])
            if hit:
                a, b = hit
                on_ln = D + a * (E - D)
                on_ed = p[e0] + b * (p[e1] - p[e0])
                events.append(dict(t=a, edge=(e0, e1), s=b,
                                   line_val=float(on_ln[comp]),
                                   edge_val=float(on_ed[comp]),
                                   line_nearer=on_ln[comp] > on_ed[comp]))
        events.sort(key=lambda e: e["t"])
        assert len(events) == 2, f"{name} view: expected two crossings"
        # the hidden stretch runs from the piercing point to whichever crossing
        # lies on the far side of the plane
        far = [e for e in events if not e["line_nearer"]][0]
        vis[name] = dict(enter=events[0]["t"], leave=events[1]["t"],
                         events=events, hidden=(min(t, far["t"]), max(t, far["t"])))

    # ---- auxiliary chain for the true angle -------------------------------
    s_ = (A[2] - B[2]) / (C[2] - B[2])
    M = B + s_ * (C - B)                                   # horizontal line of the plane
    u1 = np.array([M[0], -M[1]]) - tv["A"]
    u1 /= np.linalg.norm(u1)
    w1 = np.array([-u1[1], u1[0]])
    p0 = u1 * (max(np.dot(tv[k], u1) for k in p) + gaps[0])
    aux1 = _project(tv, p0, w1, u1, {k: p[k][2] for k in p})          # carry HEIGHTS

    r, q = aux1["B"] - aux1["A"], aux1["C"] - aux1["A"]
    assert abs(r[0] * q[1] - r[1] * q[0]) / np.linalg.norm(r) < 1e-6, "aux1 is not an edge view"

    v2 = r / np.linalg.norm(r)
    n2 = np.array([-v2[1], v2[0]])
    q0 = aux1["A"] + n2 * gaps[1]
    aux2 = _project(aux1, q0, v2, n2,
                    {k: -float(np.dot(tv[k] - p0, u1)) for k in p})   # carry from TOP view
    for e0, e1 in EDGES:
        assert abs(np.linalg.norm(aux2[e0] - aux2[e1])
                   - np.linalg.norm(p[e0] - p[e1])) < 1e-6, "aux2 is not the true shape"

    v3 = aux2["E"] - aux2["D"]
    v3 /= np.linalg.norm(v3)
    n3 = np.array([-v3[1], v3[0]])
    r0 = aux2["A"] + n3 * gaps[2]
    aux3 = _project(aux2, r0, v3, n3,
                    {k: -float(np.dot(aux1[k] - q0, n2)) for k in p})  # carry from AUX1

    f, g2 = aux3["B"] - aux3["A"], aux3["C"] - aux3["A"]
    assert abs(f[0] * g2[1] - f[1] * g2[0]) / np.linalg.norm(f) < 1e-6, "aux3 is not edge-on"
    assert abs(np.linalg.norm(aux3["E"] - aux3["D"]) - np.linalg.norm(E - D)) < 1e-6, \
        "the line is not true length in aux3"
    pe, li = aux3["B"] - aux3["A"], aux3["E"] - aux3["D"]
    read = math.degrees(math.acos(abs(np.dot(pe, li))
                                  / (np.linalg.norm(pe) * np.linalg.norm(li))))
    assert abs(read - true_angle) < 1e-6, "aux3 does not show the true angle"

    return dict(fv=fv, tv=tv, t=t, P=P, true_angle=true_angle, cut=cut, vis=vis,
                aux1=aux1, aux2=aux2, aux3=aux3, u1=u1, w1=w1, p0=p0,
                v2=v2, n2=n2, q0=q0, v3=v3, n3=n3, r0=r0, M=M, n=n,
                # what the line measures in each view: only the last one is true
                de_true=float(np.linalg.norm(E - D)),
                de_fv=float(np.linalg.norm(fv["E"] - fv["D"])),
                de_tv=float(np.linalg.norm(tv["E"] - tv["D"])),
                de_aux1=float(np.linalg.norm(aux1["E"] - aux1["D"])),
                de_aux2=float(np.linalg.norm(aux2["E"] - aux2["D"])))


G = solve()


# ==========================================================================
#  The sheet: millimetre space -> Manim points, and the drawing furniture
# ==========================================================================
def P2(v2):
    """millimetre space -> Manim point"""
    return np.array([v2[0] * MM, v2[1] * MM, 0.0])


def on_line(view, t):
    """The point at parameter t along DE, in the given page view."""
    return view["D"] + t * (view["E"] - view["D"])


def on_edge(view, edge, s):
    """The point at parameter s along one side of the triangle."""
    e0, e1 = edge
    return view[e0] + s * (view[e1] - view[e0])


def sheet_tri(pts, colour, width=3.0, opacity=0.10):
    return Polygon(*[P2(pts[k]) for k in TRI], stroke_color=colour,
                   stroke_width=width, fill_color=colour, fill_opacity=opacity)


def sheet_line(pts, colour=LINE_COL, width=3.6):
    return Line(P2(pts["D"]), P2(pts["E"]), color=colour, stroke_width=width)


def riser(a, b, colour, width=1.1, opacity=0.6):
    """A projector between two views - always square to the reference line."""
    return DashedLine(P2(a), P2(b), color=colour, stroke_width=width,
                      stroke_opacity=opacity, dash_length=0.05)


def dim(p_from, p_to, text, colour, size=14, offset=0.0, gap=7.0):
    """A slim dimension: double arrow plus its value, pushed `offset` mm off
    the line it measures (measured 90° anticlockwise from p_from -> p_to)."""
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


def outward(point, cloud, keys=TRI):
    """Unit vector from the middle of `cloud` towards `point`, so a label hung
    this way lands outside the figure it belongs to."""
    mid = sum(P2(cloud[j]) for j in keys) / float(len(keys))
    d = P2(point) - mid
    return d / max(float(np.linalg.norm(d)), 1e-9)


def step_badge(number, title, detail, colour):
    """One rung of a running step rail."""
    number_mob = mono(number, color=colour, size=22)
    words = VGroup(caption(title, color=INK, size=18),
                   mono(detail, color=SLATE, size=13)
                   ).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


def ref_line(origin, direction, pts, extra=14, width=2.4):
    """A reference line long enough to carry every projector that crosses it."""
    sp = [float(np.dot(pts[k] - origin, direction)) for k in pts]
    return Line(P2(origin + direction * (min(sp) - extra)),
                P2(origin + direction * (max(sp) + extra)),
                color=INK, stroke_width=width)


# ==========================================================================
#  The 3-D stage: the same figure, stood up in space
# ==========================================================================
def pt3(v3):
    """(x, depth, height) in millimetres -> the 3-D stage
    (+x along XY, -y in front of the VP, +z above the HP)."""
    return np.array([(v3[0] - X_MID) * S3, -v3[1] * S3, v3[2] * S3])


def space_at(t):
    """The point at parameter t along D E, in space."""
    return SPACE["D"] + t * (SPACE["E"] - SPACE["D"])


# ==========================================================================
#  S01 - what a piercing point is, and what it does to the drawing
# ==========================================================================
class S01_ThePiercingPoint(ProjectionScene):
    quadrant = 1
    heading = "Where a Line Pierces a Plane"
    subheading = "Sheet 4 · the point, the hidden half, the true angle"

    def construct(self):
        self.build_stage()
        self.badge.shift(DOWN * 0.62)          # the title is a long one
        self.add(self.vp, self.hp, self.xy, *self.tags, self.bar)

        pts = {k: pt3(SPACE[k]) for k in ALL}
        plate = Polygon(*[pts[k] for k in TRI], stroke_color=PLATE_COL,
                        stroke_width=4, fill_color=PLATE_COL, fill_opacity=0.32)
        line = Line(pts["D"], pts["E"], color=LINE_COL, stroke_width=6)
        labs = VGroup(*[mono(k, color=PLATE_COL if k in TRI else LINE_COL, size=22)
                        .move_to(pts[k] + np.array([0.0, -0.14, 0.20])) for k in ALL])
        billboard(self, *labs)

        self.begin_ambient_camera_rotation(rate=0.012)
        narrate(
            self,
            "This is question eleven, standing up in space before we draw a line of "
            "it. A triangular plate A B C, and a straight line D E that runs clean "
            "through it.",
            Create(plate), Create(line), FadeIn(labs),
            lag_ratio=0.3,
        )

        Pp = pt3(G["P"])
        pdot = marker(Pp, POINT_COL, 0.085)
        plab = billboard(self, mono("P", color=POINT_COL, size=24)
                         .move_to(Pp + np.array([0.10, -0.10, 0.22])))
        narrate(
            self,
            "A line and a plane that are not parallel must meet, and they meet at "
            "exactly one point. That point is the piercing point - the trace of the "
            "line on the plane. It is the one point that belongs to the line and to "
            "the plate at the same time.",
            FadeIn(pdot), FadeIn(plab),
            lag_ratio=0.4,
        )
        self.stop_ambient_camera_rotation()

        # ---- why half the line then disappears -------------------------------
        # Both demonstrations are set up while the camera is still in three-
        # quarter view. A ray of sight seen from the observer's OWN position
        # points straight at you and foreshortens to a dot, so it has to be
        # watched from the side before we go and stand where he stands.
        def on_vp(v3):
            q = pt3(v3)
            return np.array([q[0], 0.0, q[2]])

        def on_hp(v3):
            q = pt3(v3)
            return np.array([q[0], q[1], 0.0])

        t_f = 0.65
        Qf = space_at(t_f)
        s_f = float(np.dot(G["n"], Qf - SPACE["A"]) / G["n"][1])
        Hf = Qf - np.array([0.0, s_f, 0.0])          # where that ray meets the plate
        ray_f = DashedLine(pt3(np.array([Qf[0], 86.0, Qf[2]])),
                           pt3(np.array([Qf[0], 0.0, Qf[2]])),
                           color=SLATE, stroke_width=2.6, dash_length=0.09)
        hit_f = marker(pt3(Hf), PLATE_COL, 0.065)
        on_f = marker(pt3(Qf), LINE_COL, 0.065)

        # close in: at stage zoom the figure is small, and a ray of sight that
        # cannot be seen proves nothing
        figure_centre = np.array([0.0, -0.60, 0.95])
        fly_camera(
            self,
            "The front view is taken by an observer out in front of the vertical "
            "plane, and his rays of sight all run horizontally, square to it. Follow "
            "one ray in - one that is aimed at a point on the E half of the line.",
            Create(ray_f),
            phi=64 * DEGREES, theta=-52 * DEGREES, zoom=1.2,
            frame_center=figure_centre,
        )
        narrate(
            self,
            "It meets the plate first, here, and only afterwards reaches the line. "
            "The plate is a solid sheet, not a wire frame, so from that side this "
            "piece of the line cannot be seen at all.",
            FadeIn(hit_f), FadeIn(on_f),
            lag_ratio=0.5,
        )

        fv_tri = Polygon(*[on_vp(SPACE[k]) for k in TRI], stroke_color=PLATE_COL,
                         stroke_width=3.2, fill_color=PLATE_COL, fill_opacity=0.35)
        lo, hi = G["vis"]["front"]["hidden"]
        fv_line = VGroup(
            Line(on_vp(space_at(0.0)), on_vp(space_at(lo)), color=LINE_COL, stroke_width=4),
            DashedLine(on_vp(space_at(lo)), on_vp(space_at(hi)), color=LINE_COL,
                       stroke_width=3.4, dash_length=0.08),
            Line(on_vp(space_at(hi)), on_vp(space_at(1.0)), color=LINE_COL, stroke_width=4),
        )
        tag = hud(self, chip("FRONT VIEW", color=CORAL, size=20)
                  .to_edge(DOWN, buff=0.6))

        fly_camera(
            self,
            "So walk round to where he is standing and look at what he draws: the "
            "plate, the line, and one stretch of the line dashed because the plate "
            "is in front of it. The dashes start exactly at the piercing point.",
            FadeOut(ray_f), FadeOut(hit_f), FadeOut(on_f),
            FadeOut(plate), FadeOut(line), FadeOut(labs), FadeOut(pdot), FadeOut(plab),
            TransformFromCopy(plate, fv_tri), TransformFromCopy(line, fv_line),
            FadeIn(tag),
            phi=76 * DEGREES, theta=-90 * DEGREES, zoom=1.05,
            frame_center=np.array([0.0, 0.0, 0.75]),
        )

        # ---- and now the other observer, who gets a different answer ----------
        t_t = 0.58
        Qt = space_at(t_t)
        s_t = float(np.dot(G["n"], Qt - SPACE["A"]) / G["n"][2])
        Ht = Qt - np.array([0.0, 0.0, s_t])
        ray_t = DashedLine(pt3(np.array([Qt[0], Qt[1], 96.0])),
                           pt3(np.array([Qt[0], Qt[1], 0.0])),
                           color=SLATE, stroke_width=2.6, dash_length=0.09)
        hit_t = marker(pt3(Ht), PLATE_COL, 0.065)
        on_t = marker(pt3(Qt), LINE_COL, 0.065)

        fly_camera(
            self,
            "Now come back out into space and do it again for the other observer - "
            "the one overhead, whose rays come straight down.",
            FadeOut(fv_tri), FadeOut(fv_line), FadeOut(tag),
            FadeIn(plate), FadeIn(line), FadeIn(labs), FadeIn(pdot), FadeIn(plab),
            Create(ray_t), FadeIn(hit_t), FadeIn(on_t),
            phi=64 * DEGREES, theta=-52 * DEGREES, zoom=1.2,
            frame_center=figure_centre,
        )

        tv_tri = Polygon(*[on_hp(SPACE[k]) for k in TRI], stroke_color=PLATE_COL,
                         stroke_width=3.2, fill_color=PLATE_COL, fill_opacity=0.35)
        lo_t, hi_t = G["vis"]["top"]["hidden"]
        tv_line = VGroup(
            Line(on_hp(space_at(0.0)), on_hp(space_at(lo_t)), color=LINE_COL, stroke_width=4),
            DashedLine(on_hp(space_at(lo_t)), on_hp(space_at(hi_t)), color=LINE_COL,
                       stroke_width=3.4, dash_length=0.08),
            Line(on_hp(space_at(hi_t)), on_hp(space_at(1.0)), color=LINE_COL, stroke_width=4),
        )
        tag2 = hud(self, chip("TOP VIEW", color=TEAL, size=20)
                   .to_edge(DOWN, buff=0.6))

        fly_camera(
            self,
            "Same plate, same line, different observer - and his ray meets the plate "
            "first at a different place. Climb up to where he is, and there is the "
            "top view, with a dashed stretch of its own. A shorter one, ending "
            "sooner.",
            FadeOut(ray_t), FadeOut(hit_t), FadeOut(on_t),
            FadeOut(plate), FadeOut(line), FadeOut(labs), FadeOut(pdot), FadeOut(plab),
            TransformFromCopy(plate, tv_tri), TransformFromCopy(line, tv_line),
            FadeIn(tag2),
            phi=14 * DEGREES, theta=-90 * DEGREES, zoom=1.0,
            frame_center=np.array([0.0, -0.55, 0.0]),
        )

        note = hud(self, VGroup(
            chip("the piercing point is where full changes to dashed",
                 color=POINT_COL, size=20),
            chip("each view decides for itself · settle them separately",
                 color=GOLD, size=20),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "Two things to carry away. The piercing point is always where the change "
            "from full to dashed happens. And in front means in front of that "
            "particular observer, so you settle the front view and the top view "
            "separately, every time.",
            FadeOut(tag2), FadeIn(note),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "So the job splits into three. Find the point. Settle the visibility. "
            "Then, separately, find the true angle. The first two need no auxiliary "
            "view at all.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - the cutting plane, built in space before it is used on paper
# ==========================================================================
class S02_CuttingPlane(ProjectionScene):
    quadrant = 1
    heading = "The Cutting Plane Method"
    subheading = "three lines and you have the point"

    def construct(self):
        self.build_stage()
        self.add(self.vp, self.hp, self.xy, *self.tags, self.bar)

        pts = {k: pt3(SPACE[k]) for k in ALL}
        plate = Polygon(*[pts[k] for k in TRI], stroke_color=PLATE_COL,
                        stroke_width=4, fill_color=PLATE_COL, fill_opacity=0.30)
        line = Line(pts["D"], pts["E"], color=LINE_COL, stroke_width=6)
        labs = VGroup(*[mono(k, color=PLATE_COL if k in TRI else LINE_COL, size=22)
                        .move_to(pts[k] + np.array([0.0, -0.14, 0.20])) for k in ALL])
        billboard(self, *labs)
        self.add(plate, line, labs)

        narrate(
            self,
            "There is a quick way to find the piercing point, and it needs no "
            "auxiliary views at all. It is worth understanding in space first, "
            "because then you never have to remember it.",
        )

        # ---- the cutting plane ------------------------------------------------
        def cp(t, h):
            """A corner of the cutting plane: along the line at parameter t,
            lifted to height h. The plane is vertical by construction."""
            q = space_at(t)
            return pt3(np.array([q[0], q[1], h]))

        glass = Polygon(cp(-0.08, 0.0), cp(1.08, 0.0), cp(1.08, 82.0), cp(-0.08, 82.0),
                        stroke_color=CUT_COL, stroke_width=2.4,
                        fill_color=CUT_COL, fill_opacity=0.16)
        trace = Line(cp(-0.08, 0.0), cp(1.08, 0.0), color=CUT_COL,
                     stroke_width=7, stroke_opacity=0.55)

        narrate(
            self,
            "Stand a sheet of glass on the horizontal plane, vertical, and turn it "
            "until the line D E lies in it. Any line can be contained in a vertical "
            "plane like that, and there is only one.",
            Create(glass),
            lag_ratio=0.2,
        )

        cutseg = Line(pt3(G["cut"][0]["space"]), pt3(G["cut"][1]["space"]),
                      color=CUT_COL, stroke_width=6)
        cutdots = VGroup(marker(pt3(G["cut"][0]["space"]), CUT_COL, 0.07),
                         marker(pt3(G["cut"][1]["space"]), CUT_COL, 0.07))
        cutlabs = billboard(
            self,
            mono("1", color=CUT_COL, size=22).move_to(
                pt3(G["cut"][0]["space"]) + np.array([-0.16, 0.0, 0.16])),
            mono("2", color=CUT_COL, size=22).move_to(
                pt3(G["cut"][1]["space"]) + np.array([0.16, 0.0, 0.16])),
        )
        narrate(
            self,
            "The glass slices straight through the plate, in through one side and "
            "out through another. That slice is a straight line. Call its ends one "
            "and two.",
            Create(cutseg), FadeIn(cutdots), FadeIn(cutlabs),
            lag_ratio=0.3,
        )

        # ---- look at the glass face on: two lines in one plane must cross -----
        plan_dir = pt3(SPACE["E"]) - pt3(SPACE["D"])
        plan_dir[2] = 0.0
        plan_dir = plan_dir / np.linalg.norm(plan_dir)
        face_theta = math.atan2(-plan_dir[0], plan_dir[1])   # normal, observer's side
        centre = (pt3(SPACE["D"]) + pt3(SPACE["E"])) / 2.0
        Pp = pt3(G["P"])
        pdot = marker(Pp, POINT_COL, 0.085)
        plab = billboard(self, mono("P", color=POINT_COL, size=24)
                         .move_to(Pp + np.array([0.12, 0.0, 0.22])))

        fly_camera(
            self,
            "Now come round and look at the glass face on.",
            phi=90 * DEGREES, theta=face_theta, zoom=1.45, focal_distance=60.0,
            frame_center=np.array([centre[0], centre[1], centre[2] + 0.15]),
        )
        narrate(
            self,
            "Two lines are drawn on this one sheet of glass: the line D E, and the "
            "cut, one to two. Two lines in the same plane, not parallel, must cross - "
            "and where they cross is a point on the line and on the plate at once. "
            "That is the piercing point, with no construction at all.",
            FadeIn(pdot), FadeIn(plab),
            lag_ratio=0.5,
        )

        # ---- and from straight above, the glass IS the top view of the line ---
        fly_camera(
            self,
            "One more move, and this is the one that makes it practical. Go straight "
            "up and look down on the whole arrangement.",
            FadeOut(plab), FadeOut(self.tags[0]),
            phi=0.0, theta=-90 * DEGREES, zoom=1.3, focal_distance=60.0,
            frame_center=ORIGIN,
        )
        narrate(
            self,
            "The glass is vertical, so from directly above it closes up into a single "
            "line - and that line is d e, the top view of the line itself. So in the "
            "top view the cutting plane is already drawn for you. You never have to "
            "put it on the paper.",
            Create(trace),
            Indicate(trace, color=CUT_COL, scale_factor=1.04),
            lag_ratio=0.6,
        )
        narrate(
            self,
            "And look where one and two are sitting: exactly where d e crosses two "
            "sides of the top view of the plate. That is how you find them on the "
            "sheet - no measuring, just two crossings.",
            Indicate(cutdots, color=CUT_COL, scale_factor=1.6),
        )

        # ---- the method, now that it has been watched ------------------------
        steps = [
            ("1", "contain the line in a vertical cutting plane",
             "in the TOP view that plane is the line de itself", CUT_COL),
            ("2", "mark where de crosses two sides of abc",
             "those crossings are 1 and 2, the ends of the slice", CUT_COL),
            ("3", "carry 1 and 2 up to the front view",
             "onto the matching sides of a′b′c′, and join 1′2′", CORAL),
            ("4", "1′2′ meets d′e′ at the piercing point p′",
             "both lines lie in the cutting plane, so they must meet", POINT_COL),
        ]
        rows = VGroup(*[step_badge(n, h, d, c) for n, h, d, c in steps])
        rows.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        for row in rows[2:]:
            row.set_opacity(0.32)          # the pencil work, still to come
        card = hud(self, card_back(rows, pad=0.35).move_to(ORIGIN))
        card.levels = [1.0, 1.0, 0.32, 0.32]

        narrate(
            self,
            "So here is the whole method, and you have just watched the first half of "
            "it happen.",
            FadeOut(plate), FadeOut(line), FadeOut(glass), FadeOut(cutseg),
            FadeOut(cutdots), FadeOut(cutlabs), FadeOut(labs), FadeOut(pdot),
            FadeOut(trace), FadeOut(self.vp), FadeOut(self.hp), FadeOut(self.xy),
            FadeOut(self.tags[1]), FadeOut(self.tags[2]), FadeOut(self.tags[3]),
            FadeIn(card),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Steps three and four are the only part that needs a pencil. Carry the "
            "two crossings up into the front view, onto the same two sides of the "
            "triangle, and join them. That line one prime two prime is the front "
            "view of the slice, and where it meets d prime e prime is the front view "
            "of the piercing point.",
            rail_focus(card, rows, (2, 3), dim_level=0.45),
        )

        note = hud(self, chip(
            "the cutting plane gives the POINT · auxiliary views give the ANGLE",
            color=GOLD, size=20).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "That gives the point, and with it the visibility. The true angle is a "
            "separate job, and for that we do need auxiliary views.",
            settle(FadeIn(note)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S03 - Q.11 part one: the piercing point, then visibility settled properly
# ==========================================================================
class S03_Piercing(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        fv, tv = G["fv"], G["tv"]

        # ---------------- the given figure ------------------------------------
        xy = Line(P2(np.array([-16.0, 0.0])), P2(np.array([121.0, 0.0])),
                  color=INK, stroke_width=2.8)
        xy_lab = VGroup(mono("X", color=INK, size=16).next_to(xy, LEFT, buff=0.1),
                        mono("Y", color=INK, size=16).next_to(xy, RIGHT, buff=0.1))
        fv_tri = sheet_tri(fv, PLATE_COL, 3.0)
        tv_tri = sheet_tri(tv, PLATE_COL, 3.0)
        fv_line = sheet_line(fv)
        tv_line = sheet_line(tv)
        dots = VGroup(*[Dot(P2(fv[k]), radius=0.04,
                            color=PLATE_COL if k in TRI else LINE_COL) for k in ALL],
                      *[Dot(P2(tv[k]), radius=0.04,
                            color=PLATE_COL if k in TRI else LINE_COL) for k in ALL])
        labs = VGroup()
        for k in ALL:
            col = PLATE_COL if k in TRI else LINE_COL
            labs.add(mono(f"{k.lower()}′", color=col, size=15)
                     .next_to(P2(fv[k]), outward(fv[k], fv, ALL), buff=0.07))
            labs.add(mono(k.lower(), color=col, size=15)
                     .next_to(P2(tv[k]), outward(tv[k], tv, ALL), buff=0.07))
        # parked out to the right of each view: above them is where the
        # visibility verdicts go, and to the left is where the caption sits
        tag_fv = chip("FRONT VIEW", color=CORAL, size=14).move_to(
            P2(np.array([136.0, 58.0])))
        tag_tv = chip("TOP VIEW", color=TEAL, size=14).move_to(
            P2(np.array([136.0, -42.0])))
        given = VGroup(xy, xy_lab, fv_tri, tv_tri, fv_line, tv_line, dots, labs,
                       tag_fv, tag_tv)

        # ---------------- the cutting plane, seen edge-on in the top view ------
        cut_band = Line(P2(on_line(tv, -0.10)), P2(on_line(tv, 1.10)),
                        color=CUT_COL, stroke_width=10, stroke_opacity=0.28)
        c1, c2 = G["cut"]
        tv1, tv2 = on_line(tv, c1["t"]), on_line(tv, c2["t"])
        fv1, fv2 = on_edge(fv, c1["edge"], c1["s"]), on_edge(fv, c2["edge"], c2["s"])
        marks_tv = VGroup(
            Dot(P2(tv1), radius=0.05, color=CUT_COL),
            Dot(P2(tv2), radius=0.05, color=CUT_COL),
            mono("1", color=CUT_COL, size=16).next_to(P2(tv1), DL, buff=0.05),
            mono("2", color=CUT_COL, size=16).next_to(P2(tv2), DR, buff=0.05))
        risers12 = VGroup(riser(tv1, fv1, CUT_COL), riser(tv2, fv2, CUT_COL))
        marks_fv = VGroup(
            Dot(P2(fv1), radius=0.05, color=CUT_COL),
            Dot(P2(fv2), radius=0.05, color=CUT_COL),
            mono("1′", color=CUT_COL, size=16).next_to(P2(fv1), UL, buff=0.05),
            mono("2′", color=CUT_COL, size=16).next_to(P2(fv2), UR, buff=0.05))
        cutline = Line(P2(fv1), P2(fv2), color=CUT_COL, stroke_width=3.4)

        # ---------------- the piercing point ----------------------------------
        pfv, ptv = on_line(fv, G["t"]), on_line(tv, G["t"])
        ring_fv = Circle(radius=0.13, color=POINT_COL, stroke_width=2.8).move_to(P2(pfv))
        ring_tv = Circle(radius=0.13, color=POINT_COL, stroke_width=2.8).move_to(P2(ptv))
        drop = riser(pfv, ptv, POINT_COL, width=1.3, opacity=0.75)
        plabs = VGroup(mono("p′", color=POINT_COL, size=17).next_to(ring_fv, UR, buff=0.05),
                       mono("p", color=POINT_COL, size=17).next_to(ring_tv, DR, buff=0.05))
        p_dims = VGroup(
            dim(np.array([pfv[0], 0.0]), pfv, f"{G['P'][2]:.1f}", CORAL, offset=-8.0, gap=6.5),
            dim(np.array([ptv[0], 0.0]), ptv, f"{G['P'][1]:.1f}", TEAL, offset=8.0, gap=6.5))

        # ---------------- visibility, crossing by crossing --------------------
        # TOP view: read the two heights off the FRONT view at the same projector
        top_ev = G["vis"]["top"]["events"]
        top_read = VGroup()
        for ev in top_ev:
            ln = on_line(fv, ev["t"])
            ed = on_edge(fv, ev["edge"], ev["s"])
            winner = ln if ev["line_nearer"] else ed
            top_read.add(VGroup(
                Line(P2(np.array([ln[0], min(ln[1], ed[1]) - 4])),
                     P2(np.array([ln[0], 74.0])),
                     color=SLATE, stroke_width=1.2, stroke_opacity=0.7),
                Dot(P2(ln), radius=0.05, color=LINE_COL),
                Dot(P2(ed), radius=0.05, color=PLATE_COL),
                Circle(radius=0.11, color=POINT_COL, stroke_width=2.0).move_to(P2(winner)),
                # the verdict goes clear above the front view, never on it
                mono("SEEN" if ev["line_nearer"] else "HIDDEN",
                     color=LINE_COL if ev["line_nearer"] else PLATE_COL, size=14)
                .move_to(P2(np.array([ln[0], 80.0])))))

        # FRONT view: read the two depths off the TOP view at the same projector
        front_ev = G["vis"]["front"]["events"]
        front_read = VGroup()
        for ev in front_ev:
            ln = on_line(tv, ev["t"])
            ed = on_edge(tv, ev["edge"], ev["s"])
            winner = ln if ev["line_nearer"] else ed
            front_read.add(VGroup(
                Line(P2(np.array([ln[0], max(ln[1], ed[1]) + 4])),
                     P2(np.array([ln[0], -74.0])),
                     color=SLATE, stroke_width=1.2, stroke_opacity=0.7),
                Dot(P2(ln), radius=0.05, color=LINE_COL),
                Dot(P2(ed), radius=0.05, color=PLATE_COL),
                Circle(radius=0.11, color=POINT_COL, stroke_width=2.0).move_to(P2(winner)),
                mono("SEEN" if ev["line_nearer"] else "HIDDEN",
                     color=LINE_COL if ev["line_nearer"] else PLATE_COL, size=14)
                .move_to(P2(np.array([ln[0], -80.0])))))

        def split_line(view, hidden):
            lo, hi = hidden
            a, b = on_line(view, lo), on_line(view, hi)
            return VGroup(
                Line(P2(view["D"]), P2(a), color=LINE_COL, stroke_width=3.6),
                DashedLine(P2(a), P2(b), color=LINE_COL, stroke_width=3.2,
                           dash_length=0.07),
                Line(P2(b), P2(view["E"]), color=LINE_COL, stroke_width=3.6))

        new_fv = split_line(fv, G["vis"]["front"]["hidden"])
        new_tv = split_line(tv, G["vis"]["top"]["hidden"])

        # ---------------- furniture -------------------------------------------
        centre, W = frame_target([given])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 4 (Set A) · Q.11",
            "Figure P4.11 · piercing point and visibility")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "plot the given views", "triangle abc and line de", SLATE),
            step_badge("2", "cut with a vertical plane", "in the top view it IS de · mark 1, 2", CUT_COL),
            step_badge("3", "carry 1 and 2 up, join 1′2′", "it meets d′e′ at p′ · drop p′ to p", POINT_COL),
            step_badge("4", "settle the visibility", "at each crossing, look in the OTHER view", GOLD),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)

        data_rows = VGroup(
            mono("GIVEN (mm)", color=SLATE, size=15),
            mono("         x   front    up", color=SLATE, size=13),
            *[mono(f"  {k}    {SPACE[k][0]:5.0f}   {SPACE[k][1]:5.0f} {SPACE[k][2]:5.0f}",
                   color=PLATE_COL if k in TRI else LINE_COL, size=15) for k in ALL],
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        data = card_back(data_rows, pad=0.22, opacity=0.85)
        data.add(SurroundingRectangle(data_rows, color=SLATE, buff=0.22,
                                      corner_radius=0.1, stroke_width=1.2))
        pin_to_frame(self, data, corner=DOWN + RIGHT, buff=0.45)

        self.add(bar, rail)

        # ------------------------------ animate --------------------------------
        narrate(
            self,
            "Question eleven. A triangular plane A B C and a straight line D E, both "
            "given by their two views. Find the piercing point, say which stretch of "
            "the line is hidden, and find the true angle between them.",
            FadeIn(bar), FadeIn(data),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Set the question down. Front view above X Y, top view below, and the "
            "five points at the heights and depths given.",
            rail_focus(rail, rungs, 0),
            Create(xy), FadeIn(xy_lab), FadeIn(dots), FadeIn(tag_fv), FadeIn(tag_tv),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Join the triangle in both views, and draw the line in both views. "
            "Nothing has been constructed yet - this is just the question.",
            Create(fv_tri), Create(tv_tri), Create(fv_line), Create(tv_line),
            FadeIn(labs),
            lag_ratio=0.2,
        )

        narrate(
            self,
            "Step two. The vertical cutting plane through D E is already on the paper: "
            "seen from above it is the line d e itself. Think of the pale band as the "
            "sheet of glass, edge on.",
            rail_focus(rail, rungs, 1),
            look_at(self, [tv_tri, cut_band, tag_tv], right=0.34),
            FadeIn(cut_band),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"Follow it across the triangle. It crosses side "
            f"{c1['edge'][0].lower()}{c1['edge'][1].lower()} at one, and side "
            f"{c2['edge'][0].lower()}{c2['edge'][1].lower()} at two. Those two "
            "crossings are the ends of the slice.",
            Create(marks_tv),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Step three. Carry one and two straight up into the front view, onto the "
            "same two sides of the triangle, and join one prime to two prime. That "
            "line is the front view of the slice.",
            rail_focus(rail, rungs, 2),
            look_at(self, [given]),
            Create(risers12), Create(marks_fv), Create(cutline),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Now the payoff. One prime two prime and d prime e prime both lie in the "
            "cutting plane, so they must cross - and that crossing is p prime, the "
            "front view of the piercing point.",
            look_at(self, [fv_tri, cutline, ring_fv], right=0.34),
            Create(ring_fv), FadeIn(plabs[0]),
            lag_ratio=0.4,
        )
        narrate(
            self,
            "Drop it straight down onto d e for the top view, p. Measure it and the "
            f"piercing point stands {G['P'][2]:.1f} millimetres above the H P and "
            f"{G['P'][1]:.1f} in front of the V P.",
            look_at(self, [given]),
            Create(drop), Create(ring_tv), FadeIn(plabs[1]), Create(p_dims),
            lag_ratio=0.25,
        )

        # ---- visibility -------------------------------------------------------
        narrate(
            self,
            "Step four, visibility - and this is the part that is usually guessed. It "
            "does not have to be. At a crossing of the two outlines, whichever is "
            "nearer the observer is drawn full, and you read which is nearer in the "
            "OTHER view.",
            rail_focus(rail, rungs, 3), FadeOut(p_dims),
        )
        narrate(
            self,
            "Take the top view first. Looking down, nearer means higher, and height "
            "is what the front view shows. The two crossings are the ones we have "
            "already marked: one and two.",
            look_at(self, [fv_tri, fv_line], right=0.34),
            FadeIn(top_read[0][0]), FadeIn(top_read[1][0]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"At the first, the line is {top_ev[0]['line_val']:.0f} up and the side of "
            f"the triangle only {top_ev[0]['edge_val']:.0f}: the line is higher, so in "
            "the top view it is seen. At the second the plate wins - "
            f"{top_ev[1]['edge_val']:.0f} against {top_ev[1]['line_val']:.0f} - so "
            "there the line is hidden.",
            FadeIn(top_read[0][1:]), FadeIn(top_read[1][1:]),
            lag_ratio=0.4,
        )
        narrate(
            self,
            "Now the front view, where nearer means further forward - and depth is "
            "what the top view shows, measured down from X Y. The same test, at that "
            "view's own two crossings.",
            look_at(self, [tv_tri, tv_line], right=0.34),
            FadeIn(front_read[0][0]), FadeIn(front_read[1][0]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"Here the line is {front_ev[0]['line_val']:.0f} in front against "
            f"{front_ev[0]['edge_val']:.0f}, so it is seen; and there it is "
            f"{front_ev[1]['line_val']:.0f} against the plate's "
            f"{front_ev[1]['edge_val']:.0f}, so it is hidden.",
            FadeIn(front_read[0][1:]), FadeIn(front_read[1][1:]),
            lag_ratio=0.4,
        )
        narrate(
            self,
            "Put the dashes in between the piercing point and the crossing where the "
            "plate took over, and stop them at the outline: past the edge of the "
            "triangle there is nothing left to hide the line.",
            look_at(self, [given]),
            FadeOut(top_read), FadeOut(front_read),
            ReplacementTransform(fv_line, new_fv),
            ReplacementTransform(tv_line, new_tv),
            lag_ratio=0.25,
        )

        ans_rows = VGroup(
            mono("piercing point p", color=POINT_COL, size=18),
            mono(f"  {G['P'][2]:.1f} above the HP", color=CORAL, size=15),
            mono(f"  {G['P'][1]:.1f} in front of the VP", color=TEAL, size=15),
            mono("Dp   full in both views", color=LINE_COL, size=15),
            mono("pE   dashed within the outline", color=LINE_COL, size=15),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=GOLD, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)

        narrate(
            self,
            "And the first half of question eleven is finished. The D half of the "
            "line is visible throughout; the E half is hidden from the piercing point "
            "out to the edge of the triangle, and the two views hide different "
            "amounts of it.",
            settle(FadeOut(data), FadeIn(ans)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 / S05 - the true angle, in three auxiliary views
# ==========================================================================
def aux_view(pts, width=2.8, opacity=0.10, line_width=3.2):
    """One view of the whole figure: the plate and the line, in series colours."""
    return VGroup(sheet_tri(pts, PLATE_COL, width, opacity),
                  sheet_line(pts, LINE_COL, line_width))


def aux_rays(src, dst, colour=MUTED):
    """The projectors that carry every point from one view into the next."""
    return VGroup(*[riser(src[k], dst[k], colour, width=0.9, opacity=0.45)
                    for k in src])


def ref_label(text, line, buff=0.30):
    """The name of a reference line, parked just beyond its far end and on its
    own axis - anywhere else and it lands in the middle of the next view."""
    d = line.get_unit_vector()
    return mono(text, color=INK, size=14).move_to(line.get_end() + d * buff)


class S04_TrueAngleA(MovingCameraScene):
    """Screen one of two: why the angle is awkward, then the edge view and the
    true shape."""

    def construct(self):
        self.camera.background_color = NAVY
        fv, tv = G["fv"], G["tv"]
        a1, a2 = G["aux1"], G["aux2"]

        xy = Line(P2(np.array([-16.0, 0.0])), P2(np.array([121.0, 0.0])),
                  color=INK, stroke_width=2.4)
        given = VGroup(xy, aux_view(fv), aux_view(tv))

        # the horizontal line of the plate, which sets the direction of X1Y1
        m_fv = np.array([G["M"][0], G["M"][2]])
        m_tv = np.array([G["M"][0], -G["M"][1]])
        hz = VGroup(
            Line(P2(fv["A"]), P2(m_fv), color=CUT_COL, stroke_width=3.2),
            riser(m_fv, m_tv, CUT_COL, width=1.0, opacity=0.5),
            Line(P2(tv["A"]), P2(m_tv), color=CUT_COL, stroke_width=3.2),
            mono("m′", color=CUT_COL, size=14).next_to(P2(m_fv), UR, buff=0.05),
            mono("m", color=CUT_COL, size=14).next_to(P2(m_tv), DR, buff=0.05),
            mono("true length", color=CUT_COL, size=12).move_to(
                P2((tv["A"] + m_tv) / 2 + np.array([0.0, 9.0]))))

        x1 = ref_line(G["p0"], G["w1"], {**tv, **a1})
        x2 = ref_line(G["q0"], G["v2"], {**a1, **a2})
        x1l = ref_label("X1Y1", x1)
        x2l = ref_label("X2Y2", x2)
        r1, r2 = aux_rays(tv, a1), aux_rays(a1, a2)
        v1 = aux_view(a1, width=3.0)
        v2m = aux_view(a2, width=3.2)
        e1_lab = mono("plate EDGE ON", color=PLATE_COL, size=13).move_to(
            P2(a1["C"] + np.array([-6.0, -13.0])))
        e2_lab = mono("plate TRUE SHAPE", color=PLATE_COL, size=13).move_to(
            P2((a2["A"] + a2["B"] + a2["C"]) / 3.0 + np.array([0.0, -15.0])))

        centre, W = frame_target([given])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 4 (Set A) · Q.11",
            "true angle · 1 of 2 · edge view, then true shape")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("aux 1", "X1Y1 ⊥ am", "carry HEIGHTS · plate goes edge on", PLATE_COL),
            step_badge("aux 2", "X2Y2 ∥ the edge view", "carry from the TOP view · true shape", PLATE_COL),
            step_badge("aux 3", "X3Y3 ∥ d₂e₂", "next screen · where the angle is read", SLATE),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)

        goal_rows = VGroup(
            mono("to MEASURE the angle we need", color=SLATE, size=15),
            mono("one view showing", color=SLATE, size=15),
            mono("  the plate as an EDGE", color=PLATE_COL, size=16),
            mono("  the line at TRUE LENGTH", color=LINE_COL, size=16),
            mono("at the same time", color=SLATE, size=15),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        goal = card_back(goal_rows, pad=0.22, opacity=0.9)
        goal.add(SurroundingRectangle(goal_rows, color=SLATE, buff=0.22,
                                      corner_radius=0.1, stroke_width=1.2))
        pin_to_frame(self, goal, corner=DOWN + RIGHT, buff=0.45)

        self.add(bar, rail)

        narrate(
            self,
            "Part two: the true angle between the line and the plane. An angle can "
            "only be measured where both of its arms are true, and in these two views "
            "neither arm is.",
            FadeIn(bar), Create(given),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "So we are hunting for one particular view: one that shows the plate as a "
            "straight edge and the line at its true length, both at once. Three "
            "auxiliaries get us there, and the first two are last episode's work.",
            FadeIn(goal),
        )

        narrate(
            self,
            "First, a horizontal line of the plate: through a prime, parallel to X Y, "
            "cutting b prime c prime at m prime. Its top view a m is true length and "
            "true direction, and it is what aims the first auxiliary.",
            look_at(self, [given, hz]),
            Create(hz),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Auxiliary one. X one Y one perpendicular to a m, projectors across, and "
            "each point carries its height above the H P from the front view. The "
            "plate closes up into an edge, and the line comes along for the ride.",
            rail_focus(rail, rungs, 0),
            look_at(self, [given[2], x1, v1]),
            Create(x1), FadeIn(x1l), Create(r1), Create(v1), FadeIn(e1_lab),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Auxiliary two. X two Y two parallel to that edge, and this time each "
            "point carries its distance from X one Y one, measured back in the top "
            "view. Now the plate is in true shape.",
            rail_focus(rail, rungs, 1),
            look_at(self, [v1, x2, v2m]),
            Create(x2), FadeIn(x2l), Create(r2), Create(v2m), FadeIn(e2_lab),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "But look at the line. It has an image in this view too, d two e two, and "
            "it is still not true length. That image, though, is the key to the last "
            "step - because the next reference line is drawn parallel to it.",
            look_at(self, [v2m]),
            Indicate(v2m[1], color=LINE_COL, scale_factor=1.06),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.3)


class S05_TrueAngleB(MovingCameraScene):
    """Screen two of two: the third auxiliary, and the angle."""

    def construct(self):
        self.camera.background_color = NAVY
        a1, a2, a3 = G["aux1"], G["aux2"], G["aux3"]

        x2 = ref_line(G["q0"], G["v2"], {**a1, **a2}, width=2.2)
        x3 = ref_line(G["r0"], G["v3"], {**a2, **a3})
        x2l = ref_label("X2Y2", x2)
        x3l = ref_label("X3Y3", x3)
        v1 = aux_view(a1, width=2.0, opacity=0.06, line_width=2.2)
        v2m = aux_view(a2, width=3.0)
        v3m = aux_view(a3, width=3.4, line_width=4.0)
        r3 = aux_rays(a2, a3)

        # the parallel marks that justify the whole step
        mid2 = (a2["D"] + a2["E"]) / 2.0
        foot = G["r0"] + G["v3"] * float(np.dot(mid2 - G["r0"], G["v3"]))

        def par_marks(point, direction, colour, size=5.0, gap=5.0):
            d = np.array([direction[0], direction[1], 0.0])
            d = d / np.linalg.norm(d)
            n = np.array([-d[1], d[0], 0.0])
            g = VGroup()
            for s in (-0.5, 0.5):
                c = P2(point) + d * s * gap * MM
                arm = (n * 0.9 + d * 0.45) * size * MM
                g.add(Line(c - arm, c + arm, color=colour, stroke_width=2.4))
            return g

        par = VGroup(par_marks(mid2, G["v3"], LINE_COL),
                     par_marks(foot, G["v3"], LINE_COL))

        # the angle itself, at the piercing point's own end of the line
        edge_dir = (a3["B"] - a3["A"]) / np.linalg.norm(a3["B"] - a3["A"])
        line_dir = (a3["E"] - a3["D"]) / np.linalg.norm(a3["E"] - a3["D"])
        if np.dot(edge_dir, line_dir) < 0:
            edge_dir = -edge_dir
        # the two arms cross at the piercing point - projection is affine along
        # the line, so p keeps its parameter t in every single view
        p3 = on_line(a3, G["t"])
        edge_res = abs(np.cross(a3["B"] - a3["A"], p3 - a3["A"])) / np.linalg.norm(
            a3["B"] - a3["A"])
        assert edge_res < 1e-6, "p is not on the edge view in aux 3"
        vertex = P2(p3)
        a_start = math.atan2(edge_dir[1], edge_dir[0])
        a_end = math.atan2(line_dir[1], line_dir[0])
        sweep = (a_end - a_start + PI) % TAU - PI
        arc = Arc(radius=0.45, start_angle=a_start, angle=sweep,
                  arc_center=vertex, color=GOLD, stroke_width=3.0)
        # a 23 degree wedge will hold the value if the label lies ALONG the
        # bisector: what has to fit between the arms is its height, not its width
        bis = a_start + sweep / 2.0
        alab = mono(f"φ = {G['true_angle']:.1f}°", color=GOLD, size=16).move_to(
            vertex + 1.0 * np.array([math.cos(bis), math.sin(bis), 0.0]))
        focus = Circle(radius=0.9).move_to(vertex)      # never drawn: a camera target
        pdot3 = VGroup(Circle(radius=0.1, color=POINT_COL, stroke_width=2.4).move_to(vertex),
                       mono("p", color=POINT_COL, size=14).next_to(vertex, DL, buff=0.06))
        tl_dim = dim(a3["D"], a3["E"], f"{G['de_true']:.1f}  TRUE LENGTH", LINE_COL,
                     size=14, offset=-9.0, gap=7.0)
        edge_lab = mono("plate EDGE ON again", color=PLATE_COL, size=13).move_to(
            P2(a3["A"] + np.array([-4.0, 13.0])))

        centre, W = frame_target([VGroup(v1, v2m, x2)])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 4 (Set A) · Q.11",
            "true angle · 2 of 2 · the third auxiliary")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("aux 1", "X1Y1 ⊥ am", "plate edge on", SLATE),
            step_badge("aux 2", "X2Y2 ∥ the edge view", "plate true shape", SLATE),
            step_badge("aux 3", "X3Y3 ∥ d₂e₂", "edge on AND true length", GOLD),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)
        self.add(bar, rail)

        lens = VGroup(
            mono("the line measures", color=SLATE, size=14),
            mono(f"  front view   {G['de_fv']:.1f}", color=CORAL, size=15),
            mono(f"  top view     {G['de_tv']:.1f}", color=TEAL, size=15),
            mono(f"  aux 1        {G['de_aux1']:.1f}", color=PLATE_COL, size=15),
            mono(f"  aux 2        {G['de_aux2']:.1f}", color=PLATE_COL, size=15),
            mono(f"  aux 3        {G['de_true']:.1f}", color=LINE_COL, size=16),
            mono("  ← the true length", color=LINE_COL, size=13),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        lens_card = card_back(lens, pad=0.22, opacity=0.9)
        lens_card.add(SurroundingRectangle(lens, color=SLATE, buff=0.22,
                                           corner_radius=0.1, stroke_width=1.2))
        pin_to_frame(self, lens_card, corner=DOWN + RIGHT, buff=0.45)

        narrate(
            self,
            "Picking up where we left off: the edge view behind us, the true shape in "
            "front of us, and the line's image lying across it.",
            FadeIn(bar), FadeIn(v1), Create(x2), FadeIn(x2l), Create(v2m),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Third auxiliary, and this is the whole trick of the problem. Draw X "
            "three Y three parallel to d two e two - parallel to the line's image in "
            "the true shape view.",
            look_at(self, [v2m, x3]),
            Create(x3), FadeIn(x3l), FadeIn(par),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Project every point across, square to the new reference line, and carry "
            "the distances from X two Y two as measured back in the first auxiliary. "
            "Two things now happen together, and neither is luck.",
            look_at(self, [v2m, x3, v3m]),
            Create(r3),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "The direction we are looking along still lies in the plate, so the plate "
            "closes into an edge again.",
            look_at(self, [v3m]),
            Create(v3m), FadeIn(edge_lab),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "And because the new reference line was drawn parallel to the line's "
            "image, the line is parallel to the new plane of projection - so it comes "
            f"out at its true length, {G['de_true']:.1f} millimetres. Every earlier "
            "view had it shorter.",
            Create(tl_dim), FadeIn(lens_card),
            lag_ratio=0.35,
        )
        narrate(
            self,
            "A plate seen as an edge, a line seen true length, in one view. The angle "
            "between them is the angle itself, and it measures "
            f"{G['true_angle']:.1f} degrees.",
            look_at(self, [focus], right=0.30),
            FadeOut(tl_dim), FadeOut(edge_lab), FadeOut(r3),
            Create(arc), FadeIn(pdot3), FadeIn(alab),
            lag_ratio=0.3,
        )

        ans = pin_to_frame(self, card_back(
            chip(f"true angle between DE and ABC = {G['true_angle']:.1f}°",
                 color=GOLD, size=20), pad=0.1), corner=DOWN, buff=0.4)
        narrate(
            self,
            "And that completes question eleven.",
            FadeOut(lens_card), FadeIn(ans),
            lag_ratio=0.3,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S06 - recap: three jobs, three tools, one chain
# ==========================================================================
class S06_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "line meets plane")
        self.add(bar)

        rows = VGroup(
            mono("piercing point   a cutting plane through the line · no auxiliaries",
                 color=CUT_COL, size=19),
            mono("visibility       at each crossing, compare in the OTHER view",
                 color=GOLD, size=19),
            mono("true angle       edge view · true shape · then ∥ the line's image",
                 color=PLATE_COL, size=19),
        ).arrange(DOWN, buff=0.32, aligned_edge=LEFT).move_to(np.array([-0.2, 1.55, 0]))

        # the chain: one branch needs no auxiliary at all, the other needs three
        start = chip("FRONT + TOP VIEWS", color=INK, size=15)
        point = chip("PIERCING POINT · VISIBILITY", color=CUT_COL, size=15)
        a1c = chip("aux 1 · EDGE VIEW", color=PLATE_COL, size=14)
        a2c = chip("aux 2 · TRUE SHAPE", color=PLATE_COL, size=14)
        a3c = chip("aux 3 · EDGE + TRUE LENGTH", color=PLATE_COL, size=14)
        angc = chip(f"φ = {G['true_angle']:.1f}°", color=GOLD, size=16)

        start.move_to(np.array([-5.1, -1.35, 0]))
        point.move_to(np.array([-0.2, -0.30, 0]))
        lower = VGroup(a1c, a2c, a3c, angc).arrange(RIGHT, buff=0.42)
        lower.move_to(np.array([0.55, -2.65, 0]))

        def link(a, b, text="", colour=SLATE, up=True):
            arrow = Arrow(a.get_right(), b.get_left(), buff=0.14, color=colour,
                          stroke_width=2.4, max_tip_length_to_length_ratio=0.16)
            g = VGroup(arrow)
            if text:
                g.add(mono(text, color=colour, size=13)
                      .next_to(arrow, UP if up else DOWN, buff=0.07))
            return g

        branch_up = link(start, point, "cutting plane", CUT_COL, up=False)
        branch_dn = link(start, a1c, "⊥ am", PLATE_COL, up=False)
        chain = VGroup(link(a1c, a2c), link(a2c, a3c), link(a3c, angc))

        narrate(self, "Three jobs, and three different tools.", FadeIn(bar))
        narrate(
            self,
            "The piercing point needs no auxiliary view at all. Contain the line in a "
            "vertical cutting plane - which in the top view is the line itself - cut "
            "the triangle, carry the two crossings up, and intersect.",
            FadeIn(rows[0]), FadeIn(start), FadeIn(branch_up), FadeIn(point),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Visibility is then decided crossing by crossing, and always in the other "
            "view: for the top view compare heights in the front view, and for the "
            "front view compare depths in the top view. Never by eye.",
            FadeIn(rows[1]),
        )
        narrate(
            self,
            "Only the true angle needs the auxiliary chain, and it needs three views. "
            "Edge view first, then true shape, then one more taken parallel to the "
            "line's image in that true shape.",
            FadeIn(rows[2]), FadeIn(branch_dn), FadeIn(a1c), FadeIn(chain[0]),
            FadeIn(a2c), FadeIn(chain[1]), FadeIn(a3c),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "That last view is the only place the angle can be measured, because it "
            "is the only place where the plate is an edge and the line is true length "
            "at the same time.",
            FadeIn(chain[2]), FadeIn(angc),
            lag_ratio=0.4,
        )

        ansc = VGroup(
            chip(f"p:  {G['P'][2]:.1f} above the HP,  {G['P'][1]:.1f} in front of the VP",
                 color=POINT_COL, size=18),
            chip(f"true angle between DE and ABC = {G['true_angle']:.1f}°",
                 color=GOLD, size=18),
        ).arrange(DOWN, buff=0.22).move_to(np.array([0.0, 1.55, 0]))
        narrate(
            self,
            f"For question eleven the piercing point sits {G['P'][2]:.1f} above the "
            f"H P and {G['P'][1]:.1f} in front of the V P, and the true angle comes "
            f"to {G['true_angle']:.1f} degrees.",
            FadeOut(rows), FadeIn(ansc),
            lag_ratio=0.4,
        )
        narrate(
            self,
            "Work it through on paper, and check yourself the way the drawing does: "
            "the cut line must pass through the piercing point in both views, and the "
            "three points of an edge view must fall in one straight line.",
        )
        narrate(
            self,
            "Next time, the last two items on the sheet: the true angle between two "
            "planes, and the shortest distance between skew lines. Both are built out "
            "of exactly these moves.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme: run the file directly and it prints the answers it is about
#  to animate, so the video can be checked against a worked solution before a
#  single frame is rendered.
#
#      py -3.11 ed07_piercing_point.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 4 (Set A) Q.11 - Figure P4.11")
    print(f"  piercing point P   x {G['P'][0]:.1f}   {G['P'][1]:.1f} in front of the VP"
          f"   {G['P'][2]:.1f} above the HP     (t = {G['t']:.3f} along DE)")
    print(f"  true angle DE ^ ABC   {G['true_angle']:.2f}°")
    print("  cutting plane crosses:")
    for c in G["cut"]:
        print(f"    side {c['edge'][0]}{c['edge'][1]} at {c['s']:.3f} of its length"
              f"  -> {np.round(c['space'], 1)}")
    for view in ("front", "top"):
        v = G["vis"][view]
        what = "depth in front of the VP" if view == "front" else "height above the HP"
        print(f"  {view} view: hidden from t = {v['hidden'][0]:.3f} to "
              f"{v['hidden'][1]:.3f}   (nearer = more {what})")
        for e in v["events"]:
            print(f"    crossing t = {e['t']:.3f} on {e['edge'][0]}{e['edge'][1]}: "
                  f"line {e['line_val']:.1f} vs plate {e['edge_val']:.1f} -> "
                  f"{'line' if e['line_nearer'] else 'plate'} nearer")
    print(f"  DE measures: front {G['de_fv']:.1f}   top {G['de_tv']:.1f}"
          f"   aux1 {G['de_aux1']:.1f}   aux2 {G['de_aux2']:.1f}"
          f"   aux3 {G['de_true']:.1f} (true)")
