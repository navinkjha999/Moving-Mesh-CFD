"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 11: The Cone - true length, and why a generator lies to you
            + worked solution to Exercise 7 (Set A), Q.2(e)  (Figure P7.2e)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed11_cone.py S03_Sheet
    ... or use render_ed11.bat to build all five scenes in order.

Scene order (about thirteen minutes in all):

    S01_TheCone      the cone, its twelve generators, and the TWO planes that
                     cut it: horizontal across the left half, 30 degrees up
                     the right. The waste lifts off and leaves two section
                     faces meeting on one diameter
    S02_TrueLength   the whole difficulty of cones and pyramids in one scene.
                     Every generator is the same length, but in the front view
                     only the two on the outline are drawn at that length. The
                     fix - rotate the point about the axis until it lands on
                     the outline - is watched in space before it is drawn
    S03_Sheet        the orthographic drawing, the twelve cut points, and the
                     twelve true lengths lifted off by rotation
    S04_Development  the sector: radius equal to the slant height, angle
                     360 R / L, and the true lengths stepped off from the apex
    S05_Recap        the method, the pyramid (which is the same method), and
                     the trap

Everything is computed by solve(), which asserts that the two cutting planes
agree where they meet, that the rotation construction returns exactly the
apex distance computed from the geometry, and that the development's sector
angle is 360 R / L. A wrong number stops the render instead of teaching it.

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

# ==========================================================================
#  Figure P7.2(e): a right circular cone, base 42 diameter, 50 high, cut by
#  TWO planes that meet on the axis 25 above the base - one horizontal across
#  the left half, one rising to the right at 30 degrees.
# ==========================================================================
DIA = 42.0
RAD = DIA / 2.0
HEIGHT = 50.0
CUT_AT = 25.0            # where both planes meet, on the axis
TILT = 30.0              # degrees, the right-hand plane
N = 12

SLANT = math.hypot(RAD, HEIGHT)
SECTOR = 360.0 * RAD / SLANT

SOLID_COL = GOLD         # the cone and its generators
CUT_COL = CORAL          # the cutting planes and the sections
TL_COL = TEAL            # the true-length construction - the point of the episode
DEV_COL = VIOLET         # the development
AUX_COL = CREAM

MM = 0.030
S3 = 0.058               # the cone is a small object against a wide frame


def radius_at(z):
    """Radius of the cone at height z above the base."""
    return RAD * (1.0 - z / HEIGHT)


def cut_t(theta):
    """Where the cut falls on the generator at `theta`, as a fraction of the
    way from the BASE to the apex.

    theta is measured from the +x axis, so cos(theta) > 0 is the right-hand
    half, where the 30 degree plane does the cutting; on the left the
    horizontal plane cuts every generator at the same height and so at the
    same fraction.
    """
    c = math.cos(theta)
    if c <= 0.0:
        return CUT_AT / HEIGHT
    k = RAD * math.tan(math.radians(TILT))
    return (CUT_AT + k * c) / (HEIGHT + k * c)


def gen_point(theta, t):
    """A point on the generator at `theta`, `t` of the way base -> apex."""
    r = RAD * (1.0 - t)
    return np.array([r * math.cos(theta), r * math.sin(theta), HEIGHT * t])


def solve(n=N):
    k = RAD * math.tan(math.radians(TILT))

    # ---- the two planes agree where they meet -----------------------------
    for th in (math.pi / 2, -math.pi / 2):
        assert abs(cut_t(th) - CUT_AT / HEIGHT) < 1e-12, \
            "the planes disagree on the line where they meet"
    assert abs(cut_t(math.pi / 2 - 1e-9) - cut_t(math.pi / 2 + 1e-9)) < 1e-6, \
        "the cut is not continuous across the junction"

    # ---- the twelve generators --------------------------------------------
    gens = []
    for i in range(n):
        th = math.radians(180.0 - 360.0 * i / n)
        t = cut_t(th)
        p = gen_point(th, t)
        gens.append(dict(k=i + 1, theta=th, t=t, p=p, z=p[2],
                         apex=SLANT * (1.0 - t), base=SLANT * t,
                         horizontal=math.cos(th) <= 1e-12,
                         dev=math.radians(SECTOR) * i / n))
    assert abs(gens[0]["z"] - CUT_AT) < 1e-12, "generator 1 is not on the horizontal plane"

    # the apex distance, checked against the ROTATION construction: swing the
    # cut point about the axis until it lands on the contour generator, which
    # keeps its height and its distance from the axis, and measure there
    for g in gens:
        z = g["z"]
        contour = np.array([radius_at(z), 0.0, z])        # same height, on the outline
        apex = np.array([0.0, 0.0, HEIGHT])
        rotated = float(np.linalg.norm(contour - apex))
        assert abs(rotated - g["apex"]) < 1e-9, \
            f"rotation gives {rotated:.4f} but the geometry says {g['apex']:.4f}"
        # and the front view, measured directly, does NOT give it
        flat = math.hypot(g["p"][0], HEIGHT - z)
        g["front"] = flat
        assert flat <= g["apex"] + 1e-9, "a foreshortened generator came out too long"

    # ---- the development ---------------------------------------------------
    assert abs(SECTOR - 360.0 * RAD / SLANT) < 1e-12
    arc = math.radians(SECTOR) * SLANT
    assert abs(arc - 2 * math.pi * RAD) < 1e-9, \
        "the sector's arc is not the base circle straightened out"

    # ---- the two section faces ---------------------------------------------
    r_join = radius_at(CUT_AT)
    assert abs(r_join - RAD / 2.0) < 1e-12, "the junction circle is the wrong size"

    # the inclined face, in its own plane's axes
    ang = math.radians(TILT)
    u_hat = np.array([0.0, 1.0, 0.0])                     # across the slope
    v_hat = np.array([math.cos(ang), 0.0, math.sin(ang)])  # up it
    origin = np.array([0.0, 0.0, CUT_AT])

    def to_plane(p):
        d = np.asarray(p, float) - origin
        return np.array([float(d @ u_hat), float(d @ v_hat)])

    incl = []
    for i in range(241):
        th = -math.pi / 2 + math.pi * i / 240.0           # the right-hand half only
        t = cut_t(th)
        incl.append(to_plane(gen_point(th, t)))
    span = max(p[1] for p in incl) - min(p[1] for p in incl)
    width = max(p[0] for p in incl) - min(p[0] for p in incl)
    assert abs(width - 2 * r_join) < 1e-6, \
        "the inclined face should be exactly the junction diameter across"

    return dict(gens=gens, slant=SLANT, sector=SECTOR, pitch=SECTOR / n,
                r_join=r_join, incl=incl, incl_span=span, incl_width=width,
                to_plane=to_plane, u_hat=u_hat, v_hat=v_hat, origin=origin,
                tip=gen_point(0.0, cut_t(0.0)), k=k)


G = solve()


# ==========================================================================
#  The 3-D stage
# ==========================================================================
def pt3(p):
    """(x, y, z above the base) in millimetres -> the 3-D stage."""
    x, y, z = p
    return np.array([x * S3, y * S3, (z - HEIGHT / 2.0) * S3])


def cone_strips(cut=False, segments=96, fill=0.5, colour=None):
    """The lateral surface as a fan from the base, cut off where the planes say."""
    g = VGroup()
    for i in range(segments):
        th0 = 2 * math.pi * i / segments
        th1 = 2 * math.pi * (i + 1) / segments
        t0 = cut_t(th0) if cut else 1.0
        t1 = cut_t(th1) if cut else 1.0
        a, b = gen_point(th0, 0.0), gen_point(th1, 0.0)
        c, d = gen_point(th1, t1), gen_point(th0, t0)
        g.add(Polygon(pt3(a), pt3(b), pt3(c), pt3(d), stroke_width=0,
                      fill_color=colour or SOLID_COL, fill_opacity=fill))
    return g


def ring_curve(t_of_theta, colour, width=4.0, samples=192):
    pts = []
    for i in range(samples + 1):
        th = 2 * math.pi * i / samples
        pts.append(pt3(gen_point(th, t_of_theta(th))))
    line = VMobject(stroke_color=colour, stroke_width=width)
    line.set_points_as_corners(pts)
    return line


def gen_lines_3d(cut=False, colour=AUX_COL, width=1.6, opacity=0.75):
    g = VGroup()
    for gen in G["gens"]:
        t = gen["t"] if cut else 1.0
        g.add(Line(pt3(gen_point(gen["theta"], 0.0)),
                   pt3(gen_point(gen["theta"], t)),
                   color=colour, stroke_width=width, stroke_opacity=opacity))
    return g


def section_faces_3d():
    """The two cut faces: a semicircle on the left, half an ellipse on the right."""
    flat = [pt3((G["r_join"] * math.cos(th), G["r_join"] * math.sin(th), CUT_AT))
            for th in np.linspace(math.pi / 2, 3 * math.pi / 2, 60)]
    horizontal = Polygon(*flat, stroke_color=CUT_COL, stroke_width=3,
                         fill_color=CUT_COL, fill_opacity=0.45)
    sloped = [pt3(gen_point(th, cut_t(th)))
              for th in np.linspace(-math.pi / 2, math.pi / 2, 60)]
    inclined = Polygon(*sloped, stroke_color=CUT_COL, stroke_width=3,
                       fill_color=CUT_COL, fill_opacity=0.32)
    return horizontal, inclined


# ==========================================================================
#  S01 - the cone and the two planes
# ==========================================================================
class S01_TheCone(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=72 * DEGREES, theta=-62 * DEGREES,
                                    zoom=1.05, focal_distance=60.0)
        bar = hud(self, title_bar("The Cone",
                                  "Sheet 8 · Q.2(e) · cut by two planes at once"))
        self.add(bar)

        whole = cone_strips()
        base = ring_curve(lambda th: 0.0, SOLID_COL)
        gens = gen_lines_3d()
        apex = Dot3D(pt3((0, 0, HEIGHT)), radius=0.06, color=SOLID_COL)

        narrate(
            self,
            "A right circular cone: forty-two across the base, fifty high. Every "
            "straight line you can draw on it from the apex down to the base is "
            "called a generator, and on a right cone every one of them is exactly "
            "the same length.",
            FadeIn(whole), Create(base), FadeIn(apex), FadeIn(gens),
            lag_ratio=0.2,
        )
        slant_line = Line(pt3((0, 0, HEIGHT)), pt3((RAD, 0, 0)),
                          color=TL_COL, stroke_width=6)
        slant_lab = billboard(self, mono(f"slant height {G['slant']:.2f}",
                                         color=TL_COL, size=22)
                              .move_to(pt3((RAD + 16, 0, HEIGHT * 0.55))))
        narrate(
            self,
            f"That length is the slant height: root of twenty-one squared plus "
            f"fifty squared, which is {G['slant']:.2f} millimetres. Hold on to it - "
            "the whole episode is about measuring it and never being fooled into "
            "measuring something else.",
            Create(slant_line), FadeIn(slant_lab),
            lag_ratio=0.3,
        )

        # the two planes
        sheet_h = Polygon(*[pt3(p) for p in
                            ((-32, 32, CUT_AT), (2, 32, CUT_AT),
                             (2, -32, CUT_AT), (-32, -32, CUT_AT))],
                          stroke_color=CUT_COL, stroke_width=3,
                          fill_color=CUT_COL, fill_opacity=0.2)
        ang = math.radians(TILT)
        v = np.array([math.cos(ang), 0.0, math.sin(ang)])
        u = np.array([0.0, 1.0, 0.0])
        c0 = np.array([0.0, 0.0, CUT_AT])
        sheet_i = Polygon(*[pt3(c0 + u * a * 32 + v * b * 30 + v * 15)
                            for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))],
                          stroke_color=CUT_COL, stroke_width=3,
                          fill_color=CUT_COL, fill_opacity=0.2)
        narrate(
            self,
            "Now the question. Two planes cut this cone, and they meet each other "
            "on the axis, twenty-five above the base. On the left, a horizontal "
            "plane.",
            FadeOut(slant_line), FadeOut(slant_lab), Create(sheet_h),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "And on the right, a plane tilted at thirty degrees, hinged on the same "
            "line. So the left half of the solid is cut level and the right half is "
            "cut on the slope, and the two cuts meet along one diameter.",
            Create(sheet_i),
            lag_ratio=0.3,
        )

        cut_strips = cone_strips(cut=True)
        cut_curve = ring_curve(cut_t, CUT_COL)
        cut_gens = gen_lines_3d(cut=True)
        horizontal, inclined = section_faces_3d()
        narrate(
            self,
            "Take the top away.",
            FadeOut(whole), FadeOut(gens), FadeOut(apex),
            FadeOut(sheet_h), FadeOut(sheet_i),
            FadeIn(cut_strips), FadeIn(cut_curve), FadeIn(cut_gens),
            FadeIn(horizontal), FadeIn(inclined),
            lag_ratio=0.15,
        )
        fly_camera(
            self,
            "Two new faces. A flat half-circle where the level plane went through, "
            f"and half an ellipse where the sloping one did - {G['r_join'] * 2:.0f} "
            "across where they meet, because that is the diameter of the cone at "
            "twenty-five up.",
            phi=58 * DEGREES, theta=-25 * DEGREES, zoom=1.15,
        )

        note = hud(self, VGroup(
            chip("the question wants: the sections, and the DEVELOPMENT",
                 color=CUT_COL, size=19),
            chip("and a development is built from TRUE LENGTHS only",
                 color=TL_COL, size=19),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "So far this is the cylinder all over again.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "But a cone is not a cylinder, and there is one difference that catches "
            "almost everybody. On the cylinder, the generators were vertical, so the "
            "front view drew every one of them at its true length and you could take "
            "the heights straight off the drawing. On a cone they lean - and a "
            "leaning line is foreshortened. Next scene.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - the true length problem, and the rotation that solves it
# ==========================================================================
class S02_TrueLength(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=74 * DEGREES, theta=-70 * DEGREES,
                                    zoom=1.2, focal_distance=60.0)
        bar = hud(self, title_bar("True Length",
                                  "why a generator lies, and how to make it talk"))
        self.add(bar)

        # The WHOLE cone here, not the truncated one. This scene is about how
        # long a generator is, so the apex has to be on screen: with the top
        # cut away the generators and the true-length line run up to a corner
        # of empty sky and the measurement looks like a mistake.
        strips = cone_strips(cut=False, fill=0.3)
        base = ring_curve(lambda th: 0.0, SOLID_COL)
        cut = ring_curve(cut_t, CUT_COL, width=3.0)
        apex3 = pt3((0, 0, HEIGHT))
        apex_dot = Dot3D(apex3, radius=0.055, color=SOLID_COL)
        self.add(strips, base, cut, apex_dot)

        # the contour generator, and a leaning one
        contour = Line(apex3, pt3(gen_point(0.0, 0.0)), color=TL_COL, stroke_width=5)
        pick = G["gens"][3]                       # generator 4: the worst offender
        leaning = Line(apex3, pt3(gen_point(pick["theta"], 0.0)),
                       color=SOLID_COL, stroke_width=5)
        labs = billboard(self, VGroup(
            mono("7", color=TL_COL, size=22).move_to(pt3(gen_point(0.0, -0.18))),
            mono("4", color=SOLID_COL, size=22).move_to(
                pt3(gen_point(pick["theta"], -0.18)))))

        narrate(
            self,
            "Here is the cone again with two of its generators picked out. Number "
            "seven runs straight towards us along the outline. Number four runs away "
            "to the side.",
            Create(contour), Create(leaning), FadeIn(labs),
            lag_ratio=0.25,
        )
        narrate(
            self,
            f"In space they are the same length - {G['slant']:.2f}, both of them, "
            "because that is what a right cone is.",
        )

        fly_camera(
            self,
            "Now go and stand where the front view is taken from.",
            FadeOut(labs),
            phi=90 * DEGREES, theta=-90 * DEGREES, zoom=1.25,
        )
        narrate(
            self,
            "From here number seven still measures its full length, because it lies "
            "square across your line of sight. Number four does not: it is leaning "
            "away from you, so the front view draws it short. Every generator except "
            "the two on the outline is drawn short.",
            Indicate(leaning, color=SOLID_COL, scale_factor=1.0),
            lag_ratio=0.3,
        )

        # the cut point, and the rotation
        p_cut = pt3(pick["p"])
        dot = Dot3D(p_cut, radius=0.055, color=CUT_COL)
        z = pick["z"]
        circle = ParametricFunction(
            lambda a: pt3((radius_at(z) * math.cos(a), radius_at(z) * math.sin(a), z)),
            t_range=[0, 2 * math.pi], color=TL_COL, stroke_width=2.5)
        landed = Dot3D(pt3((radius_at(z), 0.0, z)), radius=0.055, color=TL_COL)

        fly_camera(
            self,
            "Which matters, because the point we actually need is this one - where "
            "the cutting plane crosses generator four. To develop the cone we must "
            "know its true distance from the apex, and the front view will not give "
            "it to us.",
            FadeIn(dot),
            phi=70 * DEGREES, theta=-58 * DEGREES, zoom=1.2,
        )
        narrate(
            self,
            "So here is the trick, and it is the only new idea in the episode. Swing "
            "that point round the axis of the cone, keeping it at the same height, "
            "until it lands on the outline.",
            Create(circle),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "The cone is a solid of revolution, so the surface turns into itself: the "
            "point is still on the cone, still the same distance from the apex, and "
            "now it is sitting on the one generator the front view draws honestly.",
            FadeIn(landed),
            lag_ratio=0.3,
        )

        true_line = Line(apex3, pt3((radius_at(z), 0.0, z)), color=TL_COL,
                         stroke_width=6)
        tl_lab = billboard(self, mono(f"{pick['apex']:.2f}  TRUE", color=TL_COL, size=22)
                           .move_to(pt3((radius_at(z) + 20, 0.0, (HEIGHT + z) / 2))))
        fr_lab = billboard(self, mono(f"{pick['front']:.2f}  as drawn",
                                      color=MUTED, size=20)
                           .move_to(pt3((pick["p"][0] - 22, pick["p"][1], z + 9))))
        narrate(
            self,
            f"Measure it there and it comes to {pick['apex']:.2f}. Measure it where "
            f"it was drawn in the front view and you get {pick['front']:.2f} - over "
            "two millimetres short, on a fifty millimetre cone. Do that twelve times "
            "and the development closes up wrong.",
            Create(true_line), FadeIn(tl_lab), FadeIn(fr_lab),
            lag_ratio=0.3,
        )

        note = hud(self, VGroup(
            chip("swing the point about the axis onto the OUTLINE", color=TL_COL, size=20),
            chip("the height does not change · the distance from the apex does not change",
                 color=SLATE, size=17),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "On paper that swing is one horizontal line.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "The point keeps its height, so you simply draw across from it, level, "
            "until you meet the outline of the cone - and measure from the apex to "
            "there. That single horizontal line is the whole of the true length "
            "construction, and it is what the next scene does twelve times over.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  The sheet
# ==========================================================================
XY_Y = -12.0
TV_Y = -46.0
DEV_AT = np.array([96.0, 40.0])      # the apex of the development


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


def fv(x, z):
    return P2(x, z)


def tv(x, y):
    return P2(x, TV_Y + y)


def dev_dir(phi):
    """A unit vector in the development, phi measured from straight down."""
    return np.array([math.sin(phi), -math.cos(phi), 0.0])


def dev(phi, d):
    return P2(DEV_AT[0], DEV_AT[1]) + dev_dir(phi) * d * MM


def dim(a, b, text, colour, size=14, offset=0.0, gap=6.0):
    d = b - a
    length = float(np.linalg.norm(d))
    n = np.array([-d[1], d[0], 0.0])
    n = n / max(float(np.linalg.norm(n)), 1e-9)
    a, b = a + n * offset * MM, b + n * offset * MM
    arrow = DoubleArrow(a, b, buff=0, color=colour, stroke_width=1.7,
                        tip_length=float(min(0.10, 0.30 * length)))
    side = 1.0 if offset >= 0 else -1.0
    lab = mono(text, color=colour, size=size).move_to((a + b) / 2 + n * side * gap * MM)
    return VGroup(arrow, lab)


def step_badge(number, title, detail, colour):
    number_mob = mono(number, color=colour, size=22)
    words = VGroup(caption(title, color=INK, size=18),
                   mono(detail, color=SLATE, size=13)
                   ).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


def front_view_group():
    """The cone's front view: outline, axis, the two cut lines."""
    outline = VGroup(
        Line(fv(-RAD, 0), fv(RAD, 0), color=SOLID_COL, stroke_width=3.4),
        Line(fv(-RAD, 0), fv(0, HEIGHT), color=SOLID_COL, stroke_width=3.4),
        Line(fv(RAD, 0), fv(0, HEIGHT), color=SOLID_COL, stroke_width=3.4),
    )
    axis = DashedLine(fv(0, -5), fv(0, HEIGHT + 6), color=MUTED,
                      stroke_width=1.4, dash_length=0.06)
    tip = G["tip"]
    cuts = VGroup(
        Line(fv(-radius_at(CUT_AT), CUT_AT), fv(0, CUT_AT),
             color=CUT_COL, stroke_width=4.5),
        Line(fv(0, CUT_AT), fv(tip[0], tip[2]), color=CUT_COL, stroke_width=4.5),
    )
    return outline, axis, cuts


# ==========================================================================
#  S03 - the sheet, and twelve true lengths
# ==========================================================================
class S03_Sheet(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        outline, axis, cuts = front_view_group()
        xy = Line(P2(-38, XY_Y), P2(40, XY_Y), color=INK, stroke_width=2.4)
        xy_lab = VGroup(mono("X", color=INK, size=14).next_to(xy, LEFT, buff=0.08),
                        mono("Y", color=INK, size=14).next_to(xy, RIGHT, buff=0.08))

        circle = Circle(radius=RAD * MM, color=SOLID_COL, stroke_width=3.4
                        ).move_to(tv(0, 0))
        join_circle = DashedLine(tv(0, 0), tv(0, 0))       # placeholder, replaced below
        join_circle = Circle(radius=G["r_join"] * MM, color=CUT_COL, stroke_width=2.6
                             ).move_to(tv(0, 0))
        centre_lines = VGroup(
            DashedLine(tv(-RAD - 6, 0), tv(RAD + 6, 0), color=MUTED,
                       stroke_width=1.4, dash_length=0.06),
            DashedLine(tv(0, -RAD - 6), tv(0, RAD + 6), color=MUTED,
                       stroke_width=1.4, dash_length=0.06))
        spokes = VGroup(*[Line(tv(0, 0), tv(RAD * math.cos(g["theta"]),
                                            RAD * math.sin(g["theta"])),
                               color=AUX_COL, stroke_width=1.0, stroke_opacity=0.45)
                          for g in G["gens"]])
        numbers = VGroup(*[
            mono(str(g["k"]), color=SLATE, size=11).move_to(
                tv(RAD * 1.17 * math.cos(g["theta"]), RAD * 1.17 * math.sin(g["theta"])))
            for g in G["gens"]])
        dims = VGroup(
            dim(fv(RAD, 0), fv(0, HEIGHT), f"{G['slant']:.2f}", TL_COL,
                size=13, offset=-9.0, gap=5.0),
            dim(fv(-RAD - 10, 0), fv(-RAD - 10, CUT_AT), f"{CUT_AT:.0f}", SLATE,
                size=13, offset=0.0, gap=5.0),
            mono("30°", color=CUT_COL, size=13).move_to(fv(9, 25.5)),
            mono(f"Ø{DIA:.0f}", color=SLATE, size=13).move_to(tv(0, -RAD - 9)),
        )
        given = VGroup(xy, xy_lab, outline, axis, cuts, circle, centre_lines)

        # ---- the cut points in the front view ---------------------------------
        fv_gens = VGroup(*[Line(fv(0, HEIGHT), fv(RAD * math.cos(g["theta"]), 0),
                                color=AUX_COL, stroke_width=1.0, stroke_opacity=0.5)
                           for g in G["gens"]])
        cut_dots = VGroup(*[Dot(fv(g["p"][0], g["z"]), radius=0.032, color=CUT_COL)
                            for g in G["gens"]])

        # ---- the rotation: level across to the outline ------------------------
        levels = sorted({round(g["z"], 6) for g in G["gens"]})
        swings = VGroup(*[
            DashedLine(fv(min(g["p"][0], 0) - 0.0, g["z"]),
                       fv(radius_at(g["z"]), g["z"]), color=TL_COL,
                       stroke_width=1.3, stroke_opacity=0.8, dash_length=0.05)
            for g in G["gens"]])
        landed = VGroup(*[Dot(fv(radius_at(z), z), radius=0.034, color=TL_COL)
                          for z in levels])
        tl_lines = VGroup(*[Line(fv(0, HEIGHT), fv(radius_at(z), z),
                                 color=TL_COL, stroke_width=3.0) for z in levels])
        tl_tags = VGroup(*[
            mono(f"{SLANT * (1 - z / HEIGHT):.2f}", color=TL_COL, size=12).move_to(
                fv(radius_at(z) + 12, z + 1.5)) for z in levels])

        sheet = VGroup(given, dims, spokes, numbers, join_circle, fv_gens,
                       cut_dots, swings, landed, tl_lines, tl_tags)

        centre, W = frame_target([given, dims])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 7 (Set A) · Q.2(e)",
            "Figure P7.2e · the cut, and the twelve true lengths")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "the given views", "a triangle and a circle, with two cut lines", SLATE),
            step_badge("2", "twelve generators", "in the top view, and carried into the front", SOLID_COL),
            step_badge("3", "mark the cut points", "where each generator meets a cutting plane", CUT_COL),
            step_badge("4", "swing them to the outline", "level across · measure from the apex", TL_COL),
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
            "The cone on paper. A triangle in the front view, a circle in the top "
            f"view, and the slant height {G['slant']:.2f} showing true on both "
            "sloping sides of the triangle - because those two edges are the "
            "generators that face us squarely.",
            FadeIn(bar), Create(given), FadeIn(dims),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The two cuts are drawn in the front view, where both planes are edge "
            "on: level from the left-hand side across to the axis, then away at "
            "thirty degrees to the right-hand side.",
            rail_focus(rail, rungs, 0),
            Indicate(cuts, color=CUT_COL),
            lag_ratio=0.3,
        )

        narrate(
            self,
            "Divide the base circle into twelve and number them. One at the far "
            "left, seven at the far right - the two that sit on the outline.",
            rail_focus(rail, rungs, 1),
            look_at(self, [circle, numbers], right=0.34),
            Create(spokes), FadeIn(numbers),
            lag_ratio=0.15,
        )
        narrate(
            self,
            "Carry them up into the front view as twelve lines from the apex. "
            "Remember what they really are: twelve straight lines lying on the "
            "surface, all the same length, drawn at twelve different lengths.",
            look_at(self, [given, fv_gens], right=0.32),
            Create(fv_gens),
            lag_ratio=0.12,
        )
        narrate(
            self,
            "Step three. Mark where each one crosses a cutting plane. The seven on "
            "the left all cross the level plane at the same height, twenty-five. The "
            "five on the right cross the sloping one, each a little higher than the "
            "last.",
            rail_focus(rail, rungs, 2),
            FadeIn(cut_dots),
            lag_ratio=0.12,
        )

        narrate(
            self,
            "And step four is the one that matters. Swing each of those points "
            "level across to the outline of the triangle.",
            rail_focus(rail, rungs, 3),
            Create(swings), FadeIn(landed),
            lag_ratio=0.12,
        )
        ans_rows = VGroup(
            mono("TRUE LENGTHS from the apex", color=TL_COL, size=17),
            *[mono(f"  {'1–4, 10–12' if abs(z - CUT_AT) < 1e-9 else ''}"
                   f"{'' if abs(z - CUT_AT) < 1e-9 else ('5, 9' if abs(z - 27.703) < 0.01 else ('6, 8' if abs(z - 29.339) < 0.01 else '7'))}"
                   f"   {SLANT * (1 - z / HEIGHT):.2f}", color=TL_COL, size=14)
              for z in levels],
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=TL_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Measure from the apex down to where each one lands, and those are the "
            "true distances.",
            settle(Create(tl_lines), FadeIn(tl_tags), FadeIn(ans)),
        )
        narrate(
            self,
            f"And there is a mercy in this particular question: there are only four "
            f"different answers. The seven generators cut level all give "
            f"{SLANT * (1 - CUT_AT / HEIGHT):.2f}. The sloping cut is symmetrical "
            "about the centre, so five and nine agree, six and eight agree, and "
            "seven is on its own. Four measurements, not twelve.",
            look_at(self, [sheet], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - the development, and the true shapes of the two sections
# ==========================================================================
class S04_Development(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        outline, axis, cuts = front_view_group()
        levels = sorted({round(g["z"], 6) for g in G["gens"]})
        tl_lines = VGroup(*[Line(fv(0, HEIGHT), fv(radius_at(z), z),
                                 color=TL_COL, stroke_width=2.6) for z in levels])
        front = VGroup(outline, axis, cuts, tl_lines)
        tag_fv = chip("FRONT VIEW", color=SLATE, size=12).move_to(fv(0, -20))

        # ---------------- the sector -------------------------------------------
        half = math.radians(SECTOR) / 2.0
        apex_dot = Dot(dev(0, 0), radius=0.045, color=DEV_COL)
        base_arc = ParametricFunction(
            lambda a: dev(a, SLANT), t_range=[-half, half],
            color=DEV_COL, stroke_width=4)
        edges = VGroup(Line(dev(-half, 0), dev(-half, SLANT), color=DEV_COL,
                            stroke_width=4),
                       Line(dev(half, 0), dev(half, SLANT), color=DEV_COL,
                            stroke_width=4))
        rays = VGroup(*[Line(dev(-half + g["dev"], 0), dev(-half + g["dev"], SLANT),
                             color=AUX_COL, stroke_width=1.1, stroke_opacity=0.6)
                        for g in G["gens"]])
        ray_nums = VGroup(*[
            mono(str(g["k"]), color=SLATE, size=11).move_to(
                dev(-half + g["dev"], SLANT + 7)) for g in G["gens"]])
        sector_dim = VGroup(
            mono(f"R = {G['slant']:.2f}", color=DEV_COL, size=15).move_to(
                dev(-half * 0.55, SLANT * 0.55)),
            mono(f"{SECTOR:.2f}°", color=DEV_COL, size=15).move_to(dev(0, 13)))

        cut_dots = VGroup(*[Dot(dev(-half + g["dev"], g["apex"]), radius=0.032,
                                color=CUT_COL) for g in G["gens"]]
                          + [Dot(dev(half, G["gens"][0]["apex"]), radius=0.032,
                                 color=CUT_COL)])
        cut_curve = VMobject(stroke_color=CUT_COL, stroke_width=4)
        pts = []
        for i in range(361):
            a = -half + 2 * half * i / 360.0
            th = math.pi - 2 * math.pi * (a + half) / math.radians(SECTOR)
            pts.append(dev(a, SLANT * (1.0 - cut_t(th))))
        cut_curve.set_points_as_corners(pts)
        development = VGroup(apex_dot, base_arc, edges, rays, ray_nums,
                             cut_dots, cut_curve)
        tag_dev = chip("DEVELOPMENT", color=DEV_COL, size=13).move_to(
            dev(-half, SLANT + 20))

        sheet = VGroup(front, tag_fv, development, sector_dim, tag_dev)
        centre, W = frame_target([front, development], right=0.26)
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "The Development", "Q.2(e) · a sector, and twelve true lengths")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "a sector of radius L", f"L = {G['slant']:.2f}, the slant height", DEV_COL),
            step_badge("2", "angle 360 R / L", f"= {SECTOR:.2f}°, divided into 12", DEV_COL),
            step_badge("3", "step off each true length", "from the APEX, along its own ray", TL_COL),
            step_badge("4", "join · add the sections", "half-circle and half-ellipse", CUT_COL),
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
            "The front view again, with the four true lengths already lifted onto "
            "the outline. Everything the development needs is in those four numbers.",
            FadeIn(bar), Create(front), FadeIn(tag_fv),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"A cone opens out into a sector of a circle. Its radius is the slant "
            f"height - {G['slant']:.2f} - because every generator, laid flat, still "
            "runs that far from the apex.",
            rail_focus(rail, rungs, 0),
            look_at(self, [development], right=0.28),
            FadeIn(apex_dot), Create(edges), Create(base_arc), FadeIn(sector_dim),
            lag_ratio=0.25,
        )
        narrate(
            self,
            f"And its angle is three hundred and sixty times R over L - twenty-one "
            f"over {G['slant']:.2f} - which is {SECTOR:.2f} degrees. That is not a "
            "formula to memorise: it is just the statement that the arc of the "
            "sector has to be the base circle straightened out, and it is. Divide "
            f"it into twelve, {G['pitch']:.4f} degrees each.",
            rail_focus(rail, rungs, 1),
            Create(rays), FadeIn(ray_nums),
            lag_ratio=0.15,
        )

        narrate(
            self,
            "Step three. Along each ray, measure the true length of that generator "
            "from the apex down to the cut - straight off the front view, where we "
            "swung it onto the outline.",
            rail_focus(rail, rungs, 2),
            look_at(self, [front, development], right=0.26),
            *[TransformFromCopy(tl_lines[min(i, len(levels) - 1)], cut_dots[i])
              for i in range(len(G["gens"]))],
            lag_ratio=0.1,
        )

        ans_rows = VGroup(
            mono("DEVELOPMENT of the lateral surface", color=DEV_COL, size=17),
            mono(f"  sector radius  {G['slant']:.2f}", color=DEV_COL, size=14),
            mono(f"  sector angle   {SECTOR:.2f}°", color=DEV_COL, size=14),
            mono(f"  cut at  {SLANT * (1 - CUT_AT / HEIGHT):.2f} · "
                 f"{G['gens'][4]['apex']:.2f} · {G['gens'][5]['apex']:.2f} · "
                 f"{G['gens'][6]['apex']:.2f}", color=TL_COL, size=14),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=DEV_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Join the marks, and the pattern is finished.",
            settle(Create(cut_curve), FadeIn(tag_dev), FadeIn(ans)),
        )
        narrate(
            self,
            "Notice the shape of that inner curve. It runs level across the middle "
            "third, because those seven generators were all cut at the same height "
            "by the level plane, so they are all the same distance from the apex - "
            "and on the development, equal distances from the apex is an ARC, not a "
            "straight line. Then it dips in on both sides where the sloping plane "
            "cut deeper.",
            look_at(self, [development], right=0.26),
        )
        narrate(
            self,
            "Add the two section faces and the base, each at true size, and the "
            "surface is completely developed. The level cut is a half-circle of "
            f"radius {G['r_join']:.2f}, and it is already true in the top view "
            "because a horizontal face always is. The sloping cut is half an "
            f"ellipse, {G['incl_width']:.0f} across and {G['incl_span']:.2f} up the "
            "slope, and that one needs an auxiliary view square to the plane - "
            "exactly as the cylinder's did.",
            rail_focus(rail, rungs, 3),
            look_at(self, [sheet], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S05 - recap, and the pyramid
# ==========================================================================
class S05_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "cones, pyramids, and true length")
        self.add(bar)

        rows = VGroup(
            mono("a cone develops into a SECTOR   radius L,  angle 360 R / L",
                 color=DEV_COL, size=20),
            mono("a generator is TRUE LENGTH only on the outline", color=TL_COL, size=20),
            mono("swing each cut point level onto the outline, then measure",
                 color=TL_COL, size=20),
            mono("step those true lengths from the apex · join · add the faces",
                 color=CUT_COL, size=19),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(np.array([-0.15, 1.35, 0]))

        narrate(self, "The method in four lines.", FadeIn(bar))
        narrate(
            self,
            f"A cone opens into a sector: radius the slant height, angle three "
            f"hundred and sixty R over L. For this cone, {G['slant']:.2f} and "
            f"{SECTOR:.2f} degrees.",
            FadeIn(rows[0]),
        )
        narrate(
            self,
            "The one thing that catches people is that a generator is only drawn at "
            "its true length when it lies on the outline of the view. Every other "
            "one leans away and is drawn short.",
            FadeIn(rows[1]),
        )
        narrate(
            self,
            "So before you measure anything, swing the point level onto the outline "
            "and measure it there. Then step those true lengths off from the apex, "
            "join them up, and hang the sections and the base on the pattern.",
            FadeIn(rows[2]), FadeIn(rows[3]),
            lag_ratio=0.25,
        )

        pyr = VGroup(
            chip("A PYRAMID IS THE SAME PROBLEM", color=TL_COL, size=20),
            mono("develop it as a fan of triangles, one per face", color=SLATE, size=17),
            mono("the slant EDGES are true length only on the outline — rotate them too",
                 color=SLATE, size=17),
            mono("a cone is just a pyramid with a great many very thin faces",
                 color=DEV_COL, size=17),
        ).arrange(DOWN, buff=0.16).move_to(np.array([0.0, -1.35, 0]))
        narrate(
            self,
            "And the same episode covers the pyramid.",
            settle(FadeIn(pyr[0]), FadeIn(pyr[1])),
        )
        narrate(
            self,
            "A pyramid develops as a fan of triangles, one for each face, and its "
            "slant edges have exactly the same problem: only the ones on the outline "
            "of the view are drawn true, and the rest have to be rotated before they "
            "can be measured. Which should not be a surprise - a cone is only a "
            "pyramid with a very great many very thin faces.",
            FadeIn(pyr[2]), FadeIn(pyr[3]),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Two traps to finish. The sector angle uses the radius of the BASE and "
            "the SLANT height, not the vertical height - mixing those two up is the "
            "commonest mistake on the sheet. And never measure a generator in the "
            "top view either: there it is not foreshortened, it is simply the plan "
            "of a sloping line, and it is shorter still.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme
#
#      py -3.11 ed11_cone.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 7 (Set A) Q.2(e) - Figure P7.2e")
    print(f"  right circular cone  Ø{DIA:.0f} base × {HEIGHT:.0f} high")
    print(f"  slant height L = √({RAD:.0f}² + {HEIGHT:.0f}²) = {G['slant']:.4f} mm")
    print(f"  cut by TWO planes meeting on the axis {CUT_AT:.0f} above the base:")
    print(f"     horizontal across the left half")
    print(f"     {TILT:.0f}° rising to the right, meeting the outline at "
          f"z = {G['tip'][2]:.3f}, x = {G['tip'][0]:.3f}")
    print()
    print("  gen  θ        cut z     TRUE from apex    as drawn in the FV")
    for g in G["gens"]:
        flag = "" if abs(g["front"] - g["apex"]) < 1e-9 else "   <- short"
        print(f"  {g['k']:3}  {math.degrees(g['theta']):6.0f}°  {g['z']:7.3f}   "
              f"{g['apex']:8.3f}        {g['front']:8.3f}{flag}")
    print()
    print(f"  DEVELOPMENT  sector of radius {G['slant']:.2f} mm")
    print(f"               angle 360 × {RAD:.0f} / {G['slant']:.2f} = {SECTOR:.3f}°")
    print(f"               {N} divisions of {G['pitch']:.4f}°")
    print(f"  SECTIONS     level cut: half-circle, radius {G['r_join']:.2f} "
          f"(true in the top view)")
    print(f"               sloping cut: half-ellipse, {G['incl_width']:.2f} across "
          f"× {G['incl_span']:.2f} up the slope")
