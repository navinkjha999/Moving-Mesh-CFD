"""
Engineering Drawing I - Sheet 3 / Lecture 4
Episode 08: The True Angle Between Two Planes
            + worked solution to Exercise 4 (Set A), Q.12  (Figure P4.12)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed08_dihedral_angle.py S03_Construction

Scene order:
    S01_Dihedral      what the angle between two planes actually means, and
                      why you have to look ALONG their common edge
    S02_Strategy      two auxiliary views: true length of the edge, then its
                      point view
    S03_Construction  Q.12 solved on one screen
    S04_Recap

solve() derives everything from the given dimensions and asserts that the first
auxiliary really shows BC at true length and the second really reduces it to a
point, and that the angle then read equals the dihedral angle computed from the
two plane normals.

No LaTeX anywhere - every glyph is Unicode Text().
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

from ed_stage import ProjectionScene, marker
from ed_common import (
    CORAL,
    GOLD,
    INK,
    MUTED,
    NAVY,
    SLATE,
    TEAL,
    VIOLET,
    caption,
    chip,
    finish_audio,
    hud,
    mono,
    narrate,
    title_bar,
)

# ==========================================================================
#  Figure P4.12: (x along XY, distance in front of the VP, height above the HP)
# ==========================================================================
# Read off Figure P4.12: the chain 26 | 10 | 38 along XY fixes the four
# projectors, the heights 44 / 50 / 18 / 54 are measured up from XY, and the
# depths 70 / 58 / 48 / 12 down from it.
SPACE = {
    "A": np.array([0.0,  70.0, 44.0]),
    "B": np.array([74.0, 58.0, 50.0]),
    "C": np.array([36.0, 48.0, 18.0]),
    "D": np.array([26.0, 12.0, 54.0]),
}
FACES = (("A", "B", "C"), ("D", "B", "C"))      # they share the edge BC
GAPS = (32.0, 15.0)                             # X1Y1 and X2Y2 set-backs
                                                # (searched for max scale with
                                                #  no view landing on another)


def _project(src, origin, along, normal, dist):
    return {k: origin + along * np.dot(src[k] - origin, along) + normal * dist[k]
            for k in src}


def solve(gaps=GAPS):
    P = SPACE
    A, B, C, D = (P[k] for k in "ABCD")

    # the true dihedral angle, straight from the geometry
    e = (C - B) / np.linalg.norm(C - B)
    vA = (A - B) - np.dot(A - B, e) * e
    vD = (D - B) - np.dot(D - B, e) * e
    theta = math.degrees(math.acos(np.dot(vA, vD)
                                   / (np.linalg.norm(vA) * np.linalg.norm(vD))))

    fv = {k: np.array([v[0], v[2]]) for k, v in P.items()}
    tv = {k: np.array([v[0], -v[1]]) for k, v in P.items()}

    # ---- aux 1: X1Y1 PARALLEL to the top view of BC -> BC true length ------
    u1 = tv["C"] - tv["B"]
    u1 /= np.linalg.norm(u1)
    n1 = np.array([-u1[1], u1[0]])
    if n1[1] > 0:
        n1 = -n1                                     # keep it below the top view
    p0 = tv["B"] + n1 * gaps[0]
    # the auxiliary goes on the FAR side of X1Y1 from the top view - offsetting
    # back towards it drops the new view straight on top of the old one
    aux1 = _project(tv, p0, u1, n1, {k: P[k][2] for k in P})     # carry HEIGHTS

    assert abs(np.linalg.norm(aux1["C"] - aux1["B"]) - np.linalg.norm(C - B)) < 1e-6, \
        "aux 1 does not show BC at true length"

    # ---- aux 2: X2Y2 PERPENDICULAR to b1c1 -> BC becomes a point -----------
    u2 = -(aux1["C"] - aux1["B"])
    u2 /= np.linalg.norm(u2)
    w2 = np.array([-u2[1], u2[0]])
    q0 = aux1["B"] + u2 * gaps[1]
    aux2 = _project(aux1, q0, w2, u2,
                    {k: abs(float(np.dot(tv[k] - p0, n1))) for k in P})

    assert np.linalg.norm(aux2["C"] - aux2["B"]) < 1e-6, "aux 2 is not a point view of BC"
    d1, d2 = aux2["A"] - aux2["B"], aux2["D"] - aux2["B"]
    read = math.degrees(math.acos(np.dot(d1, d2)
                                  / (np.linalg.norm(d1) * np.linalg.norm(d2))))
    assert abs(read - theta) < 1e-6, "the point view does not show the true angle"

    return dict(fv=fv, tv=tv, aux1=aux1, aux2=aux2, theta=theta,
                u1=u1, n1=n1, p0=p0, u2=u2, w2=w2, q0=q0,
                bc=float(np.linalg.norm(C - B)))


G = solve()
MM = 0.0427


def pt(v2):
    return np.array([v2[0] * MM, v2[1] * MM, 0.0])


def faces(pts, colour, width=3.0, fill=0.10):
    g = VGroup()
    for f in FACES:
        g.add(Polygon(*[pt(pts[k]) for k in f], stroke_color=colour,
                      stroke_width=width, fill_color=colour, fill_opacity=fill))
    return g


def edge_bc(pts, width=5.0):
    return Line(pt(pts["B"]), pt(pts["C"]), color=GOLD, stroke_width=width)


# ==========================================================================
#  S01 - what the angle between two planes means
# ==========================================================================
class S01_Dihedral(ProjectionScene):
    quadrant = 1
    heading = "The True Angle Between Two Planes"
    subheading = "Lecture 4 · the dihedral angle"

    def construct(self):
        self.build_stage()
        self.add(self.vp, self.hp, self.xy, *self.tags, self.bar)

        Bp = np.array([-0.4, -1.2, 0.35])
        Cp = np.array([1.0, -2.2, 1.55])
        Ap = np.array([1.3, -0.6, 1.35])
        Dp = np.array([-1.9, -1.8, 1.85])

        f1 = Polygon(Ap, Bp, Cp, stroke_color=CORAL, stroke_width=3.5,
                     fill_color=CORAL, fill_opacity=0.32)
        f2 = Polygon(Dp, Bp, Cp, stroke_color=TEAL, stroke_width=3.5,
                     fill_color=TEAL, fill_opacity=0.32)
        hinge = Line(Bp, Cp, color=GOLD, stroke_width=7)

        narrate(
            self,
            "Two planes that are not parallel meet along a line, and they open out "
            "from that line like the two covers of a book.",
            Create(f1),
            Create(f2),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Here the two triangles A B C and D B C share the edge B C. That shared "
            "edge is the hinge, and the angle we want is how far the book is open. "
            "It is called the dihedral angle.",
            Create(hinge),
        )
        narrate(
            self,
            "Now think about how you would measure it on a real book. You would put "
            "your eye at the end of the spine and look straight down it. From there "
            "each cover shows as a line, and the angle between those two lines is "
            "the angle you want.",
        )

        note = hud(
            self,
            VGroup(
                chip("look ALONG the common edge", color=GOLD, size=21),
                chip("the edge becomes a POINT, both planes become LINES",
                     color=INK, size=21),
            ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.55),
        )
        narrate(
            self,
            "That is the whole method. Get a view looking straight along B C. The "
            "edge shrinks to a point, both planes collapse to lines, and the angle "
            "between those lines is the true dihedral angle.",
            FadeIn(note),
        )
        narrate(
            self,
            "Look at it from any other direction and the angle is distorted, exactly "
            "as it was for a single line or a single plane. There is nothing new "
            "here except which line you have to look along.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - the strategy
# ==========================================================================
class S02_Strategy(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Two Steps", "true length, then point view")
        self.add(bar)

        steps = [
            ("1", "X1Y1 PARALLEL to one view of BC",
             "carry the distances from the other view → BC comes out true length",
             VIOLET),
            ("2", "X2Y2 PERPENDICULAR to that true length",
             "carry again → BC shrinks to a point, both planes become lines",
             CORAL),
        ]
        rows = VGroup()
        for num, head, sub, colour in steps:
            n = mono(num, color=colour, size=30)
            text = VGroup(caption(head, color=colour, size=22),
                          mono(sub, color=SLATE, size=17)
                          ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
            rows.add(VGroup(n, text).arrange(RIGHT, buff=0.4, aligned_edge=UP))
        rows.arrange(DOWN, buff=0.55, aligned_edge=LEFT).move_to(np.array([-0.5, 0.55, 0]))

        narrate(
            self,
            "You cannot jump straight to the point view of a line. You have to see "
            "it at true length first, and that is a rule worth remembering on its "
            "own.",
            FadeIn(bar),
        )
        narrate(
            self,
            "Step one. Draw X one Y one parallel to one view of B C - either view "
            "will do - and carry the distances across from the other. In that "
            "auxiliary, B C appears at true length.",
            FadeIn(rows[0]),
        )
        narrate(
            self,
            "Step two. Now draw X two Y two perpendicular to that true length, and "
            "project again. Looking square on to the end of a line that is true "
            "length makes it a point, and everything attached to it flattens into "
            "lines.",
            FadeIn(rows[1]),
        )

        rule = VGroup(
            chip("a line only reaches POINT VIEW from a TRUE LENGTH view",
                 color=GOLD, size=20),
            chip("and everything else in both planes comes along with it",
                 color=SLATE, size=18),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.7)
        narrate(
            self,
            "One line of advice. If your point view does not come out as a single "
            "point, the mistake is almost always that X two Y two was not exactly "
            "perpendicular to the true length.",
            FadeIn(rule[0]),
            FadeIn(rule[1]),
            lag_ratio=0.35,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S03 - Q.12 on one screen
# ==========================================================================
class S03_Construction(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Exercise 4 (Set A) · Q.12",
                        "Figure P4.12 · true size of the angle between ABC and BCD")
        self.add(bar)

        fv, tv, a1, a2 = G["fv"], G["tv"], G["aux1"], G["aux2"]

        xy = Line(pt(np.array([-16, 0])), pt(np.array([69, 0])),
                  color=INK, stroke_width=2.6)
        xy_lab = VGroup(mono("X", color=INK, size=16).next_to(xy, LEFT, buff=0.1),
                        mono("Y", color=INK, size=16).next_to(xy, RIGHT, buff=0.1))
        fv_f = faces(fv, CORAL)
        tv_f = faces(tv, TEAL)
        fv_bc, tv_bc = edge_bc(fv), edge_bc(tv)
        labs = VGroup()
        for k in "ABCD":
            labs.add(mono(f"{k.lower()}′", color=CORAL, size=16)
                     .next_to(pt(fv[k]), UP, buff=0.07))
            labs.add(mono(k.lower(), color=TEAL, size=16)
                     .next_to(pt(tv[k]), DOWN, buff=0.07))

        def refline(origin, direction, pts, extra=13):
            sp = [np.dot(pts[k] - origin, direction) for k in pts]
            return Line(pt(origin + direction * (min(sp) - extra)),
                        pt(origin + direction * (max(sp) + extra)),
                        color=INK, stroke_width=2.2)

        x1 = refline(G["p0"], G["u1"], {**tv, **a1})
        x2 = refline(G["q0"], G["w2"], {**a1, **a2})
        x1l = mono("X1Y1", color=INK, size=14).next_to(x1.get_end(), UR, buff=0.05)
        x2l = mono("X2Y2", color=INK, size=14).next_to(x2.get_end(), UR, buff=0.05)

        def rays(src, dst):
            return VGroup(*[DashedLine(pt(src[k]), pt(dst[k]), color=MUTED,
                                       stroke_width=0.9, stroke_opacity=0.45,
                                       dash_length=0.05) for k in src])

        r1, r2 = rays(tv, a1), rays(a1, a2)
        a1_f = faces(a1, VIOLET, 2.8)
        a1_bc = edge_bc(a1, 5.5)
        a1_tl = mono("TL", color=GOLD, size=15).next_to(
            pt((a1["B"] + a1["C"]) / 2), UR, buff=0.1)
        a1_labs = VGroup(*[mono(f"{k.lower()}1", color=VIOLET, size=14)
                           .next_to(pt(a1[k]), DOWN, buff=0.06) for k in "AD"])

        # the point view: both faces collapse onto two lines out of one point
        pv = pt(a2["B"])
        line_a = Line(pv, pt(a2["A"]), color=CORAL, stroke_width=4.5)
        line_d = Line(pv, pt(a2["D"]), color=TEAL, stroke_width=4.5)
        pv_ring = Circle(radius=0.11, color=GOLD, stroke_width=3).move_to(pv)
        pv_lab = mono("b2 c2", color=GOLD, size=14).next_to(pv_ring, DOWN, buff=0.08)
        a2_labs = VGroup(mono("a2", color=CORAL, size=15).next_to(pt(a2["A"]), UR, buff=0.06),
                         mono("d2", color=TEAL, size=15).next_to(pt(a2["D"]), UL, buff=0.06))

        dirA = (a2["A"] - a2["B"]) / np.linalg.norm(a2["A"] - a2["B"])
        dirD = (a2["D"] - a2["B"]) / np.linalg.norm(a2["D"] - a2["B"])
        s0 = math.atan2(dirA[1], dirA[0])
        s1 = math.atan2(dirD[1], dirD[0])
        arc = Arc(radius=0.55, start_angle=s0, angle=(s1 - s0 + PI) % TAU - PI,
                  arc_center=pv, color=GOLD, stroke_width=3)
        alab = mono("θ", color=GOLD, size=19).move_to(
            pv + 0.85 * np.array([math.cos(s0 + (((s1 - s0 + PI) % TAU - PI) / 2)),
                                  math.sin(s0 + (((s1 - s0 + PI) % TAU - PI) / 2)), 0]))

        drawing = VGroup(xy, xy_lab, fv_f, tv_f, fv_bc, tv_bc, labs,
                         x1, x1l, r1, a1_f, a1_bc, a1_tl, a1_labs,
                         x2, x2l, r2, line_a, line_d, pv_ring, pv_lab, a2_labs,
                         arc, alab)
        drawing.scale(min(8.4 / drawing.width, 5.6 / drawing.height))
        drawing.move_to(np.array([-3.0, -0.4, 0]))

        data = VGroup(
            mono("        above HP   in front of VP", color=SLATE, size=15),
            mono(f"  A      {SPACE['A'][2]:7.0f} {SPACE['A'][1]:12.0f}", color=INK, size=16),
            mono(f"  B      {SPACE['B'][2]:7.0f} {SPACE['B'][1]:12.0f}", color=GOLD, size=16),
            mono(f"  C      {SPACE['C'][2]:7.0f} {SPACE['C'][1]:12.0f}", color=GOLD, size=16),
            mono(f"  D      {SPACE['D'][2]:7.0f} {SPACE['D'][1]:12.0f}", color=INK, size=16),
            mono("  projectors  "
                 + " · ".join(f"{SPACE[k][0]:.0f}" for k in "ADCB"), color=SLATE, size=15),
        ).arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to(np.array([4.4, 1.5, 0]))

        narrate(
            self,
            "Question twelve. Two triangular faces, A B C and B C D, given by their "
            "two views. Find the true size of the angle between them.",
            FadeIn(bar),
            FadeIn(data),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Transfer the question first. A is forty-four above the H P and seventy "
            "in front of the V P. B is fifty and fifty-eight. C is eighteen and "
            "forty-eight. D is fifty-four and twelve.",
            Create(xy), FadeIn(xy_lab), Create(fv_f), Create(tv_f), FadeIn(labs),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The two faces share the edge B C, and that is the hinge. Everything now "
            "aims at one thing: a view looking straight along it.",
            Create(fv_bc), Create(tv_bc),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Step one. Draw X one Y one parallel to the top view b c, and project "
            "across, carrying each corner's height above the H P from the front "
            "view.",
            Create(x1), FadeIn(x1l), Create(r1),
            lag_ratio=0.25,
        )
        narrate(
            self,
            f"In that auxiliary view b one c one is the true length of the edge, "
            f"{G['bc']:.1f} millimetres. The two faces are still open, and still "
            "distorted.",
            Create(a1_f), Create(a1_bc), FadeIn(a1_tl), FadeIn(a1_labs),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Step two. Draw X two Y two perpendicular to that true length, and "
            "project once more, carrying the distances from X one Y one measured "
            "back in the top view.",
            Create(x2), FadeIn(x2l), Create(r2),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Now b two and c two land on top of one another. The edge has become a "
            "point, and we are looking straight down the hinge.",
            Create(pv_ring), FadeIn(pv_lab),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Each face has flattened into a single line out of that point: one to a "
            "two, one to d two.",
            Create(line_a), Create(line_d), FadeIn(a2_labs),
            lag_ratio=0.25,
        )
        ans = VGroup(
            chip(f"θ = {G['theta']:.1f}°", color=GOLD, size=24),
            mono(f"(the two faces open at {G['theta']:.1f}°; extended as full planes "
                 f"they also cross at {180 - G['theta']:.1f}°)", color=SLATE, size=14),
        ).arrange(DOWN, buff=0.2).move_to(np.array([4.4, -1.9, 0]))

        narrate(
            self,
            "And the angle between those two lines is the true dihedral angle: "
            f"{G['theta']:.1f} degrees.",
            Create(arc), FadeIn(alab), FadeIn(ans[0]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Quote the angle the faces actually make with each other - the one you "
            "can see at the point view, between the two lines that the faces have "
            f"become. Two planes carried on for ever cross at {G['theta']:.1f} degrees "
            f"and at {180 - G['theta']:.1f} degrees, but only one of those is the "
            "angle this pair of triangles opens at.",
            FadeIn(ans[1]),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - recap
# ==========================================================================
class S04_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "angle between two planes")
        self.add(bar)

        rows = VGroup(
            mono("the angle lives on the COMMON EDGE", color=GOLD, size=22),
            mono("aux 1   X1Y1 ∥ one view of the edge   → true length", color=VIOLET, size=21),
            mono("aux 2   X2Y2 ⊥ that true length       → point view", color=CORAL, size=21),
            mono("both faces are then lines; read the angle between them", color=SLATE, size=19),
        ).arrange(DOWN, buff=0.32, aligned_edge=LEFT).move_to(np.array([-0.3, 0.5, 0]))

        narrate(self, "The whole method in four lines.", FadeIn(bar))
        narrate(
            self,
            "Find the common edge, get it to true length, then get it to a point. "
            "Once you are looking down the hinge, both faces are lines and the angle "
            "is there to be measured.",
            FadeIn(rows[0]), FadeIn(rows[1]), FadeIn(rows[2]), FadeIn(rows[3]),
            lag_ratio=0.32,
        )

        ansc = chip(f"Q.12   θ = {G['theta']:.1f}°", color=GOLD, size=22).to_edge(DOWN, buff=0.95)
        narrate(
            self,
            f"For question twelve the answer is {G['theta']:.1f} degrees.",
            FadeIn(ansc),
        )
        narrate(
            self,
            "Notice how much of this sheet is the same three moves in different "
            "orders: true length, point view, edge view. Question thirteen, the "
            "shortest distance between skew lines, is built from the very same "
            "pair of auxiliaries you have just drawn.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)
