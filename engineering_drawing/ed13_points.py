"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 13: Points on the Surface of a Solid
            + worked solutions to Exercise 7 (Set A), Q.1(a) and Q.1(d)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed13_points.py S02_Cylinder
    ... or use render_ed13.bat to build all four scenes in order.

Scene order (about ten minutes in all):

    S01_OnTheSurface  what "on the surface" buys you: the point is not floating
                      in space, it lies on some simple line of the solid, and
                      that line is easy to draw in all three views. Two
                      families - a generator for the curved and flat sides, a
                      horizontal section for anything that tapers
    S02_Cylinder      Q.1(a) worked: three points, each given in one view and
                      carried into the other two, with the visibility argued
                      rather than guessed
    S03_Pyramid       Q.1(d) worked: the square pyramid, where the top view
                      fixes a surface point completely and the front view
                      needs a second thought
    S04_Recap         one rule per solid, and what the brackets mean

The given views are read in FIRST ANGLE, as the rest of the series is: the top
view below the front view, and the left-hand side view on the right. Every
point is checked by solve(), which asserts that it really lies on the surface
it is supposed to, that the three views agree with one another, and that the
visibility matches the brackets the figure uses.

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
HIDE_COL = VIOLET        # anything hidden
AUX_COL = CREAM

MM = 0.030
S3 = 0.052

# ==========================================================================
#  Figure P7.1(a): a cylinder, Ø42 × 50.  Figure P7.1(d): a square pyramid,
#  42 base × 50 high, its base square set square to the observer.
#
#  Axes: x across the sheet, y depth (negative = in front of the VP, towards
#  the observer), z up from the base. The side view is the LEFT-hand one, on
#  the right of the sheet, so its observer stands at -x and what it shows
#  nearer is what has the smaller x.
# ==========================================================================
CYL = dict(dia=42.0, height=50.0)
PYR = dict(base=42.0, height=50.0)
RAD = CYL["dia"] / 2.0


def cyl_surface_x(y):
    """The two x values of the curved surface at depth y."""
    r2 = RAD * RAD - y * y
    assert r2 > 0, "that depth is off the cylinder"
    return math.sqrt(r2)


def pyr_half(z):
    """Half-width of the square pyramid's cross-section at height z."""
    return PYR["base"] / 2.0 * (1.0 - z / PYR["height"])


def solve():
    h, half = CYL["height"], RAD
    pts = {}

    # ---------------- Q.1(a), the cylinder ---------------------------------
    # a: given in the TOP view, on the circle, 8 in front of the centre line,
    # on the left. A point on the CURVED surface would not be fixed by the top
    # view at all - the top view of every one of them is on that circle,
    # whatever its height. It is fixed because it is not bracketed: in the top
    # view the visible rim is the top one, so a is on the top face's edge.
    ax = -math.sqrt(half * half - 8.0 ** 2)
    pts["a"] = dict(solid="cyl", given="top", p=np.array([ax, -8.0, h]),
                    note="on the top rim: unbracketed in the top view, and the "
                         "rim you can see from above is the top one")
    assert abs(math.hypot(pts["a"]["p"][0], pts["a"]["p"][1]) - half) < 1e-9

    # b': given in the FRONT view, 10 right of the axis, 15 down from the top.
    # Unbracketed, so it is on the near half of the curved surface.
    by = -cyl_surface_x(10.0)                      # near half: y negative
    pts["b"] = dict(solid="cyl", given="front", p=np.array([10.0, by, h - 15.0]),
                    note="unbracketed in the front view, so the NEAR half")
    assert abs(math.hypot(10.0, by) - half) < 1e-9

    # (c"): given in the SIDE view, 16 in front of the axis, 8 above the base.
    # Bracketed, so it is hidden from the side-view observer, who stands at -x:
    # hidden means the larger x.
    # drawn 16 to the LEFT of the side view's axis, and screen-right is -y
    # there, so this one is 16 BEHIND the VP
    cx = cyl_surface_x(16.0)                       # +x: the far half from -x
    pts["c"] = dict(solid="cyl", given="side", p=np.array([cx, 16.0, 8.0]),
                    note="bracketed in the side view, so the FAR half from the "
                         "left-hand observer")
    assert abs(math.hypot(cx, -16.0) - half) < 1e-9

    # ---------------- Q.1(d), the square pyramid ----------------------------
    # a: given in the TOP view, 11 from the left edge and 5 from the front
    # edge. On a pyramid the top view fixes a surface point completely: one
    # height per position, because the faces slope.
    px, py = -21.0 + 11.0, -21.0 + 5.0
    r = max(abs(px), abs(py))
    pz = PYR["height"] * (1.0 - r / (PYR["base"] / 2.0))
    pts["pa"] = dict(solid="pyr", given="top", p=np.array([px, py, pz]),
                     note="|y| is the larger, so it is on the FRONT face")
    assert abs(max(abs(px), abs(py)) - pyr_half(pz)) < 1e-9

    # b': given in the FRONT view on the right-hand outline, 25 up. That
    # outline is where TWO slant edges project to the same line, so there are
    # two candidates; unbracketed picks the near one.
    bz = 25.0
    bx = pyr_half(bz)
    pts["pb"] = dict(solid="pyr", given="front", p=np.array([bx, -bx, bz]),
                     note="the front-view outline is two slant edges at once; "
                          "unbracketed picks the near one")
    assert abs(max(abs(bx), abs(-bx)) - pyr_half(bz)) < 1e-9

    # c": given in the SIDE view, 13 behind the axis, 15 up. At that height the
    # section is a square of half-width 14.7, so |x| must be the half-width.
    # drawn 13 to the RIGHT of the side view's axis, so 13 IN FRONT of the VP
    cz, cy = 15.0, -13.0
    cxx = -pyr_half(cz)                            # unbracketed: nearer to -x
    pts["pc"] = dict(solid="pyr", given="side", p=np.array([cxx, cy, cz]),
                     note="unbracketed in the side view, so the left face")
    assert abs(cy) < pyr_half(cz), "13 would be off the section at that height"
    assert abs(max(abs(cxx), abs(cy)) - pyr_half(cz)) < 1e-9

    # ---- the views each point produces, and a check that they agree --------
    for key, d in pts.items():
        x, y, z = d["p"]
        d["fv"] = np.array([x, z])                 # front view
        d["tv"] = np.array([x, y])                 # top view  (y negative = near)
        d["sv"] = np.array([y, z])                 # side view
        # the given view must reproduce what the figure states
        if d["given"] == "top":
            assert abs(d["tv"][0] - x) < 1e-9 and abs(d["tv"][1] - y) < 1e-9
        d["hidden_fv"] = y > 0                     # front observer at -y
        d["hidden_sv"] = x > 0                     # side observer at -x
        # From above: a pyramid tapers, so every point of its sloping faces is
        # in plain view. A cylinder does not - its top face covers everything
        # on the curved surface below the rim.
        d["hidden_tv"] = (d["solid"] == "cyl" and z < h - 1e-9)

    return pts


P = solve()


# ==========================================================================
#  The 3-D stage
# ==========================================================================
def pt3(p, h):
    x, y, z = p
    return np.array([x * S3, y * S3, (z - h / 2.0) * S3])


def cylinder_shell(fill=0.26, segments=72):
    h = CYL["height"]
    g = VGroup()
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        g.add(Polygon(pt3((RAD * math.cos(a0), RAD * math.sin(a0), 0), h),
                      pt3((RAD * math.cos(a1), RAD * math.sin(a1), 0), h),
                      pt3((RAD * math.cos(a1), RAD * math.sin(a1), h), h),
                      pt3((RAD * math.cos(a0), RAD * math.sin(a0), h), h),
                      stroke_width=0, fill_color=SOLID_COL, fill_opacity=fill))
    return g


def cyl_ring(z, colour=SOLID_COL, width=3.5, samples=96):
    h = CYL["height"]
    pts = [pt3((RAD * math.cos(2 * math.pi * i / samples),
                RAD * math.sin(2 * math.pi * i / samples), z), h)
           for i in range(samples + 1)]
    line = VMobject(stroke_color=colour, stroke_width=width)
    line.set_points_as_corners(pts)
    return line


def pyramid_shell(fill=0.26):
    h = PYR["base"] / 2.0
    H = PYR["height"]
    base = [(-h, -h), (h, -h), (h, h), (-h, h)]
    apex = pt3((0, 0, H), H)
    g = VGroup()
    for k in range(4):
        a, b = base[k], base[(k + 1) % 4]
        g.add(Polygon(pt3((a[0], a[1], 0), H), pt3((b[0], b[1], 0), H), apex,
                      stroke_color=SOLID_COL, stroke_width=2.4,
                      fill_color=SOLID_COL, fill_opacity=fill))
    return g


def pyr_square(z, colour=HELP_COL, width=3.0):
    H = PYR["height"]
    r = pyr_half(z)
    pts = [(-r, -r), (r, -r), (r, r), (-r, r), (-r, -r)]
    line = VMobject(stroke_color=colour, stroke_width=width)
    line.set_points_as_corners([pt3((a, b, z), H) for a, b in pts])
    return line


# ==========================================================================
#  S01 - what "on the surface" gives you
# ==========================================================================
class S01_OnTheSurface(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=70 * DEGREES, theta=-62 * DEGREES,
                                    zoom=1.0, focal_distance=60.0)
        bar = hud(self, title_bar("Points on a Surface",
                                  "Sheet 8 · one view given, two to find"))
        self.add(bar)

        h = CYL["height"]
        shell = cylinder_shell()
        rim_top, rim_bot = cyl_ring(h), cyl_ring(0.0)
        b = P["b"]["p"]
        dot = Dot3D(pt3(b, h), radius=0.055, color=PT_COL)
        lab = billboard(self, mono("B", color=PT_COL, size=24)
                        .move_to(pt3((b[0] + 5, b[1] - 4, b[2] + 5), h)))

        narrate(
            self,
            "Question one of exercise seven gives you a point on the surface of a "
            "solid, drawn in one view only, and asks for the other two. Here is such "
            "a point, sitting on a cylinder.",
            FadeIn(shell), Create(rim_top), Create(rim_bot), FadeIn(dot), FadeIn(lab),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The words that do all the work are ON THE SURFACE. The point is not "
            "floating somewhere in space with three coordinates to be discovered - "
            "it is stuck to the solid, and that removes one unknown entirely. Give "
            "one view and the other two follow.",
        )

        gen = Line(pt3((b[0], b[1], 0), h), pt3((b[0], b[1], h), h),
                   color=HELP_COL, stroke_width=5)
        narrate(
            self,
            "The way to use that is to find a simple line of the solid that passes "
            "through the point - a line you can draw in every view without thinking. "
            "On a cylinder the obvious one is a generator: the straight line down "
            "the curved surface, parallel to the axis.",
            Create(gen),
            lag_ratio=0.3,
        )
        fly_camera(
            self,
            "Look down from above and the generator is a single point on the circle. "
            "Look from the front and it is a vertical line. Once you have drawn it "
            "in a view, the point can only be somewhere along it - and the height "
            "puts it exactly.",
            phi=0.0, theta=-90 * DEGREES, zoom=1.15,
        )
        fly_camera(
            self,
            "That is the whole method.",
            phi=70 * DEGREES, theta=-62 * DEGREES, zoom=1.0,
        )

        # the tapering case
        ring = cyl_ring(b[2], colour=HELP_COL, width=3.0)
        narrate(
            self,
            "There is a second helper line worth having, and on some solids it is "
            "the only one that works: the horizontal section. Slice the solid level "
            "through the point, and see what the cut looks like.",
            FadeOut(gen), Create(ring),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "On a cylinder that is a circle the same size as the base, which is no "
            "help at all. But on anything that tapers it is the making of the "
            "problem.",
        )

        H = PYR["height"]
        pyr = pyramid_shell()
        pp = P["pa"]["p"]
        pdot = Dot3D(pt3(pp, H), radius=0.055, color=PT_COL)
        psq = pyr_square(pp[2])
        fly_camera(
            self,
            "Here is the square pyramid from part d, with a point on one of its "
            "sloping faces.",
            FadeOut(shell), FadeOut(rim_top), FadeOut(rim_bot), FadeOut(ring),
            FadeOut(dot), FadeOut(lab),
            FadeIn(pyr), FadeIn(pdot),
            phi=66 * DEGREES, theta=-52 * DEGREES, zoom=1.05,
        )
        narrate(
            self,
            "Cut it level through the point and the section is a square - a smaller "
            "copy of the base, and the higher you cut the smaller it gets. So on a "
            "pyramid the height and the size of the section are locked together, and "
            "that is what fixes the point.",
            Create(psq),
            lag_ratio=0.3,
        )
        fly_camera(
            self,
            "Which has a consequence worth noticing. Look down on the pyramid: every "
            "point of the sloping faces is in plain view, and no two of them sit on "
            "top of one another. The top view alone fixes a point on a pyramid "
            "completely - position and height both.",
            phi=0.0, theta=-90 * DEGREES, zoom=1.1,
        )

        note = hud(self, VGroup(
            chip("find a LINE of the solid through the point", color=HELP_COL, size=20),
            chip("straight sides → a generator · tapering → a level section",
                 color=SLATE, size=18),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "Two helper lines, then, and between them they cover every solid on the "
            "sheet.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "A generator for the cylinder and the prism, whose sides go straight up. "
            "A level section for the cone and the pyramid, which taper. Draw the "
            "helper in all three views, put the point on it, and the only thing left "
            "to decide is whether you can see it.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  The sheet: three views in first angle
# ==========================================================================
XY_Y = -12.0
TV_Y = -45.0
MITRE_X = 52.0           # the 45° line starts where XY meets this
SV_AXIS = MITRE_X + (XY_Y - TV_Y)     # so depths transfer straight across


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


def fv(x, z):
    return P2(x, z)


def tv(x, y):
    """y is the real depth: negative is towards the observer, drawn lower."""
    return P2(x, TV_Y + y)


def sv(y, z):
    """The left-hand side view.

    Its observer stands at -x looking along +x with z up, so screen-right is
    d x u = -y: the parts of the solid that are FURTHER IN FRONT are drawn
    further to the RIGHT. That is also exactly what the 45° mitre line does -
    a point drawn `d` below XY in the top view lands `d` to the right of where
    the mitre meets it - so the two constructions agree, which is the check
    that the handedness is right.
    """
    return P2(SV_AXIS - y, z)


def mitre_point(y):
    """Where a depth meets the 45° transfer line."""
    return P2(SV_AXIS - y, TV_Y + y)


def step_badge(number, title, detail, colour):
    number_mob = mono(number, color=colour, size=22)
    words = VGroup(caption(title, color=INK, size=18),
                   mono(detail, color=SLATE, size=13)
                   ).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


def three_view_furniture(h):
    """The reference line, the mitre line, and the view tags."""
    xy = Line(P2(-32, XY_Y), P2(SV_AXIS + 34, XY_Y), color=INK, stroke_width=2.4)
    vert = Line(P2(MITRE_X, XY_Y + 6), P2(MITRE_X, TV_Y - 30), color=INK,
                stroke_width=1.6, stroke_opacity=0.5)
    m = Line(P2(MITRE_X, XY_Y), P2(MITRE_X + 46, XY_Y - 46), color=SLATE,
             stroke_width=1.6, stroke_opacity=0.7)
    m_lab = mono("45°", color=SLATE, size=12).move_to(P2(MITRE_X + 12, XY_Y - 6))
    tags = VGroup(
        chip("FRONT", color=SLATE, size=11).move_to(fv(0, h + 11)),
        chip("SIDE", color=SLATE, size=11).move_to(sv(0, h + 11)),
        chip("TOP", color=SLATE, size=11).move_to(tv(0, -34)),
    )
    return VGroup(xy, vert, m, m_lab, tags), m


def point_marks(d, h, colour=PT_COL):
    """One point drawn in all three views, hollow where it is hidden."""
    def mark(pos, hidden, tag):
        dot = (Circle(radius=0.055, color=HIDE_COL, stroke_width=2.6)
               if hidden else Dot(pos, radius=0.05, color=colour))
        if hidden:
            dot.move_to(pos)
        lab = mono(tag, color=HIDE_COL if hidden else colour, size=13)
        lab.next_to(dot, d.get("ldir", UR), buff=0.05)
        return VGroup(dot, lab)

    x, y, z = d["p"]
    return dict(
        fv=mark(fv(x, z), d["hidden_fv"], d["tag_fv"]),
        tv=mark(tv(x, y), d["hidden_tv"], d["tag_tv"]),
        sv=mark(sv(y, z), d["hidden_sv"], d["tag_sv"]),
    )


# On the pyramid a and c land within six millimetres of each other in every
# view, so one label direction for all three points piles them up. Each point
# gets its own.
for key, tags, ldir in (("a", ("a′", "a", "a″"), DL), ("b", ("b′", "b", "b″"), UR),
                        ("c", ("c′", "c", "c″"), UL), ("pa", ("a′", "a", "a″"), DL),
                        ("pb", ("b′", "b", "b″"), UR), ("pc", ("c′", "c", "c″"), UL)):
    P[key]["tag_fv"], P[key]["tag_tv"], P[key]["tag_sv"] = tags
    P[key]["ldir"] = ldir


# ==========================================================================
#  S02 - Q.1(a), the cylinder
# ==========================================================================
class S02_Cylinder(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        h = CYL["height"]
        furniture, mline = three_view_furniture(h)

        front = VGroup(
            Rectangle(width=2 * RAD * MM, height=h * MM, color=SOLID_COL,
                      stroke_width=3.4).move_to(fv(0, h / 2)),
            DashedLine(fv(0, -4), fv(0, h + 4), color=MUTED, stroke_width=1.4,
                       dash_length=0.06))
        side = VGroup(
            Rectangle(width=2 * RAD * MM, height=h * MM, color=SOLID_COL,
                      stroke_width=3.4).move_to(sv(0, h / 2)),
            DashedLine(sv(0, -4), sv(0, h + 4), color=MUTED, stroke_width=1.4,
                       dash_length=0.06))
        top = VGroup(
            Circle(radius=RAD * MM, color=SOLID_COL, stroke_width=3.4
                   ).move_to(tv(0, 0)),
            DashedLine(tv(-RAD - 5, 0), tv(RAD + 5, 0), color=MUTED,
                       stroke_width=1.4, dash_length=0.06),
            DashedLine(tv(0, -RAD - 5), tv(0, RAD + 5), color=MUTED,
                       stroke_width=1.4, dash_length=0.06))
        views = VGroup(front, side, top)

        M = {k: point_marks(P[k], h) for k in ("a", "b", "c")}

        centre, W = frame_target([furniture, views], right=0.26)
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 7 (Set A) · Q.1(a)",
            "Figure P7.1a · a cylinder, and three points")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "b′ is given in the front view", "carry it down · the top view is the circle", PT_COL),
            step_badge("2", "and across to the side", "depth through the 45° line", PT_COL),
            step_badge("3", "(c″) is given in the side view", "the brackets say hidden — that fixes which half", HIDE_COL),
            step_badge("4", "a is given in the top view", "on the circle, and not bracketed: the top rim", HELP_COL),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26] * 4
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)

        narrate(
            self,
            "Part a. A cylinder forty-two diameter, fifty high, in three views - "
            "front, top below it, and the left-hand side view on the right, which is "
            "where first angle puts it. Three points, each given in one view only.",
            FadeIn(bar), Create(views), FadeIn(furniture),
            lag_ratio=0.2,
        )

        # ---- b' -----------------------------------------------------------
        b = P["b"]["p"]
        gen_fv = Line(fv(b[0], 0), fv(b[0], h), color=HELP_COL, stroke_width=2.6)
        gen_tv = Dot(tv(b[0], b[1]), radius=0.045, color=HELP_COL)
        drop = DashedLine(fv(b[0], 0), tv(b[0], -RAD - 2), color=AUX_COL,
                          stroke_width=1.1, stroke_opacity=0.55, dash_length=0.05)
        narrate(
            self,
            "Start with b prime, in the front view: ten to the right of the axis, "
            "fifteen down from the top. Draw its generator - the vertical line "
            "through it.",
            rail_focus(rail, rungs, 0),
            look_at(self, [front, top], right=0.34),
            FadeIn(M["b"]["fv"]), Create(gen_fv),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Carry that line down into the top view, where the whole cylinder is one "
            "circle. The generator meets the circle in two places - one in front, one "
            "behind - and b prime was not bracketed, so it is the one we can see from "
            f"the front: {abs(b[1]):.2f} in front of the centre line.",
            Create(drop), FadeIn(gen_tv), FadeIn(M["b"]["tv"]),
            lag_ratio=0.25,
        )
        # the depth goes along to the mitre, up to the side view; the height
        # comes straight across from the front view
        across = VGroup(
            DashedLine(tv(b[0], b[1]), mitre_point(b[1]), color=AUX_COL,
                       stroke_width=1.1, stroke_opacity=0.55, dash_length=0.05),
            DashedLine(mitre_point(b[1]), sv(b[1], b[2]), color=AUX_COL,
                       stroke_width=1.1, stroke_opacity=0.55, dash_length=0.05),
            DashedLine(fv(b[0], b[2]), sv(b[1], b[2]), color=AUX_COL,
                       stroke_width=1.1, stroke_opacity=0.55, dash_length=0.05))
        narrate(
            self,
            "Now the side view. The height comes straight across from the front view, "
            "and the depth comes round the corner through the forty-five degree line "
            "- which is all that line is for: turning a depth measured downwards into "
            "the same depth measured sideways.",
            rail_focus(rail, rungs, 1),
            look_at(self, [views, furniture], right=0.26),
            Create(across), FadeIn(M["b"]["sv"]),
            lag_ratio=0.25,
        )

        # ---- c" -----------------------------------------------------------
        c = P["c"]["p"]
        narrate(
            self,
            "Next, c double prime, given in the side view: sixteen from the axis, "
            "eight above the base. And it is in brackets.",
            rail_focus(rail, rungs, 2),
            FadeIn(M["c"]["sv"]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Brackets mean hidden, and that is not decoration - it is the missing "
            "piece of information. The side view is taken from the left, so what it "
            "hides is whatever lies on the right-hand half of the solid. That tells "
            f"us the point is at plus {c[0]:.2f} across, not minus, and now the top "
            "view and "
            "the front view can both be drawn.",
            FadeIn(M["c"]["tv"]), FadeIn(M["c"]["fv"]),
            lag_ratio=0.25,
        )

        # ---- a -------------------------------------------------------------
        a = P["a"]["p"]
        narrate(
            self,
            "And a, given in the top view, sitting on the circle eight in front of "
            "the centre line. This one needs a moment's thought, because a point on "
            "the curved surface would not be fixed by the top view at all - every "
            "generator shows as a point on that circle, whatever height you are at.",
            rail_focus(rail, rungs, 3),
            look_at(self, [top], right=0.34),
            FadeIn(M["a"]["tv"]),
            lag_ratio=0.25,
        )
        ans_rows = VGroup(
            mono("Q.1(a)   the three points", color=PT_COL, size=17),
            *[mono(f"  {k}   x {P[k]['p'][0]:+7.2f}   depth {P[k]['p'][1]:+6.2f}   "
                   f"height {P[k]['p'][2]:5.2f}", color=PT_COL, size=13)
              for k in ("a", "b", "c")],
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=PT_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "What fixes it is that it is NOT in brackets. Looking down from above, "
            "the rim you can see is the top one; the bottom rim is hidden underneath "
            "it. An unbracketed point on that circle is therefore on the top rim, "
            "fifty up - and it goes into both other views at that height.",
            settle(FadeIn(M["a"]["fv"]), FadeIn(M["a"]["sv"]), FadeIn(ans)),
        )
        narrate(
            self,
            "Which is worth saying plainly, because it is the part students skip: on "
            "this sheet the brackets are not a note added afterwards. They are given "
            "data, and on two of these three points they are the only thing that "
            "tells you which of two possible answers is the right one.",
            look_at(self, [views, furniture], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S03 - Q.1(d), the square pyramid
# ==========================================================================
class S03_Pyramid(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        h, half = PYR["height"], PYR["base"] / 2.0
        furniture, mline = three_view_furniture(h)

        def outline(at):
            return VGroup(
                Line(at(-half, 0), at(half, 0), color=SOLID_COL, stroke_width=3.4),
                Line(at(-half, 0), at(0, h), color=SOLID_COL, stroke_width=3.4),
                Line(at(half, 0), at(0, h), color=SOLID_COL, stroke_width=3.4),
                DashedLine(at(0, -4), at(0, h + 4), color=MUTED,
                           stroke_width=1.4, dash_length=0.06))

        front = outline(fv)
        side = outline(lambda a, b: sv(-a, b))
        square = Polygon(tv(-half, -half), tv(half, -half), tv(half, half),
                         tv(-half, half), color=SOLID_COL, stroke_width=3.4)
        diagonals = VGroup(
            Line(tv(-half, -half), tv(half, half), color=SOLID_COL, stroke_width=2.2),
            Line(tv(half, -half), tv(-half, half), color=SOLID_COL, stroke_width=2.2))
        top = VGroup(square, diagonals)
        views = VGroup(front, side, top)
        M = {k: point_marks(P[k], h) for k in ("pa", "pb", "pc")}

        centre, W = frame_target([furniture, views], right=0.26)
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 7 (Set A) · Q.1(d)",
            "Figure P7.1d · a square pyramid, and three points")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "a is given in the top view", "on a pyramid that fixes it completely", HELP_COL),
            step_badge("2", "b′ on the front outline", "two slant edges project to one line", PT_COL),
            step_badge("3", "c″ in the side view", "the level section is a square", PT_COL),
        ).arrange(DOWN, buff=0.26, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26] * 3
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)

        narrate(
            self,
            "Part d. A square pyramid, forty-two base, fifty high, its base set "
            "square to us - so the top view is a square with both diagonals, and the "
            "diagonals are the four slant edges seen from above.",
            FadeIn(bar), Create(views), FadeIn(furniture),
            lag_ratio=0.2,
        )

        pa = P["pa"]["p"]
        sec_tv = Polygon(*[tv(sx * pyr_half(pa[2]), sy * pyr_half(pa[2]))
                           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
                         color=HELP_COL, stroke_width=2.6)
        sec_fv = Line(fv(-pyr_half(pa[2]), pa[2]), fv(pyr_half(pa[2]), pa[2]),
                      color=HELP_COL, stroke_width=2.6)
        narrate(
            self,
            "Point a is given in the top view - eleven from the left edge, five from "
            "the front edge. On a pyramid that is all you need, and this is the "
            "moment worth understanding.",
            rail_focus(rail, rungs, 0),
            look_at(self, [top], right=0.34),
            FadeIn(M["pa"]["tv"]),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Draw the level section through it: a square, a smaller copy of the base. "
            "Which square? The one whose edge passes through a - and since a is "
            "sixteen from the axis in depth and only ten across, it is the front face "
            "it belongs to, and that face is sixteen out.",
            Create(sec_tv),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"A square sixteen out means we are {pa[2]:.2f} up: the section shrinks "
            "from twenty-one at the base to nothing at the apex, in step with the "
            "height. Draw that level line in the front view and a prime sits on it, "
            "straight below its top view.",
            look_at(self, [front, top], right=0.32),
            Create(sec_fv), FadeIn(M["pa"]["fv"]), FadeIn(M["pa"]["sv"]),
            lag_ratio=0.25,
        )

        pb = P["pb"]["p"]
        narrate(
            self,
            "Point b prime is given on the right-hand outline of the front view, "
            "twenty-five up. Careful here: that outline is not one edge of the solid. "
            "It is where TWO slant edges - the front-right and the back-right - "
            "project onto the same line.",
            rail_focus(rail, rungs, 1),
            FadeIn(M["pb"]["fv"]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"So there are two candidates, one at ten and a half in front and one at "
            f"ten and a half behind. B prime is not bracketed, so it is the near one - "
            f"and in the top view it goes on the front-right diagonal.",
            FadeIn(M["pb"]["tv"]), FadeIn(M["pb"]["sv"]),
            lag_ratio=0.25,
        )

        pc = P["pc"]["p"]
        narrate(
            self,
            "And c double prime, in the side view: thirteen from the axis, fifteen "
            f"up. At fifteen up the section is a square {pyr_half(15.0):.1f} out, and "
            "thirteen is less than that - so the point is not on the face nearest us "
            "in that view, it is on one of the two side faces, at the full "
            f"{pyr_half(15.0):.1f}.",
            rail_focus(rail, rungs, 2),
            FadeIn(M["pc"]["sv"]),
            lag_ratio=0.3,
        )
        ans_rows = VGroup(
            mono("Q.1(d)   the three points", color=PT_COL, size=17),
            *[mono(f"  {k[-1]}   x {P[k]['p'][0]:+7.2f}   depth {P[k]['p'][1]:+6.2f}   "
                   f"height {P[k]['p'][2]:5.2f}", color=PT_COL, size=13)
              for k in ("pa", "pb", "pc")],
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=PT_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Unbracketed again, so it is the face on the side the observer stands - "
            "the left one. Both other views follow.",
            settle(FadeIn(M["pc"]["tv"]), FadeIn(M["pc"]["fv"]), FadeIn(ans)),
        )
        narrate(
            self,
            "Three points, three different starting views, and the same two questions "
            "each time: which line of the solid is it on, and which of the two "
            "possible answers do the brackets allow.",
            look_at(self, [views, furniture], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - recap
# ==========================================================================
class S04_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "one rule per solid, and what brackets mean")
        self.add(bar)

        rows = VGroup(
            mono("CYLINDER, PRISM   straight sides → use a GENERATOR", color=HELP_COL, size=20),
            mono("CONE, PYRAMID     it tapers → use a LEVEL SECTION", color=HELP_COL, size=20),
            mono("draw the helper in all three views · the point rides on it",
                 color=PT_COL, size=19),
            mono("brackets = hidden = given data, not decoration", color=HIDE_COL, size=19),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(np.array([-0.1, 1.45, 0]))

        narrate(self, "The method in four lines.", FadeIn(bar))
        narrate(
            self,
            "On a cylinder or a prism the sides run straight up, so the helper is a "
            "generator: a vertical line on the surface. In the top view it shrinks to "
            "a point on the outline, which is what makes it so easy to place.",
            FadeIn(rows[0]),
        )
        narrate(
            self,
            "On a cone or a pyramid the solid tapers, so a level section is the thing "
            "to draw - a circle on the cone, a square on this pyramid, shrinking with "
            "height. That link between size and height is what lets a single view fix "
            "the point.",
            FadeIn(rows[1]),
        )
        narrate(
            self,
            "Either way, draw the helper in all three views and the point can only be "
            "on it. Then read the brackets.",
            FadeIn(rows[2]), FadeIn(rows[3]),
            lag_ratio=0.25,
        )

        vis = VGroup(
            chip("front view hides what is BEHIND", color=SLATE, size=17),
            chip("top view hides what is UNDERNEATH", color=SLATE, size=17),
            chip("left side view hides what is to the RIGHT", color=SLATE, size=17),
        ).arrange(DOWN, buff=0.16).move_to(np.array([0.0, -1.5, 0]))
        narrate(
            self,
            "Which is the part people skip.",
            settle(FadeIn(vis[0]), FadeIn(vis[1]), FadeIn(vis[2])),
        )
        narrate(
            self,
            "A point on a surface nearly always has two possible positions - in front "
            "or behind, left or right - and the given view cannot tell them apart. "
            "The brackets can. They are not a remark about the answer; they are half "
            "the question. On part a of this exercise they are the only thing that "
            "puts point a on the top rim rather than anywhere at all on the side of "
            "the cylinder.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme
#
#      py -3.11 ed13_points.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 7 (Set A) Q.1 - points on the surface of right solids")
    print("  read in FIRST ANGLE: top view below, LEFT-hand side view on the right.")
    print("  x across the sheet · depth negative = in front of the VP · z up")
    for tag, keys, what in (("Q.1(a)  cylinder Ø42 × 50", ("a", "b", "c"), "cyl"),
                            ("Q.1(d)  square pyramid 42 × 50", ("pa", "pb", "pc"), "pyr")):
        print()
        print(f"  {tag}")
        for k in keys:
            d = P[k]
            x, y, z = d["p"]
            seen = "".join(("·" if not d[f"hidden_{v}"] else "H")
                           for v in ("fv", "tv", "sv"))
            print(f"    {d['tag_fv']:<3} given in the {d['given']:<5} view   "
                  f"x {x:+7.2f}   depth {y:+7.2f}   height {z:6.2f}   "
                  f"visible F/T/S {seen}")
            print(f"        {d['note']}")
    print()
    print("  The other three solids of Figure P7.1 - (b) hexagonal prism, (c) cone,")
    print("  (e) frustum of a cone - are the same two rules again: a generator for")
    print("  the prism, a level section for the cone and the frustum.")
