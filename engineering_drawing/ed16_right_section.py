"""
Engineering Drawing I - Sheet 8  (Development of Surfaces)
Episode 16: The Right Section - developing an oblique prism and cylinder

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed16_right_section.py S02_ObliquePrism
    ... or use render_ed16.bat to build all four scenes in order.

Scene order (about ten minutes in all):

    S01_RollItFlat      why episode 10's stretch-out line stops working the
                        moment the axis leans. A base edge meets a vertical
                        generator at 90°, which is the only reason rolling the
                        solid leaves the base along a straight line. Lean the
                        axis and that angle is gone - so cut a section that
                        restores it, perpendicular to the axis
    S02_ObliquePrism    an oblique square prism, cut. The right section, its
                        true shape, the stretch-out line, and the pattern with
                        the base BELOW the line and the cut mostly above it
    S03_ObliqueCylinder the same sheet with twelve generators instead of four,
                        where the right section is an ellipse - and the one
                        check that catches every arithmetic slip
    S04_Recap           three developments, three stretch-out lines, and how to
                        tell which one a question wants

THE METHOD, in one line: a right section is perpendicular to every generator,
so it - and only it - rolls out as a straight line.

A NOTE ON THE FIGURE. The oblique cylinder is the book's, from Figure P8.1(a):
Ø40, axis 60 long at 60° to the base. Exercise 8 Q.2's own figure was not
available when this was written, so the prism (square, 30 side, same axis) and
the cutting plane (30° to the base, through the point 32 along the axis) are
chosen to exercise the method rather than copied from it.

Everything is computed by solve(), which asserts that the right section really
is perpendicular to every generator, that its true shape is the base
foreshortened by sin of the lean, that every generator measures the same 60
from base to top on the pattern - the check the scene ends on - and that the
cut stays between the two on all of them.

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
RS_COL = TEAL            # the right section - the whole method
CUT_COL = CORAL
DEV_COL = VIOLET
AUX_COL = CREAM

MM = 0.030
S3 = 0.062

# ==========================================================================
#  One axis serves both solids: 60 long, leaning at 60° to the base, in the
#  x-z plane. x across the sheet, y depth (negative = towards the observer),
#  z up from the base.
# ==========================================================================
LEAN = 60.0
AXIS = 60.0
RS_AT = 30.0             # the right section is taken half way along the axis
CUT_AT = 32.0            # the cutting plane crosses the axis 32 from the base
TILT = 30.0              # ... inclined at 30° to the base

A = np.array([AXIS * math.cos(math.radians(LEAN)), 0.0,
              AXIS * math.sin(math.radians(LEAN))])
AHAT = A / AXIS
SIN_LEAN = math.sin(math.radians(LEAN))
CUT_N = np.array([-math.sin(math.radians(TILT)), 0.0, math.cos(math.radians(TILT))])
CUT_P0 = AHAT * CUT_AT

PRISM = dict(side=30.0)
CYL = dict(dia=40.0)
PRISM_HALF = PRISM["side"] / math.sqrt(2.0)
CYL_R = CYL["dia"] / 2.0


def t_rs(v):
    """Where the generator through base point v crosses the RIGHT SECTION."""
    return (RS_AT - float(AHAT @ v)) / AXIS


def t_cut(v):
    """... and where it crosses the cutting plane."""
    return float(CUT_N @ CUT_P0 - CUT_N @ v) / float(CUT_N @ A)


def uv(v):
    """True-shape coordinates of a right-section point.

    The right section is the base plane turned about the y axis until it is
    square to the axis, so depths are untouched and everything across the sheet
    is foreshortened by exactly sin of the lean. Two lines of arithmetic
    instead of an auxiliary view - though S02 draws the auxiliary view anyway,
    because that is what a student has to be able to set out.
    """
    return np.array([v[0] * SIN_LEAN, v[1]])


def generator(v):
    """Everything the development needs about one generator."""
    tr, tc = t_rs(v), t_cut(v)
    return dict(v=np.asarray(v, float), t_rs=tr, t_cut=tc,
                rs=np.asarray(v, float) + tr * A,
                cut=np.asarray(v, float) + tc * A,
                to_cut=(tc - tr) * AXIS,          # + above the right section
                to_base=-tr * AXIS,               # always negative
                to_top=(1.0 - tr) * AXIS,         # always positive
                uv=uv(v))


def stretch_out(gens):
    """Distances along the stretch-out line, starting at the first generator.

    The seam is generator 1 and the pattern closes back on it, so the list runs
    one longer than the number of generators.
    """
    out = [0.0]
    for k in range(len(gens)):
        a = gens[k]["uv"]
        b = gens[(k + 1) % len(gens)]["uv"]
        out.append(out[-1] + float(np.linalg.norm(b - a)))
    return out


def prism_corners():
    h = PRISM_HALF
    return [np.array([-h, 0.0, 0.0]), np.array([0.0, -h, 0.0]),
            np.array([h, 0.0, 0.0]), np.array([0.0, h, 0.0])]


def cyl_base(k, n=12):
    th = math.pi - 2 * math.pi * k / n
    return np.array([CYL_R * math.cos(th), CYL_R * math.sin(th), 0.0])


def solve():
    P = [generator(v) for v in prism_corners()]
    C = [generator(cyl_base(k)) for k in range(12)]

    for name, gens in (("prism", P), ("cylinder", C)):
        for g in gens:
            # the right section really is perpendicular to the generator
            assert abs(float(AHAT @ (g["rs"] - AHAT * RS_AT))) < 1e-9, \
                f"{name}: the right section is not square to the axis"
            # its true shape is the base foreshortened by sin(lean)
            span = g["rs"] - AHAT * RS_AT
            assert abs(float(np.linalg.norm(span)) -
                       float(np.linalg.norm(g["uv"]))) < 1e-9, \
                f"{name}: the true shape is not the base foreshortened"
            # every generator is the same length from base to top
            assert abs((g["to_top"] - g["to_base"]) - AXIS) < 1e-9, \
                f"{name}: generator came out {g['to_top'] - g['to_base']:.4f} long"
            # and the cut lies strictly between them
            assert g["to_base"] < g["to_cut"] < g["to_top"], \
                f"{name}: the plane misses the solid on one generator"
            assert 0.0 < g["t_cut"] < 1.0

    # the rhombus really is one: four equal sides, unequal diagonals
    ps = stretch_out(P)
    sides = [ps[k + 1] - ps[k] for k in range(4)]
    assert max(sides) - min(sides) < 1e-9, "the right section is not a rhombus"
    assert abs(abs(P[0]["uv"][0]) - abs(P[1]["uv"][1])) > 1.0, \
        "pick a lean that does not turn the right section back into a square"

    # the ellipse: semi-axes are R sin(lean) across and R deep
    assert abs(abs(C[0]["uv"][0]) - CYL_R * SIN_LEAN) < 1e-9
    assert abs(abs(C[3]["uv"][1]) - CYL_R) < 1e-9
    return dict(prism=P, cyl=C, prism_run=ps, cyl_run=stretch_out(C))


S = solve()


# ==========================================================================
#  The 3-D stage
# ==========================================================================
S1_CX, S1_H = 15.0, 60.0


def pt3(p, cx=S1_CX, h=S1_H):
    x, y, z = p
    return np.array([(x - cx) * S3, y * S3, (z - h / 2.0) * S3])


def ring_3d(pts, colour=SOLID_COL, width=3.2, **kw):
    m = VMobject(stroke_color=colour, stroke_width=width)
    m.set_points_as_corners([pt3(p, **kw) for p in list(pts) + [pts[0]]])
    return m


def prism_3d(base, ax, fill=0.20, **kw):
    ax = np.asarray(ax, float)
    g = VGroup()
    for k in range(len(base)):
        a, b = base[k], base[(k + 1) % len(base)]
        g.add(Polygon(pt3(a, **kw), pt3(b, **kw), pt3(b + ax, **kw), pt3(a + ax, **kw),
                      stroke_width=0, fill_color=SOLID_COL, fill_opacity=fill))
    return g


def gens_3d(base, ax, colour=SOLID_COL, width=2.2, **kw):
    ax = np.asarray(ax, float)
    return VGroup(*[Line(pt3(p, **kw), pt3(p + ax, **kw), color=colour,
                         stroke_width=width) for p in base])


def sq_mark(p, u, w, size=5.5, colour=INK, width=2.4, **kw):
    """A right-angle mark in space, on the plane of u and w."""
    u = np.asarray(u, float) / np.linalg.norm(u)
    w = np.asarray(w, float) / np.linalg.norm(w)
    m = VMobject(stroke_color=colour, stroke_width=width)
    m.set_points_as_corners([pt3(p + u * size, **kw),
                             pt3(p + u * size + w * size, **kw),
                             pt3(p + w * size, **kw)])
    return m


class S01_RollItFlat(ThreeDScene):
    def construct(self):
        self.camera.background_color = NAVY
        self.set_camera_orientation(phi=70 * DEGREES, theta=-70 * DEGREES,
                                    zoom=1.0, focal_distance=150.0)
        bar = hud(self, title_bar("The Right Section",
                                  "Sheet 8 · §10 · the only line that rolls out straight"))
        self.add(bar)

        base = prism_corners()
        up = np.array([0.0, 0.0, AXIS])
        edge = base[2] - base[1]                       # the near base edge, 2 -> 3
        corner = base[1]

        solid = prism_3d(base, up)
        rims = VGroup(ring_3d(base), ring_3d([p + up for p in base]))
        gens = gens_3d(base, up)
        mark = sq_mark(corner, edge, up, size=7.5, colour=RS_COL, width=3.0)
        base_hi = ring_3d(base, colour=RS_COL, width=5)

        narrate(
            self,
            "Episode ten developed a right prism by rolling it along a line. The "
            "pattern came out as a straight stretch-out line with the generators "
            "standing on it, and nobody had to think about why.",
            FadeIn(bar), FadeIn(solid), Create(rims), Create(gens),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "This is why. Where a base edge meets a vertical generator, the angle is "
            "ninety degrees. Roll the solid over and every one of those edges lies "
            "down along one straight line, because each is square to the edge it is "
            "pivoting about.",
            Create(base_hi), Create(mark),
            lag_ratio=0.2,
        )

        ang = math.degrees(math.acos(abs(float(np.dot(edge / np.linalg.norm(edge), AHAT)))))
        new_solid = prism_3d(base, A)
        new_rims = VGroup(ring_3d(base), ring_3d([p + A for p in base]))
        new_gens = gens_3d(base, A)
        new_mark = sq_mark(corner, edge, A, size=7.5, colour=CUT_COL, width=3.0)
        narrate(
            self,
            "Now lean the axis over to sixty degrees. The base has not moved, the "
            f"edges have not moved - but that angle is now {ang:.1f} degrees, not "
            "ninety. The base is no longer square to the generators.",
            Transform(solid, new_solid), Transform(rims, new_rims),
            Transform(gens, new_gens), Transform(mark, new_mark),
            FadeOut(base_hi),
            rate_func=rate_functions.ease_in_out_sine,
        )
        # top right is where the title bar's subtitle ends up; these go low
        warn = hud(self, VGroup(
            chip("roll it now and the base does NOT lie straight",
                 color=CUT_COL, size=18),
            chip("the base's perimeter is the wrong stretch-out",
                 color=CUT_COL, size=18),
        ).arrange(DOWN, buff=0.14).to_corner(DOWN + RIGHT, buff=0.55))
        narrate(
            self,
            "So rolling it no longer works. The base wanders off the line, and its "
            "perimeter - the number episode ten used - is not the width of the "
            "pattern any more.",
            settle(FadeIn(warn)),
        )

        rs_pts = [g["rs"] for g in S["prism"]]
        rs_ring = ring_3d(rs_pts, colour=RS_COL, width=5)
        rs_face = Polygon(*[pt3(p) for p in rs_pts], stroke_width=0,
                          fill_color=RS_COL, fill_opacity=0.22)
        rs_marks = VGroup(*[
            sq_mark(rs_pts[k], rs_pts[(k + 1) % 4] - rs_pts[k], A, size=5.0, colour=RS_COL)
            for k in range(4)])
        narrate(
            self,
            "The cure is to make ourselves a base that is square to the generators. "
            "Slice the solid with a plane perpendicular to the axis. That is called a "
            "RIGHT SECTION, and by construction it meets every single generator at "
            "ninety degrees.",
            FadeOut(warn), FadeOut(mark),
            FadeIn(rs_face), Create(rs_ring), Create(rs_marks),
            lag_ratio=0.2,
        )
        note = hud(self, VGroup(
            chip("the RIGHT SECTION rolls out straight — nothing else does",
                 color=RS_COL, size=18),
            chip("on a right solid the base already IS one — that is why ep.10 worked",
                 color=GOLD, size=18),
            chip("everything else is measured from it, above and below",
                 color=DEV_COL, size=18),
        ).arrange(DOWN, buff=0.15).to_edge(DOWN, buff=0.45))
        narrate(
            self,
            "Roll the solid on THAT and it lies down straight. Which also explains "
            "episode ten: on a right prism the base already is a right section, so "
            "the question never came up. Everything else - the base, the top, the cut "
            "- is then measured from that line, above it or below it.",
            settle(FadeIn(note)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.3)


# ==========================================================================
#  The sheet
# ==========================================================================
XY_Y = -12.0
TV_Y = -48.0
AUX_OFF = 70.0           # how far the auxiliary stands off along the axis
DEV_X, DEV_Z = 122.0, 42.0

AX_DIR = np.array([math.cos(math.radians(LEAN)), math.sin(math.radians(LEAN)), 0.0])
U_DIR = np.array([SIN_LEAN, -math.cos(math.radians(LEAN)), 0.0])
C_FV = np.array([AHAT[0] * RS_AT, AHAT[2] * RS_AT, 0.0])


def P2(x, y):
    return np.array([x * MM, y * MM, 0.0])


def fv(x, z):
    return P2(x, z)


def tv(x, y):
    return P2(x, TV_Y + y)


def fv_of(p):
    """Front view of a point in space."""
    return fv(p[0], p[2])


def rs_fv(u):
    """A point of the right-section LINE in the front view, u from its centre."""
    q = C_FV + U_DIR * u
    return fv(q[0], q[1])


def aux_pt(u, v):
    """The auxiliary view: u along the section line, v out along the projector."""
    q = C_FV + AX_DIR * AUX_OFF + U_DIR * u + AX_DIR * v
    return fv(q[0], q[1])


def dev_pt(run, off):
    return P2(DEV_X + run, DEV_Z + off)


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


def sq_mark2(p, u, w, size=4.5, colour=INK, width=2.0):
    """A right-angle mark on the sheet."""
    u = np.asarray(u, float)[:2]
    w = np.asarray(w, float)[:2]
    u = u / np.linalg.norm(u)
    w = w / np.linalg.norm(w)
    a = np.array([p[0] + (u[0] + 0) * size * MM, p[1] + u[1] * size * MM, 0.0])
    b = np.array([p[0] + (u[0] + w[0]) * size * MM, p[1] + (u[1] + w[1]) * size * MM, 0.0])
    c = np.array([p[0] + w[0] * size * MM, p[1] + w[1] * size * MM, 0.0])
    m = VMobject(stroke_color=colour, stroke_width=width)
    m.set_points_as_corners([a, b, c])
    return m


def cut_line_fv(x_lo, x_hi, colour=CUT_COL, width=2.0, opacity=0.5):
    m = math.tan(math.radians(TILT))
    z_at = lambda x: CUT_P0[2] + (x - CUT_P0[0]) * m
    return Line(fv(x_lo, z_at(x_lo)), fv(x_hi, z_at(x_hi)), color=colour,
                stroke_width=width, stroke_opacity=opacity)


def prism_views():
    base = prism_corners()
    top = [p + A for p in base]
    xs = [p[0] for p in base]
    fv_out = VGroup(
        Line(fv(min(xs), 0), fv(max(xs), 0), color=SOLID_COL, stroke_width=3.4),
        Line(fv(min(xs) + A[0], A[2]), fv(max(xs) + A[0], A[2]),
             color=SOLID_COL, stroke_width=3.4),
        Line(fv(min(xs), 0), fv(min(xs) + A[0], A[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(max(xs), 0), fv(max(xs) + A[0], A[2]), color=SOLID_COL, stroke_width=3.4),
        DashedLine(fv(0, 0), fv(A[0], A[2]), color=MUTED, stroke_width=1.8,
                   dash_length=0.06),
    )
    tv_out = VGroup(
        Polygon(*[tv(p[0], p[1]) for p in base], color=SOLID_COL, stroke_width=2.4,
                stroke_opacity=0.85),
        Polygon(*[tv(p[0], p[1]) for p in top], color=SOLID_COL, stroke_width=3.4),
        *[Line(tv(base[k][0], base[k][1]), tv(top[k][0], top[k][1]),
               color=SOLID_COL, stroke_width=2.4) for k in range(4)],
    )
    return fv_out, tv_out


# ==========================================================================
#  S02 - the oblique square prism
# ==========================================================================
class S02_ObliquePrism(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        G = S["prism"]
        run = S["prism_run"]
        base = prism_corners()
        fv_out, tv_out = prism_views()
        xy = Line(P2(-30, XY_Y), P2(DEV_X + run[-1] + 14, XY_Y), color=INK, stroke_width=2.2)
        views = VGroup(fv_out, tv_out)

        givens = VGroup(
            dim(fv(0, 0), fv(A[0], A[2]), f"{AXIS:.0f}", SLATE, offset=0.0, gap=30.0, size=12),
            Arc(radius=0.34, start_angle=0, angle=math.radians(LEAN),
                arc_center=fv(0, 0), color=SLATE, stroke_width=1.6),
            mono(f"{LEAN:.0f}°", color=SLATE, size=12).move_to(fv(17, 4)),
            dim(tv(base[0][0], base[0][1]), tv(base[1][0], base[1][1]),
                f"{PRISM['side']:.0f}", SLATE, offset=-6.0, gap=4.5, size=12),
        )
        # the top face's plan sits right over corner 3, so that one number goes
        # into the clear wedge inside it rather than radially out
        tag_at = {0: (-30.0, 0.0), 1: (0.0, -28.5), 2: (25.2, -8.0), 3: (0.0, 28.5)}
        corner_tags = VGroup(*[
            mono(str(k + 1), color=SOLID_COL, size=13).move_to(tv(*tag_at[k]))
            for k in range(4)])

        # ---- the cutting plane ------------------------------------------------
        cut_ext = cut_line_fv(-30, 60)
        cut_fv = Line(fv_of(G[0]["cut"]), fv_of(G[2]["cut"]), color=CUT_COL, stroke_width=4.2)
        cut_dots = VGroup(*[Dot(fv_of(g["cut"]), radius=0.038, color=CUT_COL) for g in G])
        ang_arc = Arc(radius=0.28, start_angle=0, angle=math.radians(TILT),
                      arc_center=fv(CUT_P0[0], CUT_P0[2]), color=CUT_COL, stroke_width=1.7)
        ang_tag = mono(f"{TILT:.0f}°", color=CUT_COL, size=12).move_to(
            fv(CUT_P0[0] + 17, CUT_P0[2] + 3))
        cut_tag = mono(f"{CUT_AT:.0f} along the axis", color=CUT_COL, size=12).move_to(
            fv(64, 34))
        # stop the leader short of the tag's own left edge, or it pokes into it
        cut_lead = Line(fv(40, CUT_P0[2] + 24 * math.tan(math.radians(TILT))),
                        fv(47, 37), color=MUTED, stroke_width=1.0)

        # ---- the right section ------------------------------------------------
        rs_line = Line(rs_fv(-31), rs_fv(31), color=RS_COL, stroke_width=4.2)
        rs_dots = VGroup(*[Dot(fv_of(g["rs"]), radius=0.038, color=RS_COL) for g in G])
        rs_mark = sq_mark2(fv(C_FV[0], C_FV[1]), U_DIR, AX_DIR, colour=RS_COL, width=2.2)
        rs_tag = mono("right section ⟂ axis", color=RS_COL, size=13).move_to(rs_fv(-48))

        # ---- the auxiliary view -----------------------------------------------
        projectors = VGroup(*[
            DashedLine(fv_of(G[k]["rs"]), aux_pt(G[k]["uv"][0], max(0.0, G[k]["uv"][1]) + 7),
                       color=AUX_COL, stroke_width=1.1, stroke_opacity=0.5, dash_length=0.05)
            for k in (0, 1, 2)])
        aux_poly = Polygon(*[aux_pt(*g["uv"]) for g in G], color=RS_COL, stroke_width=4.0,
                           fill_color=RS_COL, fill_opacity=0.15)
        aux_dots = VGroup(*[Dot(aux_pt(*g["uv"]), radius=0.034, color=RS_COL) for g in G])
        aux_tags = VGroup(*[
            mono(f"{k + 1}₁", color=RS_COL, size=12).move_to(
                aux_pt(g["uv"][0] * 1.34, g["uv"][1] * 1.34))
            for k, g in enumerate(G)])
        aux_dia = VGroup(
            Line(aux_pt(*G[0]["uv"]), aux_pt(*G[2]["uv"]), color=MUTED, stroke_width=1.2),
            Line(aux_pt(*G[1]["uv"]), aux_pt(*G[3]["uv"]), color=MUTED, stroke_width=1.2),
        )
        u_full, v_full = 2 * abs(G[0]["uv"][0]), 2 * abs(G[1]["uv"][1])
        aux_cap = VGroup(
            caption("TRUE SHAPE", color=RS_COL, size=16),
            mono(f"{u_full:.2f} × {v_full:.2f}", color=RS_COL, size=13),
            mono(f"side {run[1]:.2f}", color=RS_COL, size=13),
        ).arrange(DOWN, buff=0.09).move_to(P2(93, 86))

        sheet_left = VGroup(xy, views, givens, corner_tags, cut_ext, cut_fv, cut_dots,
                            ang_arc, ang_tag, cut_tag, cut_lead, rs_line, rs_dots,
                            rs_mark, rs_tag, projectors, aux_poly, aux_dots, aux_tags,
                            aux_dia, aux_cap)

        # ---- the development ---------------------------------------------------
        so = Line(dev_pt(0, 0), dev_pt(run[-1], 0), color=RS_COL, stroke_width=4.2)
        so_ticks = VGroup(*[Dot(dev_pt(r, 0), radius=0.032, color=RS_COL) for r in run])
        seq = [G[k % 4] for k in range(5)]
        rays = VGroup(*[
            Line(dev_pt(run[k], seq[k]["to_base"]), dev_pt(run[k], seq[k]["to_top"]),
                 color=DEV_COL, stroke_width=1.8) for k in range(5)])
        base_line = VMobject(stroke_color=SOLID_COL, stroke_width=3.2)
        base_line.set_points_as_corners([dev_pt(run[k], seq[k]["to_base"]) for k in range(5)])
        top_line = VMobject(stroke_color=SOLID_COL, stroke_width=3.2)
        top_line.set_points_as_corners([dev_pt(run[k], seq[k]["to_top"]) for k in range(5)])
        cut_dev = VMobject(stroke_color=CUT_COL, stroke_width=4.0)
        cut_dev.set_points_as_corners([dev_pt(run[k], seq[k]["to_cut"]) for k in range(5)])
        cut_dev_dots = VGroup(*[Dot(dev_pt(run[k], seq[k]["to_cut"]), radius=0.034,
                                    color=CUT_COL) for k in range(5)])
        pattern = Polygon(*([dev_pt(run[k], seq[k]["to_base"]) for k in range(5)] +
                            [dev_pt(run[k], seq[k]["to_cut"]) for k in range(4, -1, -1)]),
                          stroke_width=0, fill_color=DEV_COL, fill_opacity=0.16)
        dev_nums = VGroup(*[
            mono(str((k % 4) + 1), color=DEV_COL, size=13).move_to(
                dev_pt(run[k], seq[k]["to_base"] - 7)) for k in range(5)])
        so_dim = dim(dev_pt(0, 0), dev_pt(run[-1], 0), f"{run[-1]:.2f}", RS_COL,
                     offset=-52.0, gap=6.0, size=13)
        # a vertical dim() puts its figure at mid-height, which here is exactly
        # on the stretch-out line - so this one is built by hand, outside the seam
        check = VGroup(
            DoubleArrow(dev_pt(-11, seq[0]["to_base"]), dev_pt(-11, seq[0]["to_top"]),
                        buff=0, color=GOLD, stroke_width=1.6, tip_length=0.09),
            Line(dev_pt(0, seq[0]["to_base"]), dev_pt(-13, seq[0]["to_base"]),
                 color=MUTED, stroke_width=1.0),
            Line(dev_pt(0, seq[0]["to_top"]), dev_pt(-13, seq[0]["to_top"]),
                 color=MUTED, stroke_width=1.0),
            mono(f"{AXIS:.0f}", color=GOLD, size=13).move_to(dev_pt(-20, -10.6)),
        )
        dev_cap = caption("DEVELOPMENT", color=DEV_COL, size=17).move_to(
            dev_pt(run[-1] / 2, 62))
        development = VGroup(pattern, so, so_ticks, rays, base_line, top_line, cut_dev,
                             cut_dev_dots, dev_nums, so_dim, check, dev_cap)

        bar = pin_to_frame(self, card_back(title_bar(
            "Oblique prism, cut", "right section · true shape · stretch-out")),
            corner=UP + LEFT, buff=0.30)
        rail, rungs = make_rail(
            self,
            step_badge("1", "cut a section square to the axis", "the RIGHT section", RS_COL),
            step_badge("2", "find its true shape", "auxiliary: depths from the plan", RS_COL),
            step_badge("3", "roll THAT out as a straight line", "its perimeter is the stretch-out", DEV_COL),
            step_badge("4", "set every generator off it", "base below, top above, cut where it falls", CUT_COL),
        )
        self.add(bar, rail)
        self.add_foreground_mobjects(bar, rail)
        centre, W = frame_target([views, givens], right=0.28)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "An oblique square prism: base thirty on the side, set on its diagonals, "
            "axis sixty long leaning at sixty degrees. Cut by a plane inclined at "
            "thirty degrees, crossing the axis thirty-two from the base.",
            FadeIn(bar), FadeIn(rail), Create(views), FadeIn(xy), FadeIn(givens),
            FadeIn(corner_tags),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Draw the cutting plane first - in the front view it is one line, and "
            f"where it crosses the four edges gives four heights: {G[0]['cut'][2]:.2f}, "
            f"{G[1]['cut'][2]:.2f} twice, and {G[2]['cut'][2]:.2f}. Nothing new there; "
            "that is episode ten.",
            Create(cut_ext), Create(ang_arc), FadeIn(ang_tag), FadeIn(cut_tag),
            Create(cut_lead), Create(cut_fv), FadeIn(cut_dots),
            lag_ratio=0.18,
        )
        narrate(
            self,
            "Now the part that is new. Draw a second line through the axis, at right "
            "angles to it. That is the right section. It is not a cut anyone is "
            "asking for - it is a measuring line we are inventing, because it is the "
            "only line on this solid that is square to every generator.",
            rail_focus(rail, rungs, 0),
            Create(rs_line), Create(rs_mark), FadeIn(rs_dots), FadeIn(rs_tag),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Its true shape comes from an auxiliary view looking straight down the "
            "axis. Throw the projectors out parallel to the axis, and take the depths "
            "from the top view - depths are never foreshortened here, because the "
            "solid leans across the sheet, not towards you.",
            rail_focus(rail, rungs, 1),
            look_at(self, [sheet_left], right=0.28, top=0.12),
            Create(projectors), Create(aux_poly), FadeIn(aux_dots), FadeIn(aux_tags),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"And it is not a square. It is a rhombus, {u_full:.2f} across by "
            f"{v_full:.2f} deep: the depth is untouched, and everything across the "
            "sheet is squashed by the sine of sixty. Four equal sides of "
            f"{run[1]:.2f}, which is what we actually need.",
            FadeIn(aux_dia), FadeIn(aux_cap),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Roll that rhombus out flat. Four sides of {run[1]:.2f} make a stretch-out "
            f"line {run[-1]:.2f} long - and notice it is the perimeter of the RIGHT "
            "SECTION, not of the base. The base's perimeter is a hundred and twenty, "
            "and it is the wrong number.",
            rail_focus(rail, rungs, 2),
            look_at(self, [development], right=0.24),
            Create(so), FadeIn(so_ticks), FadeIn(so_dim), FadeIn(dev_nums),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "At each station put up a perpendicular - that is the generator - and "
            "measure along it from the stretch-out line, because the stretch-out line "
            "IS the right section. The base is below it, between nineteen and "
            "forty-one down. The top is above it, by the same amounts the other way "
            "round.",
            rail_focus(rail, rungs, 3),
            Create(rays), Create(base_line), Create(top_line),
            lag_ratio=0.18,
        )
        narrate(
            self,
            f"And here is the check. Every generator of a prism is the same length, "
            f"so between those two lines every perpendicular must measure exactly "
            f"{AXIS:.0f}. If one of them does not, the arithmetic is wrong and you "
            "have found it before you cut any metal.",
            FadeIn(check),
        )
        narrate(
            self,
            f"Last, the cut. Corner three's cut point is {G[2]['to_cut']:.2f} ABOVE the "
            f"right section; corner one's is {abs(G[0]['to_cut']):.2f} BELOW it. Set "
            "each one off on its own perpendicular, sign and all, join them up, and "
            "the shaded piece is the development.",
            Create(cut_dev), FadeIn(cut_dev_dots), FadeIn(pattern), FadeIn(dev_cap),
            lag_ratio=0.2,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S03 - the oblique cylinder: twelve generators, and an elliptical section
# ==========================================================================
def cyl_views():
    R = CYL_R
    fv_out = VGroup(
        Line(fv(-R, 0), fv(R, 0), color=SOLID_COL, stroke_width=3.4),
        Line(fv(A[0] - R, A[2]), fv(A[0] + R, A[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(-R, 0), fv(A[0] - R, A[2]), color=SOLID_COL, stroke_width=3.4),
        Line(fv(R, 0), fv(A[0] + R, A[2]), color=SOLID_COL, stroke_width=3.4),
        DashedLine(fv(0, 0), fv(A[0], A[2]), color=MUTED, stroke_width=1.6,
                   dash_length=0.06),
    )
    tv_out = VGroup(
        Circle(radius=R * MM, color=SOLID_COL, stroke_width=2.4,
               stroke_opacity=0.8).move_to(tv(0, 0)),
        Circle(radius=R * MM, color=SOLID_COL, stroke_width=3.4).move_to(tv(A[0], 0)),
        Line(tv(0, R), tv(A[0], R), color=SOLID_COL, stroke_width=3.4),
        Line(tv(0, -R), tv(A[0], -R), color=SOLID_COL, stroke_width=3.4),
    )
    return fv_out, tv_out


class S03_ObliqueCylinder(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        G = S["cyl"]
        run = S["cyl_run"]
        R = CYL_R
        fv_out, tv_out = cyl_views()
        xy = Line(P2(-30, XY_Y), P2(DEV_X + run[-1] + 14, XY_Y), color=INK, stroke_width=2.2)
        views = VGroup(fv_out, tv_out)
        givens = VGroup(
            DoubleArrow(tv(-R, 0), tv(R, 0), buff=0, color=SLATE, stroke_width=1.6,
                        tip_length=0.09),
            mono(f"Ø{CYL['dia']:.0f}", color=SLATE, size=12).move_to(tv(-R - 26, 0)),
            dim(fv(0, 0), fv(A[0], A[2]), f"{AXIS:.0f}", SLATE, offset=0.0, gap=22.0, size=12),
            mono(f"{LEAN:.0f}°", color=SLATE, size=12).move_to(fv(17, 4)),
            Arc(radius=0.34, start_angle=0, angle=math.radians(LEAN),
                arc_center=fv(0, 0), color=SLATE, stroke_width=1.6),
        )

        gens_fv = VGroup(*[
            Line(fv(g["v"][0], 0), fv(g["v"][0] + A[0], A[2]), color=SOLID_COL,
                 stroke_width=1.4, stroke_opacity=0.7) for g in G])
        gens_tv = VGroup(*[
            Line(tv(g["v"][0], g["v"][1]), tv(g["v"][0] + A[0], g["v"][1]),
                 color=SOLID_COL, stroke_width=1.4, stroke_opacity=0.7) for g in G])
        nums_tv = VGroup(*[
            mono(str(k + 1), color=SLATE, size=11).move_to(
                tv(32.0, -14.0) if k == 6 else tv(g["v"][0] * 1.32, g["v"][1] * 1.32))
            for k, g in enumerate(G)])
        lead7 = Line(tv(22, -1), tv(30, -11), color=SLATE, stroke_width=1.0,
                     stroke_opacity=0.7)

        cut_ext = cut_line_fv(-28, 56)
        cut_fv = Line(fv_of(G[0]["cut"]), fv_of(G[6]["cut"]), color=CUT_COL, stroke_width=4.2)
        cut_dots = VGroup(*[Dot(fv_of(g["cut"]), radius=0.030, color=CUT_COL) for g in G])
        ang_arc = Arc(radius=0.28, start_angle=0, angle=math.radians(TILT),
                      arc_center=fv(CUT_P0[0], CUT_P0[2]), color=CUT_COL, stroke_width=1.7)
        ang_tag = mono(f"{TILT:.0f}°", color=CUT_COL, size=12).move_to(
            fv(CUT_P0[0] + 17, CUT_P0[2] + 3))

        rs_line = Line(rs_fv(-29), rs_fv(29), color=RS_COL, stroke_width=4.2)
        rs_mark = sq_mark2(fv(C_FV[0], C_FV[1]), U_DIR, AX_DIR, colour=RS_COL, width=2.2)
        rs_dots = VGroup(*[Dot(fv_of(g["rs"]), radius=0.028, color=RS_COL) for g in G])

        u_semi, v_semi = R * SIN_LEAN, R
        aux_ell = Ellipse(width=2 * u_semi * MM, height=2 * v_semi * MM,
                          color=RS_COL, stroke_width=4.0, fill_color=RS_COL,
                          fill_opacity=0.14)
        aux_ell.rotate(-math.radians(90.0 - LEAN)).move_to(aux_pt(0, 0))
        aux_dots = VGroup(*[Dot(aux_pt(*g["uv"]), radius=0.028, color=RS_COL) for g in G])
        aux_axes = VGroup(
            Line(aux_pt(-u_semi, 0), aux_pt(u_semi, 0), color=MUTED, stroke_width=1.2),
            Line(aux_pt(0, -v_semi), aux_pt(0, v_semi), color=MUTED, stroke_width=1.2),
        )
        projectors = VGroup(*[
            DashedLine(fv_of(G[k]["rs"]), aux_pt(G[k]["uv"][0], v_semi + 7),
                       color=AUX_COL, stroke_width=1.1, stroke_opacity=0.45,
                       dash_length=0.05)
            for k in (0, 3, 6)])
        aux_cap = VGroup(
            caption("TRUE SHAPE", color=RS_COL, size=16),
            mono("an ellipse", color=RS_COL, size=13),
            mono(f"{2 * v_semi:.2f} × {2 * u_semi:.2f}", color=RS_COL, size=13),
        ).arrange(DOWN, buff=0.09).move_to(P2(93, 86))
        sheet_left = VGroup(xy, views, givens, gens_fv, gens_tv, nums_tv, cut_ext,
                            cut_fv, cut_dots, ang_arc, ang_tag, rs_line, rs_mark,
                            rs_dots, projectors, aux_ell, aux_dots, aux_axes, aux_cap)

        n = len(G)
        seq = [G[k % n] for k in range(n + 1)]
        so = Line(dev_pt(0, 0), dev_pt(run[-1], 0), color=RS_COL, stroke_width=4.2)
        so_ticks = VGroup(*[Dot(dev_pt(r, 0), radius=0.026, color=RS_COL) for r in run])
        rays = VGroup(*[
            Line(dev_pt(run[k], seq[k]["to_base"]), dev_pt(run[k], seq[k]["to_top"]),
                 color=DEV_COL, stroke_width=1.5) for k in range(n + 1)])
        base_curve = VMobject(stroke_color=SOLID_COL, stroke_width=3.2)
        base_curve.set_points_smoothly([dev_pt(run[k], seq[k]["to_base"]) for k in range(n + 1)])
        top_curve = VMobject(stroke_color=SOLID_COL, stroke_width=3.2)
        top_curve.set_points_smoothly([dev_pt(run[k], seq[k]["to_top"]) for k in range(n + 1)])
        cut_curve = VMobject(stroke_color=CUT_COL, stroke_width=4.0)
        cut_curve.set_points_smoothly([dev_pt(run[k], seq[k]["to_cut"]) for k in range(n + 1)])
        cut_dev_dots = VGroup(*[Dot(dev_pt(run[k], seq[k]["to_cut"]), radius=0.028,
                                    color=CUT_COL) for k in range(n + 1)])
        pattern = Polygon(*([dev_pt(run[k], seq[k]["to_base"]) for k in range(n + 1)] +
                            [dev_pt(run[k], seq[k]["to_cut"]) for k in range(n, -1, -1)]),
                          stroke_width=0, fill_color=DEV_COL, fill_opacity=0.15)
        dev_nums = VGroup(*[
            mono(str((k % n) + 1), color=DEV_COL, size=11).move_to(
                dev_pt(run[k], seq[k]["to_base"] - 7)) for k in range(n + 1)])
        so_dim = dim(dev_pt(0, 0), dev_pt(run[-1], 0), f"{run[-1]:.2f}", RS_COL,
                     offset=-52.0, gap=6.0, size=13)
        check = VGroup(
            DoubleArrow(dev_pt(-11, seq[0]["to_base"]), dev_pt(-11, seq[0]["to_top"]),
                        buff=0, color=GOLD, stroke_width=1.6, tip_length=0.09),
            Line(dev_pt(0, seq[0]["to_base"]), dev_pt(-13, seq[0]["to_base"]),
                 color=MUTED, stroke_width=1.0),
            Line(dev_pt(0, seq[0]["to_top"]), dev_pt(-13, seq[0]["to_top"]),
                 color=MUTED, stroke_width=1.0),
            mono(f"{AXIS:.0f}", color=GOLD, size=13).move_to(dev_pt(-21, -10.0)),
        )
        dev_cap = caption("DEVELOPMENT", color=DEV_COL, size=17).move_to(
            dev_pt(run[-1] / 2, 62))
        development = VGroup(pattern, so, so_ticks, rays, base_curve, top_curve,
                             cut_curve, cut_dev_dots, dev_nums, so_dim, check, dev_cap)

        bar = pin_to_frame(self, card_back(title_bar(
            "Oblique cylinder, cut", "Ø40 · axis 60 at 60° · twelve generators")),
            corner=UP + LEFT, buff=0.30)
        self.add(bar)
        self.add_foreground_mobjects(bar)
        centre, W = frame_target([views, givens], right=0.20, top=0.14)
        self.camera.frame.set(width=W).move_to(centre)

        narrate(
            self,
            "The same sheet again, for the cylinder from question one - forty "
            "diameter, axis sixty at sixty degrees. A cylinder has no edges, so "
            "divide the base into twelve and work with generators.",
            FadeIn(bar), Create(views), FadeIn(xy), FadeIn(givens),
            Create(gens_fv), Create(gens_tv), FadeIn(nums_tv), Create(lead7),
            lag_ratio=0.16,
        )
        narrate(
            self,
            "The cutting plane is the one from the prism: thirty degrees, crossing "
            "the axis thirty-two up. And the right section is the same idea - one "
            "line square to the axis, cutting every generator at ninety degrees.",
            Create(cut_ext), Create(ang_arc), FadeIn(ang_tag), Create(cut_fv),
            FadeIn(cut_dots), Create(rs_line), Create(rs_mark), FadeIn(rs_dots),
            lag_ratio=0.16,
        )
        narrate(
            self,
            f"Its true shape is an ellipse - {2 * v_semi:.0f} deep, which is the "
            f"diameter untouched, by {2 * u_semi:.2f} across, which is the diameter "
            "times the sine of sixty. A circle looked at from an angle, which is "
            "exactly what it is.",
            look_at(self, [sheet_left], right=0.22, top=0.12),
            Create(projectors), Create(aux_ell), FadeIn(aux_dots), FadeIn(aux_axes),
            FadeIn(aux_cap),
            lag_ratio=0.2,
        )
        narrate(
            self,
            f"Step the twelve divisions round that ellipse and lay them out in a "
            f"line. They are NOT all equal - they run from {run[4] - run[3]:.2f} to "
            f"{run[1] - run[0]:.2f} - and they add up to {run[-1]:.2f}, which is the "
            "width of the pattern. Not pi D. Pi D would have given you a hundred and "
            "twenty-six.",
            look_at(self, [development], right=0.20),
            Create(so), FadeIn(so_ticks), FadeIn(so_dim), FadeIn(dev_nums),
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Perpendicular at every station, and measure from the line. The base runs "
            "from twenty below at generator seven to forty below at generator one; "
            "the top mirrors it. Join both with smooth curves.",
            Create(rays), Create(base_curve), Create(top_curve),
            lag_ratio=0.15,
        )
        narrate(
            self,
            f"The check still holds: between those two curves, every perpendicular is "
            f"{AXIS:.0f}. On a cylinder that is the easiest thing in the world to "
            "verify with dividers, and it catches a mis-stepped division instantly.",
            FadeIn(check),
        )
        narrate(
            self,
            f"Then the cut, {G[6]['to_cut']:.0f} above the line at generator seven and "
            f"{abs(G[0]['to_cut']):.0f} below it at generator one, through a smooth "
            "curve - and the shaded piece is the development of what is left.",
            Create(cut_curve), FadeIn(cut_dev_dots), FadeIn(pattern), FadeIn(dev_cap),
            lag_ratio=0.2,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S04 - which stretch-out line does the question want?
# ==========================================================================
class S04_Recap(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Four solids, four patterns", "Sheet 8 · how to tell which method")
        self.add(bar)

        # A cell is text inside an invisible box of fixed height, so the columns
        # line up row for row. set(width=...) SCALES a Text mobject - it does not
        # pad it - so using it to size a column blows the font up with it.
        def cell(text, colour, size):
            t = mono(text, color=colour, size=size)
            box = Rectangle(width=max(t.width, 0.02), height=0.40,
                            stroke_width=0, fill_opacity=0)
            t.move_to(box.get_left(), aligned_edge=LEFT)
            return VGroup(box, t)

        DATA = [
            ("solid", "its generators", "stretch-out line", "ep.", MUTED, 14),
            ("right prism · cylinder", "parallel AND square to the base",
             "the base — perimeter or πD", "10·12", GOLD, 15),
            ("right cone · pyramid", "all meet the apex, all equal",
             "a sector, 360 R/L", "11", TEAL, 15),
            ("oblique cone · pyramid", "meet the apex, all different",
             "none — triangulate face by face", "14", VIOLET, 15),
            ("oblique prism · cylinder", "parallel, NOT square to the base",
             "the RIGHT SECTION", "16", CORAL, 15),
        ]
        cols = []
        for i in range(4):
            colour_of = lambda r, i=i: (r[4] if i == 0 else
                                        SLATE if i == 1 else
                                        INK if i == 2 else MUTED)
            cols.append(VGroup(*[cell(r[i], colour_of(r) if k else MUTED, r[5])
                                 for k, r in enumerate(DATA)])
                        .arrange(DOWN, buff=0.22, aligned_edge=LEFT))
        table = VGroup(*cols).arrange(RIGHT, buff=0.42, aligned_edge=UP)
        head = VGroup(*[c[0] for c in cols])
        rows = VGroup(*[VGroup(*[c[k + 1] for c in cols]) for k in range(4)])
        table.set(width=min(table.width, 12.4))
        table.next_to(bar, DOWN, buff=0.55).to_edge(LEFT, buff=0.7)

        narrate(
            self,
            "Sheet eight has four developments in it, and the whole of choosing "
            "between them is one question: what line does the solid roll along?",
            settle(FadeIn(head)),
        )
        narrate(
            self,
            "A right prism or cylinder rolls on its base, because the base is square "
            "to the generators. Perimeter, or pi D. A right cone or pyramid does not "
            "roll at all - it opens about its apex into a sector, or a fan of "
            "identical triangles.",
            settle(FadeIn(rows[0]), FadeIn(rows[1]), lag=0.3),
        )
        narrate(
            self,
            "Lean a cone or a pyramid and the generators stop being equal, so there "
            "is no sector and no stretch-out line at all - you build the pattern one "
            "triangle at a time, which was episode fourteen.",
            settle(FadeIn(rows[2])),
        )
        narrate(
            self,
            "And lean a prism or a cylinder and the generators stay parallel and stay "
            "equal - they just stop being square to the base. So you make yourself a "
            "base that is square to them: the right section. That one line is the "
            "whole of this episode.",
            settle(FadeIn(rows[3])),
        )

        last = card_back(VGroup(
            chip("the stretch-out is the RIGHT SECTION's perimeter, never the base's",
                 color=RS_COL, size=18),
            chip("measure every generator from that line — above it and below it",
                 color=DEV_COL, size=18),
            chip("check: base to top is the same on every generator", color=GOLD, size=18),
        ).arrange(DOWN, buff=0.16))
        last.next_to(table, DOWN, buff=0.5).to_edge(LEFT, buff=0.7)
        narrate(
            self,
            "Three things to take away, and the last one is the one that saves you: "
            "on any prism or cylinder, right or oblique, base to top is the same "
            "distance on every single generator. Measure it. If it is not, something "
            "upstream is wrong.",
            settle(FadeIn(last)),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  Marking scheme
# ==========================================================================
if __name__ == "__main__":
    print("Sheet 8 - development of an OBLIQUE prism and cylinder by right section")
    print("  x across the sheet · y depth (negative = in front) · z up · mm")
    print(f"  axis {AXIS:.0f} long at {LEAN:.0f}° to the base  ->  "
          f"({A[0]:.0f}, 0, {A[2]:.4f})")
    print(f"  right section taken {RS_AT:.0f} along the axis; cutting plane at "
          f"{TILT:.0f}° crossing the axis {CUT_AT:.0f} along")
    print(f"  a right-section point is the base point with x foreshortened by "
          f"sin {LEAN:.0f}° = {SIN_LEAN:.6f}; depth untouched")

    for name, gens, runs, extra in (
        ("oblique square prism, side %.0f on its diagonals" % PRISM["side"],
         S["prism"], S["prism_run"],
         "right section: a RHOMBUS %.3f x %.3f, four sides of %.4f"
         % (2 * abs(S["prism"][0]["uv"][0]), 2 * abs(S["prism"][1]["uv"][1]),
            S["prism_run"][1])),
        ("oblique cylinder, Ø%.0f" % CYL["dia"], S["cyl"], S["cyl_run"],
         "right section: an ELLIPSE %.3f x %.3f (πD would be %.3f)"
         % (2 * CYL_R, 2 * CYL_R * SIN_LEAN, math.pi * CYL["dia"])),
    ):
        print()
        print(f"  {name}")
        print(f"    {extra}")
        print(f"    stretch-out {runs[-1]:.4f}")
        print("    gen    base x    z of cut    run       below RS    above RS    cut")
        for k, g in enumerate(gens):
            print(f"     {k + 1:2}  {g['v'][0]:+8.3f}  {g['cut'][2]:9.3f}  "
                  f"{runs[k]:8.3f}  {abs(g['to_base']):9.3f}  {g['to_top']:9.3f}  "
                  f"{g['to_cut']:+9.3f}")

    print()
    print("  Checks that run at import:")
    print("    · the right section is square to every generator, to 1e-9")
    print("    · its true shape is the base foreshortened by sin of the lean")
    print(f"    · base to top is {AXIS:.0f} on EVERY generator of both solids")
    print("    · the cutting plane stays strictly between base and top throughout")
    print("    · the prism's right section is a rhombus, not a square")
