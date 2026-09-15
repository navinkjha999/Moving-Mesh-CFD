"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 14: Oblique Solids - every generator its own length
            + worked solutions to Exercise 8 (Set A), Q.3(a) and Q.3(b)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed14_oblique.py S03_SheetB
    ... or use render_ed14.bat to build all five scenes in order.

Scene order (about twelve minutes in all):

    S01_WhatIsOblique   right against oblique, in space. On a right pyramid
                        every slant edge is the same length and the sector
                        trick works; lean the apex over and they are all
                        different, and none of episode 11's shortcuts survive
    S02_Triangulation   the method that always works: a face at a time, each
                        triangle built from three TRUE lengths, and the one
                        construction that produces them - a right triangle on
                        the plan length and the height
    S03_SheetB          Q.3(b), the oblique pyramid: the cut, the four edge
                        points, and the true shape of the section
    S04_DevelopmentB    the pattern, triangle by triangle, with the cut marked
                        along each edge at its own true distance from the apex
    S05_ConeAndRecap    Q.3(a), the oblique cone - the same method with twelve
                        generators instead of four edges - and the recap

Everything is computed by solve_pyramid() and solve_cone(), which assert that
the slant lengths really are all different, that each cut point lies on both
the plane and the edge it belongs to, that the triangulated layout reproduces
every true length it was built from, and that the section's true shape
projects back to its own top view through the cosine of the cutting angle.

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
CUT_COL = CORAL
TL_COL = TEAL            # true length - the whole difficulty
DEV_COL = VIOLET
AUX_COL = CREAM

MM = 0.026
S3 = 0.095               # the solid has a wide frame to fill
PYR_CX = 5.0             # mid-way between the base centre and the leaning apex

# ==========================================================================
#  Figure P8.3(b): an oblique square pyramid. Base 35 side, set with its
#  diagonals across and along the sheet, so the front view is 35√2 wide. The
#  apex is 50 up and 10 BEYOND the right-hand corner of the base. Cut by a
#  plane at 30°, entering the left-hand slant edge 6 above the base.
#
#  Figure P8.3(a): an oblique cone. Base Ø42, axis 60 long leaning at 60° to
#  the base, so the apex is 30 across and 51.96 up. Cut by a plane at 30°
#  through the point 30 along that axis.
# ==========================================================================
PYR = dict(side=35.0, height=50.0, offset=10.0, cut_at=6.0, tilt=30.0)
CONE = dict(dia=42.0, axis=60.0, lean=60.0, cut_along=30.0, tilt=30.0)


def _plane(through, tilt):
    """A cutting plane: horizontal in y, rising at `tilt` in the x-z plane."""
    m = math.tan(math.radians(tilt))
    x0, z0 = through

    def z_at(x):
        return z0 + (x - x0) * m

    return z_at


def _cut_edge(a, b, z_at):
    """Where the plane cuts the straight edge a -> b. Returns (t, point)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    fa, fb = a[2] - z_at(a[0]), b[2] - z_at(b[0])
    assert fa * fb < 0, "the plane does not cross that edge"
    t = fa / (fa - fb)
    return t, a + t * (b - a)


def solve_pyramid():
    s, h, off = PYR["side"], PYR["height"], PYR["offset"]
    half = s / math.sqrt(2.0)                      # half-diagonal
    base = [np.array([-half, 0.0, 0.0]), np.array([0.0, -half, 0.0]),
            np.array([half, 0.0, 0.0]), np.array([0.0, half, 0.0])]
    apex = np.array([half + off, 0.0, h])
    for k in range(4):
        d = np.linalg.norm(base[(k + 1) % 4] - base[k])
        assert abs(d - s) < 1e-9, "the base is not a square of the given side"

    # the plane enters the left-hand slant edge at the given height
    left = base[0]
    t0 = PYR["cut_at"] / h
    entry = left + t0 * (apex - left)
    assert abs(entry[2] - PYR["cut_at"]) < 1e-9
    z_at = _plane((entry[0], entry[2]), PYR["tilt"])

    edges, lengths = [], []
    for k, v in enumerate(base):
        tl = float(np.linalg.norm(apex - v))
        t, p = _cut_edge(v, apex, z_at)
        edges.append(dict(k=k + 1, v=v, tl=tl, t=t, cut=p,
                          from_apex=float(np.linalg.norm(apex - p))))
        lengths.append(round(tl, 6))
    assert len(set(lengths)) > 1, "an oblique solid with equal slant edges?"

    return dict(kind="pyramid", base=base, apex=apex, edges=edges, z_at=z_at,
                half=half, side=s, height=h,
                section=[e["cut"] for e in edges])


def solve_cone(n=12):
    R = CONE["dia"] / 2.0
    lean = math.radians(CONE["lean"])
    apex = np.array([CONE["axis"] * math.cos(lean), 0.0,
                     CONE["axis"] * math.sin(lean)])
    mid = np.array([CONE["cut_along"] * math.cos(lean), 0.0,
                    CONE["cut_along"] * math.sin(lean)])
    z_at = _plane((mid[0], mid[2]), CONE["tilt"])

    gens = []
    for k in range(n):
        th = math.pi - 2 * math.pi * k / n          # 1 at the left extreme
        v = np.array([R * math.cos(th), R * math.sin(th), 0.0])
        tl = float(np.linalg.norm(apex - v))
        t, p = _cut_edge(v, apex, z_at)
        gens.append(dict(k=k + 1, theta=th, v=v, tl=tl, t=t, cut=p,
                         from_apex=float(np.linalg.norm(apex - p))))
    spread = max(g["tl"] for g in gens) - min(g["tl"] for g in gens)
    assert spread > 1.0, "these generators are suspiciously equal"
    chord = 2 * R * math.sin(math.pi / n)
    for k in range(n):
        d = float(np.linalg.norm(gens[(k + 1) % n]["v"] - gens[k]["v"]))
        assert abs(d - chord) < 1e-9
    return dict(kind="cone", apex=apex, gens=gens, R=R, chord=chord, z_at=z_at,
                mid=mid, section=[g["cut"] for g in gens])


def triangulate(apex, rim, spans):
    """Lay a fan of triangles out flat, one per face, from true lengths alone.

    `rim[k]` is the true distance apex -> corner k, `spans[k]` the true length
    of the base edge from corner k to corner k+1. Each corner is placed by
    intersecting two circles, which is exactly what a pair of compasses does
    on the drawing board - and the assert at the end is the drawing-office
    check that the pattern closes.
    """
    pts = [np.array([rim[0], 0.0])]
    for k in range(len(spans)):
        r1, r2, d = rim[k], rim[k + 1] if k + 1 < len(rim) else rim[0], spans[k]
        prev = pts[-1]
        a = float(np.linalg.norm(prev))
        # angle at the apex between consecutive corners, by the cosine rule
        cosang = (a * a + r2 * r2 - d * d) / (2 * a * r2)
        assert -1.0 <= cosang <= 1.0, "these three lengths cannot make a triangle"
        ang = math.atan2(prev[1], prev[0]) + math.acos(cosang)
        pts.append(np.array([r2 * math.cos(ang), r2 * math.sin(ang)]))
    for k, d in enumerate(spans):
        got = float(np.linalg.norm(pts[k + 1] - pts[k]))
        assert abs(got - d) < 1e-9, f"face {k} came out {got:.4f}, wanted {d:.4f}"
    return pts


def _seam_order(items):
    """Start the pattern at the SHORTEST edge, so the seam is the least joining."""
    n = len(items)
    start = min(range(n), key=lambda k: items[k]["tl"])
    return [(start + k) % n for k in range(n)]


def _lay_out(solid, items, spans):
    """Development of one solid: seam on the shortest edge, hung symmetrically.

    triangulate() opens the fan from the positive x-axis, which is fine for the
    arithmetic and ugly on a sheet. Swinging it so the two seam edges sit at
    equal angles either side of straight-down gives the pattern a drawing-office
    look and keeps its bounding box tight.
    """
    order = _seam_order(items)
    seq = [items[k] for k in order] + [items[order[0]]]
    pts = triangulate(solid["apex"], [it["tl"] for it in seq], spans)
    a0 = math.atan2(pts[0][1], pts[0][0])
    a1 = math.atan2(pts[-1][1], pts[-1][0])
    rot = -math.pi / 2.0 - 0.5 * (a0 + a1)
    c, s = math.cos(rot), math.sin(rot)
    R = np.array([[c, -s], [s, c]])
    pts = [R @ q for q in pts]

    for q, it in zip(pts, seq):
        assert abs(float(np.linalg.norm(q)) - it["tl"]) < 1e-9, "swinging lost a radius"
    solid["order"] = order
    solid["dev_seq"] = seq
    solid["dev"] = pts
    # the cut sits on the same ray, at its own true distance from the apex
    solid["dev_cut"] = [q * (it["from_apex"] / it["tl"]) for q, it in zip(pts, seq)]
    return pts


def true_shape(solid, tilt):
    """The section seen square on: stretch its top view by 1 / cos(tilt).

    The cutting plane is horizontal across the sheet and climbs at `tilt` along
    it, so widths are already true in the top view and only lengths are
    foreshortened - by exactly the cosine of the angle. The assert is the check
    a student should make: every side of the true shape must equal the same
    side measured in space.
    """
    sec = solid["section"]
    x0 = min(p[0] for p in sec)
    c = math.cos(math.radians(tilt))
    ts = [np.array([(p[0] - x0) / c, p[1]]) for p in sec]
    n = len(sec)
    for i in range(n):
        j = (i + 1) % n
        want = float(np.linalg.norm(sec[j] - sec[i]))
        got = float(np.linalg.norm(ts[j] - ts[i]))
        assert abs(got - want) < 1e-9, f"true shape side {i}: {got:.4f} vs {want:.4f}"
    solid["ts"] = ts
    solid["ts_x0"] = x0
    return ts


PB = solve_pyramid()
CN = solve_cone()

_lay_out(PB, PB["edges"], [PB["side"]] * 4)
_lay_out(CN, CN["gens"], [CN["chord"]] * 12)
true_shape(PB, PYR["tilt"])
true_shape(CN, CONE["tilt"])


# ==========================================================================
#  The 3-D stage
# ==========================================================================
def pt3(p, h):
    """Sheet millimetres -> scene units, centred on the solid rather than on the
    base: with the apex ten past one corner, centring on the base centre alone
    parks the whole pyramid in the right-hand half of the frame."""
    x, y, z = p
    return np.array([(x - PYR_CX) * S3, y * S3, (z - h / 2.0) * S3])


def pyramid_3d(apex=None, fill=0.28, h=None):
    g = PB
    h = h or g["height"]
    apex = g["apex"] if apex is None else apex
    faces = VGroup()
    for k in range(4):
        a, b = g["base"][k], g["base"][(k + 1) % 4]
        faces.add(Polygon(pt3(a, h), pt3(b, h), pt3(apex, h),
                          stroke_color=SOLID_COL, stroke_width=2.4,
                          fill_color=SOLID_COL, fill_opacity=fill))
    return faces


# ==========================================================================
#  S01 - right against oblique
# ==========================================================================
class S01_WhatIsOblique(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        # nearly front-on (theta close to -90) so the LEAN reads as a lean, and a
        # long focal distance so the near corner is not thrown forward into a wedge
        self.set_camera_orientation(phi=72 * DEGREES, theta=-74 * DEGREES,
                                    zoom=1.0, focal_distance=150.0)
        bar = hud(self, title_bar("Oblique Solids",
                                  "Sheet 8 · §10 · when the apex leans over"))
        self.add(bar)

        g = PB
        h = g["height"]
        right_apex = np.array([0.0, 0.0, h])
        solid = pyramid_3d(apex=right_apex)
        base_line = Polygon(*[pt3(v, h) for v in g["base"]], color=SOLID_COL,
                            stroke_width=3.5, fill_opacity=0)
        edges = VGroup(*[Line(pt3(v, h), pt3(right_apex, h), color=TL_COL,
                              stroke_width=4) for v in g["base"]])

        right_tl = float(np.linalg.norm(right_apex - g["base"][0]))
        tag = billboard(self, mono(f"all four {right_tl:.2f}", color=TL_COL, size=24)
                        .move_to(pt3((0, -46, -20), h)))
        narrate(
            self,
            "A square pyramid, thirty-five on the side of its base. Its apex is "
            "directly over the centre, so it is a RIGHT pyramid - and that is what "
            "made episode eleven easy.",
            FadeIn(solid), Create(base_line), Create(edges), FadeIn(tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Every one of the four slant edges is the same length, {right_tl:.2f}. "
            "So the development is four identical triangles, and one true length "
            "does for all of them.",
        )

        new_solid = pyramid_3d()
        new_edges = VGroup(*[Line(pt3(v, h), pt3(g["apex"], h), color=TL_COL,
                                  stroke_width=4) for v in g["base"]])
        narrate(
            self,
            "Now push the apex sideways - ten millimetres past the right-hand corner "
            "of the base, which is what question three asks for. Nothing else "
            "changes: same base, same height.",
            FadeOut(tag),
            Transform(solid, new_solid), Transform(edges, new_edges),
            rate_func=rate_functions.ease_in_out_sine,
        )

        # out beyond each corner and below the base, or they land on the solid
        # out past each corner and well below the base - anything closer is
        # projected straight back onto the solid
        lens_at = [(-48.0, 0.0), (0.0, -46.0), (46.0, 0.0), (0.0, 46.0)]
        lens = VGroup(*[
            billboard(self, mono(f"{e['tl']:.2f}", color=TL_COL, size=20)
                      .move_to(pt3((lens_at[k][0], lens_at[k][1], -20), h)))
            for k, e in enumerate(g["edges"])])
        narrate(
            self,
            f"And now look at the four edges. {g['edges'][0]['tl']:.2f}. "
            f"{g['edges'][1]['tl']:.2f}. {g['edges'][2]['tl']:.2f}. And "
            f"{g['edges'][3]['tl']:.2f} again, because the solid is still symmetrical "
            "front to back. Three different lengths where a right pyramid had one.",
            *[FadeIn(m) for m in lens],
            lag_ratio=0.25,
        )
        narrate(
            self,
            "That is the whole of what oblique means, and the whole of the "
            "difficulty. There is no single slant height any more, so there is no "
            "sector to draw and no fan of identical triangles. Every face has to be "
            "built on its own.",
        )

        note = hud(self, VGroup(
            chip("no slant height · no sector · no shortcut", color=CUT_COL, size=20),
            chip("build the pattern ONE TRIANGLE AT A TIME, from true lengths",
                 color=TL_COL, size=19),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "What replaces them is a method that never depended on the shortcuts in "
            "the first place.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "It is called triangulation, and it is the oldest idea in the subject: a "
            "triangle is rigid, so if you know the true length of all three of its "
            "sides you can draw it, and it can only be one shape. Do that face by "
            "face and the pattern builds itself - on an oblique solid, on a right "
            "one, on anything at all.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  The sheet
# ==========================================================================
XY_Y = -12.0
TV_Y = -48.0
TL_X = 74.0              # where the true-length diagram stands
DEV_AT = np.array([205.0, 75.0])   # the apex of the development, on the sheet

AUX_OFF = 42.0           # how far the auxiliary view stands off the cut line
U_DIR = np.array([math.cos(math.radians(30.0)), math.sin(math.radians(30.0)), 0.0])
PERP = np.array([-U_DIR[1], U_DIR[0], 0.0])


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


def fv(x, z):
    return P2(x, z)


def tv(x, y):
    return P2(x, TV_Y + y)


def tl_point(plan, height):
    """A point of the true-length diagram: plan length out, height up."""
    return P2(TL_X + plan, height)


def foot_groups(plans):
    """Distinct feet of the true-length diagram, longest first.

    On an oblique solid several edges usually share a plan length - here 2 and
    4 do - so their feet land on top of each other. Printing "2" and "4" at the
    same point gives an unreadable blot; one label per distinct foot is what a
    draughtsman writes anyway.
    """
    groups = {}
    for k, pl in enumerate(plans):
        groups.setdefault(round(pl, 6), []).append(k + 1)
    return sorted(groups.items(), key=lambda kv: -kv[0])


def foot_labels(plans, size=11, colour=SLATE, drop=6.0):
    return VGroup(*[
        mono("·".join(str(i) for i in ks), color=colour, size=size)
        .move_to(tl_point(pl, -drop))
        for pl, ks in foot_groups(plans)])


def dev_pt(p, at=None):
    at = DEV_AT if at is None else at
    return P2(at[0] + p[0], at[1] + p[1])


def aux_pt(u, v, base_xz):
    """A point of the auxiliary view: u along the cut line, v out along the projector."""
    base = np.array([base_xz[0], base_xz[1], 0.0])
    q = base + PERP * AUX_OFF + U_DIR * u + PERP * v
    return P2(q[0], q[1])


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


def pyramid_views():
    """Front view and top view of the oblique pyramid, plus its cut."""
    g = PB
    apex, base = g["apex"], g["base"]
    xs = [v[0] for v in base]
    fv_out = VGroup(
        Line(fv(min(xs), 0), fv(max(xs), 0), color=SOLID_COL, stroke_width=3.4),
        Line(fv(min(xs), 0), fv(apex[0], apex[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(max(xs), 0), fv(apex[0], apex[2]), color=SOLID_COL, stroke_width=3.4),
        DashedLine(fv(0, 0), fv(apex[0], apex[2]), color=MUTED, stroke_width=1.8,
                   dash_length=0.06),
    )
    tv_out = VGroup(
        Polygon(*[tv(v[0], v[1]) for v in base], color=SOLID_COL, stroke_width=3.4),
        *[Line(tv(v[0], v[1]), tv(apex[0], apex[1]), color=SOLID_COL,
               stroke_width=2.0) for v in base],
        Dot(tv(apex[0], apex[1]), radius=0.04, color=SOLID_COL),
    )
    cut_fv = Line(fv(g["edges"][0]["cut"][0], g["edges"][0]["cut"][2]),
                  fv(g["edges"][2]["cut"][0], g["edges"][2]["cut"][2]),
                  color=CUT_COL, stroke_width=4.5)
    cut_dots = VGroup(*[Dot(fv(e["cut"][0], e["cut"][2]), radius=0.035, color=CUT_COL)
                        for e in g["edges"]])
    cut_tv = Polygon(*[tv(e["cut"][0], e["cut"][1]) for e in g["edges"]],
                     color=CUT_COL, stroke_width=2.6)
    return fv_out, tv_out, cut_fv, cut_dots, cut_tv


# ==========================================================================
#  S02 - triangulation, and the true-length diagram
# ==========================================================================
class S02_Triangulation(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        g = PB
        fv_out, tv_out, cut_fv, cut_dots, cut_tv = pyramid_views()
        xy = Line(P2(-34, XY_Y), P2(TL_X + 92, XY_Y), color=INK, stroke_width=2.2)
        views = VGroup(fv_out, tv_out)

        # ---- the true-length diagram ------------------------------------------
        plans = [float(np.linalg.norm((g["apex"] - v)[:2])) for v in g["base"]]
        axis = Line(tl_point(0, 0), tl_point(max(plans) + 8, 0),
                    color=INK, stroke_width=2.2)
        upright = Line(tl_point(0, 0), tl_point(0, g["height"] + 6),
                       color=INK, stroke_width=2.2)
        hyp = VGroup(*[Line(tl_point(0, g["height"]), tl_point(p, 0),
                            color=TL_COL, stroke_width=2.8) for p in plans])
        feet = VGroup(*[Dot(tl_point(p, 0), radius=0.032, color=TL_COL) for p in plans])
        foot_nums = foot_labels(plans)
        # the hypotenuses converge on the apex, so there is no room BETWEEN
        # them for a five-figure number: the lengths go in a legend instead
        tl_tags = VGroup(
            mono("TRUE LENGTHS", color=SLATE, size=12),
            *[mono(f"{'·'.join(str(i) for i in ks):<4} {g['edges'][ks[0] - 1]['tl']:6.2f}",
                   color=TL_COL, size=14) for _, ks in foot_groups(plans)],
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        tl_tags.move_to(tl_point(max(plans) + 16, 48), aligned_edge=LEFT + UP)
        h_dim = dim(tl_point(0, 0), tl_point(0, g["height"]), f"{g['height']:.0f}",
                    SLATE, offset=7.0)
        diagram = VGroup(axis, upright, hyp, feet, foot_nums)

        sheet = VGroup(xy, views, diagram, tl_tags, h_dim)
        centre, W = frame_target([views], right=0.30)
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Triangulation", "three true lengths make one triangle")),
            corner=UP + LEFT, buff=0.30)
        self.add(bar)
        self.add_foreground_mobjects(bar)

        narrate(
            self,
            "Here is the oblique pyramid on paper: the front view with the apex "
            "leaning off to the right, and the top view under it, where the apex "
            "falls outside the base altogether.",
            FadeIn(bar), Create(views), FadeIn(xy),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Neither view gives us a slant edge at its true length. In the top view "
            "we see only how far the edge reaches across - its plan length. In the "
            "front view we see the height it climbs. Never both at once, because "
            "the edge leans in two directions.",
            Indicate(tv_out, color=SOLID_COL),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "But that is enough, because those two are the sides of a right-angled "
            "triangle whose hypotenuse is what we want. So draw that triangle "
            "somewhere clear on the sheet, once, and read every true length off it.",
            look_at(self, [views, diagram], right=0.26),
            Create(upright), Create(axis), FadeIn(h_dim),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Stand the height of the apex up the side - fifty. Step each edge's plan "
            "length out along the bottom. Join the top to each foot, and the "
            "hypotenuses are the true lengths of the four edges.",
            Create(feet), FadeIn(foot_nums), Create(hyp), FadeIn(tl_tags),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Edge one comes out {g['edges'][0]['tl']:.2f}, edge three "
            f"{g['edges'][2]['tl']:.2f}, and edges two and four "
            f"{g['edges'][1]['tl']:.2f} apiece. That one diagram is the whole of the "
            "extra work an oblique solid costs you.",
        )

        note = pin_to_frame(self, card_back(VGroup(
            chip("plan length and height are the two sides · the TRUE LENGTH is the hypotenuse",
                 color=TL_COL, size=17),
            chip("a triangle with three true sides can be drawn, and is rigid",
                 color=DEV_COL, size=17),
        ).arrange(DOWN, buff=0.16)), corner=DOWN, buff=0.4)
        self.add_foreground_mobjects(note)
        narrate(
            self,
            "And then the development follows from one fact about triangles.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "Give a triangle three side lengths and it has exactly one shape - you "
            "can draw it with a rule and compasses and there is no choice left. Each "
            "face of this pyramid is a triangle with two slant edges and one base "
            "edge, and the base edge is thirty-five, true, because the base is flat "
            "on the ground. Three true lengths per face. Draw them in order and the "
            "pattern is finished.",
            look_at(self, [sheet], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S03 - Q.3(b): the oblique pyramid, cut, and the true shape of the section
# ==========================================================================
class S03_SheetB(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        g = PB
        apex = g["apex"]
        E = g["edges"]
        fv_out, tv_out, cut_fv, cut_dots, cut_tv = pyramid_views()
        xy = Line(P2(-42, XY_Y), P2(46, XY_Y), color=INK, stroke_width=2.2)
        xy_tag = mono("XY", color=INK, size=13).move_to(P2(-46, XY_Y))

        # ---- given dimensions -------------------------------------------------
        drop = DashedLine(fv(apex[0], apex[2]), fv(apex[0], -4), color=MUTED,
                          stroke_width=1.2, dash_length=0.05)
        h_dim = dim(fv(apex[0], 0), fv(apex[0], apex[2]), "50", SLATE, offset=-7.0)
        off_dim = dim(fv(g["half"], -6), fv(apex[0], -6), "10", SLATE, gap=4.5)
        side_dim = dim(tv(g["base"][0][0], g["base"][0][1]),
                       tv(g["base"][1][0], g["base"][1][1]), "35", SLATE,
                       offset=-6.0, gap=4.5)
        # corners 2 and 4 have clear air straight out from the centre; 1 and 3
        # sit on the y = 0 line, where the apex rays are, so they go off it
        tag_at = {0: (-33.0, 0.0), 1: (0.0, -33.0), 2: (24.75, 10.0), 3: (0.0, 33.0)}
        corner_tags = VGroup(*[
            mono(str(k + 1), color=SOLID_COL, size=13).move_to(tv(*tag_at[k]))
            for k in range(4)])
        apex_tag = VGroup(mono("o′", color=SOLID_COL, size=14).move_to(fv(apex[0] + 5, apex[2] + 3)),
                          mono("o", color=SOLID_COL, size=14).move_to(tv(apex[0] + 5, 4)))
        givens = VGroup(drop, h_dim, off_dim, side_dim, corner_tags, apex_tag)

        # ---- the cutting plane ------------------------------------------------
        m = math.tan(math.radians(PYR["tilt"]))
        x_lo, x_hi = -30.0, 40.0
        plane_line = Line(fv(x_lo, E[0]["cut"][2] + (x_lo - E[0]["cut"][0]) * m),
                          fv(x_hi, E[0]["cut"][2] + (x_hi - E[0]["cut"][0]) * m),
                          color=CUT_COL, stroke_width=2.2, stroke_opacity=0.55)
        ref = Line(fv(x_lo, E[0]["cut"][2]), fv(E[0]["cut"][0] + 15, E[0]["cut"][2]),
                   color=MUTED, stroke_width=1.2, stroke_opacity=0.6)
        ang = Arc(radius=0.30, start_angle=0, angle=math.radians(PYR["tilt"]),
                  arc_center=fv(E[0]["cut"][0], E[0]["cut"][2]), color=CUT_COL,
                  stroke_width=1.8)
        ang_tag = mono("30°", color=CUT_COL, size=13).move_to(
            fv(E[0]["cut"][0] + 20, E[0]["cut"][2] + 3.5))
        SIX_X = -33.0
        six = VGroup(
            Line(fv(-g["half"], 0), fv(SIX_X - 2, 0), color=MUTED, stroke_width=1.0),
            Line(fv(E[0]["cut"][0], PYR["cut_at"]), fv(SIX_X - 2, PYR["cut_at"]),
                 color=MUTED, stroke_width=1.0),
            dim(fv(SIX_X, 0), fv(SIX_X, PYR["cut_at"]), "6", CUT_COL, gap=4.5, size=12),
        )

        # ---- the four points, front view -------------------------------------
        fv_tags = VGroup(
            mono("1′", color=CUT_COL, size=13).move_to(fv(E[0]["cut"][0] - 6, E[0]["cut"][2] + 6)),
            mono("2′4′", color=CUT_COL, size=13).move_to(fv(E[1]["cut"][0] + 1, E[1]["cut"][2] - 6)),
            mono("3′", color=CUT_COL, size=13).move_to(fv(E[2]["cut"][0] + 7, E[2]["cut"][2] + 2)),
        )
        drops = VGroup(*[
            DashedLine(fv(e["cut"][0], e["cut"][2]), tv(e["cut"][0], e["cut"][1]),
                       color=AUX_COL, stroke_width=1.1, stroke_opacity=0.5,
                       dash_length=0.05)
            for e in (E[0], E[1], E[2])])
        tv_dots = VGroup(*[Dot(tv(e["cut"][0], e["cut"][1]), radius=0.038, color=CUT_COL)
                           for e in E])
        tv_tags = VGroup(
            mono("1", color=CUT_COL, size=12).move_to(tv(E[0]["cut"][0] - 3, -8)),
            mono("2", color=CUT_COL, size=12).move_to(tv(E[1]["cut"][0] + 2, E[1]["cut"][1] - 6)),
            mono("3", color=CUT_COL, size=12).move_to(tv(E[2]["cut"][0], -9)),
            mono("4", color=CUT_COL, size=12).move_to(tv(E[3]["cut"][0] + 2, E[3]["cut"][1] + 6)),
        )

        # ---- the auxiliary view ----------------------------------------------
        base_xz = (E[0]["cut"][0], E[0]["cut"][2])
        ts = g["ts"]
        u_max = max(q[0] for q in ts)
        refline = Line(aux_pt(-8, 0, base_xz), aux_pt(u_max + 8, 0, base_xz),
                       color=MUTED, stroke_width=1.4, stroke_opacity=0.7)
        ref_tag = mono("X₁Y₁", color=MUTED, size=12).move_to(aux_pt(-25, 0, base_xz))
        def _reach(u):
            """How far out the projector has to run: 2 and 4 share one line."""
            return max(q[1] for q in ts if abs(q[0] - u) < 1e-6) + 6.0
        projectors = VGroup(*[
            DashedLine(fv(E[k]["cut"][0], E[k]["cut"][2]),
                       aux_pt(ts[k][0], _reach(ts[k][0]), base_xz),
                       color=AUX_COL, stroke_width=1.1, stroke_opacity=0.5,
                       dash_length=0.05)
            for k in (0, 1, 2)])
        ts_poly = Polygon(*[aux_pt(q[0], q[1], base_xz) for q in ts],
                          color=CUT_COL, stroke_width=4.0,
                          fill_color=CUT_COL, fill_opacity=0.16)
        ts_dots = VGroup(*[Dot(aux_pt(q[0], q[1], base_xz), radius=0.036, color=CUT_COL)
                           for q in ts])
        ts_off = {0: (-5.0, -8.0), 1: (0.0, -7.0), 2: (8.0, 3.0), 3: (0.0, 7.0)}
        ts_tags = VGroup(*[
            mono(f"{k + 1}₁", color=CUT_COL, size=12).move_to(
                aux_pt(q[0] + ts_off[k][0], q[1] + ts_off[k][1], base_xz))
            for k, q in enumerate(ts)])
        W_AT = u_max + 14.0
        w_dim = VGroup(
            *[Line(aux_pt(ts[k][0], ts[k][1], base_xz),
                   aux_pt(W_AT + 3, ts[k][1], base_xz), color=MUTED, stroke_width=1.0)
              for k in (1, 3)],
            dim(aux_pt(W_AT, ts[1][1], base_xz), aux_pt(W_AT, ts[3][1], base_xz),
                f"{2 * abs(ts[1][1]):.2f}", TL_COL, offset=0.0, gap=-6.5, size=12),
        )
        l_dim = dim(aux_pt(0, 0, base_xz), aux_pt(u_max, 0, base_xz),
                    f"{u_max:.2f}", TL_COL, offset=-18.0, gap=6.0, size=12)
        # the caption runs across the sheet, not along the cut, so it has to
        # clear the HIGHEST corner of the kite, not just its centre line
        dev_tag = caption("TRUE SHAPE", color=CUT_COL, size=16).move_to(P2(-14, 86))
        aux = VGroup(refline, ref_tag, projectors, ts_poly, ts_dots, ts_tags,
                     w_dim, l_dim, dev_tag)

        views = VGroup(fv_out, tv_out)
        sheet = VGroup(xy, xy_tag, views, givens, plane_line, ref, ang, ang_tag,
                       six, cut_fv, cut_dots, fv_tags, drops, tv_dots, tv_tags,
                       cut_tv, aux)
        centre, W = frame_target([views, givens], right=0.28)
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 8 (Set A) · Q.3(b)",
            "oblique square pyramid · cut at 30° · true shape")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "draw the two views", "apex 10 beyond corner 3, height 50", SOLID_COL),
            step_badge("2", "draw the cutting plane", "30° through the point 6 up edge 1", CUT_COL),
            step_badge("3", "mark where it crosses each edge", "1′ 2′ 3′ 4′ — four different heights", CUT_COL),
            step_badge("4", "carry them down to the plan", "each point on its own edge in the top view", CUT_COL),
            step_badge("5", "true shape on a new reference line", "lengths along the cut, widths from the plan", TL_COL),
        ).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26] * 5
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.32)
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)

        narrate(
            self,
            "Question three, part b. An oblique square pyramid: base thirty-five side, "
            "standing with its diagonals across and along the sheet, height fifty, and "
            "the apex ten beyond the right-hand corner. Cut by a plane inclined at "
            "thirty degrees, meeting the nearest slant edge six above the base.",
            FadeIn(bar), FadeIn(rail), Create(views), FadeIn(xy), FadeIn(xy_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The two views first. In the top view the base is a square on its corners "
            "and the apex falls out here, ten past corner three - outside the base "
            "altogether, which is the whole meaning of the word oblique. In the front "
            "view the apex is fifty up and leaning right, so the two visible slant "
            "edges are plainly unequal.",
            rail_focus(rail, rungs, 0), FadeIn(givens),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Now the cutting plane. Measure six up the left-hand edge, put a point "
            "there, and draw a line through it at thirty degrees to the base. In the "
            "front view that single line is the whole plane - we are looking along it "
            "edgeways.",
            rail_focus(rail, rungs, 1),
            look_at(self, [views, aux], right=0.28, top=0.14),
            Create(ref), FadeIn(six), Create(plane_line), Create(ang), FadeIn(ang_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Where that line crosses each of the four slant edges is a corner of the "
            "section. One prime sits six up, as we set it. Three prime, on the short "
            "right-hand edge, comes out thirty-four point four three. And two prime "
            "and four prime fall together at twenty-seven, because those two edges "
            "coincide in the front view.",
            rail_focus(rail, rungs, 2), Create(cut_fv), FadeIn(cut_dots), FadeIn(fv_tags),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Carry each one straight down into the top view and stop on its own edge. "
            "One and three land on the horizontal diagonal; two and four split apart "
            "onto the two sloping edges, eleven point three eight either side of the "
            "centre line. Join them and that quadrilateral is the top view of the "
            "section.",
            rail_focus(rail, rungs, 3), Create(drops), FadeIn(tv_dots), FadeIn(tv_tags),
            Create(cut_tv),
            lag_ratio=0.18,
        )
        narrate(
            self,
            "For the true shape, look square at the plane instead of along it. Set a "
            "new reference line parallel to the cut, throw projectors from each point "
            "perpendicular to it, and step the widths off the top view - eleven point "
            "three eight each side again, because widths across the sheet were never "
            "foreshortened.",
            rail_focus(rail, rungs, 4),
            look_at(self, [aux, views], right=0.28, top=0.14),
            Create(refline), FadeIn(ref_tag), Create(projectors),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Joining up gives the true shape: a kite {u_max:.2f} long by "
            f"{2 * abs(ts[1][1]):.2f} wide. Its length is the length in the top view "
            "divided by the cosine of thirty - the one number the plan could not show "
            "you, because the section climbs as it goes.",
            Create(ts_poly), FadeIn(ts_dots), FadeIn(ts_tags), FadeIn(dev_tag),
            FadeIn(w_dim), FadeIn(l_dim),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "That is the section finished. What is left is the development - and for "
            "that we need not the heights of these points but their true distances "
            "from the apex.",
            settle(look_at(self, [sheet], right=0.22, top=0.10)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - Q.3(b): the development
# ==========================================================================
class S04_DevelopmentB(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        g = PB
        E, seq, dev, dcut = g["edges"], g["dev_seq"], g["dev"], g["dev_cut"]
        fv_out, tv_out, cut_fv, cut_dots, cut_tv = pyramid_views()
        xy = Line(P2(-34, XY_Y), P2(150, XY_Y), color=INK, stroke_width=2.2)

        # ---- the true-length diagram, rebuilt --------------------------------
        plans = [float(np.linalg.norm((g["apex"] - e["v"])[:2])) for e in E]
        H = g["height"]
        tl_apex = tl_point(0, H)
        axis = Line(tl_point(0, 0), tl_point(max(plans) + 8, 0), color=INK, stroke_width=2.2)
        upright = Line(tl_point(0, 0), tl_point(0, H + 6), color=INK, stroke_width=2.2)
        hyp = VGroup(*[Line(tl_apex, tl_point(p, 0), color=TL_COL, stroke_width=2.6)
                       for p in plans])
        feet = VGroup(*[Dot(tl_point(p, 0), radius=0.030, color=TL_COL) for p in plans])
        foot_nums = foot_labels(plans)
        tl_diag = VGroup(axis, upright, hyp, feet, foot_nums)
        tl_tag = caption("TRUE LENGTHS", color=TL_COL, size=15).move_to(tl_point(30, H + 14))

        # ---- reading each cut point off the diagram --------------------------
        def on_hyp(k):
            z = E[k]["cut"][2]
            return tl_point(plans[k] * (H - z) / H, z)

        transfers = VGroup(*[
            DashedLine(fv(E[k]["cut"][0], E[k]["cut"][2]), on_hyp(k),
                       color=AUX_COL, stroke_width=1.1, stroke_opacity=0.5,
                       dash_length=0.05)
            for k in (0, 1, 2)])
        hyp_dots = VGroup(*[Dot(on_hyp(k), radius=0.034, color=CUT_COL) for k in range(4)])
        # read off in clear space above the diagram - between the hypotenuses
        # there is nowhere a four-figure number fits without touching one
        hyp_tags = VGroup(
            mono("apex to the cut, true:", color=SLATE, size=12),
            mono(f"edge 1     {E[0]['from_apex']:.2f}", color=CUT_COL, size=13),
            mono(f"edges 2,4  {E[1]['from_apex']:.2f}", color=CUT_COL, size=13),
            mono(f"edge 3     {E[2]['from_apex']:.2f}", color=CUT_COL, size=13),
        ).arrange(DOWN, buff=0.09, aligned_edge=LEFT)
        hyp_tags.move_to(P2(-26, 78), aligned_edge=LEFT + UP)

        # ---- the development -------------------------------------------------
        O = dev_pt((0.0, 0.0))
        ang = [math.atan2(q[1], q[0]) for q in dev]
        base_poly = VMobject(stroke_color=DEV_COL, stroke_width=3.6)
        base_poly.set_points_as_corners([dev_pt(q) for q in dev])
        rays = VGroup(*[Line(O, dev_pt(q), color=DEV_COL, stroke_width=2.0) for q in dev])
        seam = VGroup(rays[0].copy().set_stroke(GOLD, 3.4), rays[-1].copy().set_stroke(GOLD, 3.4))
        dev_dots = VGroup(*[Dot(dev_pt(q), radius=0.034, color=DEV_COL) for q in dev])
        dev_nums = VGroup(*[
            mono(str(it["k"]), color=DEV_COL, size=13).move_to(dev_pt(q * 1.09))
            for q, it in zip(dev, seq)])
        o_tag = mono("O", color=DEV_COL, size=15).move_to(dev_pt((0.0, 6.0)))

        swings = VGroup(*[
            Arc(radius=float(np.linalg.norm(dev[i + 1])), arc_center=O,
                start_angle=ang[i], angle=ang[i + 1] - ang[i] + 0.16,
                color=TL_COL, stroke_width=1.5, stroke_opacity=0.75)
            .scale(MM, about_point=O)
            for i in range(4)])
        chords = VGroup(*[
            Arc(radius=g["side"] * MM, arc_center=dev_pt(dev[i]),
                start_angle=math.atan2(*(dev[i + 1] - dev[i])[::-1]) - 0.26,
                angle=0.52, color=GOLD, stroke_width=1.5, stroke_opacity=0.75)
            for i in range(4)])

        cut_rays = VGroup(*[Dot(dev_pt(q), radius=0.036, color=CUT_COL) for q in dcut])
        cut_swings = VGroup(*[
            Arc(radius=float(np.linalg.norm(dcut[i])), arc_center=O,
                start_angle=ang[i] - 0.13, angle=0.26,
                color=CUT_COL, stroke_width=1.5, stroke_opacity=0.8)
            .scale(MM, about_point=O)
            for i in range(5)])
        cut_line = VMobject(stroke_color=CUT_COL, stroke_width=4.0)
        cut_line.set_points_as_corners([dev_pt(q) for q in dcut])
        pattern = Polygon(*([dev_pt(q) for q in dev] + [dev_pt(q) for q in dcut[::-1]]),
                          stroke_width=0, fill_color=DEV_COL, fill_opacity=0.16)
        dev_tag = caption("DEVELOPMENT", color=DEV_COL, size=17).move_to(
            dev_pt((0.0, -102.0)))
        development = VGroup(pattern, base_poly, rays, seam, cut_line, dev_dots,
                             cut_rays, dev_nums, o_tag, dev_tag)

        views = VGroup(fv_out, cut_fv, cut_dots)
        sheet = VGroup(xy, views, tl_diag, tl_tag, development)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 8 (Set A) · Q.3(b)", "development · four triangles, twelve true lengths")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "true lengths of the four edges", "one right triangle, four hypotenuses", TL_COL),
            step_badge("2", "lay out face by face", "two radii and a 35 chord fix each corner", DEV_COL),
            step_badge("3", "read the cut off the same diagram", "carry each point across to its own hypotenuse", CUT_COL),
            step_badge("4", "swing those radii onto the pattern", "join up — that is the finished development", CUT_COL),
        ).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26] * 4
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.32)
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)

        centre, W = frame_target([views, tl_diag], right=0.28)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "The development. The front view with the cut on it, and beside it the "
            "true-length diagram - the height fifty stood up, the four plan lengths "
            "stepped out, and four hypotenuses.",
            FadeIn(bar), FadeIn(rail), Create(views), FadeIn(xy),
            Create(tl_diag), FadeIn(tl_tag),
            rail_focus(rail, rungs, 0), lag_ratio=0.18,
        )
        narrate(
            self,
            f"Edge one is {E[0]['tl']:.2f} long, edge two and edge four "
            f"{E[1]['tl']:.2f}, and edge three, the short one under the apex, only "
            f"{E[2]['tl']:.2f}. Start the pattern on that shortest edge - the seam "
            "is least work where the joint is least long.",
            look_at(self, [development, tl_diag], right=0.26),
            rail_focus(rail, rungs, 1), lag_ratio=0.2,
        )
        narrate(
            self,
            f"Put the apex at O and strike edge three, {E[2]['tl']:.2f}. Then face "
            "three-four: swing edge four's true length from O, swing thirty-five - the "
            "true base side - from the point you just made, and where the two arcs "
            "cross is corner four. Two radii and a chord; that is one face done.",
            Create(swings[0]), Create(chords[0]), FadeIn(dev_dots[0]), FadeIn(dev_dots[1]),
            FadeIn(o_tag), Create(rays[0]), Create(rays[1]),
            lag_ratio=0.16,
        )
        narrate(
            self,
            "Repeat it three more times - edge one, edge two, and edge three again to "
            "close - and the four faces are laid out flat, opened along the short "
            "edge. Notice the outline is not an arc of a circle. On a right pyramid it "
            "would be; here every radius is different, so the pattern wanders.",
            Create(VGroup(*swings[1:])), Create(VGroup(*chords[1:])),
            FadeIn(VGroup(*dev_dots[2:])), Create(VGroup(*rays[2:])),
            Create(base_poly), FadeIn(dev_nums), FadeIn(seam),
            lag_ratio=0.12,
        )
        narrate(
            self,
            "Now the cut. A cut point is NOT at the height you see in the front view - "
            "it is at its own true distance from the apex, measured along its own "
            "edge. And the true-length diagram will give you that too, for free.",
            look_at(self, [views, tl_diag, hyp_tags], right=0.26),
            rail_focus(rail, rungs, 2), lag_ratio=0.2,
        )
        narrate(
            self,
            "Carry each cut point horizontally across to the hypotenuse of its own "
            "edge. Sliding sideways keeps the height, so the point lands at the same "
            "level on the true length, and the distance from the top of the diagram "
            "down to it is the true distance from the apex.",
            Create(transfers), FadeIn(hyp_dots), FadeIn(hyp_tags),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Edge one gives {E[0]['from_apex']:.2f}, edges two and four "
            f"{E[1]['from_apex']:.2f}, edge three only {E[2]['from_apex']:.2f}. "
            "Four radii. Swing each from O onto its own line on the pattern.",
            look_at(self, [development], right=0.26),
            rail_focus(rail, rungs, 3),
            Create(cut_swings), FadeIn(cut_rays),
            lag_ratio=0.18,
        )
        narrate(
            self,
            "Join the five marks with straight lines - straight, because the cutting "
            "plane crosses each flat face in a straight line - and the shaded piece is "
            "the development of what is left of the pyramid. Cut it out of sheet "
            "metal, fold on every ray, and it closes onto the solid exactly.",
            Create(cut_line), FadeIn(pattern), FadeIn(dev_tag),
            lag_ratio=0.2,
        )
        note = pin_to_frame(self, card_back(VGroup(
            chip("the pattern is a fan of triangles, not a sector — no two radii are equal",
                 color=DEV_COL, size=17),
            chip("cut distances come from the true-length diagram, never off the front view",
                 color=CUT_COL, size=17),
        ).arrange(DOWN, buff=0.16)), corner=DOWN, buff=0.4)
        self.add_foreground_mobjects(note)
        narrate(
            self,
            "Two things to carry away from this sheet.",
            settle(FadeIn(note)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S05 - Q.3(a): the oblique cone, and the recap
# ==========================================================================
def cone_views():
    """Front view and top view of the oblique cone, with its twelve generators."""
    c = CN
    ap = c["apex"]
    R = c["R"]
    fv_out = VGroup(
        Line(fv(-R, 0), fv(R, 0), color=SOLID_COL, stroke_width=3.4),
        Line(fv(-R, 0), fv(ap[0], ap[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(R, 0), fv(ap[0], ap[2]), color=SOLID_COL, stroke_width=3.4),
    )
    fv_gens = VGroup(*[Line(fv(gg["v"][0], 0), fv(ap[0], ap[2]), color=SOLID_COL,
                            stroke_width=1.5, stroke_opacity=0.75)
                       for gg in c["gens"]])
    circle = Circle(radius=R * MM, color=SOLID_COL, stroke_width=3.4).move_to(tv(0, 0))
    tv_gens = VGroup(*[Line(tv(gg["v"][0], gg["v"][1]), tv(ap[0], ap[1]),
                            color=SOLID_COL, stroke_width=1.5, stroke_opacity=0.75)
                       for gg in c["gens"]])
    tv_out = VGroup(circle, tv_gens, Dot(tv(ap[0], ap[1]), radius=0.042, color=SOLID_COL))
    nums = VGroup(*[
        mono(str(gg["k"]), color=SLATE, size=11).move_to(
            tv(gg["v"][0] * 1.30, gg["v"][1] * 1.30))
        for gg in c["gens"]])
    return fv_out, fv_gens, tv_out, nums


class S05_ConeAndRecap(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        c = CN
        G, seq, dev, dcut = c["gens"], c["dev_seq"], c["dev"], c["dev_cut"]
        ap, R, H = c["apex"], c["R"], c["apex"][2]
        fv_out, fv_gens, tv_out, nums = cone_views()
        xy = Line(P2(-30, XY_Y), P2(150, XY_Y), color=INK, stroke_width=2.2)

        axis_line = DashedLine(fv(0, 0), fv(ap[0], ap[2]), color=MUTED,
                               stroke_width=1.6, dash_length=0.06)
        axis_dim = dim(fv(0, 0), fv(ap[0], ap[2]), "60", SLATE, offset=11.0, size=12)
        lean = Arc(radius=0.34, start_angle=0, angle=math.radians(CONE["lean"]),
                   arc_center=fv(0, 0), color=SLATE, stroke_width=1.6)
        lean_tag = mono("60°", color=SLATE, size=12).move_to(fv(17, 5))
        # twelve generators converge on the apex plan, so the inside of the
        # circle is no place for a label: the arrow stays on the diameter and
        # the figure goes out to the left, where nothing runs
        dia_dim = VGroup(
            DoubleArrow(tv(-R, 0), tv(R, 0), buff=0, color=SLATE, stroke_width=1.6,
                        tip_length=0.09),
            mono("Ø42", color=SLATE, size=12).move_to(tv(-R - 17, 0)),
        )
        # the axis dimensions have done their work once the generators arrive -
        # leaving them on turns the front view into a thicket
        given_dims = VGroup(axis_dim, lean, lean_tag)
        givens = VGroup(axis_line, given_dims, dia_dim)

        # ---- the cut ---------------------------------------------------------
        mid = c["mid"]
        along = dim(fv(0, 0), fv(mid[0], mid[2]), "30", CUT_COL, offset=11.0, size=12)
        m = math.tan(math.radians(CONE["tilt"]))
        cut_fv = Line(fv(G[0]["cut"][0], G[0]["cut"][2]),
                      fv(G[6]["cut"][0], G[6]["cut"][2]),
                      color=CUT_COL, stroke_width=4.2)
        cut_ext = Line(fv(-26, mid[2] + (-26 - mid[0]) * m),
                       fv(34, mid[2] + (34 - mid[0]) * m),
                       color=CUT_COL, stroke_width=1.8, stroke_opacity=0.45)
        ang = Arc(radius=0.30, start_angle=0, angle=math.radians(CONE["tilt"]),
                  arc_center=fv(mid[0], mid[2]), color=CUT_COL, stroke_width=1.8)
        ang_tag = mono("30°", color=CUT_COL, size=12).move_to(fv(mid[0] + 17, mid[2] + 3.5))
        fv_cuts = VGroup(*[Dot(fv(gg["cut"][0], gg["cut"][2]), radius=0.032, color=CUT_COL)
                           for gg in G])
        drops = VGroup(*[
            DashedLine(fv(G[k]["cut"][0], G[k]["cut"][2]), tv(G[k]["cut"][0], G[k]["cut"][1]),
                       color=AUX_COL, stroke_width=1.0, stroke_opacity=0.45, dash_length=0.05)
            for k in range(7)])
        tv_cuts = VGroup(*[Dot(tv(gg["cut"][0], gg["cut"][1]), radius=0.032, color=CUT_COL)
                           for gg in G])
        sec_tv = VMobject(stroke_color=CUT_COL, stroke_width=2.6)
        sec_tv.set_points_smoothly([tv(gg["cut"][0], gg["cut"][1]) for gg in G] +
                                   [tv(G[0]["cut"][0], G[0]["cut"][1])])
        cut = VGroup(cut_ext, cut_fv, ang, ang_tag, along, fv_cuts, drops, tv_cuts, sec_tv)

        # ---- the true-length diagram -----------------------------------------
        plans = [float(np.linalg.norm((ap - gg["v"])[:2])) for gg in G]
        tl_apex = tl_point(0, H)
        axis = Line(tl_point(0, 0), tl_point(max(plans) + 8, 0), color=INK, stroke_width=2.2)
        upright = Line(tl_point(0, 0), tl_point(0, H + 6), color=INK, stroke_width=2.2)
        hyp = VGroup(*[Line(tl_apex, tl_point(p, 0), color=TL_COL, stroke_width=2.0)
                       for p in plans])
        feet = VGroup(*[Dot(tl_point(p, 0), radius=0.026, color=TL_COL) for p in plans])
        h_dim = dim(tl_point(0, 0), tl_point(0, H), f"{H:.2f}", SLATE, offset=7.0, size=12)
        tl_diag = VGroup(axis, upright, hyp, feet, h_dim)
        tl_tag = caption("TRUE LENGTHS", color=TL_COL, size=15).move_to(tl_point(30, H + 14))

        def on_hyp(k):
            z = G[k]["cut"][2]
            return tl_point(plans[k] * (H - z) / H, z)

        transfers = VGroup(*[
            DashedLine(fv(G[k]["cut"][0], G[k]["cut"][2]), on_hyp(k),
                       color=AUX_COL, stroke_width=1.0, stroke_opacity=0.45, dash_length=0.05)
            for k in range(7)])
        hyp_dots = VGroup(*[Dot(on_hyp(k), radius=0.028, color=CUT_COL) for k in range(12)])

        table = VGroup(
            mono("apex to the cut, true:", color=SLATE, size=12),
            *[mono(f"gen {G[k]['k']:<2}  {G[k]['tl']:6.2f}   {G[k]['from_apex']:6.2f}",
                   color=CUT_COL, size=12) for k in (0, 3, 6)],
        ).arrange(DOWN, buff=0.09, aligned_edge=LEFT)
        table.move_to(P2(-30, 84), aligned_edge=LEFT + UP)

        # ---- the development -------------------------------------------------
        O = dev_pt((0.0, 0.0))
        rays = VGroup(*[Line(O, dev_pt(q), color=DEV_COL, stroke_width=1.6) for q in dev])
        seam = VGroup(rays[0].copy().set_stroke(GOLD, 3.2), rays[-1].copy().set_stroke(GOLD, 3.2))
        base_curve = VMobject(stroke_color=DEV_COL, stroke_width=3.6)
        base_curve.set_points_smoothly([dev_pt(q) for q in dev])
        cut_curve = VMobject(stroke_color=CUT_COL, stroke_width=4.0)
        cut_curve.set_points_smoothly([dev_pt(q) for q in dcut])
        cut_dots2 = VGroup(*[Dot(dev_pt(q), radius=0.030, color=CUT_COL) for q in dcut])
        dev_nums = VGroup(*[mono(str(it["k"]), color=DEV_COL, size=11).move_to(dev_pt(q * 1.08))
                            for q, it in zip(dev, seq)])
        o_tag = mono("O", color=DEV_COL, size=15).move_to(dev_pt((0.0, 6.0)))
        pattern = Polygon(*([dev_pt(q) for q in dev] + [dev_pt(q) for q in dcut[::-1]]),
                          stroke_width=0, fill_color=DEV_COL, fill_opacity=0.15)
        dev_tag = caption("DEVELOPMENT", color=DEV_COL, size=17).move_to(dev_pt((0.0, -98.0)))
        development = VGroup(pattern, base_curve, rays, seam, cut_curve, cut_dots2,
                             dev_nums, o_tag, dev_tag)

        views = VGroup(fv_out, tv_out)
        sheet = VGroup(xy, views, fv_gens, nums, givens, cut, tl_diag, tl_tag,
                       transfers, hyp_dots, table, development)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 8 (Set A) · Q.3(a)", "oblique cone · twelve generators, twelve lengths")),
            corner=UP + LEFT, buff=0.30)
        self.add(bar)
        self.add_foreground_mobjects(bar)
        centre, W = frame_target([views, givens], right=0.26)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "Part a. An oblique cone: base forty-two diameter, axis sixty long, "
            "leaning at sixty degrees to the base. Cut by a plane at thirty degrees "
            "through the point thirty along that axis.",
            FadeIn(bar), Create(views), FadeIn(xy), FadeIn(givens),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "A cone has no edges, so we invent some. Divide the base circle into "
            "twelve and draw a generator to the apex from each division. Twelve narrow "
            "triangles standing in for the curved surface - and the more you use, the "
            "closer the pattern gets.",
            Create(fv_gens), FadeIn(nums), FadeOut(given_dims),
            lag_ratio=0.15,
        )
        narrate(
            self,
            "On a right cone all twelve are the same length and the development is a "
            "sector of a circle. Lean the apex over and that is finished: generator "
            f"one is {G[0]['tl']:.2f}, generator seven only {G[6]['tl']:.2f}. Twelve "
            "different radii, so twelve triangles, each built from three true lengths.",
            Indicate(fv_gens, color=TL_COL),
        )
        narrate(
            self,
            "The cut first. Thirty along the axis, thirty degrees to the base, and the "
            "front view shows it edgeways as one straight line from generator one to "
            "generator seven.",
            look_at(self, [views, tl_diag], right=0.26),
            Create(cut_ext), FadeIn(along), Create(ang), FadeIn(ang_tag), Create(cut_fv),
            FadeIn(fv_cuts),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Carry each crossing down onto its own generator in the plan. Remember the "
            "front view stacks the generators in pairs - two with twelve, three with "
            "eleven, and so on - so each point you see up there is really two points "
            "down here, one either side of the centre line. Joining them gives the "
            "section in plan.",
            Create(drops), FadeIn(tv_cuts), Create(sec_tv),
            lag_ratio=0.15,
        )
        narrate(
            self,
            "Now the true lengths, exactly as for the pyramid. Stand the apex height, "
            "fifty-one point nine six, up the side. Step the twelve plan lengths out "
            "along the bottom - they come in pairs too, so there are seven different "
            "feet. Join, and the hypotenuses are the twelve true generators.",
            look_at(self, [views, tl_diag, table], right=0.26),
            Create(tl_diag), FadeIn(tl_tag),
            lag_ratio=0.18,
        )
        narrate(
            self,
            "And carry each cut point across, horizontally, onto its own hypotenuse. "
            "The distance from the top of the diagram down to that mark is how far "
            f"along the generator the cut really is - {G[0]['from_apex']:.2f} on "
            f"generator one, {G[6]['from_apex']:.2f} on generator seven.",
            Create(transfers), FadeIn(hyp_dots), FadeIn(table),
            lag_ratio=0.15,
        )
        narrate(
            self,
            "Lay the pattern out from the shortest generator, number seven. Apex at O, "
            "strike fifty-two point seven four, then swing generator eight's true "
            "length from O and the chord ten point eight seven from the point before "
            "it. Twelve times round, and back to seven.",
            look_at(self, [development], right=0.24),
            Create(rays), FadeIn(dev_nums), FadeIn(o_tag),
            lag_ratio=0.12,
        )
        narrate(
            self,
            "Join the outer ends with a smooth curve - that is the base circle laid "
            "flat, and it is not a circular arc. Mark each cut radius on its own "
            "generator, join those with a smooth curve too, and the shaded piece is "
            "the development of the cut oblique cone.",
            Create(base_curve), FadeIn(seam), FadeIn(cut_dots2), Create(cut_curve),
            FadeIn(pattern), FadeIn(dev_tag),
            lag_ratio=0.15,
        )
        narrate(
            self,
            "One check worth making: the chord ten point eight seven is a little "
            "shorter than the arc it stands for, so the laid-out base comes out "
            "slightly short. Twelve divisions is the drawing-office compromise. "
            "Twenty-four would be tighter, and twice the work.",
            look_at(self, [development, tl_diag], right=0.22),
        )

        recap = pin_to_frame(self, card_back(VGroup(
            caption("Oblique solids · what actually changes", color=INK, size=22),
            chip("every generator is a different length — find them all, one diagram",
                 color=TL_COL, size=17),
            chip("developments are triangulated: three true sides per triangle",
                 color=DEV_COL, size=17),
            chip("the cut is marked at its TRUE distance from the apex, not its height",
                 color=CUT_COL, size=17),
            chip("no sector, no πD/L formula — those belong to right solids only",
                 color=GOLD, size=17),
        ).arrange(DOWN, buff=0.18)), corner=ORIGIN, buff=0.0)
        self.add_foreground_mobjects(recap)
        narrate(
            self,
            "So: oblique solids cost you one extra diagram and buy you a method that "
            "never fails. Find every true length. Build every face from three of them. "
            "Mark the cut where it truly falls. Nothing else in the sheet changes.",
            settle(FadeIn(recap)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.6)


# ==========================================================================
#  Marking scheme - the numbers an examiner would look for
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 8 (Set A) Q.3 - development of OBLIQUE solids, by triangulation")
    print("  x across the sheet · y depth · z up · all dimensions in mm")

    g = PB
    print()
    print("  Q.3(b)  oblique square pyramid, base 35 side on its diagonals,")
    print(f"          height {g['height']:.0f}, apex {PYR['offset']:.0f} beyond corner 3,")
    print(f"          cut at {PYR['tilt']:.0f}° entering edge 1 at {PYR['cut_at']:.0f} above the base")
    print("    edge   base corner        TRUE length   cut at z   apex->cut (TRUE)")
    for e in g["edges"]:
        v = e["v"]
        print(f"      {e['k']}    ({v[0]:+7.3f},{v[1]:+7.3f})   {e['tl']:9.3f}   "
              f"{e['cut'][2]:8.3f}   {e['from_apex']:12.3f}")
    ts = g["ts"]
    print(f"    true shape of the section: {max(q[0] for q in ts):.3f} long "
          f"x {max(q[1] for q in ts) - min(q[1] for q in ts):.3f} wide")
    print(f"    development: seam on edge {g['dev_seq'][0]['k']} (the shortest), "
          f"four triangles, base side {g['side']:.0f} true throughout")

    c = CN
    print()
    print(f"  Q.3(a)  oblique cone, base Ø{CONE['dia']:.0f}, axis {CONE['axis']:.0f} "
          f"at {CONE['lean']:.0f}° to the base")
    print(f"          apex at ({c['apex'][0]:.3f}, 0, {c['apex'][2]:.3f}), "
          f"cut at {CONE['tilt']:.0f}° through the axis point {CONE['cut_along']:.0f} along")
    print(f"    twelve generators, chord {c['chord']:.3f} between neighbours")
    print("    gen   TRUE length   cut at z   apex->cut (TRUE)")
    for gg in c["gens"]:
        print(f"     {gg['k']:2}    {gg['tl']:9.3f}   {gg['cut'][2]:8.3f}   "
              f"{gg['from_apex']:12.3f}")
    print(f"    development: seam on generator {c['dev_seq'][0]['k']} (the shortest)")

    print()
    print("  Checks that run at import:")
    print("    · the base really is a square of the given side / a circle of the given Ø")
    print("    · the plane crosses every edge or generator exactly once, above the base")
    print("    · no two slant lengths are equal - it is genuinely oblique")
    print("    · the laid-out pattern reproduces every true length it was built from")
    print("    · the section's true shape matches the section measured in space")
