"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 12: Prisms - the development is a polygon, not a curve
            + worked solutions to Exercise 7 (Set A), Q.2(b), (c) and (d)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed12_prisms.py S02_SheetB
    ... or use render_ed12.bat to build all four scenes in order.

Scene order (about ten minutes in all):

    S01_FoldItOut    a prism unrolled by hinging each face flat about the edge
                     it shares with the last one - the polygon's answer to the
                     cylinder's roll, and just as exact
    S02_SheetB       Q.2(b) in full: the triangular prism cut at 30 degrees,
                     its three edge heights, the development, and the true
                     shape of the section
    S03_TwoPlanes    Q.2(c) and (d), where TWO planes cut the solid and the
                     junction between them falls in the middle of a face - so
                     the development gets a corner where there is no edge
    S04_Recap        prisms against cylinders, and the one number people get
                     wrong

Everything is computed by solve_prism(), which asserts that the development is
exactly the perimeter wide, that every edge height matches the plane that cuts
it, that a face crossed by the junction is given its extra point, and that the
true shape of the section is the right size. A wrong number stops the render.

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
DEV_COL = VIOLET
TL_COL = TEAL
AUX_COL = CREAM

MM = 0.030
S3 = 0.042

# ==========================================================================
#  Figure P7.2 (b), (c) and (d).
#
#  (b) and (c) are the same triangular prism - 40 side, 50 high, the apex of
#  the triangle pointing at the observer - cut two different ways. (d) is a
#  pentagonal prism, 30 side, 60 high, with a face towards the observer, so
#  its BACK vertex is hidden and shows dashed in the front view.
# ==========================================================================
PRISMS = {
    "b": dict(n=3, side=40.0, height=50.0, orient="apex-front",
              cuts=[("incline", 22.0, 30.0)],
              title="Q.2(b) · triangular prism, one plane at 30°"),
    "c": dict(n=3, side=40.0, height=50.0, orient="apex-front",
              cuts=[("level", 27.0), ("incline", 27.0, 30.0)],
              title="Q.2(c) · triangular prism, level then 30°"),
    "d": dict(n=5, side=30.0, height=60.0, orient="edge-front",
              cuts=[("level", 28.0), ("incline", 28.0, 45.0)],
              title="Q.2(d) · pentagonal prism, level then 45°"),
}


def corners(n, side, orient):
    """The cross-section, as a list of (x, y) in millimetres."""
    R = side / (2 * math.sin(math.pi / n))
    off = -90.0 + (180.0 / n if orient == "edge-front" else 0.0)

    def snap(t):
        # cos(90°) is 6e-17, not 0, and these solids have a corner sitting
        # exactly on the axis - the triangle's front apex, the pentagon's
        # back one. Left un-snapped it tests as "just to the right of the
        # junction", and a face that merely touches the junction is taken
        # for one that crosses it.
        return 0.0 if abs(t) < 1e-9 else t

    return [np.array([snap(R * math.cos(math.radians(off + 360.0 * k / n))),
                      snap(R * math.sin(math.radians(off + 360.0 * k / n)))])
            for k in range(n)], R


def cut_height(spec, x):
    """Height of the cut above the base, at distance x from the axis."""
    cuts = spec["cuts"]
    if len(cuts) == 1:
        _, at, ang = cuts[0]
        half = max(abs(c[0]) for c in corners(spec["n"], spec["side"],
                                             spec["orient"])[0])
        return at + (x + half) * math.tan(math.radians(ang))
    # two planes, meeting on the axis: level to the left, inclined to the right
    level_at = cuts[0][1]
    _, at, ang = cuts[1]
    if x <= 0.0:
        return level_at
    return at + x * math.tan(math.radians(ang))


def solve_prism(key):
    spec = PRISMS[key]
    n, side, height = spec["n"], spec["side"], spec["height"]
    verts, R = corners(n, side, spec["orient"])
    split = len(spec["cuts"]) > 1          # is there a junction at x = 0?

    # Start the numbering - and so the seam - at the SHORTEST edge, which is
    # where the convention puts the join on a truncated solid. Rotating the
    # list keeps the cyclic order, so the development still unrolls the right
    # way round; it only changes where it is cut open.
    heights = [cut_height(spec, v[0]) for v in verts]
    start = min(range(n), key=lambda i: (round(heights[i], 9), i))
    verts = verts[start:] + verts[:start]

    for v in verts:
        z = cut_height(spec, v[0])
        assert 0.0 < z < height, f"{key}: the cut leaves the solid at a corner"

    # ---- the development: perimeter along, cut height up -------------------
    profile, edges = [], []
    for k in range(n + 1):
        v = verts[k % n]
        s = k * side
        edges.append(dict(k=k % n + 1, v=v, s=s, z=cut_height(spec, v[0])))
        profile.append((s, cut_height(spec, v[0])))
        if k == n:
            break
        w = verts[(k + 1) % n]
        # a face crossed by the junction gets a point there - the development
        # has a corner in the middle of a face, where there is no edge at all
        if split and (v[0] < 0.0 < w[0] or w[0] < 0.0 < v[0]):
            f = (0.0 - v[0]) / (w[0] - v[0])
            assert 0.0 < f < 1.0
            profile.append((s + f * side, cut_height(spec, 0.0)))
    profile.sort()
    assert abs(profile[-1][0] - n * side) < 1e-9, \
        f"{key}: the development is not the perimeter wide"

    breaks = [p for p in profile
              if abs(p[0] / side - round(p[0] / side)) > 1e-9]
    if split:
        assert len(breaks) >= 1, f"{key}: a junction crossing was missed"

    # ---- the true shape of the section --------------------------------------
    ang = math.radians(spec["cuts"][-1][2])
    u_hat = np.array([0.0, 1.0, 0.0])
    v_hat = np.array([math.cos(ang), 0.0, math.sin(ang)])
    if len(spec["cuts"]) == 1:
        origin = np.array([-R if spec["orient"] == "apex-front" else 0.0, 0.0, 0.0])
        origin = np.array([min(c[0] for c in verts), 0.0, spec["cuts"][0][1]])
    else:
        origin = np.array([0.0, 0.0, spec["cuts"][0][1]])

    def to_plane(p):
        d = np.asarray(p, float) - origin
        return np.array([float(d @ u_hat), float(d @ v_hat)])

    # the section polygon in space: each corner, at the height the plane cuts
    # it - plus, when two planes share the job, the junction points
    space = []
    for k in range(n):
        v, w = verts[k], verts[(k + 1) % n]
        space.append(np.array([v[0], v[1], cut_height(spec, v[0])]))
        if split and (v[0] < 0.0 < w[0] or w[0] < 0.0 < v[0]):
            f = (0.0 - v[0]) / (w[0] - v[0])
            mid = v + f * (w - v)
            space.append(np.array([mid[0], mid[1], cut_height(spec, 0.0)]))
    incl = [p for p in space if p[0] >= -1e-9] if split else space
    shape = [to_plane(p) for p in incl]

    def shoelace(poly):
        a = 0.0
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            a += x0 * y1 - x1 * y0
        return abs(a) / 2.0

    # the section's own area against its shadow in the top view, an
    # independent route to the same number
    flat = [(p[0], p[1]) for p in incl]
    if len(shape) >= 3:
        assert abs(shoelace(shape) * math.cos(ang) - shoelace(flat)) < 1e-6, \
            f"{key}: the true shape does not project to its own top view"

    return dict(key=key, spec=spec, verts=verts, R=R, n=n, side=side,
                height=height, perimeter=n * side, edges=edges,
                profile=profile, breaks=breaks, split=split,
                shape=shape, space=space, to_plane=to_plane, ang=ang,
                half=max(abs(v[0]) for v in verts),
                width=max(v[0] for v in verts) - min(v[0] for v in verts))


G = {k: solve_prism(k) for k in PRISMS}
B = G["b"]


# ==========================================================================
#  The 3-D stage, and the fold
# ==========================================================================
def pt3(x, y, z, h):
    return np.array([x * S3, y * S3, (z - h / 2.0) * S3])


def unroll_trace(g, alpha):
    """The cross-section, part way between folded (alpha=1) and flat (alpha=0).

    Each corner is hinged by alpha times the exterior angle, so the side
    lengths never change - which is the whole of what a development claims.
    At alpha = 1 the trace closes back on itself; at alpha = 0 it is a straight
    line the length of the perimeter.
    """
    pts = [np.array([0.0, 0.0])]
    d = np.array([1.0, 0.0])
    ext = 2 * math.pi / g["n"]
    for _ in range(g["n"]):
        pts.append(pts[-1] + g["side"] * d)
        c, s = math.cos(alpha * ext), math.sin(alpha * ext)
        d = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
    centre = sum(pts) / len(pts)
    return [p - centre for p in pts]


def fold_faces(g, alpha, cut=False, fill=0.5):
    trace = unroll_trace(g, alpha)
    h = g["height"]
    grp = VGroup()
    for k in range(g["n"]):
        z0 = g["edges"][k]["z"] if cut else h
        z1 = g["edges"][k + 1]["z"] if cut else h
        a, b = trace[k], trace[k + 1]
        grp.add(Polygon(pt3(a[0], a[1], 0, h), pt3(b[0], b[1], 0, h),
                        pt3(b[0], b[1], z1, h), pt3(a[0], a[1], z0, h),
                        stroke_color=SOLID_COL, stroke_width=1.6,
                        fill_color=SOLID_COL, fill_opacity=fill))
    return grp


def fold_top(g, alpha, cut=False, colour=None, width=4.0):
    trace = unroll_trace(g, alpha)
    h = g["height"]
    pts = [pt3(p[0], p[1], g["edges"][k]["z"] if cut else h, h)
           for k, p in enumerate(trace)]
    line = VMobject(stroke_color=colour or (CUT_COL if cut else SOLID_COL),
                    stroke_width=width)
    line.set_points_as_corners(pts)
    return line


def fold_base(g, alpha, colour=SOLID_COL, width=4.0):
    trace = unroll_trace(g, alpha)
    h = g["height"]
    line = VMobject(stroke_color=colour, stroke_width=width)
    line.set_points_as_corners([pt3(p[0], p[1], 0, h) for p in trace])
    return line


def fold_edges(g, alpha, cut=False, colour=AUX_COL, width=1.8):
    trace = unroll_trace(g, alpha)
    h = g["height"]
    grp = VGroup()
    for k, p in enumerate(trace):
        z = g["edges"][k]["z"] if cut else h
        grp.add(Line(pt3(p[0], p[1], 0, h), pt3(p[0], p[1], z, h),
                     color=colour, stroke_width=width, stroke_opacity=0.85))
    return grp


def fold(scene, g, mobs, cut=False, reverse=False):
    a0, a1 = (0.0, 1.0) if reverse else (1.0, 0.0)

    def _bend(_, t):
        alpha = interpolate(a0, a1, t)
        mobs["faces"].become(fold_faces(g, alpha, cut))
        mobs["top"].become(fold_top(g, alpha, cut))
        mobs["base"].become(fold_base(g, alpha))
        mobs["edges"].become(fold_edges(g, alpha, cut))

    return UpdateFromAlphaFunc(VGroup(*mobs.values()), _bend)


# ==========================================================================
#  S01 - fold it out
# ==========================================================================
class S01_FoldItOut(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=70 * DEGREES, theta=-58 * DEGREES,
                                    zoom=1.0, focal_distance=60.0)
        bar = hud(self, title_bar("Prisms",
                                  "Sheet 8 · the development is a polygon"))
        self.add(bar)
        g = B
        mobs = dict(faces=fold_faces(g, 1.0), base=fold_base(g, 1.0),
                    top=fold_top(g, 1.0), edges=fold_edges(g, 1.0))

        narrate(
            self,
            "A triangular prism: forty on each side of the triangle, fifty tall. "
            "Three flat faces, and three vertical edges where they meet.",
            FadeIn(mobs["faces"]), Create(mobs["base"]), Create(mobs["top"]),
            FadeIn(mobs["edges"]),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The cylinder had to be rolled out. A prism is easier - you just open "
            "it, like unfolding a cardboard box. Each face swings flat about the "
            "edge it shares with the last one, and nothing stretches, because the "
            "edges are hinges.",
            fold(self, g, mobs),
            rate_func=rate_functions.ease_in_out_sine,
        )

        per = g["perimeter"]
        dim_w = DoubleArrow(pt3(-per / 2, 0, -7, g["height"]),
                            pt3(per / 2, 0, -7, g["height"]),
                            buff=0, color=DEV_COL, stroke_width=2.4, tip_length=0.18)
        lab_w = billboard(self, mono(f"3 × {g['side']:.0f} = {per:.0f}",
                                     color=DEV_COL, size=24)
                          .move_to(pt3(0, 0, -14, g["height"])))
        lab_h = billboard(self, mono(f"{g['height']:.0f}", color=DEV_COL, size=24)
                          .move_to(pt3(-per / 2 - 14, 0, g["height"] / 2, g["height"])))
        fly_camera(
            self,
            f"Three rectangles in a row. Each is forty wide, so the pattern is a "
            f"hundred and twenty across - the perimeter of the triangle - and fifty "
            "high. That is the development of the whole prism.",
            FadeIn(dim_w), FadeIn(lab_w), FadeIn(lab_h),
            phi=90 * DEGREES, theta=-90 * DEGREES, zoom=1.15,
        )

        note = hud(self, VGroup(
            chip("width = the PERIMETER of the base", color=DEV_COL, size=20),
            chip("one rectangle per face · the edges are the fold lines",
                 color=SLATE, size=18),
        ).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.5))
        narrate(
            self,
            "Which gives the rule.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "Where the cylinder used pi D, a prism uses the perimeter of its base - "
            "and for the same reason. Both are the distance once round the bottom "
            "of the solid, straightened out. The only difference is that a polygon's "
            "way round is a sum of straight sides, so you can measure it exactly "
            "instead of reaching for pi.",
        )

        # and now the cut
        cut_mobs = dict(faces=fold_faces(g, 1.0, cut=True),
                        base=fold_base(g, 1.0),
                        top=fold_top(g, 1.0, cut=True),
                        edges=fold_edges(g, 1.0, cut=True))
        fly_camera(
            self,
            "Now cut it, the way question two asks: a plane in at the left-hand edge "
            "twenty-two above the base, climbing to the right at thirty degrees.",
            FadeOut(mobs["faces"]), FadeOut(mobs["top"]), FadeOut(mobs["edges"]),
            FadeOut(mobs["base"]), FadeOut(dim_w), FadeOut(lab_w), FadeOut(lab_h),
            FadeOut(note),
            FadeIn(cut_mobs["faces"]), FadeIn(cut_mobs["base"]),
            FadeIn(cut_mobs["top"]), FadeIn(cut_mobs["edges"]),
            phi=72 * DEGREES, theta=-58 * DEGREES, zoom=1.0,
        )
        narrate(
            self,
            "The three edges are now three different heights. And here is the one "
            "thing that makes a prism easier than a cylinder: between two edges, the "
            "face is flat and the cutting plane is flat, so where they meet is a "
            "STRAIGHT line. Open it out and see.",
        )
        narrate(
            self,
            "No curve anywhere. The top of the development is a chain of straight "
            "lines, one per face, and all you ever need are the heights at the "
            "edges. Three numbers, and the pattern is drawn.",
            fold(self, g, cut_mobs),
            rate_func=rate_functions.ease_in_out_sine,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  The sheet
# ==========================================================================
XY_Y = -12.0
TV_Y = -44.0
DEV_X = 40.0


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


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


def prism_sheet(g, dev_x=DEV_X, tv_y=TV_Y):
    """Every piece of one prism's drawing: front view, top view, development."""
    h, n, side = g["height"], g["n"], g["side"]
    xs = sorted({round(v[0], 6) for v in g["verts"]})
    lo, hi = min(xs), max(xs)

    def fv(x, z):
        return P2(x, z)

    def tv(x, y):
        return P2(x, tv_y + y)

    def dv(s, z):
        return P2(dev_x + s, z)

    # ---- front view ----
    base = Line(fv(lo, 0), fv(hi, 0), color=SOLID_COL, stroke_width=3.4)
    sides = VGroup(Line(fv(lo, 0), fv(lo, g["edges"][0]["z"] if False else
                                      cut_height(g["spec"], lo)),
                        color=SOLID_COL, stroke_width=3.4),
                   Line(fv(hi, 0), fv(hi, cut_height(g["spec"], hi)),
                        color=SOLID_COL, stroke_width=3.4))
    inner = VGroup()
    for x in xs[1:-1]:
        back = all(abs(v[0] - x) > 1e-9 or v[1] > 0 for v in g["verts"])
        line = (DashedLine(fv(x, 0), fv(x, cut_height(g["spec"], x)),
                           color=SOLID_COL, stroke_width=2.2, dash_length=0.07)
                if back else
                Line(fv(x, 0), fv(x, cut_height(g["spec"], x)),
                     color=SOLID_COL, stroke_width=2.6))
        inner.add(line)
    cuts = VGroup()
    if g["split"]:
        cuts.add(Line(fv(lo, cut_height(g["spec"], lo)), fv(0, cut_height(g["spec"], 0)),
                      color=CUT_COL, stroke_width=4.5),
                 Line(fv(0, cut_height(g["spec"], 0)), fv(hi, cut_height(g["spec"], hi)),
                      color=CUT_COL, stroke_width=4.5))
    else:
        cuts.add(Line(fv(lo, cut_height(g["spec"], lo)),
                      fv(hi, cut_height(g["spec"], hi)),
                      color=CUT_COL, stroke_width=4.5))
    front = VGroup(base, sides, inner, cuts)

    # ---- top view ----
    poly = Polygon(*[tv(v[0], v[1]) for v in g["verts"]], color=SOLID_COL,
                   stroke_width=3.4)
    corner_nums = VGroup(*[
        mono(str(k + 1), color=SLATE, size=12).move_to(tv(v[0] * 1.22, v[1] * 1.22))
        for k, v in enumerate(g["verts"])])
    junction = (DashedLine(tv(0, min(v[1] for v in g["verts"]) - 4),
                           tv(0, max(v[1] for v in g["verts"]) + 4),
                           color=CUT_COL, stroke_width=1.8, dash_length=0.06)
                if g["split"] else VGroup())
    top = VGroup(poly, corner_nums, junction)

    # ---- the development ----
    dev_base = Line(dv(0, 0), dv(g["perimeter"], 0), color=DEV_COL, stroke_width=4)
    folds = VGroup(*[Line(dv(k * side, 0), dv(k * side, g["edges"][k]["z"]),
                          color=AUX_COL, stroke_width=1.4, stroke_opacity=0.8)
                     for k in range(n + 1)])
    fold_nums = VGroup(*[
        mono(str(g["edges"][k]["k"]), color=SLATE, size=11).move_to(dv(k * side, -6.5))
        for k in range(n + 1)])
    top_line = VMobject(stroke_color=CUT_COL, stroke_width=4)
    top_line.set_points_as_corners([dv(s, z) for s, z in g["profile"]])
    break_dots = VGroup(*[Dot(dv(s, z), radius=0.04, color=CUT_COL)
                          for s, z in g["breaks"]])
    ends = VGroup(Line(dv(0, 0), dv(0, g["edges"][0]["z"]), color=DEV_COL,
                       stroke_width=4),
                  Line(dv(g["perimeter"], 0), dv(g["perimeter"], g["edges"][n]["z"]),
                       color=DEV_COL, stroke_width=4))
    dev_dim = dim(dv(0, 0), dv(g["perimeter"], 0),
                  f"{n} × {side:.0f} = {g['perimeter']:.0f}", DEV_COL,
                  size=15, offset=-15.0, gap=7.0)
    development = VGroup(dev_base, folds, fold_nums, top_line, break_dots, ends)

    return dict(fv=fv, tv=tv, dv=dv, front=front, top=top, cuts=cuts,
                inner=inner, development=development, dev_dim=dev_dim,
                folds=folds, top_line=top_line, break_dots=break_dots,
                corner_nums=corner_nums, junction=junction, poly=poly,
                lo=lo, hi=hi, xs=xs)


# ==========================================================================
#  S02 - Q.2(b) worked through
# ==========================================================================
class S02_SheetB(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        g = B
        S = prism_sheet(g)
        fv, tv, dv = S["fv"], S["tv"], S["dv"]
        xy = Line(P2(-32, XY_Y), P2(g["perimeter"] + 48, XY_Y),
                  color=INK, stroke_width=2.2)
        # offset is measured 90° anticlockwise from the arrow's direction, and
        # these arrows all point up, so a POSITIVE offset moves the dimension
        # to the left. Send each one outward from the axis.
        heights = VGroup(*[
            dim(fv(v[0], 0), fv(v[0], g["edges"][k]["z"]),
                f"{g['edges'][k]['z']:.2f}", CUT_COL, size=12,
                offset=(7.0 if v[0] < -1e-9 else -7.0 if v[0] > 1e-9 else 5.0),
                gap=5.0)
            for k, v in enumerate(g["verts"])])
        given = VGroup(xy, S["front"], S["top"])
        sheet = VGroup(given, heights, S["development"], S["dev_dim"])

        centre, W = frame_target([given])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 7 (Set A) · Q.2(b)",
            "Figure P7.2b · triangular prism, cut at 30°")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "the two views", "a rectangle and a triangle", SLATE),
            step_badge("2", "number the edges", "from the seam, round the base", SOLID_COL),
            step_badge("3", "read the edge heights", "straight off the front view", CUT_COL),
            step_badge("4", "lay out the perimeter", "one rectangle per face · join straight", DEV_COL),
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
            "Question two, part b. The triangular prism, forty side, fifty high, "
            "with the cutting plane drawn in the front view: in at the left edge "
            "twenty-two up, away at thirty degrees.",
            FadeIn(bar), Create(given),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The middle line of the front view is not a fold in the drawing - it is "
            "the third edge of the prism, the one pointing straight at us. Solid, "
            "because we can see it.",
            rail_focus(rail, rungs, 0),
            Indicate(S["inner"], color=SOLID_COL),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Number the three edges round the base in the top view, starting wherever "
            "the seam is to go - and on a truncated solid, put the seam on the "
            "shortest edge.",
            rail_focus(rail, rungs, 1),
            look_at(self, [S["top"]], right=0.34),
            FadeIn(S["corner_nums"]),
            lag_ratio=0.2,
        )

        narrate(
            self,
            f"Now read the heights. Edge one, on the left, is the twenty-two we "
            f"were given - the shortest, which is why the seam goes there. Edge "
            f"two, the one pointing at us, is {g['edges'][1]['z']:.2f}. Edge three, "
            f"on the right, is {g['edges'][2]['z']:.2f}. The edges are vertical, so "
            f"the front view "
            "draws every one of them at its true length - no rotating, no "
            "auxiliaries. That is the whole advantage of a prism over a cone.",
            rail_focus(rail, rungs, 2),
            look_at(self, [S["front"], heights], right=0.32),
            Create(heights),
            lag_ratio=0.2,
        )

        narrate(
            self,
            "Step four. Lay the perimeter out in a straight line - three sides of "
            "forty, so a hundred and twenty - and mark the folds at every forty.",
            rail_focus(rail, rungs, 3),
            look_at(self, [S["development"]], right=0.28),
            Create(S["development"][0]), Create(S["folds"]),
            FadeIn(S["development"][2]), FadeIn(S["dev_dim"]),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Stand each edge up at its own height, carried straight across from the "
            "front view.",
            look_at(self, [S["front"], S["development"]], right=0.26),
            *[TransformFromCopy(heights[k % 3], S["folds"][k]) for k in range(4)],
            lag_ratio=0.15,
        )

        ans_rows = VGroup(
            mono("DEVELOPMENT · Q.2(b)", color=DEV_COL, size=18),
            mono(f"  width  {g['n']} × {g['side']:.0f} = {g['perimeter']:.0f}",
                 color=DEV_COL, size=14),
            *[mono(f"  edge {e['k']}   {e['z']:.2f}", color=CUT_COL, size=14)
              for e in g["edges"][:g["n"]]],
        ).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        ans = card_back(ans_rows, pad=0.22, opacity=0.9)
        ans.add(SurroundingRectangle(ans_rows, color=DEV_COL, buff=0.22,
                                     corner_radius=0.1, stroke_width=1.4))
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)
        self.add_foreground_mobjects(ans)

        narrate(
            self,
            "And join the tops with straight lines.",
            settle(Create(S["top_line"]), Create(S["development"][5]), FadeIn(ans)),
        )
        narrate(
            self,
            "Straight, not curved - because each face is flat and the cutting plane "
            "is flat, and two flat things meet in a straight line. On the cylinder "
            "that same step needed a smooth curve through twelve points. Here it "
            "needs a ruler and three numbers.",
            look_at(self, [sheet], right=0.24, top=0.12),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S03 - two planes at once: Q.2(c) and Q.2(d)
# ==========================================================================
class S03_TwoPlanes(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        c, d = G["c"], G["d"]
        Sc = prism_sheet(c, dev_x=44.0, tv_y=-44.0)
        Sd = prism_sheet(d, dev_x=44.0, tv_y=-52.0)

        bar = pin_to_frame(self, card_back(title_bar(
            "Two Planes at Once", "Q.2(c) and Q.2(d) · a corner with no edge")),
            corner=UP + LEFT, buff=0.30)
        self.add(bar)
        self.add_foreground_mobjects(bar)

        group_c = VGroup(Sc["front"], Sc["top"], Sc["development"], Sc["dev_dim"])
        centre, W = frame_target([Sc["front"], Sc["top"], Sc["development"]],
                                 right=0.22)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "Part c is the same prism again, cut a different way: level from the "
            "left-hand edge as far as the axis, and then away at thirty degrees. Two "
            "planes, meeting on a line down the middle of the solid.",
            FadeIn(bar), Create(Sc["front"]), Create(Sc["top"]),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "The three edge heights come off the front view exactly as before - "
            f"{c['edges'][0]['z']:.0f}, {c['edges'][1]['z']:.2f}, "
            f"{c['edges'][2]['z']:.0f}. But this time the edges are not enough, and "
            "the top view says why.",
            Indicate(Sc["cuts"], color=CUT_COL),
            lag_ratio=0.25,
        )

        s_break, z_break = c["breaks"][0]
        mark_tv = Dot(Sc["tv"](0.0, max(v[1] for v in c["verts"])), radius=0.045,
                      color=CUT_COL)
        narrate(
            self,
            "The line where the two planes meet runs straight across the back face - "
            "not along an edge, but through the middle of it. So that face is cut by "
            "the level plane on one side and the sloping plane on the other, and the "
            "cut across it is bent.",
            Create(Sc["junction"]), FadeIn(mark_tv),
            lag_ratio=0.3,
        )
        narrate(
            self,
            f"Which means the development needs a fourth point, {s_break:.0f} along "
            "the base line, where that face is crossed. Miss it and you draw one "
            "straight line where there ought to be two, and the pattern is wrong by "
            "a triangle.",
            look_at(self, [Sc["front"], Sc["development"]], right=0.24),
            Create(Sc["development"][0]), Create(Sc["folds"]),
            FadeIn(Sc["development"][2]), FadeIn(Sc["dev_dim"]),
            Create(Sc["top_line"]), FadeIn(Sc["break_dots"]),
            Create(Sc["development"][5]),
            lag_ratio=0.15,
        )

        # ---- and the pentagon --------------------------------------------------
        group_d = VGroup(Sd["front"], Sd["top"], Sd["development"], Sd["dev_dim"])
        s_break_d, _ = d["breaks"][0]
        narrate(
            self,
            "Part d is the same idea on a pentagonal prism - thirty side, sixty "
            "high, level to the axis and then forty-five degrees up. Five edges, so "
            "five heights, and a hundred and fifty round the base.",
            FadeOut(group_c), FadeOut(mark_tv),
            lag_ratio=0.2,
        )
        centre, W = frame_target([Sd["front"], Sd["top"], Sd["development"]],
                                 right=0.22)
        self.camera.frame.animate.set(width=W).move_to(centre)
        narrate(
            self,
            "Note the dashed line up the middle of the front view: that is the back "
            "corner of the pentagon, hidden behind the solid, and it must be drawn "
            "dashed. It is still an edge and it still gets a height - twenty-eight, "
            "because it sits on the level half.",
            Create(Sd["front"]), Create(Sd["top"]),
            self.camera.frame.animate.set(width=W).move_to(centre),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"And here the junction crosses the FRONT face, at its midpoint - "
            f"{s_break_d:.0f} along the development. Same rule as before: wherever "
            "the meeting line of two cutting planes crosses a face, the development "
            "gets a point there.",
            Create(Sd["junction"]),
            Create(Sd["development"][0]), Create(Sd["folds"]),
            FadeIn(Sd["development"][2]), FadeIn(Sd["dev_dim"]),
            Create(Sd["top_line"]), FadeIn(Sd["break_dots"]),
            Create(Sd["development"][5]),
            lag_ratio=0.15,
        )

        note = pin_to_frame(self, card_back(VGroup(
            chip("a corner in the pattern where there is no edge on the solid",
                 color=CUT_COL, size=17),
            chip("one point per EDGE, plus one wherever the planes meet a face",
                 color=DEV_COL, size=17),
        ).arrange(DOWN, buff=0.16)), corner=DOWN, buff=0.4)
        self.add_foreground_mobjects(note)
        narrate(
            self,
            "So the rule for any prism, however many sides and however many cutting "
            "planes.",
            settle(FadeIn(note)),
        )
        narrate(
            self,
            "One point on the development for every edge of the solid, and one more "
            "wherever a cutting plane's boundary crosses a face. Join them with "
            "straight lines. Nothing else is ever needed.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - recap
# ==========================================================================
class S04_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "prisms, cylinders, and what changes")
        self.add(bar)

        rows = VGroup(
            mono("width of the pattern  =  the PERIMETER of the base", color=DEV_COL, size=20),
            mono("one point per EDGE · heights straight off the front view",
                 color=CUT_COL, size=20),
            mono("join with STRAIGHT lines · a flat face cut by a flat plane",
                 color=CUT_COL, size=19),
            mono("plus one point wherever two cutting planes meet a face",
                 color=TL_COL, size=19),
        ).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(np.array([-0.1, 1.45, 0]))

        narrate(self, "Prisms, in four lines.", FadeIn(bar))
        narrate(
            self,
            "The pattern is as wide as the perimeter of the base - three forties for "
            "the triangular prism, five thirties for the pentagonal one. Exactly the "
            "same idea as pi D on a cylinder: the distance once round the bottom, "
            "straightened out.",
            FadeIn(rows[0]),
        )
        narrate(
            self,
            "Every vertical edge gives one point. Its height is read straight off the "
            "front view, because a vertical edge is never foreshortened there - which "
            "is why a prism needs no true-length construction and a cone does.",
            FadeIn(rows[1]),
        )
        narrate(
            self,
            "Join the points with straight lines, not a curve. And if two planes cut "
            "the solid, add a point wherever the line they meet on crosses a face - "
            "the pattern gets a corner in a place the solid has no edge at all.",
            FadeIn(rows[2]), FadeIn(rows[3]),
            lag_ratio=0.25,
        )

        # generated, not typed: these numbers moved once already when the seam
        # was put on the shortest edge, and a hand-copied table would still be
        # quoting the old ones
        def row(key):
            g = G[key]
            hs = " · ".join(f"{e['z']:.2f}" for e in g["edges"][:g["n"]])
            brk = (f"  + break at {g['breaks'][0][0]:.0f}" if g["breaks"] else "")
            return mono(f"Q.2({key})   {g['perimeter']:.0f} wide   edges {hs}{brk}",
                        color=DEV_COL, size=16)

        table = VGroup(row("b"), row("c"), row("d")
                       ).arrange(DOWN, buff=0.14, aligned_edge=LEFT
                                 ).move_to(np.array([0.0, -1.5, 0]))
        narrate(
            self,
            "The three answers to check yourself against.",
            settle(FadeIn(table[0]), FadeIn(table[1]), FadeIn(table[2])),
        )
        narrate(
            self,
            "And the one number people get wrong: the width of the pattern is the "
            "perimeter of the BASE, measured in the top view where the sides are "
            "true length. Not the perimeter of the cut end, which is longer, and not "
            "anything measured in the front view, where every side of the polygon "
            "except the two facing you is foreshortened.",
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme
#
#      py -3.11 ed12_prisms.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 7 (Set A) Q.2(b), (c), (d) - prisms")
    for key in ("b", "c", "d"):
        g = G[key]
        spec = g["spec"]
        print()
        print(f"  {spec['title']}")
        print(f"    {g['n']}-sided, {g['side']:.0f} side, {g['height']:.0f} high   "
              f"perimeter {g['perimeter']:.0f} mm   front-view width {g['width']:.2f}")
        cuts = " then ".join(
            (f"level at {c[1]:.0f}" if c[0] == "level" else f"{c[2]:.0f}° from {c[1]:.0f}")
            for c in spec["cuts"])
        print(f"    cut: {cuts}")
        for e in g["edges"][:g["n"]]:
            print(f"      edge {e['k']}  at x {e['v'][0]:+7.2f}   height {e['z']:6.2f}")
        if g["breaks"]:
            for s, z in g["breaks"]:
                print(f"      break inside a face at {s:.2f} along the development, "
                      f"height {z:.2f}")
        else:
            print("      no break: one plane only, so the top of the pattern is "
                  "three straight lines")
        print(f"    DEVELOPMENT  {g['perimeter']:.0f} wide, "
              f"{g['n']} panels of {g['side']:.0f}")
