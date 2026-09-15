"""
Engineering Drawing I - Sheet 4 / Lecture 4  (Basic Descriptive Geometry II)
Episode 09: The Shortest Distance Between Two Skew Lines   (§4.10)
            + the common perpendicular put back on the given views

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed09_skew_lines.py S03_Construction
    ... or use render_ed09.bat to build all five scenes in order.

Scene order (about eleven minutes in all):

    S01_TheyDoNotMeet   the two lines in space. They cross in the front view,
                        they cross in the top view - and the two crossings are
                        not the same point, which is what "skew" means. Then
                        the one link that is square to both, watched from the
                        end of AB where it shows its true length
    S02_Strategy        why the point view is the view that answers it, and the
                        two auxiliaries that get there - the same pair episode
                        08 used, aimed at a different question
    S03_Construction    the sheet: AB to true length, AB to a point, and the
                        perpendicular dropped onto c2d2 - the answer
    S04_BackToTheViews  where that link actually is: the foot carried back into
                        aux 1, the top view and the front view, and measured in
                        each of them to show every one of those is too short
    S05_Recap           the method in four lines, and the trap

Everything is computed by solve(), which asserts that the lines really are
skew, that the link it draws is perpendicular to both of them, that the first
auxiliary shows AB at true length and the second reduces it to a point, and
that the distance read off the drawing equals the distance computed from the
space coordinates. A wrong number stops the render instead of teaching it.

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
#  The given: (x along XY, in front of the VP, above the HP) in millimetres.
#
#  Two lines, AB and CD. Chosen so that they cross in BOTH given views - at
#  two different places - which is exactly the situation the method is for.
# ==========================================================================
SPACE = {
    "A": np.array([10.0, 10.0,  5.0]),
    "B": np.array([95.0, 60.0, 45.0]),
    "C": np.array([10.0, 20.0, 65.0]),
    "D": np.array([90.0, 10.0, 35.0]),
}
LINES = (("A", "B"), ("C", "D"))
ALL = ("A", "B", "C", "D")

# Colour is meaning, as everywhere in this series. Gold is what the episode is
# chasing - here the line AB, because AB is the one we take to a point view.
# Violet is the other line. Coral is the answer: the common perpendicular.
AB_COL = GOLD
CD_COL = VIOLET
SD_COL = CORAL

GAPS = (38.0, 15.0)      # X1Y1 and X2Y2 set-backs
MM = 0.026               # drawing millimetre -> Manim unit (the flat sheet)
S3 = 0.033               # millimetre -> Manim unit on the 3-D stage
X_MID = 52.5             # the x that is centred on the 3-D stage


def _project(src, origin, along, normal, dist):
    """Drop each point onto the new reference line, then step off its distance."""
    return {k: origin + along * np.dot(src[k] - origin, along) + normal * dist[k]
            for k in src}


def _cross2(p1, p2, p3, p4):
    """Where segment p1p2 crosses p3p4 in a flat view, or None."""
    d1, d2 = p2 - p1, p4 - p3
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9:
        return None
    s = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
    u = ((p3[0] - p1[0]) * d1[1] - (p3[1] - p1[1]) * d1[0]) / den
    if not (0.0 < s < 1.0 and 0.0 < u < 1.0):
        return None
    return s, u, p1 + d1 * s


def solve(gaps=GAPS):
    P = SPACE
    A, B, C, D = (P[k] for k in ALL)
    ab, cd = B - A, D - C

    # ---- skew, and the one link square to both ----------------------------
    n = np.cross(ab, cd)
    assert np.linalg.norm(n) > 1e-6, "the lines are parallel, not skew"
    nn = n / np.linalg.norm(n)
    sd = abs(float(np.dot(C - A, nn)))
    assert sd > 1e-6, "the lines intersect, so they are not skew"

    # the feet of the common perpendicular, from the two "square to it"
    # conditions solved together
    M2 = np.array([[ab @ ab, -(ab @ cd)], [ab @ cd, -(cd @ cd)]])
    rhs = np.array([(C - A) @ ab, (C - A) @ cd])
    s_ab, t_cd = np.linalg.solve(M2, rhs)
    M, N = A + s_ab * ab, C + t_cd * cd
    assert abs(np.linalg.norm(N - M) - sd) < 1e-9, "the link is not the shortest distance"
    assert abs((N - M) @ ab) < 1e-9 and abs((N - M) @ cd) < 1e-9, \
        "the link is not square to both lines"
    assert 0.0 < s_ab < 1.0 and 0.0 < t_cd < 1.0, \
        "the common perpendicular falls outside the given segments"

    # every other link really is longer - checked, not asserted by hand-wave
    worst = min(np.linalg.norm((C + b * cd) - (A + a * ab))
                for a in np.linspace(0, 1, 61) for b in np.linspace(0, 1, 61))
    assert worst >= sd - 1e-9, "found a shorter link than the common perpendicular"

    fv = {k: np.array([v[0], v[2]]) for k, v in P.items()}      # (x, height)
    tv = {k: np.array([v[0], -v[1]]) for k, v in P.items()}     # (x, -depth)

    # the two apparent crossings - the heart of the opening scene
    xf = _cross2(fv["A"], fv["B"], fv["C"], fv["D"])
    xt = _cross2(tv["A"], tv["B"], tv["C"], tv["D"])
    assert xf is not None and xt is not None, "the lines must cross in both given views"
    assert abs(xf[2][0] - xt[2][0]) > 8.0, "the two crossings are too close to tell apart"
    # at the front view's crossing the two points are at different DEPTHS,
    # at the top view's crossing they are at different HEIGHTS: the proof
    gap_fv = abs((P["A"] + xf[0] * ab)[1] - (P["C"] + xf[1] * cd)[1])
    gap_tv = abs((P["A"] + xt[0] * ab)[2] - (P["C"] + xt[1] * cd)[2])
    assert gap_fv > 1.0 and gap_tv > 1.0, "the lines meet after all"

    # ---- aux 1: X1Y1 PARALLEL to the top view of AB -> AB true length ------
    u1 = tv["B"] - tv["A"]
    u1 = u1 / np.linalg.norm(u1)
    n1 = np.array([-u1[1], u1[0]])
    if n1[1] > 0:
        n1 = -n1                                     # keep it below the top view
    p0 = tv["A"] + n1 * gaps[0]
    aux1 = _project(tv, p0, u1, n1, {k: P[k][2] for k in P})      # carry HEIGHTS
    assert abs(np.linalg.norm(aux1["B"] - aux1["A"]) - np.linalg.norm(ab)) < 1e-9, \
        "aux 1 does not show AB at true length"

    # ---- aux 2: X2Y2 PERPENDICULAR to a1b1 -> AB becomes a point ----------
    # beyond B, not beyond A: either is geometrically fine - you are just
    # sighting along AB from one end or the other - but this way the chain of
    # views runs down the page instead of doubling back beside the given ones
    u2 = aux1["B"] - aux1["A"]
    u2 = u2 / np.linalg.norm(u2)
    w2 = np.array([-u2[1], u2[0]])
    q0 = aux1["B"] + u2 * gaps[1]
    steps = {k: -float(np.dot(tv[k] - p0, n1)) for k in P}
    assert min(steps.values()) > 2.0, "X1Y1 runs through the top view"
    aux2 = _project(aux1, q0, w2, u2, steps)
    assert np.linalg.norm(aux2["B"] - aux2["A"]) < 1e-9, "aux 2 is not a point view of AB"

    # ---- the answer, read in aux 2 ----------------------------------------
    pt = aux2["A"]                                   # the point view of the whole of AB
    e2 = aux2["D"] - aux2["C"]
    L2 = float(np.linalg.norm(e2))
    e2 = e2 / L2
    foot = aux2["C"] + e2 * float(np.dot(pt - aux2["C"], e2))
    read = float(np.linalg.norm(pt - foot))
    assert abs(read - sd) < 1e-9, "the point view does not give the true distance"

    # where that foot sits along CD, and so where the link is in every view
    t_read = float(np.dot(foot - aux2["C"], e2)) / L2
    assert abs(t_read - t_cd) < 1e-9, "the foot is not at the computed point of CD"

    # carried back: N first (it is on CD, which is a line in every view), then
    # M. In aux 1 the right angle at M projects TRUE - AB is parallel to that
    # plane of projection - so there the link is drawn square to a1b1.
    n_a1 = aux1["C"] + (aux1["D"] - aux1["C"]) * t_cd
    e1 = aux1["B"] - aux1["A"]
    L1 = float(np.linalg.norm(e1))
    e1 = e1 / L1
    m_a1 = aux1["A"] + e1 * float(np.dot(n_a1 - aux1["A"], e1))
    s_read = float(np.dot(m_a1 - aux1["A"], e1)) / L1
    assert abs(s_read - s_ab) < 1e-9, "the right angle did not project true in aux 1"

    link = {}
    for name, src in (("fv", fv), ("tv", tv), ("aux1", aux1), ("aux2", aux2)):
        src_m = src["A"] + (src["B"] - src["A"]) * s_ab
        src_n = src["C"] + (src["D"] - src["C"]) * t_cd
        link[name] = (src_m, src_n)
    assert np.allclose(link["aux1"][0], m_a1) and np.allclose(link["aux1"][1], n_a1)
    assert np.linalg.norm(link["aux2"][0] - pt) < 1e-9, "m2 is not the point view itself"
    assert np.allclose(link["aux2"][1], foot), "n2 is not the foot of the perpendicular"

    lens = {k: float(np.linalg.norm(v[1] - v[0])) for k, v in link.items()}
    for k in ("fv", "tv", "aux1"):
        assert lens[k] < sd - 0.5, f"{k} somehow shows the link longer than true"

    return dict(
        fv=fv, tv=tv, aux1=aux1, aux2=aux2, link=link, lens=lens,
        u1=u1, n1=n1, p0=p0, u2=u2, w2=w2, q0=q0, steps=steps,
        sd=sd, s=s_ab, t=t_cd, M=M, N=N,
        ab_true=float(np.linalg.norm(ab)), cd_true=float(np.linalg.norm(cd)),
        ab_fv=float(np.linalg.norm(fv["B"] - fv["A"])),
        ab_tv=float(np.linalg.norm(tv["B"] - tv["A"])),
        cd_fv=float(np.linalg.norm(fv["D"] - fv["C"])),
        cd_tv=float(np.linalg.norm(tv["D"] - tv["C"])),
        xf=xf, xt=xt, gap_fv=gap_fv, gap_tv=gap_tv,
        angle=math.degrees(math.acos(abs(ab @ cd)
                                     / (np.linalg.norm(ab) * np.linalg.norm(cd)))),
    )


G = solve()


# ==========================================================================
#  The sheet: millimetre space -> Manim points, and the drawing furniture
# ==========================================================================
def P2(v2):
    """millimetre space -> Manim point"""
    return np.array([v2[0] * MM, v2[1] * MM, 0.0])


def line_of(pts, k1, k2, colour, width=3.4):
    return Line(P2(pts[k1]), P2(pts[k2]), color=colour, stroke_width=width)


def both_lines(pts, width=3.4):
    return VGroup(line_of(pts, "A", "B", AB_COL, width),
                  line_of(pts, "C", "D", CD_COL, width))


def riser(a, b, colour=SLATE, width=1.0, opacity=0.45):
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


def right_angle(point, d1, d2, colour=INK, size=5.5, scale=MM):
    """The little square that says PERPENDICULAR."""
    p = np.array([point[0], point[1], 0.0]) * scale if len(point) == 2 else point
    e1 = np.array([d1[0], d1[1], 0.0]) * size * scale
    e2 = np.array([d2[0], d2[1], 0.0]) * size * scale
    mark = VMobject(stroke_color=colour, stroke_width=1.8)
    mark.set_points_as_corners([p + e1, p + e1 + e2, p + e2])
    return mark


def par_marks(point, direction, colour, size=5.0, gap=5.0):
    """The pair of slashes that says PARALLEL."""
    d = np.array([direction[0], direction[1], 0.0])
    d = d / np.linalg.norm(d)
    n = np.array([-d[1], d[0], 0.0])
    g = VGroup()
    for s in (-0.5, 0.5):
        c = P2(point) + d * s * gap * MM
        arm = (n * 0.9 + d * 0.45) * size * MM
        g.add(Line(c - arm, c + arm, color=colour, stroke_width=2.4))
    return g


def ref_line(origin, direction, pts, extra=14, width=2.3):
    sp = [float(np.dot(pts[k] - origin, direction)) for k in pts]
    return Line(P2(origin + direction * (min(sp) - extra)),
                P2(origin + direction * (max(sp) + extra)),
                color=INK, stroke_width=width)


def ref_label(text, line, buff=0.26):
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
#  The 3-D stage: the same two lines, stood up in space
# ==========================================================================
def pt3(v3):
    """(x, depth, height) in millimetres -> the 3-D stage."""
    return np.array([(v3[0] - X_MID) * S3, -v3[1] * S3, v3[2] * S3])


def on_ab(s):
    return SPACE["A"] + (SPACE["B"] - SPACE["A"]) * s


def on_cd(t):
    return SPACE["C"] + (SPACE["D"] - SPACE["C"]) * t


def space_lines(width=6.0):
    pts = {k: pt3(SPACE[k]) for k in ALL}
    ab = Line(pts["A"], pts["B"], color=AB_COL, stroke_width=width)
    cd = Line(pts["C"], pts["D"], color=CD_COL, stroke_width=width)
    return pts, ab, cd


# ==========================================================================
#  S01 - two lines that look as though they meet, twice, and never do
# ==========================================================================
class S01_TheyDoNotMeet(ProjectionScene):
    quadrant = 1
    heading = "The Shortest Distance Between Skew Lines"
    subheading = "Sheet 4 · §4.10 · the link that is square to both"

    def construct(self):
        self.build_stage()
        self.set_camera_orientation(zoom=1.15)
        self.add(self.vp, self.hp, self.xy, *self.tags, self.bar)

        pts, ab, cd = space_lines()
        nudge = {"A": np.array([-0.02, -0.10, -0.26]),
                 "B": np.array([0.20, -0.10, 0.22]),
                 "C": np.array([-0.18, -0.10, 0.22]),
                 "D": np.array([0.24, -0.10, -0.24])}
        labs = VGroup(*[mono(k, color=AB_COL if k in "AB" else CD_COL, size=22)
                        .move_to(pts[k] + nudge[k]) for k in ALL])
        billboard(self, *labs)

        self.begin_ambient_camera_rotation(rate=0.012)
        narrate(
            self,
            "Two straight lines standing in space: A B, and C D. They are not "
            "parallel. But look carefully - they never actually touch. One passes "
            "clean over the top of the other.",
            Create(ab), Create(cd), FadeIn(labs),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Lines like that have a name. Non-parallel, and non-intersecting: skew "
            "lines. And the question we are asked about them is always the same one. "
            "How close do they come?",
        )
        self.stop_ambient_camera_rotation()

        # ---- the front view: they appear to cross ----------------------------
        # Each apparent crossing is then resolved from the view that CAN show the
        # coordinate the first one hid: depth from the side, height from the front.
        f_ab, f_cd = on_ab(G["xf"][0]), on_cd(G["xf"][1])
        f_dot_ab = marker(pt3(f_ab), AB_COL, 0.075)
        f_dot_cd = marker(pt3(f_cd), CD_COL, 0.075)
        fly_camera(
            self,
            "Here is the trouble. Go and stand where the front view is taken from - "
            "square in front of the vertical plane.",
            phi=90 * DEGREES, theta=-90 * DEGREES, zoom=1.2,
        )
        narrate(
            self,
            "From here they cross. Right there. If that were all you had, you would "
            "say the two lines meet at that point.",
            FadeIn(f_dot_ab), FadeIn(f_dot_cd),
            lag_ratio=0.3,
        )
        f_link = DashedLine(pt3(f_ab), pt3(f_cd), color=SLATE, stroke_width=3,
                            dash_length=0.08)
        f_gap = billboard(self, mono(f"{G['gap_fv']:.0f} mm apart", color=SLATE, size=20)
                          .move_to((pt3(f_ab) + pt3(f_cd)) / 2
                                   + np.array([0.0, 0.0, 0.40])))
        fly_camera(
            self,
            "They do not. Walk round to the side - the one direction a front view "
            "cannot show you - and that single point comes apart into two, "
            f"{G['gap_fv']:.0f} millimetres apart. The point on A B is that much "
            "further back than the point on C D. They only lined up because we were "
            "standing in exactly the wrong place.",
            FadeIn(f_link), FadeIn(f_gap),
            phi=90 * DEGREES, theta=0.0, zoom=1.2,
        )

        # ---- the top view: they appear to cross somewhere else ---------------
        t_ab, t_cd = on_ab(G["xt"][0]), on_cd(G["xt"][1])
        t_dot_ab = marker(pt3(t_ab), AB_COL, 0.075)
        t_dot_cd = marker(pt3(t_cd), CD_COL, 0.075)
        fly_camera(
            self,
            "Now go and stand where the top view is taken from, straight above.",
            FadeOut(f_link), FadeOut(f_gap), FadeOut(f_dot_ab), FadeOut(f_dot_cd),
            phi=0.0, theta=-90 * DEGREES, zoom=1.2,
        )
        narrate(
            self,
            "And they cross again - but not at the same place. This crossing is at "
            "the other end of the drawing entirely.",
            FadeIn(t_dot_ab), FadeIn(t_dot_cd),
            lag_ratio=0.3,
        )
        t_link = DashedLine(pt3(t_ab), pt3(t_cd), color=SLATE, stroke_width=3,
                            dash_length=0.08)
        t_gap = billboard(self, mono(f"{G['gap_tv']:.0f} mm apart", color=SLATE, size=20)
                          .move_to((pt3(t_ab) + pt3(t_cd)) / 2
                                   + np.array([0.62, 0.0, 0.0])))
        fly_camera(
            self,
            "And drop back to the front, which is the view that cannot hide a height. "
            f"Two points again, {G['gap_tv']:.0f} millimetres apart, one well above "
            "the other. That is your test for skew lines on a drawing: the crossing "
            "in the front view and the crossing in the top view do not sit on the "
            "same projector, so there is no single point where the lines meet.",
            FadeIn(t_link), FadeIn(t_gap),
            phi=90 * DEGREES, theta=-90 * DEGREES, zoom=1.2,
        )

        # ---- the one link that is square to both ------------------------------
        mn = Line(pt3(G["M"]), pt3(G["N"]), color=SD_COL, stroke_width=7)
        mn_labs = VGroup(mono("M", color=SD_COL, size=20)
                         .move_to(pt3(G["M"]) + np.array([0.0, -0.10, -0.22])),
                         mono("N", color=SD_COL, size=20)
                         .move_to(pt3(G["N"]) + np.array([0.0, -0.10, 0.22])))
        billboard(self, *mn_labs)

        # a handful of other links, to show the perpendicular really is the least
        others = VGroup()
        other_len = []
        for a, b in ((0.30, 0.45), (0.75, 0.80), (0.45, 0.90)):
            p, q = on_ab(a), on_cd(b)
            others.add(Line(pt3(p), pt3(q), color=MUTED, stroke_width=2.6))
            other_len.append(float(np.linalg.norm(q - p)))
        assert min(other_len) > G["sd"], "a sample link came out shorter than MN"

        fly_camera(
            self,
            "So they miss. The question is by how much - and you can join the two "
            "lines up in any number of ways, each one a different length.",
            FadeOut(t_link), FadeOut(t_gap), FadeOut(t_dot_ab), FadeOut(t_dot_cd),
            Create(others),
            phi=CAM_PHI, theta=CAM_THETA, zoom=1.15,
        )
        narrate(
            self,
            f"Those three measure {other_len[0]:.0f}, {other_len[1]:.0f} and "
            f"{other_len[2]:.0f} millimetres. But exactly one link is the shortest "
            "of all of them, and it is the one that is square to A B and square to "
            "C D at the same time. The common perpendicular.",
            FadeOut(others), Create(mn), FadeIn(mn_labs),
            lag_ratio=0.3,
        )

        # ---- stand at the end of AB: the point view --------------------------
        axis = pt3(SPACE["B"]) - pt3(SPACE["A"])
        axis = axis / np.linalg.norm(axis)
        mid = (pt3(G["M"]) + pt3(G["N"])) / 2.0
        flat = {k: pt3(SPACE[k]) - axis * float(np.dot(pt3(SPACE[k]) - mid, axis))
                for k in ALL}
        assert np.linalg.norm(flat["A"] - flat["B"]) < 1e-9, "AB did not close up"
        flat_m = pt3(G["M"]) - axis * float(np.dot(pt3(G["M"]) - mid, axis))
        flat_n = pt3(G["N"]) - axis * float(np.dot(pt3(G["N"]) - mid, axis))
        assert abs(np.linalg.norm(flat_n - flat_m) - np.linalg.norm(pt3(G["N"]) - pt3(G["M"]))) < 1e-9, \
            "the link is not square to AB, so it would not show true here"

        pv_dot = marker(flat["A"], AB_COL, 0.10)
        pv_cd = Line(flat["C"], flat["D"], color=CD_COL, stroke_width=6)
        pv_mn = Line(flat_m, flat_n, color=SD_COL, stroke_width=7)

        cam = -axis if axis[1] > 0 else axis
        fly_camera(
            self,
            "And there is a place you can stand where that link shows its true "
            "length: at the end of A B, looking straight down it.",
            FadeOut(self.vp), FadeOut(self.hp), FadeOut(self.xy), FadeOut(self.tags),
            FadeOut(self.bar), FadeOut(self.badge), FadeOut(labs),
            phi=math.acos(cam[2]), theta=math.atan2(cam[1], cam[0]),
            zoom=1.45, focal_distance=60.0, frame_center=mid,
        )
        narrate(
            self,
            "A B has shrunk to a point. C D is still a line. And the link between "
            "them is square to A B - so from here, where A B is end on, that link is "
            f"lying flat across your view at its full {G['sd']:.1f} millimetres.",
            FadeOut(ab), FadeOut(cd), FadeOut(mn), FadeOut(mn_labs),
            FadeIn(pv_dot), Create(pv_cd), Create(pv_mn),
            lag_ratio=0.25,
        )
        sd_lab = billboard(self, mono(f"{G['sd']:.1f} mm", color=SD_COL, size=26)
                           .move_to((flat_m + flat_n) / 2 + np.array([0.0, 0.0, -0.45])))
        # A billboard, not a hud(): this shot is the one that re-centres the
        # camera, and a frame_center away from the origin drags Manim's
        # fixed-in-frame mobjects across the screen with it. So the note is
        # parked in space instead - in the collapse plane, under the figure.
        up = np.array([0.0, 0.0, 1.0])
        up = up - axis * float(np.dot(up, axis))
        up = up / np.linalg.norm(up)
        note = billboard(self, VGroup(
            chip("get ONE line to a POINT VIEW", color=AB_COL, size=21),
            chip("the shortest distance is then the PERPENDICULAR to the other",
                 color=SD_COL, size=21),
        ).arrange(DOWN, buff=0.2).move_to(mid - up * 1.45))
        narrate(
            self,
            "That is the whole episode in one picture. Get a view in which one of "
            "the lines is a point. The shortest distance to the other line is then "
            "simply the perpendicular dropped from that point - and it is true "
            "length, because it is square to the line you are looking down.",
            FadeIn(sd_lab), FadeIn(note),
            lag_ratio=0.3,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - why the point view answers it, and the two auxiliaries that get there
# ==========================================================================
def answer_view(scale=0.062):
    """The finished second auxiliary, small, built from the real numbers.

    Not a sketch of the idea - it IS the view the construction arrives at, so
    what the strategy scene promises is what the construction scene draws."""
    a2 = G["aux2"]
    dot_at = a2["A"]
    e = a2["D"] - a2["C"]
    e = e / np.linalg.norm(e)
    foot = G["link"]["aux2"][1]
    cluster = np.array([a2[k] for k in ALL] + [foot])
    mid = cluster.mean(axis=0)

    def D2(v2):
        return np.array([(v2[0] - mid[0]) * scale, (v2[1] - mid[1]) * scale, 0.0])

    cd = Line(D2(a2["C"]), D2(a2["D"]), color=CD_COL, stroke_width=5)
    dot = VGroup(Dot(D2(dot_at), radius=0.075, color=AB_COL),
                 Circle(radius=0.16, color=AB_COL, stroke_width=2.6).move_to(D2(dot_at)))
    perp = Line(D2(dot_at), D2(foot), color=SD_COL, stroke_width=5)
    e3 = np.array([e[0], e[1], 0.0])
    to_dot = D2(dot_at) - D2(foot)
    to_dot = to_dot / np.linalg.norm(to_dot)
    ra = right_angle(D2(foot), e3, to_dot, colour=SD_COL, size=0.16, scale=1.0)

    spread = VGroup()
    for t in (0.12, 0.34, 0.86):
        q = a2["C"] + (a2["D"] - a2["C"]) * t
        spread.add(DashedLine(D2(dot_at), D2(q), color=MUTED, stroke_width=1.8,
                              stroke_opacity=0.7, dash_length=0.07))
    return dict(cd=cd, dot=dot, perp=perp, ra=ra, spread=spread,
                dot_at=D2(dot_at), foot=D2(foot),
                body=VGroup(cd, dot, spread, perp, ra))


class S02_Strategy(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("One Point View", "and the two auxiliaries that reach it")
        self.add(bar)

        av = answer_view()
        av["body"].move_to(np.array([3.05, 0.25, 0.0]))
        ab_tag = VGroup(mono("a2 b2", color=AB_COL, size=15),
                        mono("AB, end on", color=SLATE, size=12)
                        ).arrange(DOWN, buff=0.06).next_to(av["dot"], UP, buff=0.24)
        cd_tag = mono("c2 d2", color=CD_COL, size=14).next_to(av["cd"], DOWN, buff=0.14)
        sd_tag = mono(f"{G['sd']:.1f}  TRUE", color=SD_COL, size=16).next_to(
            av["perp"], LEFT, buff=0.18)

        narrate(
            self,
            "Why is the point view the view that answers it? Because of what you can "
            "see from there all at once.",
            FadeIn(bar),
        )
        narrate(
            self,
            "Looking straight down A B, the whole line is one dot. So the distance on "
            "the paper from that dot to any point of C D is the true perpendicular "
            "distance from the line A B to that point - measured square to A B, which "
            "is the only direction left in this view.",
            FadeIn(av["dot"]), FadeIn(ab_tag), Create(av["cd"]), FadeIn(cd_tag),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Every point along C D gives you one of those distances. You are looking "
            "at all of them at the same time.",
            Create(av["spread"]),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "And the least of them is the perpendicular from the dot onto c two d "
            "two. That perpendicular is square to C D because you drew it square, and "
            "square to A B because everything in this view is. It is the common "
            "perpendicular, and it is true length.",
            Create(av["perp"]), Create(av["ra"]), FadeIn(sd_tag),
            lag_ratio=0.3,
        )

        steps = [
            ("1", "X1Y1 PARALLEL to a view of AB",
             "carry the heights  →  AB at TRUE LENGTH", AB_COL),
            ("2", "X2Y2 PERPENDICULAR to that TL",
             "carry the distances  →  AB becomes a POINT", CD_COL),
            ("3", "perpendicular onto c2d2",
             "that length is the answer, true size", SD_COL),
        ]
        rows = VGroup()
        for num, headline, sub, colour in steps:
            n = mono(num, color=colour, size=26)
            text = VGroup(caption(headline, color=colour, size=19),
                          mono(sub, color=SLATE, size=14)
                          ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            rows.add(VGroup(n, text).arrange(RIGHT, buff=0.3, aligned_edge=UP))
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT).move_to(np.array([-3.5, 0.75, 0]))

        narrate(
            self,
            "Getting there takes the two auxiliary views you already know. First X "
            "one Y one parallel to one view of A B, carrying the heights across: A B "
            "comes out at true length.",
            FadeIn(rows[0]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Then X two Y two square to that true length, carrying the distances from "
            "two views back: A B collapses to a point. Exactly the pair of auxiliaries "
            "we drew for the angle between two planes - the same two moves, pointed at "
            "a different question.",
            FadeIn(rows[1]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "And then you drop one perpendicular, and measure it.",
            FadeIn(rows[2]),
            lag_ratio=0.3,
        )

        rule = VGroup(
            chip("either line will do - take whichever reaches a point view more neatly",
                 color=AB_COL, size=18),
            chip("the answer is a LENGTH: it must be measured where it is TRUE",
                 color=SD_COL, size=18),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.45)
        narrate(
            self,
            "Two things worth knowing. It does not matter which of the two lines you "
            "take to the point view - the shortest distance between them is the same "
            "either way. And whatever you do, do not measure the answer in the given "
            "views. We will see in a moment just how wrong that goes.",
            FadeIn(rule[0]), FadeIn(rule[1]),
            lag_ratio=0.35,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  The sheet, built once and used by both drawing scenes
# ==========================================================================
def sheet_pieces():
    """Every mobject of the finished sheet, in named pieces.

    S03 draws pieces 1 to 4 and stops at the answer; S04 opens with those
    already on the paper and carries the link back into the given views. Both
    scenes build from this one function so the two halves of the sheet cannot
    drift apart."""
    fv, tv, a1, a2 = G["fv"], G["tv"], G["aux1"], G["aux2"]
    u1, n1, p0 = G["u1"], G["n1"], G["p0"]
    u2, w2, q0 = G["u2"], G["w2"], G["q0"]
    n1d = np.array([n1[0], n1[1], 0.0])
    u2d = np.array([u2[0], u2[1], 0.0])
    col = {k: (AB_COL if k in "AB" else CD_COL) for k in ALL}

    # ---------------- the given views -------------------------------------
    xy = Line(P2(np.array([-16.0, 0.0])), P2(np.array([112.0, 0.0])),
              color=INK, stroke_width=2.6)
    xy_lab = VGroup(mono("X", color=INK, size=15).next_to(xy, LEFT, buff=0.1),
                    mono("Y", color=INK, size=15).next_to(xy, RIGHT, buff=0.1))
    fv_l, tv_l = both_lines(fv), both_lines(tv)
    dots = VGroup(*[Dot(P2(fv[k]), radius=0.036, color=col[k]) for k in ALL],
                  *[Dot(P2(tv[k]), radius=0.036, color=col[k]) for k in ALL])
    # outward() sends both of A's labels towards XY, where they land on each
    # other and on the line, so the given views get their directions by hand
    fv_dir = {"A": UL, "B": UR, "C": UL, "D": DR}
    tv_dir = {"A": DL, "B": DR, "C": DL, "D": UR}
    labs = VGroup()
    for k in ALL:
        labs.add(mono(f"{k.lower()}′", color=col[k], size=15)
                 .next_to(P2(fv[k]), fv_dir[k], buff=0.07))
        labs.add(mono(k.lower(), color=col[k], size=15)
                 .next_to(P2(tv[k]), tv_dir[k], buff=0.07))
    tag_fv = chip("FRONT VIEW", color=SLATE, size=12).move_to(P2(np.array([116.0, 62.0])))
    tag_tv = chip("TOP VIEW", color=SLATE, size=12).move_to(P2(np.array([116.0, -34.0])))

    # the two apparent crossings, and the proof they are not one point
    x_fv = fv["A"] + (fv["B"] - fv["A"]) * G["xf"][0]
    x_tv = tv["A"] + (tv["B"] - tv["A"]) * G["xt"][0]
    cross_fv = VGroup(Circle(radius=0.10, color=SLATE, stroke_width=2.4).move_to(P2(x_fv)))
    cross_tv = VGroup(Circle(radius=0.10, color=SLATE, stroke_width=2.4).move_to(P2(x_tv)))
    miss = DashedLine(P2(x_fv), P2(np.array([x_fv[0], tv["A"][1] - 66.0])),
                      color=SLATE, stroke_width=1.4, stroke_opacity=0.6,
                      dash_length=0.06)
    miss2 = DashedLine(P2(np.array([x_tv[0], fv["C"][1] + 8.0])),
                       P2(x_tv), color=SLATE, stroke_width=1.4,
                       stroke_opacity=0.6, dash_length=0.06)
    given = VGroup(xy, xy_lab, fv_l, tv_l, dots, labs, tag_fv, tag_tv)

    # ---------------- aux 1: X1Y1 ∥ ab, heights carried --------------------
    x1 = ref_line(p0, u1, {**tv, **a1})
    x1l = ref_label("X1Y1", x1)
    mid_ab_tv = (tv["A"] + tv["B"]) / 2.0
    par = VGroup(par_marks(mid_ab_tv, u1, AB_COL),
                 par_marks(p0 + u1 * float(np.dot(mid_ab_tv - p0, u1)), u1, AB_COL))
    foot1 = {k: p0 + u1 * float(np.dot(tv[k] - p0, u1)) for k in ALL}
    rays1 = VGroup(*[riser(tv[k], a1[k]) for k in ALL])
    heights = VGroup(*[dim(np.array([fv[k][0], 0.0]), fv[k], f"{SPACE[k][2]:.0f}",
                           col[k], size=13, offset=off, gap=6.0)
                       for k, off in zip(ALL, (6.0, -6.0, -6.0, 6.0))])
    carried = VGroup(*[dim(foot1[k], a1[k], f"{SPACE[k][2]:.0f}", col[k],
                           size=13, offset=off, gap=6.0)
                       for k, off in zip(ALL, (5.0, -5.0, 5.0, -5.0))])
    a1_l = both_lines(a1, 3.2)
    a1_labs = VGroup(*[mono(f"{k.lower()}1", color=col[k], size=13)
                       .move_to(P2(a1[k]) + n1d * 0.20) for k in ALL])
    a1_dim = dim(a1["A"], a1["B"], f"{G['ab_true']:.1f}  TRUE LENGTH", AB_COL,
                 size=13, offset=8.0, gap=6.5)
    aux1_g = VGroup(x1, x1l, par, rays1, a1_l, a1_labs)

    # ---------------- aux 2: X2Y2 ⊥ a1b1, distances carried ----------------
    x2 = ref_line(q0, w2, {**a1, **a2})
    x2l = ref_label("X2Y2", x2)
    # at the crossing, one leg back along a1b1 and one along X2Y2 itself -
    # both legs must lie on the two lines that meet, or the little square
    # collapses into a straight stroke and says nothing
    ra2 = right_angle(q0, -u2, w2, colour=INK)
    foot2 = {k: q0 + w2 * float(np.dot(a1[k] - q0, w2)) for k in ALL}
    rays2 = VGroup(*[riser(a1[k], a2[k]) for k in ALL])
    steps_src = VGroup(*[dim(foot1[k], tv[k], f"{G['steps'][k]:.0f}", col[k],
                             size=13, offset=off, gap=6.0)
                         for k, off in zip(ALL, (-5.0, 5.0, -5.0, 5.0))])
    steps_dst = VGroup(*[dim(foot2[k], a2[k], f"{G['steps'][k]:.0f}", col[k],
                             size=13, offset=off, gap=6.0)
                         for k, off in zip(ALL, (5.0, -5.0, 5.0, -5.0))])
    pv = P2(a2["A"])
    pv_ring = Circle(radius=0.115, color=AB_COL, stroke_width=3).move_to(pv)
    pv_lab = mono("a2 b2", color=AB_COL, size=14).next_to(pv_ring, UL, buff=0.05)
    a2_cd = line_of(a2, "C", "D", CD_COL, 3.6)
    a2_labs = VGroup(mono("c2", color=CD_COL, size=14)
                     .next_to(P2(a2["C"]), outward(a2["C"], a2), buff=0.07),
                     mono("d2", color=CD_COL, size=14)
                     .next_to(P2(a2["D"]), outward(a2["D"], a2), buff=0.07))
    aux2_g = VGroup(x2, x2l, ra2, rays2, pv_ring, pv_lab, a2_cd, a2_labs)

    # ---------------- the answer -------------------------------------------
    m2, n2 = G["link"]["aux2"]
    perp = Line(P2(m2), P2(n2), color=SD_COL, stroke_width=5)
    cd_dir = (a2["D"] - a2["C"]) / np.linalg.norm(a2["D"] - a2["C"])
    to_m = (m2 - n2) / np.linalg.norm(m2 - n2)
    ra_perp = right_angle(n2, cd_dir, to_m, colour=SD_COL)
    sd_dim = dim(m2, n2, f"{G['sd']:.1f}  TRUE", SD_COL, size=15, offset=-7.0, gap=6.0)
    n2_lab = mono("n2", color=SD_COL, size=14).next_to(P2(n2), DR, buff=0.06)
    m2_lab = mono("m2", color=SD_COL, size=14).next_to(P2(m2), DL, buff=0.06)
    answer = VGroup(perp, ra_perp, n2_lab, m2_lab)

    # ---------------- carrying the link back -------------------------------
    m1, n1p = G["link"]["aux1"]
    back1 = riser(n2, n1p, SD_COL, width=1.3, opacity=0.75)
    n1_dot = Dot(P2(n1p), radius=0.042, color=SD_COL)
    ab_dir1 = (a1["B"] - a1["A"]) / np.linalg.norm(a1["B"] - a1["A"])
    link1 = Line(P2(m1), P2(n1p), color=SD_COL, stroke_width=4)
    ra_a1 = right_angle(m1, ab_dir1, (n1p - m1) / np.linalg.norm(n1p - m1), colour=SD_COL)
    m1_dot = Dot(P2(m1), radius=0.042, color=SD_COL)
    l1_labs = VGroup(mono("m1", color=SD_COL, size=13).next_to(P2(m1), DL, buff=0.06),
                     mono("n1", color=SD_COL, size=13).next_to(P2(n1p), UR, buff=0.06))
    l1_dim = dim(m1, n1p, f"{G['lens']['aux1']:.1f}", SD_COL, size=12,
                 offset=-6.0, gap=5.5)

    m_tv, n_tv = G["link"]["tv"]
    back_tv = VGroup(riser(n1p, n_tv, SD_COL, width=1.3, opacity=0.75),
                     riser(m1, m_tv, SD_COL, width=1.3, opacity=0.75))
    link_tv = Line(P2(m_tv), P2(n_tv), color=SD_COL, stroke_width=4)
    tv_dots = VGroup(Dot(P2(m_tv), radius=0.042, color=SD_COL),
                     Dot(P2(n_tv), radius=0.042, color=SD_COL))
    tv_labs = VGroup(mono("m", color=SD_COL, size=13).next_to(P2(m_tv), DL, buff=0.06),
                     mono("n", color=SD_COL, size=13).next_to(P2(n_tv), UR, buff=0.06))
    tv_dim = dim(m_tv, n_tv, f"{G['lens']['tv']:.1f}", SD_COL, size=12,
                 offset=6.0, gap=5.5)

    m_fv, n_fv = G["link"]["fv"]
    back_fv = VGroup(riser(m_tv, m_fv, SD_COL, width=1.3, opacity=0.75),
                     riser(n_tv, n_fv, SD_COL, width=1.3, opacity=0.75))
    link_fv = Line(P2(m_fv), P2(n_fv), color=SD_COL, stroke_width=4)
    fv_dots = VGroup(Dot(P2(m_fv), radius=0.042, color=SD_COL),
                     Dot(P2(n_fv), radius=0.042, color=SD_COL))
    fv_labs = VGroup(mono("m′", color=SD_COL, size=13).next_to(P2(m_fv), DR, buff=0.06),
                     mono("n′", color=SD_COL, size=13).next_to(P2(n_fv), UL, buff=0.06))
    fv_dim = dim(m_fv, n_fv, f"{G['lens']['fv']:.1f}", SD_COL, size=12,
                 offset=-6.0, gap=5.5)

    return dict(
        given=given, xy=xy, xy_lab=xy_lab, fv_l=fv_l, tv_l=tv_l, dots=dots, labs=labs,
        tag_fv=tag_fv, tag_tv=tag_tv, cross_fv=cross_fv, cross_tv=cross_tv,
        miss=miss, miss2=miss2,
        x1=x1, x1l=x1l, par=par, rays1=rays1, heights=heights, carried=carried,
        a1_l=a1_l, a1_labs=a1_labs, a1_dim=a1_dim, aux1_g=aux1_g,
        x2=x2, x2l=x2l, ra2=ra2, rays2=rays2, steps_src=steps_src, steps_dst=steps_dst,
        pv_ring=pv_ring, pv_lab=pv_lab, a2_cd=a2_cd, a2_labs=a2_labs, aux2_g=aux2_g,
        perp=perp, ra_perp=ra_perp, sd_dim=sd_dim, answer=answer,
        n2_lab=n2_lab, m2_lab=m2_lab,
        back1=back1, n1_dot=n1_dot, link1=link1, ra_a1=ra_a1, m1_dot=m1_dot,
        l1_labs=l1_labs, l1_dim=l1_dim,
        back_tv=back_tv, link_tv=link_tv, tv_dots=tv_dots, tv_labs=tv_labs, tv_dim=tv_dim,
        back_fv=back_fv, link_fv=link_fv, fv_dots=fv_dots, fv_labs=fv_labs, fv_dim=fv_dim,
        pv_point=pv,
    )


def data_card():
    rows = VGroup(
        mono("GIVEN (mm)", color=SLATE, size=15),
        mono("        above HP   in front of VP", color=SLATE, size=13),
        *[mono(f"  {k}      {SPACE[k][2]:5.0f} {SPACE[k][1]:13.0f}",
               color=AB_COL if k in "AB" else CD_COL, size=15) for k in ALL],
        mono("  projectors  " + " · ".join(f"{SPACE[k][0]:.0f}" for k in ALL),
             color=SLATE, size=13),
    ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    card = card_back(rows, pad=0.22, opacity=0.88)
    card.add(SurroundingRectangle(rows, color=SLATE, buff=0.22,
                                  corner_radius=0.1, stroke_width=1.2))
    return card


# ==========================================================================
#  S03 - the sheet: AB to true length, AB to a point, and the answer
# ==========================================================================
class S03_Construction(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        S = sheet_pieces()
        sheet = VGroup(*[S[k] for k in
                         ("given", "aux1_g", "heights", "carried", "a1_dim",
                          "steps_src", "steps_dst", "aux2_g", "answer", "sd_dim")])

        centre, W = frame_target([S["given"]])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Shortest distance · AB and CD",
            "§4.10 · two skew lines, one common perpendicular")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "plot both views", "they cross twice, in two different places", SLATE),
            step_badge("2", "X1Y1 ∥ ab", "carry the HEIGHTS · ab comes out true length", AB_COL),
            step_badge("3", "X2Y2 ⊥ a₁b₁", "carry the DISTANCES · AB shrinks to a point", CD_COL),
            step_badge("4", "drop the perpendicular", "onto c₂d₂ · that length is the answer", SD_COL),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)

        data = data_card()
        pin_to_frame(self, data, corner=DOWN + RIGHT, buff=0.45)

        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail, data)

        narrate(
            self,
            "Two skew lines, A B and C D, given by their two views. Find the shortest "
            "distance between them.",
            FadeIn(bar), FadeIn(data),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "A is five above the H P and ten in front of the V P. B is forty-five and "
            "sixty. C is sixty-five and twenty. D is thirty-five and ten.",
            rail_focus(rail, rungs, 0),
            Create(S["xy"]), FadeIn(S["xy_lab"]), FadeIn(S["dots"]),
            FadeIn(S["tag_fv"]), FadeIn(S["tag_tv"]),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Join them: A B in gold, C D in violet, in both views.",
            Create(S["fv_l"]), Create(S["tv_l"]), FadeIn(S["labs"]),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "And notice what the drawing already tells you. The two lines cross in the "
            "front view, and they cross in the top view - but the two crossings are "
            "nowhere near the same projector. They are not one point seen twice. The "
            "lines miss each other: they are skew.",
            FadeIn(S["cross_fv"]), FadeIn(S["cross_tv"]),
            Create(S["miss"]), Create(S["miss2"]),
            lag_ratio=0.25,
        )

        narrate(
            self,
            "Step two. Take A B to true length. X one Y one parallel to the top view "
            "a b, because a line parallel to the new plane of projection is a line "
            "that comes out at its full length.",
            rail_focus(rail, rungs, 1),
            look_at(self, [S["tv_l"], S["x1"], S["tag_tv"]], right=0.34),
            FadeOut(S["cross_fv"]), FadeOut(S["cross_tv"]),
            FadeOut(S["miss"]), FadeOut(S["miss2"]),
            Create(S["x1"]), FadeIn(S["x1l"]), FadeIn(S["par"]),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "The heights come from the front view: five, forty-five, sixty-five, "
            "thirty-five.",
            look_at(self, [S["fv_l"], S["heights"]], right=0.34),
            Create(S["heights"]),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project the four points square across X one Y one and step each height "
            "off on the far side.",
            look_at(self, [S["tv_l"], S["aux1_g"]]),
            Create(S["rays1"]),
            *[TransformFromCopy(S["heights"][i], S["carried"][i]) for i in range(4)],
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Join them up. a one b one measures {G['ab_true']:.1f} millimetres - the "
            f"true length of A B. The front view had it at {G['ab_fv']:.1f} and the "
            f"top view at {G['ab_tv']:.1f}; both were short, as usual. C D comes along "
            "for the ride: we are not finished with it.",
            look_at(self, [S["aux1_g"], S["a1_dim"]]),
            Create(S["a1_l"]), FadeIn(S["a1_labs"]), Create(S["a1_dim"]),
            lag_ratio=0.25,
        )

        narrate(
            self,
            "Step three. X two Y two perpendicular to that true length - now we want "
            "to look straight down A B rather than across it.",
            rail_focus(rail, rungs, 2),
            look_at(self, [S["aux1_g"], S["x2"]]),
            FadeOut(S["heights"]), FadeOut(S["carried"]), FadeOut(S["a1_dim"]),
            Create(S["x2"]), FadeIn(S["x2l"]), Create(S["ra2"]),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "The distances this time come from two views back - the top view - each "
            "measured from X one Y one. a and b are the same distance from it, "
            f"{G['steps']['A']:.0f} each, and they must be: X one Y one was drawn "
            "parallel to a b.",
            look_at(self, [S["tv_l"], S["x1"], S["steps_src"]], right=0.34),
            Create(S["steps_src"]),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project across X two Y two and step them off.",
            look_at(self, [S["a1_l"], S["aux2_g"]]),
            Create(S["rays2"]),
            *[TransformFromCopy(S["steps_src"][i], S["steps_dst"][i]) for i in range(4)],
            lag_ratio=0.2,
        )
        narrate(
            self,
            "a two and b two land on top of one another: A B is now a point, and we "
            "are looking straight down it. C D is still a line.",
            look_at(self, [S["aux2_g"]]),
            Create(S["pv_ring"]), FadeIn(S["pv_lab"]), Create(S["a2_cd"]),
            FadeIn(S["a2_labs"]),
            lag_ratio=0.3,
        )

        ans_rows = VGroup(
            mono(f"shortest distance  {G['sd']:.1f} mm", color=SD_COL, size=20),
            mono(f"  AB true length   {G['ab_true']:.1f}", color=AB_COL, size=14),
            mono(f"  measured square to a2b2", color=SLATE, size=14),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=SD_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Step four is one line. From the point, drop a perpendicular onto c two d "
            "two.",
            rail_focus(rail, rungs, 3),
            FadeOut(S["steps_src"]), FadeOut(S["steps_dst"]),
            Create(S["perp"]), Create(S["ra_perp"]),
            FadeIn(S["m2_lab"]), FadeIn(S["n2_lab"]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"Measure it: {G['sd']:.1f} millimetres. That is the shortest distance "
            "between the two lines, at true size, because it is square to A B and we "
            "are looking straight down A B.",
            Create(S["sd_dim"]), FadeOut(data), FadeIn(ans),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Its feet have names worth keeping: m two, which is the point view itself, "
            "so M is somewhere on A B; and n two on c two d two, so N is somewhere on "
            "C D. In the next scene we go and find out exactly where.",
            look_at(self, [sheet], right=0.24, top=0.12),
            lag_ratio=0.2,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - where that link actually is, and what it measures in the other views
# ==========================================================================
class S04_BackToTheViews(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        S = sheet_pieces()
        done = VGroup(S["given"], S["aux1_g"], S["aux2_g"], S["answer"], S["sd_dim"])
        sheet = VGroup(done, S["back1"], S["n1_dot"], S["link1"], S["ra_a1"],
                       S["m1_dot"], S["l1_labs"], S["l1_dim"],
                       S["back_tv"], S["link_tv"], S["tv_dots"], S["tv_labs"], S["tv_dim"],
                       S["back_fv"], S["link_fv"], S["fv_dots"], S["fv_labs"], S["fv_dim"])

        # the projectors really do run square to the reference lines they cross
        n2, n1p = G["link"]["aux2"][1], G["link"]["aux1"][1]
        assert abs(np.cross(n2 - n1p, G["u2"])) < 1e-9, "the aux2 projector is skewed"
        m1, m_tv = G["link"]["aux1"][0], G["link"]["tv"][0]
        assert abs(np.cross(m1 - m_tv, G["n1"])) < 1e-9, "the aux1 projector is skewed"
        assert abs(G["link"]["tv"][0][0] - G["link"]["fv"][0][0]) < 1e-9, \
            "m and m′ are not on one vertical projector"

        centre, W = frame_target([S["aux2_g"], S["answer"]])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Where is that link?",
            "carrying M and N back into the given views")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "n₂ back to aux 1", "along its own projector, onto c₁d₁", SD_COL),
            step_badge("2", "m₁ square to a₁b₁", "the right angle projects TRUE there", AB_COL),
            step_badge("3", "back to the top, up to the front", "m n, then m′ n′", CD_COL),
            step_badge("4", "measure it in each view", "every one of them is short", SLATE),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)

        narrate(
            self,
            "We have the length. But a shortest distance is a real link between two "
            "real points, and an examiner may well want it drawn. So where is it?",
            FadeIn(bar), FadeIn(done),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Start with N, the end on C D, because C D is a proper line in every "
            "view. In the second auxiliary it is n two, the foot of our "
            "perpendicular. Carry it straight back along its own projector until it "
            "lands on c one d one. That is n one.",
            rail_focus(rail, rungs, 0),
            look_at(self, [S["aux1_g"], S["aux2_g"]]),
            Create(S["back1"]), FadeIn(S["n1_dot"]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Now M. Here is the one piece of reasoning in this scene. In the first "
            "auxiliary A B is at true length, which means A B is parallel to that "
            "plane of projection - and a right angle with a line parallel to the "
            "plane is drawn as a right angle. So in aux one, the link appears square "
            "to a one b one.",
            rail_focus(rail, rungs, 1),
            look_at(self, [S["aux1_g"], S["link1"]]),
            Create(S["link1"]), Create(S["ra_a1"]), FadeIn(S["m1_dot"]),
            FadeIn(S["l1_labs"]),
            lag_ratio=0.28,
        )
        narrate(
            self,
            "From n one, square across onto a one b one, and there is m one. The link "
            "is now on the drawing in a view we can project from.",
        )
        narrate(
            self,
            "Carry both feet back to the top view along their projectors - m onto a b, "
            "n onto c d - and then straight up to the front view, onto a prime b prime "
            "and c prime d prime. Now the shortest distance is drawn in all four "
            "views.",
            rail_focus(rail, rungs, 2),
            look_at(self, [S["given"], S["aux1_g"]], right=0.30),
            Create(S["back_tv"]), Create(S["link_tv"]), FadeIn(S["tv_dots"]),
            FadeIn(S["tv_labs"]),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "And up to the front.",
            look_at(self, [S["given"]], right=0.30),
            Create(S["back_fv"]), Create(S["link_fv"]), FadeIn(S["fv_dots"]),
            FadeIn(S["fv_labs"]),
            lag_ratio=0.25,
        )

        tally_rows = VGroup(
            mono("the same link, measured in four views", color=SLATE, size=15),
            mono(f"  front view   {G['lens']['fv']:5.1f}", color=SD_COL, size=16),
            mono(f"  top view     {G['lens']['tv']:5.1f}", color=SD_COL, size=16),
            mono(f"  aux 1        {G['lens']['aux1']:5.1f}", color=SD_COL, size=16),
            mono(f"  aux 2        {G['sd']:5.1f}   TRUE", color=SD_COL, size=17),
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        tally = card_back(tally_rows, pad=0.22, opacity=0.9)
        tally.add(SurroundingRectangle(tally_rows, color=SD_COL, buff=0.22,
                                       corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, tally, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(tally)

        narrate(
            self,
            "Which lets us make the point this sheet exists to make. Measure that link "
            "where it is drawn in the front view and you get "
            f"{G['lens']['fv']:.1f} millimetres. In the top view, "
            f"{G['lens']['tv']:.1f}. Even in the first auxiliary, where A B is true "
            f"length, it is only {G['lens']['aux1']:.1f}.",
            rail_focus(rail, rungs, 3),
            Create(S["l1_dim"]), Create(S["tv_dim"]), Create(S["fv_dim"]),
            FadeIn(tally),
            lag_ratio=0.25,
        )
        narrate(
            self,
            f"The answer is {G['sd']:.1f}, and it is only true in the one view where "
            "A B is a point. Three of those four numbers are wrong, and they are wrong "
            "by up to a third. A length has to be measured where it is true - which is "
            "the whole of descriptive geometry in one sentence.",
            look_at(self, [sheet], right=0.24, top=0.12),
            lag_ratio=0.2,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S05 - recap
# ==========================================================================
class S05_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "shortest distance between skew lines")
        self.add(bar)

        rows = VGroup(
            mono("skew  =  not parallel, and not meeting", color=SLATE, size=20),
            mono("aux 1   X1Y1 ∥ one view of AB    → AB TRUE LENGTH", color=AB_COL, size=20),
            mono("aux 2   X2Y2 ⊥ that true length  → AB a POINT", color=CD_COL, size=20),
            mono("drop the perpendicular onto c2d2 · that is the answer",
                 color=SD_COL, size=20),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(np.array([-0.2, 1.35, 0]))

        start = chip("FRONT + TOP VIEWS", color=INK, size=15)
        c1 = chip("aux 1 · AB TRUE LENGTH", color=AB_COL, size=15)
        c2 = chip("aux 2 · AB A POINT", color=CD_COL, size=15)
        ansc = chip(f"{G['sd']:.1f} mm", color=SD_COL, size=17)
        chain = VGroup(start, c1, c2, ansc).arrange(RIGHT, buff=1.0)
        chain.scale(0.92).move_to(np.array([0.0, -1.15, 0]))

        def link(a, b, text, colour):
            arrow = Arrow(a.get_right(), b.get_left(), buff=0.1, color=colour,
                          stroke_width=2.4, max_tip_length_to_length_ratio=0.2)
            return VGroup(arrow, mono(text, color=colour, size=12)
                          .next_to(arrow, UP, buff=0.06))

        links = VGroup(link(start, c1, "∥ ab", AB_COL),
                       link(c1, c2, "⊥ a₁b₁", CD_COL),
                       link(c2, ansc, "⊥ c₂d₂", SD_COL))

        narrate(self, "The whole method in four lines.", FadeIn(bar))
        narrate(
            self,
            "Skew lines are lines that are neither parallel nor meeting. On a drawing "
            "you spot them because they cross in both views, but the two crossings do "
            "not sit on the same projector.",
            FadeIn(rows[0]),
        )
        narrate(
            self,
            "To measure how close they come, take either line to a point view. That "
            "is two auxiliaries: the first parallel to one view of the line, carrying "
            "the heights, which gives true length; the second perpendicular to that "
            "true length, carrying the distances from two views back, which gives the "
            "point.",
            FadeIn(rows[1]), FadeIn(rows[2]),
            FadeIn(start), FadeIn(links[0]), FadeIn(c1), FadeIn(links[1]), FadeIn(c2),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Then one perpendicular from that point onto the other line, and measure "
            "it. It is true length there and nowhere else.",
            FadeIn(rows[3]), FadeIn(links[2]), FadeIn(ansc),
            lag_ratio=0.3,
        )

        check = VGroup(
            chip(f"answer   {G['sd']:.1f} mm", color=SD_COL, size=21),
            mono(f"check: AB true length {G['ab_true']:.1f} · the same link measures "
                 f"{G['lens']['fv']:.1f} front, {G['lens']['tv']:.1f} top, "
                 f"{G['lens']['aux1']:.1f} in aux 1", color=SLATE, size=14),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.45)
        narrate(
            self,
            f"For this pair the answer is {G['sd']:.1f} millimetres. Check yourself "
            f"against the true length of A B, {G['ab_true']:.1f} - if that is wrong, "
            "everything after it is wrong too.",
            FadeIn(check[0]), FadeIn(check[1]),
            lag_ratio=0.35,
        )
        narrate(
            self,
            "And there is a companion to this problem, section four eleven: the true "
            "angle between two skew lines. That one needs a view where both lines are "
            "true length at once - which is a different pair of auxiliaries, and a "
            "good exercise to try before the next sheet.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme: run the file directly and it prints the answers it is about
#  to animate.
#
#      py -3.11 ed09_skew_lines.py
# ==========================================================================
if __name__ == "__main__":
    print("Shortest distance between two skew lines  (§4.10)")
    print("  given (x along XY, in front of the VP, above the HP)")
    for k in ALL:
        print(f"    {k}   {SPACE[k][0]:5.0f} {SPACE[k][1]:6.0f} {SPACE[k][2]:6.0f}")
    print(f"  the lines cross in the front view at x {G['xf'][2][0]:.0f} "
          f"({G['gap_fv']:.0f} mm apart in depth)")
    print(f"  and in the top view at x {G['xt'][2][0]:.0f} "
          f"({G['gap_tv']:.0f} mm apart in height)  ->  SKEW")
    print(f"  AB:  front {G['ab_fv']:6.2f}   top {G['ab_tv']:6.2f}"
          f"   TRUE LENGTH {G['ab_true']:6.2f} mm")
    print(f"  CD:  front {G['cd_fv']:6.2f}   top {G['cd_tv']:6.2f}"
          f"   true length {G['cd_true']:6.2f} mm")
    print("  distances carried into the second auxiliary (from X1Y1, in the top view):")
    for k in ALL:
        print(f"    {k}   {G['steps'][k]:6.2f} mm")
    print(f"  the common perpendicular MN falls at {G['s']:.3f} along AB "
          f"and {G['t']:.3f} along CD")
    print(f"    M  {G['M'][0]:.1f}, {G['M'][1]:.1f} in front, {G['M'][2]:.1f} up")
    print(f"    N  {G['N'][0]:.1f}, {G['N'][1]:.1f} in front, {G['N'][2]:.1f} up")
    print(f"  it measures  front {G['lens']['fv']:.2f}   top {G['lens']['tv']:.2f}"
          f"   aux1 {G['lens']['aux1']:.2f}")
    print(f"  SHORTEST DISTANCE  {G['sd']:.2f} mm   (true only in aux 2)")
    print(f"  angle between the lines {G['angle']:.2f}°   (§4.11, not drawn here)")
