"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 10: Cut It, Then Unroll It - section, true shape and development
            + worked solution to Exercise 7 (Set A), Q.2(a)  (Figure P7.2a)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed10_development.py S03_TrueShape
    ... or use render_ed10.bat to build all five scenes in order.

Scene order (about twelve minutes in all):

    S01_Unroll        what a development IS: the lateral surface of the solid
                      peeled off and laid flat. The cylinder unrolls in front
                      of you - and it unrolls PROPERLY, by straightening a
                      surface of decreasing curvature, so arc length is
                      preserved every frame rather than lerped away
    S02_TheCut        the 45 degree plane goes through the solid, the top
                      lifts off, and two facts appear: the section is an
                      ellipse seen edge-on in the front view, and every
                      generator now ends at a different height
    S03_TrueShape     the sheet: the twelve generators, the cut points carried
                      into the top view, and the auxiliary view that gives the
                      true shape of the section
    S04_Development   the pattern: pi*D rolled out, twelve divisions, each
                      generator's own height stepped off, and the curve joined
    S05_Recap         the method in four lines, and the two traps

Everything is computed by solve(), which asserts that each generator is cut
where the plane says, that the development is exactly pi*D wide, that the true
shape has the semi-axes the geometry demands, and that the projected area of
the section equals the true area times cos of the cutting angle. A wrong
number stops the render instead of teaching it.

No LaTeX anywhere - every glyph is Unicode Text().
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

from ed_stage import CAM_PHI, CAM_THETA
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
#  Figure P7.2(a): a right circular cylinder, diameter 42, height 50, cut by
#  a plane that passes through the left-hand generator 20 above the base and
#  rises to the right at 45 degrees.
#
#  42 * tan 45 = 42, which is more than the 30 of height left above the cut,
#  so the plane LEAVES the curved surface through the top face. That is not a
#  complication to be skirted round: it is why the development's top edge has
#  a corner in it, and the episode makes a point of it.
# ==========================================================================
DIA = 42.0
RAD = DIA / 2.0
HEIGHT = 50.0
CUT_AT = 20.0            # height of the cut on the left-hand generator
CUT_ANGLE = 45.0         # degrees, rising to the right
N = 12                   # the usual twelve divisions of the circle

SOLID_COL = GOLD         # the cylinder, and its generators
CUT_COL = CORAL          # the cutting plane, the section, its true shape
DEV_COL = VIOLET         # the development - the answer
AUX_COL = CREAM          # construction that only exists to get you there

MM = 0.030               # drawing millimetre -> Manim unit (the flat sheet)
S3 = 0.040               # millimetre -> Manim unit on the 3-D stage


def plane_z(x):
    """Height of the cutting plane above the base, at distance x from the axis."""
    return CUT_AT + (x + RAD) * math.tan(math.radians(CUT_ANGLE))


def solve(n=N):
    # ---- where the plane leaves the curved surface ------------------------
    x_top = (HEIGHT - CUT_AT) / math.tan(math.radians(CUT_ANGLE)) - RAD
    assert -RAD < x_top < RAD, "the plane does not reach the top face at all"
    half_chord = math.sqrt(RAD * RAD - x_top * x_top)
    # the angle, measured from the seam at the LEFT extreme, at which a
    # generator stops being cut by the plane and runs to the top face instead
    theta_break = math.acos(-x_top / RAD)          # from the seam, both ways
    assert 0 < theta_break < math.pi

    # ---- the twelve generators -------------------------------------------
    gens = []
    for k in range(n):
        th = 2 * math.pi * k / n                   # measured from the seam
        x, y = -RAD * math.cos(th), RAD * math.sin(th)
        z = plane_z(x)
        on_top = z > HEIGHT + 1e-9
        gens.append(dict(k=k + 1, theta=th, x=x, y=y,
                         z=min(z, HEIGHT), on_top=on_top, s=RAD * th))
    for g in gens:
        want = min(plane_z(g["x"]), HEIGHT)
        assert abs(g["z"] - want) < 1e-9, f"generator {g['k']} cut at the wrong height"
    assert gens[0]["z"] == CUT_AT, "the seam generator is not the given 20"

    # the two points where the cut crosses onto the top face - the development
    # needs them or its outline misses a corner
    breaks = [dict(theta=theta_break, s=RAD * theta_break, z=HEIGHT,
                   x=x_top, y=half_chord),
              dict(theta=2 * math.pi - theta_break,
                   s=RAD * (2 * math.pi - theta_break), z=HEIGHT,
                   x=x_top, y=-half_chord)]
    for b in breaks:
        assert abs(plane_z(b["x"]) - HEIGHT) < 1e-9, "a break point is not on the top face"

    # ---- the development --------------------------------------------------
    circumference = math.pi * DIA
    pitch = circumference / n
    outline = sorted([(g["s"], g["z"]) for g in gens]
                     + [(b["s"], b["z"]) for b in breaks])
    outline.append((circumference, gens[0]["z"]))      # the seam, come round again
    assert abs(outline[-1][0] - circumference) < 1e-9
    assert abs(max(s for s, _ in outline) - circumference) < 1e-9, \
        "the development is not pi*D wide"

    # ---- the true shape of the section ------------------------------------
    # Set up the cutting plane's own axes: u across the slope (horizontal, so
    # it is true length in the top view already) and v up the slope.
    ang = math.radians(CUT_ANGLE)
    u_hat = np.array([0.0, 1.0, 0.0])
    v_hat = np.array([math.cos(ang), 0.0, math.sin(ang)])
    origin = np.array([-RAD, 0.0, CUT_AT])            # the seam point of the cut

    def to_plane(p):
        d = np.asarray(p, dtype=float) - origin
        return np.array([float(d @ u_hat), float(d @ v_hat)])

    true_shape = []
    for k in range(361):
        th = math.radians(k)
        x, y = -RAD * math.cos(th), RAD * math.sin(th)
        z = plane_z(x)
        if z <= HEIGHT + 1e-9:
            true_shape.append(to_plane((x, y, z)))
    # ... closed off by the chord where the plane runs out onto the top face
    chord = [to_plane((x_top, half_chord, HEIGHT)),
             to_plane((x_top, -half_chord, HEIGHT))]

    semi_minor = RAD                                   # across the slope
    semi_major = RAD / math.cos(ang)                   # up the slope
    for th_deg in (90.0, 270.0):
        th = math.radians(th_deg)
        p = to_plane((-RAD * math.cos(th), RAD * math.sin(th),
                      plane_z(-RAD * math.cos(th))))
        assert abs(abs(p[0]) - semi_minor) < 1e-9, "the minor axis is wrong"
    centre_v = to_plane((0.0, 0.0, plane_z(0.0)))[1]
    assert abs(centre_v - semi_major) < 1e-9, "the major axis is wrong"

    # the section's shadow in the top view is the same region squashed by
    # cos(angle) - a check on the whole plane set-up, from an independent route
    def circ_seg_area(r, d):
        """Area of the circle of radius r on the far side of the chord at x=d."""
        return r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)

    projected = math.pi * RAD * RAD - circ_seg_area(RAD, x_top)
    true_area = projected / math.cos(ang)
    assert projected > 0 and true_area > projected

    slant = (HEIGHT - CUT_AT) / math.sin(ang)
    run = x_top + RAD
    assert abs(slant - math.hypot(run, HEIGHT - CUT_AT)) < 1e-9, \
        "the slant is not the true length of the cut line"
    assert slant < 2 * semi_major, \
        "the section cannot reach further up the slope than the full ellipse"

    return dict(
        gens=gens, breaks=breaks, outline=outline,
        circumference=circumference, pitch=pitch,
        x_top=x_top, half_chord=half_chord, theta_break=theta_break,
        true_shape=true_shape, chord=chord,
        semi_major=semi_major, semi_minor=semi_minor,
        projected_area=projected, true_area=true_area,
        # the true length of the cut LINE, from the seam generator to the chord.
        # Not the ellipse's major axis: the section is cut short of that, and
        # D / cos(angle) would be the axis of the ellipse it never completes.
        slant=(HEIGHT - CUT_AT) / math.sin(ang),
        u_hat=u_hat, v_hat=v_hat, origin=origin, to_plane=to_plane,
    )


G = solve()


# ==========================================================================
#  The 3-D stage: millimetres -> Manim, and the unrolling itself
# ==========================================================================
def pt3(x, y, z):
    """(x from the axis, y from the axis, z above the base) -> the 3-D stage."""
    return np.array([x * S3, y * S3, (z - HEIGHT / 2.0) * S3])


def roll_point(s, z, kappa):
    """A point of the lateral surface, part way through being unrolled.

    `s` is arc length from the seam, `z` is height, and `kappa` is the
    curvature the surface is bent to: 1/RAD leaves it exactly on the cylinder,
    0 lays it out flat. Arc length is preserved at every value in between,
    which is what makes this an unrolling rather than a squash - and it is the
    whole claim the scene is making, so it had better be true frame by frame.

    The surface is bent about the generator DIAMETRICALLY OPPOSITE the seam,
    which is the one that stays put. Two things follow, and both are wanted:
    the flat pattern comes out centred on the screen instead of hanging off to
    one side, and the join lands on the shortest generator, which is where the
    convention says to put a seam.

        x = R - (1 - cos(k*t)) / k        y = -sin(k*t) / k,   t = s - C/2

    Both tend to the flat case as k -> 0, so the limit is taken by hand rather
    than left to divide by zero.
    """
    t = s - G["circumference"] / 2.0
    if abs(kappa) < 1e-9:
        return pt3(RAD, -t, z)
    return pt3(RAD - (1.0 - math.cos(kappa * t)) / kappa,
               -math.sin(kappa * t) / kappa, z)


def _z_top_at(s, cut):
    """Height of the top edge of the lateral surface at arc length s."""
    if not cut:
        return HEIGHT
    th = s / RAD
    return min(plane_z(-RAD * math.cos(th)), HEIGHT)


def surface_strips(kappa, cut=False, segments=72, fill=0.55):
    """The lateral surface as a fan of quads, bent to curvature `kappa`."""
    g = VGroup()
    total = G["circumference"]
    for i in range(segments):
        s0 = total * i / segments
        s1 = total * (i + 1) / segments
        z0, z1 = _z_top_at(s0, cut), _z_top_at(s1, cut)
        quad = Polygon(roll_point(s0, 0.0, kappa), roll_point(s1, 0.0, kappa),
                       roll_point(s1, z1, kappa), roll_point(s0, z0, kappa),
                       stroke_width=0, fill_color=SOLID_COL, fill_opacity=fill)
        g.add(quad)
    return g


def restrip(group, kappa, cut=False, segments=72):
    """Move an existing strip fan onto a new curvature, in place."""
    total = G["circumference"]
    for i, quad in enumerate(group):
        s0 = total * i / segments
        s1 = total * (i + 1) / segments
        z0, z1 = _z_top_at(s0, cut), _z_top_at(s1, cut)
        quad.set_points_as_corners([
            roll_point(s0, 0.0, kappa), roll_point(s1, 0.0, kappa),
            roll_point(s1, z1, kappa), roll_point(s0, z0, kappa),
            roll_point(s0, 0.0, kappa)])
    return group


def edge_curve(kappa, cut=False, samples=145, colour=None, width=4.0):
    """The top edge of the lateral surface at a given curvature."""
    total = G["circumference"]
    pts = [roll_point(total * i / samples, _z_top_at(total * i / samples, cut), kappa)
           for i in range(samples + 1)]
    line = VMobject(stroke_color=colour or (CUT_COL if cut else SOLID_COL),
                    stroke_width=width)
    line.set_points_as_corners(pts)
    return line


def base_curve(kappa, samples=145, colour=SOLID_COL, width=4.0):
    total = G["circumference"]
    pts = [roll_point(total * i / samples, 0.0, kappa) for i in range(samples + 1)]
    line = VMobject(stroke_color=colour, stroke_width=width)
    line.set_points_as_corners(pts)
    return line


def generator_lines(kappa, cut=False, colour=AUX_COL, width=1.6, opacity=0.8):
    g = VGroup()
    for gen in G["gens"]:
        z = gen["z"] if cut else HEIGHT
        g.add(Line(roll_point(gen["s"], 0.0, kappa), roll_point(gen["s"], z, kappa),
                   color=colour, stroke_width=width, stroke_opacity=opacity))
    return g


def unroll(scene, mobs, cut=False, segments=72, reverse=False):
    """The animation itself: curvature 1/R down to 0, or back up again."""
    k0, k1 = (0.0, 1.0 / RAD) if reverse else (1.0 / RAD, 0.0)

    def _bend(_, alpha):
        kappa = interpolate(k0, k1, alpha)
        restrip(mobs["strips"], kappa, cut, segments)
        mobs["top"].become(edge_curve(kappa, cut))
        mobs["base"].become(base_curve(kappa))
        mobs["gens"].become(generator_lines(kappa, cut))

    return UpdateFromAlphaFunc(VGroup(*mobs.values()), _bend)


# ==========================================================================
#  S01 - what a development is
# ==========================================================================
class S01_Unroll(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=68 * DEGREES, theta=-62 * DEGREES,
                                    zoom=0.95, focal_distance=60.0)
        bar = hud(self, title_bar("Development of Surfaces",
                                  "Sheet 8 · the surface, peeled off and laid flat"))
        self.add(bar)

        mobs = dict(strips=surface_strips(1.0 / RAD),
                    base=base_curve(1.0 / RAD),
                    top=edge_curve(1.0 / RAD),
                    gens=generator_lines(1.0 / RAD))
        seam = Line(pt3(-RAD, 0, 0), pt3(-RAD, 0, HEIGHT),
                    color=CUT_COL, stroke_width=6)      # the shortest generator

        narrate(
            self,
            "A cylinder, forty-two across and fifty tall. Question two of exercise "
            "seven asks, in the end, for its development - so before anything else, "
            "what is a development?",
            FadeIn(mobs["strips"]), Create(mobs["base"]), Create(mobs["top"]),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "It is the surface itself, peeled off the solid and laid out flat. Think "
            "of the label on a tin. Cut it down one line, and it comes off in one "
            "piece.",
            Create(seam), FadeIn(mobs["gens"]),
            lag_ratio=0.3,
        )

        fly_camera(
            self,
            "That cut line is called the seam, and where you put it is your choice. "
            "Watch what comes off.",
            phi=76 * DEGREES, theta=-30 * DEGREES, zoom=0.9,
        )
        narrate(
            self,
            "The surface straightens out. Nothing stretches and nothing shrinks - "
            "every distance measured along the curve is the same distance measured "
            "along the flat. That is the one rule the whole subject rests on.",
            unroll(self, mobs), FadeOut(seam),
            rate_func=rate_functions.ease_in_out_sine,
        )

        # The ARROWS stay ordinary 3-D geometry - they lie in the plane of the
        # flat pattern, which the camera is about to look straight at. Only the
        # TEXT is billboarded: a fixed-orientation mobject is turned to face the
        # camera about its own centre, which would stand a horizontal dimension
        # on end.
        half = G["circumference"] / 2.0
        dim_w = VGroup(DoubleArrow(pt3(RAD, -half, -9), pt3(RAD, half, -9),
                                   buff=0, color=DEV_COL, stroke_width=2.4,
                                   tip_length=0.14))
        dim_h = VGroup(DoubleArrow(pt3(RAD, -half - 9, 0), pt3(RAD, -half - 9, HEIGHT),
                                   buff=0, color=DEV_COL, stroke_width=2.4,
                                   tip_length=0.14))
        lab_w = billboard(self, mono(f"π × {DIA:.0f} = {G['circumference']:.1f}",
                                     color=DEV_COL, size=24).move_to(pt3(RAD, 0, -19)))
        lab_h = billboard(self, mono(f"{HEIGHT:.0f}", color=DEV_COL, size=24)
                          .move_to(pt3(RAD, -half - 21, HEIGHT / 2.0)))

        fly_camera(
            self,
            "And there it is: a plain rectangle. Its height is the height of the "
            f"cylinder, fifty. Its width is the distance once round the circle - pi "
            f"times the diameter, {G['circumference']:.1f} millimetres. Cut that "
            "rectangle out of card, roll it up, and you have the cylinder back.",
            FadeIn(dim_w), FadeIn(dim_h), FadeIn(lab_w), FadeIn(lab_h),
            phi=90 * DEGREES, theta=0.0, zoom=1.25,
        )

        note = hud(self, VGroup(
            chip("a development is every face at TRUE SIZE, in order",
                 color=DEV_COL, size=20),
            chip("prism → one rectangle per face · cone → a sector · pyramid → triangles",
                 color=SLATE, size=17),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "Every solid has one.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "A prism gives one rectangle for each face, side by side. A cone opens "
            "out into a sector of a circle. A pyramid becomes a fan of triangles. In "
            "every case the rule is the same: each face drawn at its true size, "
            "joined to its neighbour along the edge they really share.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - the cut, and what it does to the development
# ==========================================================================
class S02_TheCut(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=72 * DEGREES, theta=-58 * DEGREES,
                                    zoom=0.95, focal_distance=60.0)
        bar = hud(self, title_bar("The Cut", "Q.2(a) · a 45° plane through the solid"))
        self.add(bar)

        mobs = dict(strips=surface_strips(1.0 / RAD),
                    base=base_curve(1.0 / RAD),
                    top=edge_curve(1.0 / RAD),
                    gens=generator_lines(1.0 / RAD))
        lid = Circle(radius=RAD * S3, color=SOLID_COL, stroke_width=4,
                     fill_color=SOLID_COL, fill_opacity=0.25).move_to(pt3(0, 0, HEIGHT))

        narrate(
            self,
            "Now the question itself. The same cylinder, but a plane goes through "
            "it: in at the left-hand edge, twenty above the base, and up to the "
            "right at forty-five degrees.",
            FadeIn(mobs["strips"]), Create(mobs["base"]), Create(mobs["top"]),
            FadeIn(lid), FadeIn(mobs["gens"]),
            lag_ratio=0.2,
        )

        # the cutting plane, drawn as a generous square sheet of glass
        ang = math.radians(CUT_ANGLE)
        u = np.array([0.0, 1.0, 0.0])
        v = np.array([math.cos(ang), 0.0, math.sin(ang)])
        c = np.array([-RAD, 0.0, CUT_AT]) + v * 22.0
        sheet = Polygon(*[pt3(*(c + u * a * 34.0 + v * b * 30.0))
                          for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))],
                        stroke_color=CUT_COL, stroke_width=3,
                        fill_color=CUT_COL, fill_opacity=0.22)
        narrate(
            self,
            "There is the plane. Forty-two across at forty-five degrees would climb "
            "forty-two millimetres, and there are only thirty left above the cut - so "
            "the plane runs out through the top face before it reaches the far side. "
            "Remember that: it comes back to bite at the end.",
            Create(sheet),
            lag_ratio=0.3,
        )

        # lift the waste away
        waste = VGroup(lid, sheet)
        cut_mobs = dict(strips=surface_strips(1.0 / RAD, cut=True),
                        base=base_curve(1.0 / RAD),
                        top=edge_curve(1.0 / RAD, cut=True),
                        gens=generator_lines(1.0 / RAD, cut=True))
        section = self.section_face()
        narrate(
            self,
            "Take the top away, and this is what is left standing.",
            FadeOut(mobs["strips"]), FadeOut(mobs["top"]), FadeOut(mobs["gens"]),
            FadeOut(mobs["base"]),          # or the uncut base circle is left behind
            waste.animate.shift(np.array([0.0, 0.0, 2.6])).set_opacity(0.0),
            FadeIn(cut_mobs["strips"]), FadeIn(cut_mobs["top"]),
            FadeIn(cut_mobs["gens"]), FadeIn(section),
            lag_ratio=0.15,
        )

        narrate(
            self,
            "Two things have happened, and the rest of the episode is about both of "
            "them. The first is the new face - the section. It is an ellipse, or "
            "most of one, and it is tilted, so neither the front view nor the top "
            "view will show it at its true size.",
            Indicate(section, color=CUT_COL, scale_factor=1.06),
        )
        narrate(
            self,
            "The second is what the cut did to the surface. Every one of those "
            "vertical lines - the generators - used to be fifty long. Now they are "
            "all different.",
            *[Indicate(g, color=CUT_COL, scale_factor=1.0) for g in cut_mobs["gens"]],
            lag_ratio=0.08,
        )

        fly_camera(
            self,
            "So unroll it again, and watch the top edge.",
            phi=78 * DEGREES, theta=-30 * DEGREES, zoom=0.9,
        )
        narrate(
            self,
            "The flat pattern is no longer a rectangle. Its bottom edge is still the "
            "straight line that was the base circle, but the top edge has become a "
            "curve - and every point of that curve is simply the height of one "
            "generator, carried across.",
            unroll(self, cut_mobs, cut=True), FadeOut(section),
            rate_func=rate_functions.ease_in_out_sine,
        )

        corner = billboard(self, mono("the plane leaves the\ncurved surface here",
                                      color=SLATE, size=18)
                           .move_to(pt3(RAD, 0.0, HEIGHT + 19)))
        marks = VGroup(*[Dot(roll_point(b["s"], HEIGHT, 0.0), radius=0.055,
                             color=CUT_COL) for b in G["breaks"]])
        fly_camera(
            self,
            "And there is that warning made good. In the middle the curve flattens "
            "off and runs level, because over that stretch the plane had already "
            "left the cylinder and the top face is what bounds the surface. The "
            "development has corners in it.",
            FadeIn(marks), FadeIn(corner),
            phi=90 * DEGREES, theta=0.0, zoom=1.25,
        )

        note = hud(self, VGroup(
            chip("the base stays a straight line · length π D", color=SOLID_COL, size=19),
            chip("the cut edge becomes a curve · each generator keeps its own height",
                 color=CUT_COL, size=19),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "Which gives us the plan.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "Divide the circle into twelve. Find where the plane cuts each of the "
            "twelve generators. Step those twelve heights off along the flat base "
            "line, and join them up. That is the development - and the true shape of "
            "the section is one auxiliary view away.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)

    def section_face(self):
        """The elliptical cut face, standing in space."""
        pts = []
        for k in range(0, 361, 3):
            th = math.radians(k)
            x, y = -RAD * math.cos(th), RAD * math.sin(th)
            z = plane_z(x)
            if z <= HEIGHT + 1e-9:
                pts.append(pt3(x, y, z))
        pts.append(pt3(G["x_top"], -G["half_chord"], HEIGHT))
        pts.insert(0, pt3(G["x_top"], G["half_chord"], HEIGHT))
        face = Polygon(*pts, stroke_color=CUT_COL, stroke_width=3.5,
                       fill_color=CUT_COL, fill_opacity=0.45)
        return face


# ==========================================================================
#  The sheet: millimetre space -> Manim points
#
#  The front view sits above the reference line with its base at y = 0; the
#  top view below it, centred on TV_Y; the development away to the right.
# ==========================================================================
XY_Y = -12.0
TV_Y = -45.0
DEV_X = 48.0             # where the development's base line starts


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


def fv(x, z):
    """A point of the front view: x from the axis, z above the base."""
    return P2(x, z)


def tv(x, y):
    """A point of the top view."""
    return P2(x, TV_Y + y)


def dev(s, z):
    """A point of the development: s along the base line, z up."""
    return P2(DEV_X + s, z)


def dim(a, b, text, colour, size=14, offset=0.0, gap=6.0):
    """A slim dimension, pushed `offset` mm off the line it measures
    (measured 90° anticlockwise from a -> b)."""
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


def right_angle(point, d1, d2, colour=INK, size=5.0):
    e1 = np.array([d1[0], d1[1], 0.0]) * size * MM
    e2 = np.array([d2[0], d2[1], 0.0]) * size * MM
    mark = VMobject(stroke_color=colour, stroke_width=1.8)
    mark.set_points_as_corners([point + e1, point + e1 + e2, point + e2])
    return mark


def step_badge(number, title, detail, colour):
    number_mob = mono(number, color=colour, size=22)
    words = VGroup(caption(title, color=INK, size=18),
                   mono(detail, color=SLATE, size=13)
                   ).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


def cut_dir():
    """Unit vector along the cut line in the front view, and its normal."""
    a = math.radians(CUT_ANGLE)
    d = np.array([math.cos(a), math.sin(a), 0.0])
    n = np.array([-d[1], d[0], 0.0])          # up and to the left
    return d, n


AUX_GAP = 58.0           # X1Y1 stood off from the cut line. It has to clear
                         # the section's own half-width, or the true shape is
                         # drawn straight over the view it came from.


def aux_point(x, z, y):
    """Where a point of the section lands in the auxiliary view."""
    _, n = cut_dir()
    return fv(x, z) + n * (AUX_GAP + y) * MM


# ==========================================================================
#  S03 - the sheet, and the true shape of the section
# ==========================================================================
class S03_TrueShape(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        d_hat, n_hat = cut_dir()

        # ---------------- the given views -------------------------------------
        xy = Line(P2(-40, XY_Y), P2(46, XY_Y), color=INK, stroke_width=2.4)
        xy_lab = VGroup(mono("X", color=INK, size=14).next_to(xy, LEFT, buff=0.08),
                        mono("Y", color=INK, size=14).next_to(xy, RIGHT, buff=0.08))
        body = VGroup(
            Line(fv(-RAD, 0), fv(RAD, 0), color=SOLID_COL, stroke_width=3.4),
            Line(fv(-RAD, 0), fv(-RAD, CUT_AT), color=SOLID_COL, stroke_width=3.4),
            Line(fv(RAD, 0), fv(RAD, HEIGHT), color=SOLID_COL, stroke_width=3.4),
            Line(fv(G["x_top"], HEIGHT), fv(RAD, HEIGHT), color=SOLID_COL, stroke_width=3.4),
        )
        cut_line = Line(fv(-RAD, CUT_AT), fv(G["x_top"], HEIGHT),
                        color=CUT_COL, stroke_width=4.5)
        ghost = VGroup(
            DashedLine(fv(-RAD, CUT_AT), fv(-RAD, HEIGHT), color=MUTED,
                       stroke_width=1.6, stroke_opacity=0.5, dash_length=0.05),
            DashedLine(fv(-RAD, HEIGHT), fv(G["x_top"], HEIGHT), color=MUTED,
                       stroke_width=1.6, stroke_opacity=0.5, dash_length=0.05),
        )
        circle = Circle(radius=RAD * MM, color=SOLID_COL, stroke_width=3.4
                        ).move_to(tv(0, 0))
        centre_lines = VGroup(
            DashedLine(tv(-RAD - 6, 0), tv(RAD + 6, 0), color=MUTED,
                       stroke_width=1.4, dash_length=0.06),
            DashedLine(tv(0, -RAD - 6), tv(0, RAD + 6), color=MUTED,
                       stroke_width=1.4, dash_length=0.06),
            DashedLine(fv(0, -5), fv(0, HEIGHT + 5), color=MUTED,
                       stroke_width=1.4, dash_length=0.06),
        )
        given = VGroup(xy, xy_lab, body, cut_line, ghost, circle, centre_lines)
        dims = VGroup(
            dim(fv(-RAD, 0), fv(-RAD, CUT_AT), f"{CUT_AT:.0f}", SLATE,
                size=13, offset=10.0, gap=5.0),
            dim(fv(RAD, 0), fv(RAD, HEIGHT), f"{HEIGHT:.0f}", SLATE,
                size=13, offset=-12.0, gap=5.0),
            mono(f"Ø{DIA:.0f}", color=SLATE, size=13).move_to(tv(0, -RAD - 9)),
            mono("45°", color=CUT_COL, size=14).move_to(fv(1, 28)),
        )

        # ---------------- twelve divisions ------------------------------------
        marks = VGroup(*[Dot(tv(g["x"], g["y"]), radius=0.032, color=AUX_COL)
                         for g in G["gens"]])
        numbers = VGroup(*[
            mono(str(g["k"]), color=SLATE, size=11).move_to(
                tv(g["x"] * 1.17, g["y"] * 1.17)) for g in G["gens"]])
        spokes = VGroup(*[Line(tv(0, 0), tv(g["x"], g["y"]), color=AUX_COL,
                               stroke_width=1.0, stroke_opacity=0.45)
                          for g in G["gens"]])
        chord = Line(tv(G["x_top"], -G["half_chord"]), tv(G["x_top"], G["half_chord"]),
                     color=CUT_COL, stroke_width=3.0)

        risers = VGroup(*[DashedLine(tv(g["x"], min(g["y"], -RAD - 4)),
                                     fv(g["x"], g["z"]), color=MUTED,
                                     stroke_width=1.0, stroke_opacity=0.4,
                                     dash_length=0.05) for g in G["gens"]])
        cut_pts = VGroup(*[Dot(fv(g["x"], g["z"]), radius=0.034, color=CUT_COL)
                           for g in G["gens"]])

        # ---------------- the auxiliary view ----------------------------------
        x1 = Line(fv(-RAD, CUT_AT) + n_hat * AUX_GAP * MM - d_hat * 10 * MM,
                  fv(G["x_top"], HEIGHT) + n_hat * AUX_GAP * MM + d_hat * 16 * MM,
                  color=INK, stroke_width=2.2)
        x1_lab = mono("X1Y1", color=INK, size=13).move_to(
            x1.get_end() + d_hat * 0.24)
        ra = right_angle(fv(0, plane_z(0)), d_hat, n_hat, colour=INK)
        aux_risers = VGroup(*[
            DashedLine(fv(g["x"], g["z"]), aux_point(g["x"], g["z"], g["y"]),
                       color=MUTED, stroke_width=1.0, stroke_opacity=0.4,
                       dash_length=0.05) for g in G["gens"]])
        aux_pts = VGroup(*[Dot(aux_point(g["x"], g["z"], g["y"]), radius=0.034,
                               color=CUT_COL) for g in G["gens"]])

        shape = VMobject(stroke_color=CUT_COL, stroke_width=4,
                         fill_color=CUT_COL, fill_opacity=0.2)
        ring = []
        for k in range(0, 361, 2):
            th = math.radians(k)
            x, y = -RAD * math.cos(th), RAD * math.sin(th)
            z = plane_z(x)
            if z <= HEIGHT + 1e-9:
                ring.append(aux_point(x, z, y))
        ring = ([aux_point(G["x_top"], HEIGHT, G["half_chord"])] + ring
                + [aux_point(G["x_top"], HEIGHT, -G["half_chord"])])
        shape.set_points_as_corners(ring + [ring[0]])

        major = dim(aux_point(-RAD, CUT_AT, 0), aux_point(G["x_top"], HEIGHT, 0),
                    f"{G['slant']:.1f}", CUT_COL, size=13, offset=26.0, gap=6.0)
        minor = dim(aux_point(0, plane_z(0), -RAD), aux_point(0, plane_z(0), RAD),
                    f"{DIA:.0f}", CUT_COL, size=13, offset=-30.0, gap=6.0)
        aux = VGroup(x1, x1_lab, ra, aux_risers, aux_pts, shape)

        sheet = VGroup(given, dims, marks, numbers, spokes, chord, risers,
                       cut_pts, aux, major, minor)

        centre, W = frame_target([given, dims])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 7 (Set A) · Q.2(a)",
            "Figure P7.2a · the section, and its true shape")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "the two given views", "front view with the cut, top view a circle", SLATE),
            step_badge("2", "divide the circle into 12", "number the generators from the seam", SOLID_COL),
            step_badge("3", "carry each one up", "where it meets the cut is that generator's height", CUT_COL),
            step_badge("4", "X1Y1 ∥ the cut", "widths from the top view → TRUE SHAPE", CUT_COL),
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
            "Here is the question on paper. A cylinder forty-two diameter, fifty "
            "high, and the cutting plane drawn in the front view: in at the left "
            "twenty up, and away at forty-five degrees.",
            FadeIn(bar), Create(given), FadeIn(dims),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "In the front view the plane is edge on, so the cut is that single "
            "straight line. In the top view it is the circle - the plane cuts the "
            "curved surface all the way round, and the top view of the section is "
            "just the circle you already have.",
            rail_focus(rail, rungs, 0),
            Indicate(cut_line, color=CUT_COL), Indicate(circle, color=SOLID_COL),
            lag_ratio=0.3,
        )

        narrate(
            self,
            "Step two, and it is the step that makes everything else possible: "
            "divide the circle into twelve equal parts, and number them from the "
            "seam. Each division is a generator - a straight line drawn on the "
            "curved surface, running from base to top.",
            rail_focus(rail, rungs, 1),
            look_at(self, [circle, marks, numbers], right=0.34),
            Create(spokes), FadeIn(marks), FadeIn(numbers),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Mark the chord as well, where the plane runs out through the top "
            f"face: it crosses at {G['x_top']:.0f} from the centre, and it is "
            f"{2 * G['half_chord']:.1f} long.",
            Create(chord),
            lag_ratio=0.3,
        )

        narrate(
            self,
            "Step three. Carry each division straight up into the front view. Where "
            "the projector meets the cut line is the height of that generator - and "
            "that single number is what the development will be built from.",
            rail_focus(rail, rungs, 2),
            look_at(self, [given, circle], right=0.34),
            Create(risers), FadeIn(cut_pts),
            lag_ratio=0.15,
        )
        # The first four generators are bunched into the left third of the
        # front view, so labelling them where they stand puts four numbers on
        # top of each other and on the cut line. A column off to the side,
        # with a leader to each point, says the same thing and can be read.
        rows = VGroup(*[mono(f"{g['k']}  →  {g['z']:.1f}", color=CUT_COL, size=12)
                        for g in G["gens"][:4]]
                      ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        rows.move_to(fv(-54, 30))
        leaders = VGroup(*[
            DashedLine(rows[i].get_right() + RIGHT * 0.06, fv(g["x"], g["z"]),
                       color=CUT_COL, stroke_width=0.9, stroke_opacity=0.45,
                       dash_length=0.05)
            for i, g in enumerate(G["gens"][:4])])
        heights = VGroup(rows, leaders)
        narrate(
            self,
            f"Generator one, at the seam, is the twenty we were given. Two is "
            f"{G['gens'][1]['z']:.1f}. Three, {G['gens'][2]['z']:.1f}. Four, "
            f"{G['gens'][3]['z']:.1f}. And five onwards are all fifty, because "
            "there the plane has already left the cylinder and the top face is what "
            "you meet.",
            FadeIn(heights),
            lag_ratio=0.25,
        )

        narrate(
            self,
            "Step four, the true shape. The cut is edge on in the front view, so an "
            "auxiliary view looking square at it will show it truly. Draw X one Y "
            "one parallel to the cut line.",
            rail_focus(rail, rungs, 3),
            look_at(self, [given, x1], right=0.32),
            Create(x1), FadeIn(x1_lab), Create(ra),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project every point on the cut square across X one Y one, and step off "
            "its distance from the centre line - taken from the top view, which is "
            "where those widths are true.",
            look_at(self, [given, aux], right=0.30),
            Create(aux_risers), FadeIn(aux_pts),
            lag_ratio=0.15,
        )

        ans_rows = VGroup(
            mono("TRUE SHAPE of the section", color=CUT_COL, size=18),
            mono(f"  {DIA:.0f} across the slope", color=CUT_COL, size=14),
            mono(f"  {G['slant']:.1f} up it, seam to chord", color=CUT_COL, size=14),
            mono(f"  chord {2 * G['half_chord']:.1f}", color=SLATE, size=14),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=CUT_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Join them up, and there is the true shape.",
            settle(Create(shape), FadeIn(ans)),
        )
        narrate(
            self,
            f"Part of an ellipse. Across the slope it is {DIA:.0f} - just the "
            "diameter, because in that direction nothing is foreshortened at all. "
            f"Up the slope it runs {G['slant']:.1f}, which is the true length of "
            "the cut line itself: thirty across and thirty up, so thirty root two. "
            "And the far end is cut off flat by the chord, exactly as the top view "
            "said it would be.",
            FadeIn(major), FadeIn(minor),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "That is half the question answered. Now the development.",
            look_at(self, [sheet], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - the development itself
# ==========================================================================
class S04_Development(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        C, pitch = G["circumference"], G["pitch"]

        # ---------------- the front view, kept for the transfers --------------
        body = VGroup(
            Line(fv(-RAD, 0), fv(RAD, 0), color=SOLID_COL, stroke_width=3.4),
            Line(fv(-RAD, 0), fv(-RAD, CUT_AT), color=SOLID_COL, stroke_width=3.4),
            Line(fv(RAD, 0), fv(RAD, HEIGHT), color=SOLID_COL, stroke_width=3.4),
            Line(fv(G["x_top"], HEIGHT), fv(RAD, HEIGHT), color=SOLID_COL, stroke_width=3.4),
            Line(fv(-RAD, CUT_AT), fv(G["x_top"], HEIGHT), color=CUT_COL, stroke_width=4.5),
        )
        fv_gens = VGroup(*[Line(fv(g["x"], 0), fv(g["x"], g["z"]), color=AUX_COL,
                                stroke_width=1.1, stroke_opacity=0.55)
                           for g in G["gens"]])
        fv_pts = VGroup(*[Dot(fv(g["x"], g["z"]), radius=0.03, color=CUT_COL)
                          for g in G["gens"]])
        tag_fv = chip("FRONT VIEW", color=SLATE, size=12).move_to(fv(0, -16))

        # ---------------- the development -------------------------------------
        base = Line(dev(0, 0), dev(C, 0), color=DEV_COL, stroke_width=4)
        ticks = VGroup(*[Line(dev(i * pitch, -2.2), dev(i * pitch, 2.2),
                              color=DEV_COL, stroke_width=2.0) for i in range(N + 1)])
        tick_nums = VGroup(*[
            mono(str(G["gens"][i % N]["k"]), color=SLATE, size=11)
            .move_to(dev(i * pitch, -7.0)) for i in range(N + 1)])
        base_dim = dim(dev(0, 0), dev(C, 0), f"π × {DIA:.0f} = {C:.1f}", DEV_COL,
                       size=15, offset=-26.0, gap=8.0)
        pitch_dim = dim(dev(0, 0), dev(pitch, 0), f"{pitch:.2f}", SLATE,
                        size=12, offset=-15.0, gap=5.0)

        risers = VGroup(*[Line(dev(i * pitch, 0), dev(i * pitch, G["gens"][i % N]["z"]),
                               color=AUX_COL, stroke_width=1.2, stroke_opacity=0.7)
                          for i in range(N + 1)])
        tops = VGroup(*[Dot(dev(i * pitch, G["gens"][i % N]["z"]), radius=0.032,
                            color=CUT_COL) for i in range(N + 1)])
        break_dots = VGroup(*[Dot(dev(b["s"], HEIGHT), radius=0.04, color=CUT_COL)
                              for b in G["breaks"]])

        curve = VMobject(stroke_color=CUT_COL, stroke_width=4)
        pts = []
        for i in range(721):
            s = C * i / 720.0
            th = s / RAD
            z = min(plane_z(-RAD * math.cos(th)), HEIGHT)
            pts.append(dev(s, z))
        curve.set_points_as_corners(pts)

        seam_l = Line(dev(0, 0), dev(0, G["gens"][0]["z"]), color=DEV_COL, stroke_width=4)
        seam_r = Line(dev(C, 0), dev(C, G["gens"][0]["z"]), color=DEV_COL, stroke_width=4)
        tag_dev = chip("DEVELOPMENT", color=DEV_COL, size=13).move_to(dev(C * 0.13, 63))

        development = VGroup(base, ticks, tick_nums, risers, tops, curve,
                             seam_l, seam_r, break_dots)
        sheet = VGroup(body, fv_gens, fv_pts, tag_fv, development,
                       base_dim, pitch_dim, tag_dev)

        centre, W = frame_target([body, development], right=0.26)
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "The Development", "Q.2(a) · the pattern that rolls back into the solid")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "a base line, π D long", f"{C:.1f} mm, divided into {N}", DEV_COL),
            step_badge("2", "erect each generator", "its own height, straight from the front view", CUT_COL),
            step_badge("3", "join with a smooth curve", "through the break where the plane leaves", CUT_COL),
            step_badge("4", "add the ends", "the base circle, the section, the top segment", SLATE),
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
            "The front view again, with the twelve generators drawn on it and the "
            "cut points marked. Everything the development needs is already here.",
            FadeIn(bar), Create(body), Create(fv_gens), FadeIn(fv_pts), FadeIn(tag_fv),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Step one. Draw a straight base line, and make it pi times the "
            f"diameter long - {C:.1f} millimetres. That is the base circle, "
            "straightened out. Divide it into the same twelve parts, each one "
            f"{pitch:.2f}.",
            rail_focus(rail, rungs, 0),
            look_at(self, [development], right=0.28),
            Create(base), Create(ticks), FadeIn(tick_nums),
            FadeIn(base_dim), FadeIn(pitch_dim),
            lag_ratio=0.2,
        )

        narrate(
            self,
            "Step two, and this is the whole trick. At each division, stand the "
            "generator up - and give it the height it has in the front view. The "
            "generator is a straight line on the surface, so the cut does not "
            "shorten it or bend it: its length carries across unchanged.",
            rail_focus(rail, rungs, 1),
            look_at(self, [body, development], right=0.26),
            *[TransformFromCopy(fv_gens[i % N], risers[i]) for i in range(N + 1)],
            lag_ratio=0.12,
        )
        narrate(
            self,
            f"Twenty at the seam, {G['gens'][1]['z']:.1f}, {G['gens'][2]['z']:.1f}, "
            f"{G['gens'][3]['z']:.1f}, then fifty across the middle where the top "
            "face took over, and back down the other side the same way. The pattern "
            "is symmetrical, because the solid is.",
            FadeIn(tops),
            lag_ratio=0.1,
        )

        narrate(
            self,
            "Step three. Join the tops with a smooth curve - and mind the two places "
            "where it stops being a curve. Between them the plane had already left "
            "the cylinder, so that stretch is dead straight: it is the edge of the "
            "top face, not the edge of the cut.",
            rail_focus(rail, rungs, 2),
            Create(curve), FadeIn(break_dots),
            lag_ratio=0.25,
        )

        ans_rows = VGroup(
            mono("DEVELOPMENT of the lateral surface", color=DEV_COL, size=17),
            mono(f"  base line   π × {DIA:.0f} = {C:.1f}", color=DEV_COL, size=14),
            mono(f"  {N} divisions of {pitch:.2f}", color=SLATE, size=14),
            mono(f"  heights  {G['gens'][0]['z']:.0f} · {G['gens'][1]['z']:.1f} · "
                 f"{G['gens'][2]['z']:.1f} · {G['gens'][3]['z']:.1f} · 50 …",
                 color=CUT_COL, size=14),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=DEV_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "Close it off at both ends with the seam, and that is the lateral "
            "surface developed.",
            settle(Create(seam_l), Create(seam_r), FadeIn(tag_dev), FadeIn(ans)),
        )
        narrate(
            self,
            "Cut that shape out of card, roll it round, bring the two seam edges "
            "together, and you have the curved part of the solid back exactly.",
        )

        narrate(
            self,
            "Step four, if the question wants the whole surface and not just the "
            "lateral one: add the base - a circle of diameter forty-two - the "
            "section, which is the true shape we found in the last scene, and the "
            "piece of the top face that survived, the segment beyond the chord. "
            "Three flat pieces, each at its own true size, hung on the pattern "
            "along the edge it really joins.",
            rail_focus(rail, rungs, 3),
            look_at(self, [sheet], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S05 - recap
# ==========================================================================
class S05_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "section, true shape, development")
        self.add(bar)

        rows = VGroup(
            mono("divide the base into 12 · number from the seam", color=SOLID_COL, size=20),
            mono("carry each generator up to the cut · that is its height", color=CUT_COL, size=20),
            mono("TRUE SHAPE   auxiliary view ∥ the cut, widths from the top view",
                 color=CUT_COL, size=19),
            mono("DEVELOPMENT  base line π D · step the same heights off · join",
                 color=DEV_COL, size=19),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(np.array([-0.15, 1.3, 0]))

        start = chip("FRONT + TOP", color=INK, size=15)
        c1 = chip("12 generators", color=SOLID_COL, size=15)
        c2 = chip("12 heights", color=CUT_COL, size=15)
        c3 = chip(f"π D = {G['circumference']:.1f}", color=DEV_COL, size=15)
        chain = VGroup(start, c1, c2, c3).arrange(RIGHT, buff=0.95)
        chain.scale(0.92).move_to(np.array([0.0, -1.15, 0]))

        def link(a, b, text, colour):
            arrow = Arrow(a.get_right(), b.get_left(), buff=0.1, color=colour,
                          stroke_width=2.4, max_tip_length_to_length_ratio=0.2)
            return VGroup(arrow, mono(text, color=colour, size=12)
                          .next_to(arrow, UP, buff=0.06))

        links = VGroup(link(start, c1, "divide", SOLID_COL),
                       link(c1, c2, "project", CUT_COL),
                       link(c2, c3, "step off", DEV_COL))

        narrate(self, "The whole method in four lines.", FadeIn(bar))
        narrate(
            self,
            "Divide the base circle into twelve and number the generators from "
            "wherever you mean to put the seam. On a truncated solid, put it on the "
            "shortest one.",
            FadeIn(rows[0]), FadeIn(start),
        )
        narrate(
            self,
            "Carry each generator up until it meets the cut. Those twelve heights "
            "are the answer to almost everything that follows.",
            FadeIn(rows[1]), FadeIn(links[0]), FadeIn(c1), FadeIn(links[1]), FadeIn(c2),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "For the true shape, one auxiliary view parallel to the cut, with the "
            "widths brought from the top view. For the development, a base line pi D "
            "long, the same twelve heights stepped off along it, and a smooth curve "
            "through the tops.",
            FadeIn(rows[2]), FadeIn(rows[3]), FadeIn(links[2]), FadeIn(c3),
            lag_ratio=0.25,
        )

        traps = VGroup(
            chip("π D is the BASE, not the cut · the base circle is never foreshortened",
                 color=DEV_COL, size=17),
            chip("a development is TRUE LENGTHS only · never measure it off a view",
                 color=CUT_COL, size=17),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.45)
        narrate(
            self,
            "Two traps.",
            settle(FadeIn(traps[0]), FadeIn(traps[1])),
        )
        narrate(
            self,
            "The width of the pattern is pi times the diameter of the BASE - the cut "
            "end is longer round, and it is not what you roll out. And everything "
            "you step off must be a true length. That is easy here, because a "
            "generator of a cylinder is vertical and so always true in the front "
            "view. On a cone or a pyramid it is not, and that is the next episode.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme: run the file directly and it prints the answers it is
#  about to animate.
#
#      py -3.11 ed10_development.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 7 (Set A) Q.2(a) - Figure P7.2a")
    print(f"  right circular cylinder  Ø{DIA:.0f} × {HEIGHT:.0f} high")
    print(f"  cut at {CUT_ANGLE:.0f}° through the left generator, {CUT_AT:.0f} above the base")
    print(f"  the plane leaves the curved surface {G['x_top'] + RAD:.0f} from that "
          f"generator ({G['x_top']:+.0f} from the axis)")
    print(f"  chord on the top face  {2 * G['half_chord']:.2f} mm")
    print()
    print("  generator   angle    height of the cut")
    for g in G["gens"]:
        note = "   (top face)" if g["on_top"] else ""
        print(f"    {g['k']:2}      {math.degrees(g['theta']):5.0f}°      "
              f"{g['z']:6.2f}{note}")
    print()
    print(f"  TRUE SHAPE   part of an ellipse: {DIA:.0f} across the slope,")
    print(f"               {G['slant']:.2f} up it from the seam to the chord")
    print(f"               (the full ellipse would be {2 * G['semi_major']:.2f} long,")
    print(f"                but the chord cuts it short), chord {2 * G['half_chord']:.2f}")
    print(f"               area {G['true_area']:.0f} mm²  "
          f"(top view of it {G['projected_area']:.0f} mm²)")
    print(f"  DEVELOPMENT  base line π × {DIA:.0f} = {G['circumference']:.2f} mm")
    print(f"               {N} divisions of {G['pitch']:.3f} mm")
    print(f"               breaks at {G['breaks'][0]['s']:.2f} and "
          f"{G['breaks'][1]['s']:.2f} along it")
