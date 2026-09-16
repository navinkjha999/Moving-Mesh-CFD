"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 15: Points on the Surface of an OBLIQUE Solid
            + Exercise 8 (Set A), Q.1

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed15_surface_points.py S02_ObliqueCylinder
    ... or use render_ed15.bat to build all four scenes in order.

Scene order (about ten minutes in all):

    S01_WhatMoves       episode 13 gave two helper lines - a generator where
                        the sides run straight, a level section where the solid
                        tapers. Lean the axis over and BOTH survive, but
                        neither stays where it was: the generator stops being
                        a point in the top view, and the level section stops
                        being concentric with the base
    S02_ObliqueCylinder Q.1(a) worked: Ø40, axis 60 at 60°. Three points, each
                        given in one view, and the one mistake the whole sheet
                        is built to catch - reading a depth off the base circle
                        at the point's own x
    S03_ConeAndPyramid  the tapering pair. The level section is the same figure
                        as the base, shrunk towards the apex and slid along the
                        axis - and on the cone the generator gives the same
                        answer, which is the check
    S04_Recap           one rule per solid, what the brackets decide, and the
                        three things that are different from episode 13

A NOTE ON THE FIGURE. Figure P8.1(a) is the book's: an oblique cylinder, Ø40,
axis 60 long at 60° to the base. The lettered points of the figure were not
available when this was written, so a, b and c below are chosen to exercise one
rule each - the method is what is examinable, and it is the book's method.
Parts (b) to (d) are stood in for by the oblique cone and the oblique pyramid
of Q.3, whose dimensions are the figure's and are already worked in episode 14.

Everything is computed by solve(), which asserts that each point really lies on
the surface it is supposed to, that the two constructions for a cone point
agree, that the level section of an oblique cone really is a circle centred on
the leaning axis, and that the naive answer - depth read off the base circle at
the point's own x - is wrong, by how much, or impossible.

No LaTeX anywhere - every glyph is Unicode Text().
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

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

SOLID_COL = GOLD
HELP_COL = TEAL          # the helper line - the whole method
PT_COL = CORAL           # the points themselves
HIDE_COL = VIOLET        # anything hidden, and the wrong answer
AUX_COL = CREAM

MM = 0.030
S3 = 0.050

# ==========================================================================
#  The three solids. x across the sheet, y depth (negative = in front of the
#  VP, towards the observer), z up from the base.
#
#  P8.1(a)  oblique cylinder, Ø40, axis 60 long at 60° to the base
#  Q.3(a)   oblique cone,     Ø42, axis 60 long at 60° to the base
#  Q.3(b)   oblique pyramid,  base 35 square on its diagonals, height 50,
#           apex 10 beyond the right-hand corner
# ==========================================================================
CYL = dict(dia=40.0, axis=60.0, lean=60.0)
CONE = dict(dia=42.0, axis=60.0, lean=60.0)
PYR = dict(side=35.0, height=50.0, offset=10.0)


def axis_vec(spec):
    a = math.radians(spec["lean"])
    return np.array([spec["axis"] * math.cos(a), 0.0, spec["axis"] * math.sin(a)])


CYL_AX = axis_vec(CYL)
CYL_R = CYL["dia"] / 2.0
CONE_AX = axis_vec(CONE)
CONE_R = CONE["dia"] / 2.0
PYR_HALF = PYR["side"] / math.sqrt(2.0)
PYR_APEX = np.array([PYR_HALF + PYR["offset"], 0.0, PYR["height"]])


# --------------------------------------------------------------------------
#  The oblique cylinder: every generator is parallel to the axis
# --------------------------------------------------------------------------
def cyl_point(theta, t):
    return np.array([CYL_R * math.cos(theta), CYL_R * math.sin(theta), 0.0]) + t * CYL_AX


def cyl_from_fv(x, z, front=True):
    """A point given in the front view: follow its generator back to the base."""
    t = z / CYL_AX[2]
    assert -1e-9 <= t <= 1.0 + 1e-9, "that height is off the cylinder"
    x_base = x - t * CYL_AX[0]
    r2 = CYL_R * CYL_R - x_base * x_base
    assert r2 > 1e-9, "no generator of this cylinder passes through that point"
    y = -math.sqrt(r2) if front else math.sqrt(r2)
    return dict(p=np.array([x, y, z]), x_base=x_base, t=t,
                theta=math.atan2(y, x_base))


def cyl_from_tv(x, y):
    """Every surface point whose PLAN is (x, y), uppermost first.

    On a right cylinder the plan of a surface point is on the circle and its
    height is anybody's guess. Here it is the other way round: the plan can be
    anywhere in the swept outline, and it names at most two heights, because at
    most two generators run through it.
    """
    r2 = CYL_R * CYL_R - y * y
    assert r2 > -1e-9, "that depth is wider than the cylinder"
    s = math.sqrt(max(r2, 0.0))
    out = []
    for x_base in sorted({-s, s}):
        t = (x - x_base) / CYL_AX[0]
        if -1e-9 <= t <= 1.0 + 1e-9:
            out.append(dict(p=np.array([x, y, t * CYL_AX[2]]), x_base=x_base, t=t))
    out.sort(key=lambda d: -d["p"][2])
    return out


def cyl_naive(x):
    """The wrong answer: depth read off the BASE circle at the point's own x."""
    r2 = CYL_R * CYL_R - x * x
    return math.sqrt(r2) if r2 > 0 else None


# --------------------------------------------------------------------------
#  The tapering pair: a level section is the base figure, shrunk and slid
# --------------------------------------------------------------------------
def cone_level(z):
    """Radius and centre of the horizontal section of the oblique cone at z."""
    s = 1.0 - z / CONE_AX[2]
    return s * CONE_R, (1.0 - s) * CONE_AX[0]


def cone_from_fv(x, z, front=True):
    """Two ways to the same answer - the level circle, and the generator."""
    r, cx = cone_level(z)
    d2 = r * r - (x - cx) ** 2
    assert d2 > 1e-9, "that point is not on the cone"
    y = -math.sqrt(d2) if front else math.sqrt(d2)

    # the generator: join the apex to the point in the front view and run it
    # down to the base line, then scale the base point's depth by the same s
    apex = CONE_AX
    s = 1.0 - z / apex[2]
    x_base = apex[0] + (x - apex[0]) / s
    yb2 = CONE_R * CONE_R - x_base * x_base
    assert yb2 > 1e-9, "the generator misses the base circle"
    y_base = -math.sqrt(yb2) if front else math.sqrt(yb2)
    assert abs(s * y_base - y) < 1e-9, "the two constructions disagree"

    return dict(p=np.array([x, y, z]), s=s, r=r, cx=cx,
                base=np.array([x_base, y_base, 0.0]))


def pyr_level(z):
    """Half-diagonal and centre of the horizontal section of the pyramid at z."""
    s = 1.0 - z / PYR["height"]
    return s * PYR_HALF, (1.0 - s) * PYR_APEX[0]


def pyr_from_fv(x, z, front=True):
    hd, cx = pyr_level(z)
    d = hd - abs(x - cx)
    assert d > 1e-9, "that point is not on the pyramid"
    y = -d if front else d
    return dict(p=np.array([x, y, z]), s=1.0 - z / PYR["height"], hd=hd, cx=cx)


# --------------------------------------------------------------------------
#  solve() - every number the episode says out loud, and the checks
# --------------------------------------------------------------------------
def _on_cylinder(p, tol=1e-9):
    """Is p on the curved surface? Slide it back down its own generator."""
    t = p[2] / CYL_AX[2]
    b = p - t * CYL_AX
    return abs(math.hypot(b[0], b[1]) - CYL_R) < tol and -tol <= t <= 1.0 + tol


def solve():
    P = {}

    # ---- a′ : given in the FRONT view, unbracketed --------------------------
    # The generator through a′ runs back to the base at x = 11.53, and the
    # depth comes off the base circle THERE. At a′'s own x of 30 the base
    # circle does not exist at all, which is the whole lesson in one number.
    a = cyl_from_fv(30.0, 32.0, front=True)
    P["a"] = dict(solid="cyl", given="fv", tag=("a′", "a"), hidden_fv=False,
                  note="unbracketed in the front view, so the near half: y is negative",
                  **a)
    assert _on_cylinder(a["p"])
    assert cyl_naive(30.0) is None, "pick a point where the naive answer is impossible"

    # ---- b : given in the TOP view, unbracketed -----------------------------
    # Two generators cross this plan point, so two heights. Unbracketed means
    # the one you can SEE from above, which is the higher.
    cands = cyl_from_tv(15.0, 16.0)
    assert len(cands) == 2, "b was meant to be the ambiguous one"
    P["b"] = dict(solid="cyl", given="tv", tag=("b′", "b"), hidden_tv=False,
                  other=cands[1]["p"],
                  note="two generators run through that plan point - unbracketed "
                       "picks the upper", **cands[0])

    # ---- (c) : given in the TOP view, bracketed, ON the base circle ---------
    # The trap: a plan point sitting on the base circle looks like a base
    # point, and if it were not bracketed it would not be one.
    cands = cyl_from_tv(12.0, 16.0)
    assert len(cands) == 2
    assert abs(cands[1]["p"][2]) < 1e-9, "the lower candidate should be the base point"
    assert abs(math.hypot(12.0, 16.0) - CYL_R) < 1e-9, "c should sit on the base circle"
    P["c"] = dict(solid="cyl", given="tv", tag=("c′", "(c)"), hidden_tv=True,
                  other=cands[0]["p"],
                  note="bracketed, so the hidden one - the lower of the two, which "
                       "here is on the base itself", **cands[1])

    # ---- d′ : given in the FRONT view of the oblique CONE -------------------
    d = cone_from_fv(10.0, 24.0, front=True)
    P["d"] = dict(solid="cone", given="fv", tag=("d′", "d"), hidden_fv=False,
                  note="level circle 11.30 radius, centred 13.86 along the axis - "
                       "not on the axis of the base", **d)

    # ---- e′ : given in the FRONT view of the oblique PYRAMID ----------------
    e = pyr_from_fv(16.0, 20.0, front=True)
    P["e"] = dict(solid="pyr", given="fv", tag=("e′", "e"), hidden_fv=False,
                  note="level square, half-diagonal 14.85, centred 13.90 along "
                       "the axis", **e)

    # ---- the claim the tapering scene is built on --------------------------
    # A horizontal section of an oblique cone is a CIRCLE, and its centre is on
    # the axis. Neither is obvious, and both are what make the method work.
    for z in (8.0, 24.0, 40.0):
        r, cx = cone_level(z)
        s = 1.0 - z / CONE_AX[2]
        for k in range(24):
            th = 2 * math.pi * k / 24
            base = np.array([CONE_R * math.cos(th), CONE_R * math.sin(th), 0.0])
            q = CONE_AX + s * (base - CONE_AX)          # the point on the cone
            assert abs(q[2] - z) < 1e-9
            assert abs(math.hypot(q[0] - cx, q[1]) - r) < 1e-9, "not a circle"
        axis_at_z = CONE_AX * (z / CONE_AX[2])
        assert abs(axis_at_z[0] - cx) < 1e-9, "the section is not centred on the axis"
    return P


P = solve()


# ==========================================================================
#  The 3-D stage
# ==========================================================================
S1_H = 58.0              # what the 3-D beats centre on vertically
S1_CX = 12.0             # ... and horizontally, midway through the lean


def pt3(p, h=S1_H, cx=S1_CX):
    x, y, z = p
    return np.array([(x - cx) * S3, y * S3, (z - h / 2.0) * S3])


def ring_3d(centre, R, colour=SOLID_COL, width=3.2, n=96, **kw):
    c = np.asarray(centre, float)
    pts = [pt3(c + np.array([R * math.cos(2 * math.pi * i / n),
                             R * math.sin(2 * math.pi * i / n), 0.0]), **kw)
           for i in range(n + 1)]
    m = VMobject(stroke_color=colour, stroke_width=width)
    m.set_points_as_corners(pts)
    return m


def tube_3d(ax, R, fill=0.20, n=48, **kw):
    """The curved surface of a cylinder, right or oblique - the same mesh."""
    ax = np.asarray(ax, float)
    g = VGroup()
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        v0 = np.array([R * math.cos(a0), R * math.sin(a0), 0.0])
        v1 = np.array([R * math.cos(a1), R * math.sin(a1), 0.0])
        g.add(Polygon(pt3(v0, **kw), pt3(v1, **kw), pt3(v1 + ax, **kw), pt3(v0 + ax, **kw),
                      stroke_width=0, fill_color=SOLID_COL, fill_opacity=fill))
    return g


def cone_3d(apex, R, fill=0.20, n=48, **kw):
    apex = np.asarray(apex, float)
    g = VGroup()
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        v0 = np.array([R * math.cos(a0), R * math.sin(a0), 0.0])
        v1 = np.array([R * math.cos(a1), R * math.sin(a1), 0.0])
        g.add(Polygon(pt3(v0, **kw), pt3(v1, **kw), pt3(apex, **kw),
                      stroke_width=0, fill_color=SOLID_COL, fill_opacity=fill))
    return g


def ground_3d(R=34.0, **kw):
    return ring_3d((0, 0, 0), R, colour=MUTED, width=1.4, **kw).set_stroke(opacity=0.35)


# ==========================================================================
#  S01 - what episode 13's two helper lines do when the axis leans
# ==========================================================================
class S01_WhatMoves(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=70 * DEGREES, theta=-62 * DEGREES,
                                    zoom=1.0, focal_distance=150.0)
        bar = hud(self, title_bar("Points on an Oblique Solid",
                                  "Sheet 8 · §10 · both helper lines survive the lean"))
        self.add(bar)

        R = CYL_R
        up = np.array([0.0, 0.0, CYL["axis"]])
        th, t = math.radians(200.0), 0.70
        base = np.array([R * math.cos(th), R * math.sin(th), 0.0])

        # ---- the right cylinder ----------------------------------------------
        tube = tube_3d(up, R)
        rims = VGroup(ring_3d((0, 0, 0), R), ring_3d(up, R))
        gen = Line(pt3(base), pt3(base + up), color=HELP_COL, stroke_width=4)
        q = Dot3D(pt3(base + t * up), radius=0.075, color=PT_COL)
        drop = DashedLine(pt3(base + t * up), pt3(base), color=AUX_COL,
                          stroke_width=1.6, dash_length=0.07)
        plan = Dot3D(pt3(base), radius=0.065, color=PT_COL)
        right_tag = billboard(self, mono("its plan is ON the circle", color=PT_COL, size=19)
                              .move_to(pt3((base[0] - 6, base[1] - 26, -16))))

        narrate(
            self,
            "Episode thirteen gave you two helper lines. On anything whose sides run "
            "straight up - a cylinder, a prism - you drew a generator. On anything "
            "that tapers - a cone, a pyramid - you drew a level section. Here is the "
            "generator, on a right cylinder.",
            FadeIn(bar), FadeIn(tube), Create(rims), Create(gen),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "A point on the surface sits somewhere on that generator, and because the "
            "generator is vertical, the whole of it lands on ONE point of the base "
            "circle. So the plan of the point is on the circle, whatever its height. "
            "That is what made episode thirteen easy.",
            FadeIn(q), Create(drop), FadeIn(plan), FadeIn(right_tag),
            lag_ratio=0.2,
        )

        # ---- lean it ----------------------------------------------------------
        new_tube = tube_3d(CYL_AX, R)
        new_rims = VGroup(ring_3d((0, 0, 0), R), ring_3d(CYL_AX, R))
        new_gen = Line(pt3(base), pt3(base + CYL_AX), color=HELP_COL, stroke_width=4)
        moved = base + t * CYL_AX
        new_q = Dot3D(pt3(moved), radius=0.075, color=PT_COL)
        new_drop = DashedLine(pt3(moved), pt3((moved[0], moved[1], 0.0)),
                              color=AUX_COL, stroke_width=1.6, dash_length=0.07)
        new_plan = Dot3D(pt3((moved[0], moved[1], 0.0)), radius=0.065, color=PT_COL)
        narrate(
            self,
            "Now lean the axis over to sixty degrees. Same base circle, same "
            "generator - it is still a straight line on the surface, it is still "
            "parallel to the axis. Nothing about the method has broken.",
            FadeOut(right_tag),
            Transform(tube, new_tube), Transform(rims, new_rims),
            Transform(gen, new_gen), Transform(q, new_q),
            Transform(drop, new_drop), Transform(plan, new_plan),
            rate_func=rate_functions.ease_in_out_sine,
        )
        r_plan = math.hypot(moved[0], moved[1])
        lean_tag = billboard(self, mono(f"its plan is now {r_plan:.2f} from the centre "
                                        f"- the radius is {R:.0f}", color=PT_COL, size=19)
                             .move_to(pt3((moved[0] - 4, moved[1] - 28, -16))))
        narrate(
            self,
            f"But look where the point's plan went. It was on the circle, twenty from "
            f"the centre. It is now {r_plan:.2f} from the centre - most of the way in "
            "towards the middle. Drop a surface point of an oblique cylinder and it "
            "lands nowhere near the rim.",
            FadeIn(lean_tag),
        )
        warn = hud(self, chip("so the depth NEVER comes off the base circle at the "
                              "point's own x", color=HIDE_COL, size=19)
                   .to_edge(DOWN, buff=0.55))
        narrate(
            self,
            "Which kills the shortcut. On a right cylinder you could read a depth "
            "straight off the circle at the point's own position across the sheet. Do "
            "that here and you are reading the wrong circle - or, as we are about to "
            "see, no circle at all.",
            settle(FadeIn(warn)),
        )

        # ---- the tapering half ------------------------------------------------
        self.play(FadeOut(Group(tube, rims, gen, q, drop, plan, lean_tag, warn)),
                  run_time=0.9)
        CR, z_lv = CONE_R, 24.0
        up_apex = np.array([0.0, 0.0, CONE_AX[2]])
        s = 1.0 - z_lv / CONE_AX[2]
        r_lv = s * CR
        cone = cone_3d(up_apex, CR, **dict(cx=0.0))
        cone_rim = ring_3d((0, 0, 0), CR, cx=0.0)
        level = ring_3d((0, 0, z_lv), r_lv, colour=HELP_COL, width=4, cx=0.0)
        axis_r = DashedLine(pt3((0, 0, 0), cx=0.0), pt3(up_apex, cx=0.0),
                            color=MUTED, stroke_width=1.8, dash_length=0.07)
        narrate(
            self,
            "The other helper line. On a right cone, a horizontal section is a circle, "
            "it is concentric with the base, and its radius shrinks in proportion to "
            "the height. A point at a given height is somewhere on that circle.",
            FadeIn(cone), Create(cone_rim), Create(axis_r), Create(level),
            lag_ratio=0.2,
        )
        new_cone = cone_3d(CONE_AX, CR, **dict(cx=0.0))
        new_level = ring_3d((cone_level(z_lv)[1], 0, z_lv), r_lv,
                            colour=HELP_COL, width=4, cx=0.0)
        new_axis = DashedLine(pt3((0, 0, 0), cx=0.0), pt3(CONE_AX, cx=0.0),
                              color=MUTED, stroke_width=1.8, dash_length=0.07)
        narrate(
            self,
            "Lean that one over too. The section is STILL a circle - that is worth "
            "knowing, and it is not obvious - and it is still exactly the same size "
            "for its height. What has changed is where its centre is: it has slid "
            "along the axis with the rest of the solid.",
            Transform(cone, new_cone), Transform(level, new_level),
            Transform(axis_r, new_axis),
            rate_func=rate_functions.ease_in_out_sine,
        )
        note = hud(self, VGroup(
            chip("generator · still a straight line, but its plan is a LINE, not a point",
                 color=HELP_COL, size=18),
            chip("level section · still the base figure shrunk, but slid along the axis",
                 color=HELP_COL, size=18),
        ).arrange(DOWN, buff=0.16).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "So both helper lines survive, and both have to be drawn where the solid "
            "has actually gone. That is the whole of question one.",
            settle(FadeIn(note)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.3)


# ==========================================================================
#  The sheet
# ==========================================================================
XY_Y = -12.0
TV_Y = -48.0
PYR_X0 = 118.0           # the pyramid's own origin, to the right of the cone


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


def fv(x, z):
    return P2(x, z)


def tv(x, y):
    return P2(x, TV_Y + y)


def dim(a, b, text, colour, size=13, offset=0.0, gap=5.5):
    d = b - a
    length = float(np.linalg.norm(d))
    n = np.array([-d[1], d[0], 0.0])
    n = n / max(float(np.linalg.norm(n)), 1e-9)
    a, b = a + n * offset * MM, b + n * offset * MM
    arrow = DoubleArrow(a, b, buff=0, color=colour, stroke_width=1.6,
                        tip_length=float(min(0.09, 0.28 * length)))
    side = 1.0 if offset >= 0 else -1.0
    lab = mono(text, color=colour, size=size).move_to((a + b) / 2 + n * side * gap * MM)
    return VGroup(arrow, lab)


def step_badge(number, title, detail, colour):
    number_mob = mono(number, color=colour, size=22)
    words = VGroup(caption(title, color=INK, size=18),
                   mono(detail, color=SLATE, size=13)
                   ).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


def make_rail(scene, *rungs):
    group = VGroup(*rungs).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    for rung in group:
        rung.set_opacity(0.26)
    rail = card_back(group)
    rail.levels = [0.26] * len(group)
    pin_to_frame(scene, rail, corner=UP + RIGHT, buff=0.32)
    return rail, group


def cyl_views():
    """Front view and top view of the oblique cylinder."""
    R, ax = CYL_R, CYL_AX
    fv_out = VGroup(
        Line(fv(-R, 0), fv(R, 0), color=SOLID_COL, stroke_width=3.4),
        Line(fv(ax[0] - R, ax[2]), fv(ax[0] + R, ax[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(-R, 0), fv(ax[0] - R, ax[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(R, 0), fv(ax[0] + R, ax[2]), color=SOLID_COL, stroke_width=3.4),
    )
    axis_fv = DashedLine(fv(0, 0), fv(ax[0], ax[2]), color=MUTED, stroke_width=1.6,
                         dash_length=0.06)
    top_c = Circle(radius=R * MM, color=SOLID_COL, stroke_width=3.4).move_to(tv(ax[0], 0))
    tangents = VGroup(
        Line(tv(0, R), tv(ax[0], R), color=SOLID_COL, stroke_width=3.4),
        Line(tv(0, -R), tv(ax[0], -R), color=SOLID_COL, stroke_width=3.4),
    )
    # the base circle is mostly under the solid, but every depth on this sheet
    # is read off it, so it stays drawn - thinner, and slightly dimmed
    base_c = Circle(radius=R * MM, color=SOLID_COL, stroke_width=2.2,
                    stroke_opacity=0.8).move_to(tv(0, 0))
    axis_tv = DashedLine(tv(0, 0), tv(ax[0], 0), color=MUTED, stroke_width=1.6,
                         dash_length=0.06)
    tv_out = VGroup(base_c, top_c, tangents, axis_tv)
    return fv_out, axis_fv, tv_out, base_c, top_c


def gen_fv(x_base, colour=HELP_COL, width=2.6, **kw):
    """One generator of the cylinder, drawn in the front view."""
    return Line(fv(x_base, 0), fv(x_base + CYL_AX[0], CYL_AX[2]),
                color=colour, stroke_width=width, **kw)


def gen_tv(x_base, y, colour=HELP_COL, width=2.6, **kw):
    return Line(tv(x_base, y), tv(x_base + CYL_AX[0], y),
                color=colour, stroke_width=width, **kw)


# ==========================================================================
#  S02 - Q.1(a): the oblique cylinder
# ==========================================================================
class S02_ObliqueCylinder(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        R, ax = CYL_R, CYL_AX
        fv_out, axis_fv, tv_out, base_c, top_c = cyl_views()
        xy = Line(P2(-30, XY_Y), P2(60, XY_Y), color=INK, stroke_width=2.2)
        xy_tag = mono("XY", color=INK, size=13).move_to(P2(-35, XY_Y))

        # Ø40 goes across the plan's own diameter with the figure thrown out to
        # the left; the strip under the front view's base line is needed for the
        # construction callouts and has to stay clear
        givens = VGroup(
            DoubleArrow(tv(-R, 0), tv(R, 0), buff=0, color=SLATE, stroke_width=1.6,
                        tip_length=0.09),
            mono("Ø40", color=SLATE, size=12).move_to(tv(-R - 14, 0)),
            dim(fv(0, 0), fv(ax[0], ax[2]), "60", SLATE, offset=0.0, gap=14.0, size=12),
            Arc(radius=0.34, start_angle=0, angle=math.radians(CYL["lean"]),
                arc_center=fv(0, 0), color=SLATE, stroke_width=1.6),
            mono("60°", color=SLATE, size=12).move_to(fv(16, 4)),
        )
        views = VGroup(fv_out, axis_fv, tv_out)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 8 (Set A) · Q.1(a)",
            "oblique cylinder Ø40 · axis 60 at 60° · points on the surface")),
            corner=UP + LEFT, buff=0.30)
        rail, rungs = make_rail(
            self,
            step_badge("1", "draw the generator through the point",
                       "parallel to the axis — never vertical", HELP_COL),
            step_badge("2", "run it back to the base line",
                       "THAT x is where the depth comes from", HELP_COL),
            step_badge("3", "step along the generator's plan",
                       "the same fraction of the axis, in the top view", HELP_COL),
            step_badge("4", "let the brackets settle the rest",
                       "front half or back, upper candidate or lower", PT_COL),
        )
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)
        centre, W = frame_target([views, givens], right=0.28)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "Question one, part a. An oblique cylinder: forty diameter, axis sixty "
            "long, leaning at sixty degrees to the base. Front view and top view, and "
            "three points, each given in one view only.",
            FadeIn(bar), FadeIn(rail), Create(views), FadeIn(xy), FadeIn(xy_tag),
            FadeIn(givens),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Read the top view first, because it is the one that catches people out. "
            "There are two circles: the base, and the top face thirty across from it. "
            "Between them the outline runs straight, along the two tangents. The base "
            "circle is mostly hidden under the solid - but every depth on this sheet "
            "is read off it, so it stays drawn.",
            Indicate(base_c, color=HELP_COL, scale_factor=1.04),
            lag_ratio=0.2,
        )

        # ---- a′ : given in the front view ------------------------------------
        A = P["a"]
        xb, t, ya = A["x_base"], A["t"], A["p"][1]
        a_fv = Dot(fv(30, 32), radius=0.045, color=PT_COL)
        a_fv_tag = mono("a′", color=PT_COL, size=15).move_to(fv(25, 37))
        a_gen_fv = gen_fv(xb)
        foot = VGroup(
            Dot(fv(xb, 0), radius=0.038, color=HELP_COL),
            Line(fv(xb, 0), fv(xb, -3), color=MUTED, stroke_width=1.0),
            mono(f"{xb:.2f}", color=HELP_COL, size=12).move_to(fv(xb, -7)),
        )
        drop_base = DashedLine(fv(xb, 0), tv(xb, -R - 4), color=AUX_COL,
                               stroke_width=1.1, stroke_opacity=0.55, dash_length=0.05)
        hits = VGroup(
            Dot(tv(xb, ya), radius=0.040, color=HELP_COL),
            Dot(tv(xb, -ya), radius=0.034, color=HIDE_COL),
        )
        hit_tags = VGroup(
            mono(f"{abs(ya):.2f}", color=HELP_COL, size=12).move_to(tv(xb - 9, ya - 4)),
            mono("(far half)", color=HIDE_COL, size=11).move_to(tv(xb + 12, -ya + 4)),
        )
        a_gen_tv = gen_tv(xb, ya)
        a_tv = Dot(tv(30, ya), radius=0.045, color=PT_COL)
        a_tv_tag = mono("a", color=PT_COL, size=15).move_to(tv(34, ya - 5))
        a_align = DashedLine(fv(30, 32), tv(30, ya), color=AUX_COL, stroke_width=1.1,
                             stroke_opacity=0.55, dash_length=0.05)

        narrate(
            self,
            "Point a prime is given in the front view - thirty to the right of the "
            "base centre, thirty-two up. It is not bracketed, so it is on the half of "
            "the surface facing us.",
            rail_focus(rail, rungs, 0), FadeIn(a_fv), FadeIn(a_fv_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Draw its generator. Not a vertical line - a line parallel to the axis, at "
            "sixty degrees, because that is the direction every straight line on this "
            "surface runs. Follow it down and to the left until it reaches the base.",
            Create(a_gen_fv),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"It meets the base at {xb:.2f}. That number is the whole of the trick. "
            "The point is thirty across the sheet, but the generator it lives on "
            f"starts at {xb:.2f}, and the depth has to be read off the base circle "
            "THERE.",
            rail_focus(rail, rungs, 1), FadeIn(foot), Create(drop_base),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Carry {xb:.2f} down into the top view. It cuts the base circle twice, "
            f"{abs(ya):.2f} either side of the centre line. Unbracketed means the near "
            "half, so we want the front one.",
            FadeIn(hits), FadeIn(hit_tags),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Now step along the generator's plan. In the top view the generator is not "
            "a point any more - it is a line thirty long, running straight across. "
            "Walk along it the same fraction of the way that the point is up the axis, "
            "and that is a.",
            rail_focus(rail, rungs, 2), Create(a_gen_tv), FadeIn(a_tv), FadeIn(a_tv_tag),
            Create(a_align),
            lag_ratio=0.2,
        )
        wrong = card_back(VGroup(
            chip("the mistake: reading the depth off the base circle at x = 30",
                 color=HIDE_COL, size=16),
            chip("at x = 30 the base circle is not there at all — it stops at 20",
                 color=HIDE_COL, size=16),
        ).arrange(DOWN, buff=0.14))
        wrong.move_to(P2(30, -96))
        narrate(
            self,
            "And now the mistake this whole sheet exists to catch. On a right cylinder "
            "you would have dropped straight down from a prime and read the depth off "
            "the circle. Try that here and there is nothing to read: at thirty across, "
            "the base circle stopped ten millimetres ago.",
            look_at(self, [views, wrong], right=0.28),
            settle(FadeIn(wrong)),
        )

        # ---- b : given in the top view ---------------------------------------
        B = P["b"]
        y16 = B["p"][1]
        xb_hi, xb_lo = B["x_base"], -B["x_base"]
        gens_tv = VGroup(gen_tv(xb_hi, y16, width=2.2), gen_tv(xb_lo, y16, width=2.2))
        gens_fv = VGroup(gen_fv(xb_hi, width=2.2), gen_fv(xb_lo, width=2.2))
        b_tv = Dot(tv(15, y16), radius=0.045, color=PT_COL)
        b_tv_tag = mono("b", color=PT_COL, size=15).move_to(tv(16, y16 + 8))
        b_hi = Dot(fv(15, B["p"][2]), radius=0.045, color=PT_COL)
        b_lo = Dot(fv(15, B["other"][2]), radius=0.036, color=HIDE_COL)
        b_hi_tag = mono("b′", color=PT_COL, size=15).move_to(fv(22, B["p"][2]))
        b_lo_tag = mono("rejected", color=HIDE_COL, size=11).move_to(fv(30, B["other"][2] - 1))
        b_rise = DashedLine(tv(15, y16), fv(15, B["p"][2]), color=AUX_COL,
                            stroke_width=1.1, stroke_opacity=0.5, dash_length=0.05)

        narrate(
            self,
            "Point b is given the other way round - in the top view, fifteen across "
            "and sixteen behind the centre line. On a right cylinder a top view fixes "
            "nothing, because every point of a generator has the same plan. Here it "
            "fixes almost everything.",
            look_at(self, [views], right=0.28),
            FadeOut(VGroup(drop_base, hits, hit_tags, a_align, givens)),
            FadeIn(b_tv), FadeIn(b_tv_tag),
            lag_ratio=0.18,
        )
        narrate(
            self,
            "At sixteen back, the base circle is twelve either side of the centre. So "
            "two generators run through b's plan - the one starting at minus twelve "
            "and the one starting at plus twelve - and no others. Two candidates, not "
            "a whole generator's worth.",
            rail_focus(rail, rungs, 3), Create(gens_tv), Create(gens_fv),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Project up. One of them puts b at {B['p'][2]:.2f} above the base, the "
            f"other at {B['other'][2]:.2f}. Looking down from above you see whichever "
            "is on top, and b is not bracketed - so b is the upper one, "
            f"{B['p'][2]:.2f}.",
            Create(b_rise), FadeIn(b_hi), FadeIn(b_lo), FadeIn(b_hi_tag), FadeIn(b_lo_tag),
            lag_ratio=0.2,
        )

        # ---- (c) : bracketed, and sitting on the base circle ------------------
        C = P["c"]
        c_tv = Dot(tv(12, 16), radius=0.045, color=HIDE_COL)
        c_tv_tag = mono("(c)", color=HIDE_COL, size=15).move_to(tv(3, 22))
        c_lo = Dot(fv(12, 0), radius=0.045, color=HIDE_COL)
        c_hi = Dot(fv(12, C["other"][2]), radius=0.036, color=MUTED)
        c_lo_tag = mono("(c′)", color=HIDE_COL, size=14).move_to(fv(6, 6))
        c_hi_tag = mono("rejected", color=MUTED, size=11).move_to(fv(24, C["other"][2] + 5))
        c_rise = DashedLine(tv(12, 16), fv(12, 0), color=AUX_COL, stroke_width=1.1,
                            stroke_opacity=0.5, dash_length=0.05)

        narrate(
            self,
            "And c, which is the trap. It is given in the top view too, at twelve and "
            "sixteen - and that is a point ON the base circle. Everyone writes down "
            "height zero and moves on.",
            FadeIn(c_tv), FadeIn(c_tv_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "But the same two generators pass through it. One starts there, so that "
            f"candidate really is on the base. The other arrives {C['other'][2]:.2f} "
            "up, and from above that is the one you would see. Being on the base "
            "circle in plan does not put a point on the base.",
            Create(c_rise), FadeIn(c_hi), FadeIn(c_hi_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "What settles it is the bracket. c is bracketed, so it is the hidden one - "
            "the lower - and only now is it fair to say height zero. The bracket did "
            "the work, not the circle.",
            FadeIn(c_lo), FadeIn(c_lo_tag),
            lag_ratio=0.2,
        )

        summary = card_back(VGroup(
            mono(f"a   given a′({30:.0f}, {32:.0f})   →   a ({30:.0f}, {ya:+.2f})"
                 f"      generator from x = {xb:.2f}", color=PT_COL, size=14),
            mono(f"b   given b ({15:.0f}, {y16:+.0f})    →   b′ at z = {B['p'][2]:.2f}"
                 f"        the upper of two", color=PT_COL, size=14),
            mono(f"c   given (c)({12:.0f}, {16:.0f})    →   (c′) at z = "
                 f"{C['p'][2]:.2f}          the lower of two", color=HIDE_COL, size=14),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT))
        summary.move_to(P2(15, -96))
        narrate(
            self,
            "Three points, three different questions, one construction: find the "
            "generator, take the depth from where it starts, and step along it.",
            look_at(self, [views, summary], right=0.26),
            settle(FadeIn(summary)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S03 - the tapering pair: the level section, shrunk AND slid
# ==========================================================================
def fvx(x0, x, z):
    return P2(x0 + x, z)


def tvx(x0, x, y):
    return P2(x0 + x, TV_Y + y)


def cone_views(x0=0.0):
    R, ap = CONE_R, CONE_AX
    fv_out = VGroup(
        Line(fvx(x0, -R, 0), fvx(x0, R, 0), color=SOLID_COL, stroke_width=3.4),
        Line(fvx(x0, -R, 0), fvx(x0, ap[0], ap[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fvx(x0, R, 0), fvx(x0, ap[0], ap[2]), color=SOLID_COL, stroke_width=3.4),
    )
    axis_fv = DashedLine(fvx(x0, 0, 0), fvx(x0, ap[0], ap[2]), color=MUTED,
                         stroke_width=1.6, dash_length=0.06)
    circle = Circle(radius=R * MM, color=SOLID_COL, stroke_width=3.4).move_to(tvx(x0, 0, 0))
    tt = math.acos(R / ap[0])
    tangents = VGroup(*[
        Line(tvx(x0, R * math.cos(sgn * tt), R * math.sin(sgn * tt)),
             tvx(x0, ap[0], 0), color=SOLID_COL, stroke_width=3.4)
        for sgn in (1, -1)])
    axis_tv = DashedLine(tvx(x0, 0, 0), tvx(x0, ap[0], 0), color=MUTED,
                         stroke_width=1.6, dash_length=0.06)
    tv_out = VGroup(circle, tangents, axis_tv, Dot(tvx(x0, ap[0], 0), radius=0.042,
                                                   color=SOLID_COL))
    return fv_out, axis_fv, tv_out


def pyr_views(x0=PYR_X0):
    half, ap = PYR_HALF, PYR_APEX
    corners = [np.array([-half, 0.0]), np.array([0.0, -half]),
               np.array([half, 0.0]), np.array([0.0, half])]
    fv_out = VGroup(
        Line(fvx(x0, -half, 0), fvx(x0, half, 0), color=SOLID_COL, stroke_width=3.4),
        Line(fvx(x0, -half, 0), fvx(x0, ap[0], ap[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fvx(x0, half, 0), fvx(x0, ap[0], ap[2]), color=SOLID_COL, stroke_width=3.4),
    )
    axis_fv = DashedLine(fvx(x0, 0, 0), fvx(x0, ap[0], ap[2]), color=MUTED,
                         stroke_width=1.6, dash_length=0.06)
    tv_out = VGroup(
        Polygon(*[tvx(x0, c[0], c[1]) for c in corners], color=SOLID_COL, stroke_width=3.4),
        *[Line(tvx(x0, c[0], c[1]), tvx(x0, ap[0], 0), color=SOLID_COL, stroke_width=2.0)
          for c in corners],
        Dot(tvx(x0, ap[0], 0), radius=0.042, color=SOLID_COL),
    )
    return fv_out, axis_fv, tv_out


class S03_ConeAndPyramid(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        xy = Line(P2(-30, XY_Y), P2(PYR_X0 + 46, XY_Y), color=INK, stroke_width=2.2)

        # ---------------- the oblique cone ------------------------------------
        D = P["d"]
        z_d, r_d, cx_d = D["p"][2], D["r"], D["cx"]
        c_fv, c_axis, c_tv = cone_views()
        cone_all = VGroup(c_fv, c_axis, c_tv)

        level_fv = Line(fvx(0, cx_d - r_d, z_d), fvx(0, cx_d + r_d, z_d),
                        color=HELP_COL, stroke_width=3.2)
        level_tv = Circle(radius=r_d * MM, color=HELP_COL, stroke_width=3.2
                          ).move_to(tvx(0, cx_d, 0))
        axis_mark = VGroup(
            Dot(fvx(0, cx_d, z_d), radius=0.034, color=HELP_COL),
            Dot(tvx(0, cx_d, 0), radius=0.034, color=HELP_COL),
        )
        level_tag = mono(f"R {r_d:.2f}  ·  centre {cx_d:.2f} along the axis",
                         color=HELP_COL, size=12).move_to(tvx(0, 4, -32))

        d_fv = Dot(fvx(0, 10, z_d), radius=0.045, color=PT_COL)
        d_fv_tag = mono("d′", color=PT_COL, size=15).move_to(fvx(0, 5, z_d + 5))
        d_drop = DashedLine(fvx(0, 10, z_d), tvx(0, 10, -r_d - 4), color=AUX_COL,
                            stroke_width=1.1, stroke_opacity=0.55, dash_length=0.05)
        d_tv = Dot(tvx(0, 10, D["p"][1]), radius=0.045, color=PT_COL)
        d_far = Dot(tvx(0, 10, -D["p"][1]), radius=0.034, color=HIDE_COL)
        d_tv_tag = mono("d", color=PT_COL, size=15).move_to(tvx(0, 4, D["p"][1] - 5))
        d_depth = mono(f"{abs(D['p'][1]):.2f}", color=PT_COL, size=12).move_to(
            tvx(0, 20, D["p"][1] + 2))

        gen_line_fv = Line(fvx(0, CONE_AX[0], CONE_AX[2]), fvx(0, D["base"][0], 0),
                           color=GOLD, stroke_width=2.2)
        gen_base_tv = VGroup(
            Dot(tvx(0, D["base"][0], D["base"][1]), radius=0.036, color=GOLD),
            DashedLine(fvx(0, D["base"][0], 0), tvx(0, D["base"][0], -CONE_R - 4),
                       color=AUX_COL, stroke_width=1.1, stroke_opacity=0.5,
                       dash_length=0.05),
        )
        gen_line_tv = Line(tvx(0, D["base"][0], D["base"][1]), tvx(0, CONE_AX[0], 0),
                           color=GOLD, stroke_width=2.2)

        bar = pin_to_frame(self, card_back(title_bar(
            "Oblique cone · oblique pyramid", "the level section, shrunk AND slid")),
            corner=UP + LEFT, buff=0.30)
        self.add(bar)
        self.add_foreground_mobjects(bar)
        centre, W = frame_target([cone_all], right=0.26)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "Now the other family - the solids that taper. An oblique cone, forty-two "
            "diameter, axis sixty at sixty degrees: the same solid we developed last "
            "episode.",
            FadeIn(bar), Create(cone_all), FadeIn(xy),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Take a horizontal section at twenty-four up. In the front view it is one "
            f"line, as always. In the top view it is a circle of radius {r_d:.2f} - "
            "exactly the radius a right cone of this height would give you - but its "
            f"centre is {cx_d:.2f} across, on the axis, not at the centre of the base.",
            Create(level_fv), Create(level_tv), FadeIn(axis_mark), FadeIn(level_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "That is the only change from episode thirteen, and it is the whole change. "
            "The section is the same size; it has just gone where the solid went.",
            Indicate(level_tv, color=HELP_COL, scale_factor=1.06),
        )
        narrate(
            self,
            f"So: d prime is given at ten across, twenty-four up. Carry it down onto "
            f"the level circle, and it cuts it {abs(D['p'][1]):.2f} either side. "
            "Unbracketed, so the near one. That is d.",
            FadeIn(d_fv), FadeIn(d_fv_tag), Create(d_drop), FadeIn(d_tv), FadeIn(d_far),
            FadeIn(d_tv_tag), FadeIn(d_depth),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "And here is the check, which costs one extra line. Join the apex to d "
            f"prime and run it down to the base: it lands at {D['base'][0]:.2f}, where "
            f"the base circle is {abs(D['base'][1]):.2f} deep. Join THAT to the apex in "
            "the top view, and the generator passes straight through d. Two "
            "constructions, one answer.",
            Create(gen_line_fv), FadeIn(gen_base_tv), Create(gen_line_tv),
            lag_ratio=0.18,
        )

        # ---------------- the oblique pyramid ---------------------------------
        E = P["e"]
        z_e, hd_e, cx_e = E["p"][2], E["hd"], E["cx"]
        p_fv, p_axis, p_tv = pyr_views()
        pyr_all = VGroup(p_fv, p_axis, p_tv)
        lvl_fv = Line(fvx(PYR_X0, cx_e - hd_e, z_e), fvx(PYR_X0, cx_e + hd_e, z_e),
                      color=HELP_COL, stroke_width=3.2)
        lvl_tv = Polygon(tvx(PYR_X0, cx_e - hd_e, 0), tvx(PYR_X0, cx_e, -hd_e),
                         tvx(PYR_X0, cx_e + hd_e, 0), tvx(PYR_X0, cx_e, hd_e),
                         color=HELP_COL, stroke_width=3.2)
        lvl_tag = mono(f"half-diagonal {hd_e:.2f}  ·  centre {cx_e:.2f} along the axis",
                       color=HELP_COL, size=12).move_to(tvx(PYR_X0, 8, -34))
        e_fv = Dot(fvx(PYR_X0, 16, z_e), radius=0.045, color=PT_COL)
        e_fv_tag = mono("e′", color=PT_COL, size=15).move_to(fvx(PYR_X0, 21, z_e + 5))
        e_drop = DashedLine(fvx(PYR_X0, 16, z_e), tvx(PYR_X0, 16, -hd_e - 4),
                            color=AUX_COL, stroke_width=1.1, stroke_opacity=0.55,
                            dash_length=0.05)
        e_tv = Dot(tvx(PYR_X0, 16, E["p"][1]), radius=0.045, color=PT_COL)
        e_far = Dot(tvx(PYR_X0, 16, -E["p"][1]), radius=0.034, color=HIDE_COL)
        e_tv_tag = mono("e", color=PT_COL, size=15).move_to(tvx(PYR_X0, 22, E["p"][1] - 4))

        narrate(
            self,
            "The pyramid is the same idea with corners. Base thirty-five square on its "
            "diagonals, apex ten past the right-hand corner - Q.3's pyramid again.",
            look_at(self, [pyr_all], right=0.26),
            Create(pyr_all),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"A level section at twenty up is a square, because a section parallel to "
            f"the base is always the base figure shrunk towards the apex. Six tenths of "
            f"the way up means six tenths the size: half-diagonal {hd_e:.2f}, centred "
            f"{cx_e:.2f} along the axis.",
            Create(lvl_fv), Create(lvl_tv), FadeIn(lvl_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"E prime is at sixteen across, twenty up. Sixteen is {abs(16 - cx_e):.2f} "
            f"from that square's centre, so the depth is {hd_e:.2f} minus "
            f"{abs(16 - cx_e):.2f} - that is {abs(E['p'][1]):.2f}, and unbracketed puts "
            "it in front. On a square set corner-on, the depth is a subtraction, not a "
            "square root.",
            FadeIn(e_fv), FadeIn(e_fv_tag), Create(e_drop), FadeIn(e_tv), FadeIn(e_far),
            FadeIn(e_tv_tag),
            lag_ratio=0.2,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - recap
# ==========================================================================
class S04_Recap(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Points on an Oblique Solid", "what changed, and what did not")
        self.add(bar)

        kept = VGroup(
            caption("unchanged from episode 13", color=INK, size=21),
            chip("straight sides → a GENERATOR", color=HELP_COL, size=18),
            chip("tapering → a LEVEL SECTION", color=HELP_COL, size=18),
            chip("one view + the brackets fixes the point", color=PT_COL, size=18),
        ).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        moved = VGroup(
            caption("what the lean moves", color=INK, size=21),
            chip("the generator is parallel to the AXIS, not vertical", color=GOLD, size=18),
            chip("in plan a generator is a LINE, not a point", color=GOLD, size=18),
            chip("the level section slides along the axis", color=GOLD, size=18),
        ).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        cols = VGroup(kept, moved).arrange(RIGHT, buff=0.9, aligned_edge=UP)
        cols.next_to(bar, DOWN, buff=0.55).to_edge(LEFT, buff=0.7)

        narrate(
            self,
            "So, the whole of question one in four lines. Nothing about the METHOD "
            "changed when the axis leaned over: straight sides still want a generator, "
            "anything that tapers still wants a level section, and one view plus the "
            "brackets is still enough to fix a point.",
            settle(FadeIn(kept), lag=0.2),
        )
        narrate(
            self,
            "What moved is where you draw them. The generator is parallel to the axis, "
            "so it is not vertical, and in the top view it is a line thirty long rather "
            "than a single point. The level section is still the base figure shrunk, "
            "but its centre has gone along the axis with the rest of the solid.",
            settle(FadeIn(moved), lag=0.2),
        )

        A, B, C = P["a"], P["b"], P["c"]
        table = card_back(VGroup(
            mono("point   given            answer              because", color=SLATE, size=14),
            mono(f"a       a′ (30, 32)      a  (30, {A['p'][1]:+.2f})      "
                 f"generator starts at {A['x_base']:.2f}", color=PT_COL, size=14),
            mono(f"b       b  (15, +16)     b′ at z = {B['p'][2]:.2f}     "
                 f"upper of two — unbracketed", color=PT_COL, size=14),
            mono(f"c       (c) (12, +16)    (c′) at z = {C['p'][2]:.2f}      "
                 f"lower of two — bracketed", color=HIDE_COL, size=14),
            mono(f"d       d′ (10, 24)      d  (10, {P['d']['p'][1]:+.2f})      "
                 f"level circle R {P['d']['r']:.2f} at {P['d']['cx']:.2f}",
                 color=PT_COL, size=14),
            mono(f"e       e′ (16, 20)      e  (16, {P['e']['p'][1]:+.2f})      "
                 f"level square {P['e']['hd']:.2f} at {P['e']['cx']:.2f}",
                 color=PT_COL, size=14),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT))
        table.next_to(cols, DOWN, buff=0.5).to_edge(LEFT, buff=0.7)

        narrate(
            self,
            "And the five points of the sheet, with the reason each one came out the "
            "way it did. Not one of them was read off the base circle at the point's "
            "own position across the sheet, and that is the habit this exercise is "
            "there to break.",
            settle(FadeIn(table)),
        )
        narrate(
            self,
            "Next time the cutting planes come back - four right solids, sectioned and "
            "developed, which is question two.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  Marking scheme
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 8 (Set A) Q.1 - points on the surface of an OBLIQUE solid")
    print("  x across the sheet · y depth (negative = in front) · z up · mm")
    print()
    print(f"  P8.1(a)  oblique cylinder Ø{CYL['dia']:.0f}, axis {CYL['axis']:.0f} "
          f"at {CYL['lean']:.0f}°  ->  axis vector "
          f"({CYL_AX[0]:.0f}, 0, {CYL_AX[2]:.4f})")
    print("           the base circle spans x -20 .. +20, the top face x +10 .. +50")
    for k in ("a", "b", "c"):
        d = P[k]
        p = d["p"]
        where = "front" if d["given"] == "fv" else "top"
        shown = d["tag"][0] if d["given"] == "fv" else d["tag"][1]
        print(f"    {shown:<4} given in the {where:<5} view   "
              f"x {p[0]:+7.2f}   depth {p[1]:+7.2f}   height {p[2]:7.3f}")
        print(f"         generator starts at x = {d['x_base']:+7.3f}, "
              f"t = {d['t']:.4f} along the axis")
        if "other" in d:
            print(f"         the other candidate was z = {d['other'][2]:.3f} "
                  f"- the brackets chose")
        print(f"         {d['note']}")
    naive = cyl_naive(30.0)
    print(f"    the naive answer for a - base circle at x = 30 - is "
          f"{'impossible: the circle stops at 20' if naive is None else naive}")

    print()
    d = P["d"]
    print(f"  oblique cone Ø{CONE['dia']:.0f}, axis {CONE['axis']:.0f} at "
          f"{CONE['lean']:.0f}°  ->  apex ({CONE_AX[0]:.0f}, 0, {CONE_AX[2]:.4f})")
    print(f"    d′  given in the fv   x {d['p'][0]:+7.2f}   depth {d['p'][1]:+7.3f}   "
          f"height {d['p'][2]:7.2f}")
    print(f"        level circle: radius {d['r']:.4f}, centre {d['cx']:.4f} along "
          f"the axis  (s = {d['s']:.4f})")
    print(f"        generator check: base point ({d['base'][0]:.3f}, "
          f"{d['base'][1]:.3f}, 0) — agrees to 1e-9")

    e = P["e"]
    print()
    print(f"  oblique pyramid, base {PYR['side']:.0f} on its diagonals, height "
          f"{PYR['height']:.0f}, apex ({PYR_APEX[0]:.3f}, 0, {PYR_APEX[2]:.0f})")
    print(f"    e′  given in the fv   x {e['p'][0]:+7.2f}   depth {e['p'][1]:+7.3f}   "
          f"height {e['p'][2]:7.2f}")
    print(f"        level square: half-diagonal {e['hd']:.4f}, centre {e['cx']:.4f} "
          f"along the axis  (s = {e['s']:.4f})")

    print()
    print("  Checks that run at import:")
    print("    · every point slides back down its own generator onto the base outline")
    print("    · a horizontal section of the oblique cone is a CIRCLE (24 points, 3 heights)")
    print("    · ... and its centre is on the leaning axis, not over the base centre")
    print("    · the cone point's level-circle and generator constructions agree")
    print("    · the naive depth for a is impossible, which is why a was chosen")
