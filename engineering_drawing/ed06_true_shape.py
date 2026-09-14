"""
Engineering Drawing I - Sheet 4 / Lecture 4  (Basic Descriptive Geometry II)
Episode 06: Edge View, True Shape and True Size of an Oblique Plane
            + worked solution to Exercise 4 (Set A), Q.6  (Figure P4.6)

Render (Windows, py -3.11):
    py -3.11 -m manim -qh ed06_true_shape.py S04_Construction
    ... or use render_ed06.bat to build all five scenes in order.

Scene order (about eleven minutes in all):

    S01_WhyBothViewsLie   the plate is tilted to BOTH planes, so both views lie -
                          and one side, measured three times, proves it
    S02_EdgeViewIdea      look ALONG a horizontal line of the plate and it closes
                          up into a line; the camera actually performs the look,
                          so the edge view is watched happening rather than
                          asserted
    S03_Strategy          the four steps, and the chain of views that settles
                          which distance is transferred where
    S04_Construction      Q.6 solved on one sheet, the camera following the
                          pencil and every transferred dimension flying from the
                          view it was measured in to the view it lands in
    S05_Recap             the two rules, the mirror image for the V P, homework

Nothing here is drawn by eye. `construction()` derives every point on the sheet
from the five given dimensions and then checks its own work before a single
line is animated: the edge view must be exactly collinear, the angle it makes
with X1Y1 must equal the inclination computed from the space coordinates, and
each side of the true shape must equal the true distance between the space
points. The 3-D scenes are built from the SAME five dimensions, so the plate
you watch tilt in space is the plate that is solved on the sheet.

No LaTeX anywhere - every glyph is Unicode Text(), so the file renders on a
machine with no TeX installed.
"""

from __future__ import annotations

import math

import numpy as np
from manim import *

from ed_stage import CAM_PHI, CAM_THETA, ProjectionScene, marker, projector
from ed_common import (
    CORAL,
    CREAM,
    GOLD,
    INK,
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
    title_bar,
)

# ==========================================================================
#  Figure P4.6 - the given, in millimetres
#      x = position along XY,  h = height above the HP,  d = distance in
#      front of the VP
# ==========================================================================
GIVEN = {
    "A": dict(x=0.0,  h=47.0, d=8.0),
    "B": dict(x=76.0, h=62.0, d=33.0),
    "C": dict(x=42.0, h=13.0, d=58.0),
}
KEYS = ("A", "B", "C")
SIDES = (("A", "B"), ("B", "C"), ("C", "A"))

# One colour per corner, used in every view and in space. A student should be
# able to follow ONE corner through four views by colour alone - that is what
# makes the transfers readable when three of them happen at once.
VCOL = {"A": CORAL, "B": TEAL, "C": VIOLET}

GAP1 = 49.0     # X1Y1 set back from the top view
GAP2 = 52.0     # X2Y2 set back from the edge view (searched: keeps the true
                # shape clear of the given views and of X1Y1)
MM = 0.0297     # drawing millimetre -> Manim unit (the flat sheet)
S3 = 0.030      # millimetre -> Manim unit in the 3-D stage
X_MID = 38.0    # the x that is centred in the 3-D stage


def construction():
    """
    Work the whole problem out numerically. Returns 2-D points in millimetre
    space (x to the right, y upwards, XY along y = 0).
    """
    fv = {k: np.array([GIVEN[k]["x"], GIVEN[k]["h"]]) for k in KEYS}
    tv = {k: np.array([GIVEN[k]["x"], -GIVEN[k]["d"]]) for k in KEYS}

    # --- a horizontal line of the plane: through a', parallel to XY ---------
    t = (GIVEN["A"]["h"] - GIVEN["B"]["h"]) / (GIVEN["C"]["h"] - GIVEN["B"]["h"])
    m_fv = fv["B"] + t * (fv["C"] - fv["B"])
    m_tv = tv["B"] + t * (tv["C"] - tv["B"])

    # look ALONG that line: u is the projection direction, w is X1Y1
    u = (m_tv - tv["A"]) / np.linalg.norm(m_tv - tv["A"])
    w = np.array([-u[1], u[0]])

    # --- auxiliary 1: distance from X1Y1 = height above the HP -------------
    p0 = u * (max(np.dot(tv[k], u) for k in KEYS) + GAP1)
    aux1 = {k: p0 + w * np.dot(tv[k] - p0, w) + u * GIVEN[k]["h"] for k in KEYS}
    step = {k: -float(np.dot(tv[k] - p0, u)) for k in KEYS}   # to carry into aux 2

    # --- auxiliary 2: X2Y2 parallel to the edge view -----------------------
    v = aux1["B"] - aux1["A"]
    v = v / np.linalg.norm(v)
    n2 = np.array([-v[1], v[0]])
    q0 = aux1["A"] + n2 * GAP2
    aux2 = {k: aux1[k] + n2 * (GAP2 + step[k]) for k in KEYS}

    # --- verify before drawing --------------------------------------------
    e1, e2 = aux1["B"] - aux1["A"], aux1["C"] - aux1["A"]
    residual = abs(e1[0] * e2[1] - e1[1] * e2[0]) / np.linalg.norm(e1)
    assert residual < 1e-6, f"auxiliary 1 is not an edge view ({residual})"

    space = {k: np.array([GIVEN[k]["x"], GIVEN[k]["d"], GIVEN[k]["h"]]) for k in KEYS}
    for p, q in SIDES:
        drawn = np.linalg.norm(aux2[p] - aux2[q])
        true = np.linalg.norm(space[p] - space[q])
        assert abs(drawn - true) < 1e-6, f"true shape side {p}{q} is wrong"

    normal = np.cross(space["B"] - space["A"], space["C"] - space["A"])
    theta = math.degrees(math.acos(abs(normal[2]) / np.linalg.norm(normal)))
    theta_v = math.degrees(math.acos(abs(normal[1]) / np.linalg.norm(normal)))
    # the edge view's angle has to be measured against X1Y1, not the page edge:
    # v is in page coordinates, so resolve it along w (X1Y1) and u (across it)
    drawn = math.degrees(math.atan2(abs(float(np.dot(v, u))), abs(float(np.dot(v, w)))))
    assert abs(theta - drawn) < 1e-6, f"edge view angle {drawn} != inclination {theta}"

    return dict(
        fv=fv, tv=tv, m_fv=m_fv, m_tv=m_tv, u=u, w=w, p0=p0, q0=q0,
        aux1=aux1, aux2=aux2, step=step, v=v, n2=n2,
        theta=theta, theta_v=theta_v,
        # the three lengths of every side: what it really is, and the two lies
        sides={(p, q): float(np.linalg.norm(space[p] - space[q])) for p, q in SIDES},
        fv_sides={(p, q): float(np.linalg.norm(fv[p] - fv[q])) for p, q in SIDES},
        tv_sides={(p, q): float(np.linalg.norm(tv[p] - tv[q])) for p, q in SIDES},
    )


G = construction()


# ==========================================================================
#  The flat sheet: millimetre space -> Manim points, and the drawing furniture
# ==========================================================================
def P(v2):
    """millimetre space -> Manim point"""
    return np.array([v2[0] * MM, v2[1] * MM, 0.0])


def tri(points, color, width=3.4, opacity=0.0):
    return Polygon(*[P(points[k]) for k in KEYS], stroke_color=color,
                   stroke_width=width, fill_color=color, fill_opacity=opacity)


def dim(p_from, p_to, text, color, size=15, offset=0.0, gap=7.0):
    """
    A slim dimension: a double arrow from `p_from` to `p_to` with its value
    beside it. `offset` slides the whole thing sideways off the line it is
    measuring, so a transferred distance never sits on top of the projector it
    belongs to. These are the mobjects that FLY from one view to the next.
    """
    a, b = P(p_from), P(p_to)
    d = b - a
    length = float(np.linalg.norm(d))
    n = np.array([-d[1], d[0], 0.0])
    n = n / max(float(np.linalg.norm(n)), 1e-9)
    a, b = a + n * offset * MM, b + n * offset * MM
    arrow = DoubleArrow(a, b, buff=0, color=color, stroke_width=1.7,
                        tip_length=float(min(0.10, 0.32 * length)))
    side = 1.0 if offset >= 0 else -1.0
    lab = mono(text, color=color, size=size).move_to((a + b) / 2 + n * side * gap * MM)
    return VGroup(arrow, lab)


def right_angle(point, d1, d2, color=INK, size=6.5):
    """The little square that says PERPENDICULAR, drawn in the two directions
    given - it is the whole justification for step three, so it is worth a
    mark on the sheet."""
    p = P(point)
    e1 = np.array([d1[0], d1[1], 0.0]) * size * MM
    e2 = np.array([d2[0], d2[1], 0.0]) * size * MM
    mark = VMobject(stroke_color=color, stroke_width=1.8)
    mark.set_points_as_corners([p + e1, p + e1 + e2, p + e2])
    return mark


def par_marks(point, direction, color, size=5.0, gap=5.0):
    """The pair of slashes that says PARALLEL - step four's justification."""
    d = np.array([direction[0], direction[1], 0.0])
    d = d / np.linalg.norm(d)
    n = np.array([-d[1], d[0], 0.0])
    g = VGroup()
    for s in (-0.5, 0.5):
        c = P(point) + d * s * gap * MM
        arm = (n * 0.9 + d * 0.45) * size * MM
        g.add(Line(c - arm, c + arm, color=color, stroke_width=2.4))
    return g


def step_badge(number, title, detail, color):
    """One rung of the running step rail."""
    number_mob = mono(number, color=color, size=22)
    title_mob = caption(title, color=INK, size=18)
    detail_mob = mono(detail, color=SLATE, size=13)
    words = VGroup(title_mob, detail_mob).arrange(DOWN, buff=0.06, aligned_edge=LEFT)
    return VGroup(number_mob, words).arrange(RIGHT, buff=0.18, aligned_edge=UP)


# ==========================================================================
#  The 3-D stage: the same five dimensions, stood up in space
# ==========================================================================
def pt3(x_mm, d_mm, h_mm):
    """millimetre space -> the 3-D stage (+x along XY, -y in front of the VP,
    +z above the HP)."""
    return np.array([(x_mm - X_MID) * S3, -d_mm * S3, h_mm * S3])


def vertex3(k):
    g = GIVEN[k]
    return pt3(g["x"], g["d"], g["h"])


def on_vp(p):
    return np.array([p[0], 0.0, p[2]])


def on_hp(p):
    return np.array([p[0], p[1], 0.0])


# ==========================================================================
#  S01 - neither view is the true shape, and the numbers say so
# ==========================================================================
class S01_WhyBothViewsLie(ProjectionScene):
    quadrant = 1
    heading = "True Shape of an Oblique Plane"
    subheading = "Sheet 4 · a plane tilted to BOTH reference planes"

    def construct(self):
        self.build_stage()
        # the episode title is a long one, so drop the quadrant badge a line to
        # keep the top of the frame legible
        self.badge.shift(DOWN * 0.62)
        self.add(self.vp, self.hp, self.xy, *self.tags, self.bar)

        pts = {k: vertex3(k) for k in KEYS}
        plate = Polygon(*[pts[k] for k in KEYS], stroke_color=GOLD, stroke_width=4,
                        fill_color=GOLD, fill_opacity=0.30)
        dots = VGroup(*[marker(pts[k], VCOL[k], 0.075) for k in KEYS])
        labs = VGroup(*[mono(k, color=VCOL[k], size=24).move_to(
            pts[k] + np.array([0.0, -0.18, 0.20])) for k in KEYS])
        billboard(self, *labs)

        # a slow drift, about a quarter turn over the two sentences: enough for
        # the eye to read the tilt as three-dimensional, not enough to lose the
        # observer's side of the planes
        self.begin_ambient_camera_rotation(rate=0.012)
        narrate(
            self,
            "A plane is only three points with the edges filled in, so nothing we "
            "have learned about points is thrown away. Here is a triangular plate, "
            "A B C, in the first angle: above the horizontal plane and in front of "
            "the vertical plane.",
            Create(plate), FadeIn(dots), FadeIn(labs),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "A is forty-seven millimetres above the H P, B is sixty-two and C only "
            "thirteen. Three different heights, so the plate leans away from the "
            "horizontal plane. Their distances in front of the V P differ as well, "
            "so it leans away from the vertical plane too. Tilted to both: that is "
            "what oblique means, and it is the whole difficulty of this lesson.",
            Indicate(dots, scale_factor=1.35, color=GOLD),
        )
        self.stop_ambient_camera_rotation()

        fvp = {k: on_vp(pts[k]) for k in KEYS}
        tvp = {k: on_hp(pts[k]) for k in KEYS}
        fv = Polygon(*[fvp[k] for k in KEYS], stroke_color=CORAL, stroke_width=3.5,
                     fill_color=CORAL, fill_opacity=0.32)
        tv = Polygon(*[tvp[k] for k in KEYS], stroke_color=TEAL, stroke_width=3.5,
                     fill_color=TEAL, fill_opacity=0.32)
        rays_v = VGroup(*[projector(pts[k], fvp[k], CORAL) for k in KEYS])
        rays_h = VGroup(*[projector(pts[k], tvp[k], TEAL) for k in KEYS])

        fly_camera(
            self,
            "Stand square in front of the vertical plane and look straight at it. "
            "Every corner sends a projector back to the V P, and joining the three "
            "landing points gives the front view.",
            Create(rays_v), TransformFromCopy(plate, fv),
            phi=74 * DEGREES, theta=-90 * DEGREES, zoom=0.92,
        )
        fly_camera(
            self,
            "Now climb above the arrangement and look straight down. The same three "
            "corners drop onto the horizontal plane and give the top view.",
            Create(rays_h), TransformFromCopy(plate, tv),
            phi=22 * DEGREES, theta=-90 * DEGREES, zoom=0.92,
        )

        ab3 = Line(pts["A"], pts["B"], color=GOLD, stroke_width=8)
        abf = Line(fvp["A"], fvp["B"], color=CORAL, stroke_width=7)
        abt = Line(tvp["A"], tvp["B"], color=TEAL, stroke_width=7)
        fly_camera(
            self,
            "Two triangles, then. Both of them wrong. Take one side and measure it "
            "three times to see how wrong.",
            Create(ab3), Create(abf), Create(abt),
            phi=62 * DEGREES, theta=-58 * DEGREES, zoom=0.88,
        )

        rows = VGroup(
            mono("side A B, measured three times", color=SLATE, size=17),
            mono(f"in space        {G['sides'][('A', 'B')]:.1f} mm", color=GOLD, size=20),
            mono(f"in front view   {G['fv_sides'][('A', 'B')]:.1f} mm", color=CORAL, size=20),
            mono(f"in top view     {G['tv_sides'][('A', 'B')]:.1f} mm", color=TEAL, size=20),
        ).arrange(DOWN, buff=0.13, aligned_edge=LEFT)
        card = hud(self, VGroup(
            SurroundingRectangle(rows, color=SLATE, buff=0.26, corner_radius=0.12,
                                 stroke_width=1.4, fill_color=NAVY, fill_opacity=0.88),
            rows,
        ).to_corner(DOWN + RIGHT, buff=0.5))

        narrate(
            self,
            "In space that side is eighty-one point four millimetres long. The front "
            "view calls it seventy-seven point five. The top view calls it eighty. "
            "Both views have shortened it, and neither by the same amount.",
            FadeIn(card),
        )
        narrate(
            self,
            "That shortening is not a small error you may ignore. It is simply what "
            "projection does to a line that is not parallel to the plane it is "
            "projected onto. Every side of this plate is foreshortened, so every "
            "corner angle is bent, so neither view is the shape of the plate.",
            Indicate(fv, color=CORAL), Indicate(tv, color=TEAL),
            lag_ratio=0.25,
        )

        rule = hud(self, chip(
            "true shape  ⇐  a plane of projection PARALLEL to the plane",
            color=GOLD, size=21).to_edge(DOWN, buff=0.55))
        narrate(
            self,
            "There is only one way to see a plane truly: project it onto a plane "
            "that is parallel to it. Neither the H P nor the V P is parallel to this "
            "plate, so we shall have to invent one that is. That is an auxiliary "
            "plane, and this time we shall need two of them.",
            FadeOut(card), FadeIn(rule),
            lag_ratio=0.4,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S02 - the edge view, watched happening
# ==========================================================================
class S02_EdgeViewIdea(ProjectionScene):
    quadrant = 1
    heading = "The Edge View"
    subheading = "look along the plane and it closes up"

    def construct(self):
        self.build_stage()
        self.remove(self.badge)          # the stage comes in later, after the paper
        self.add(self.bar)
        self.set_camera_orientation(zoom=1.45)   # close in on the sheet of paper

        # ---- the paper analogy, played out rather than described -----------
        # A vertical sheet whose plane has been swung round to the camera's own
        # azimuth is EXACTLY edge on, whatever the camera's elevation - so this
        # rotation ends on a line, it does not merely nearly end on one.
        sheet = Rectangle(width=2.6, height=1.75, stroke_color=INK, stroke_width=3,
                          fill_color=CREAM, fill_opacity=0.9)
        sheet.rotate(90 * DEGREES, axis=RIGHT).move_to(np.array([0.0, -0.6, 0.55]))
        edge_of_sheet = Line(sheet.get_center() + OUT * 0.9,
                             sheet.get_center() + IN * 0.9,
                             color=GOLD, stroke_width=7)

        narrate(
            self,
            "Why two auxiliary views and not one? Because you cannot jump straight "
            "to a plane parallel to the plate. There is an in-between view to make "
            "first, and it is worth having for its own sake.",
            FadeIn(sheet),
        )
        narrate(
            self,
            "Hold a sheet of paper up at eye level and turn it slowly. As its "
            "surface comes round into your line of sight the rectangle narrows, and "
            "narrows, and then it is gone.",
            Rotate(sheet, -60 * DEGREES, axis=OUT, about_point=sheet.get_center()),
            rate_func=rate_functions.ease_in_out_sine,
        )
        narrate(
            self,
            "What is left is a line. A plane looked at along itself always shows as "
            "a straight line, and that line is called the edge view.",
            Create(edge_of_sheet),
        )

        # ---- the same thing done to the plate ------------------------------
        pts = {k: vertex3(k) for k in KEYS}
        plate = Polygon(*[pts[k] for k in KEYS], stroke_color=GOLD, stroke_width=4,
                        fill_color=GOLD, fill_opacity=0.30)
        dots = VGroup(*[marker(pts[k], VCOL[k], 0.075) for k in KEYS])
        labs = VGroup(*[mono(k, color=VCOL[k], size=24).move_to(
            pts[k] + np.array([0.0, -0.18, 0.20])) for k in KEYS])
        billboard(self, *labs)

        fly_camera(
            self,
            "So do that to the plate. Your line of sight has to lie inside the plane "
            "itself, which means looking along some line of the plate. Any line "
            "would serve, but one kind of line makes the drawing easy.",
            FadeOut(sheet), FadeOut(edge_of_sheet),
            FadeIn(self.vp), FadeIn(self.hp), FadeIn(self.xy), FadeIn(self.tags),
            FadeIn(self.badge), Create(plate), FadeIn(dots), FadeIn(labs),
            phi=CAM_PHI, theta=CAM_THETA, zoom=0.88,
        )

        # the horizontal line of the plate: through A, cutting BC at the same height
        M = pt3(G["m_fv"][0], -G["m_tv"][1], G["m_fv"][1])
        horiz = Line(pts["A"], M, color=CREAM, stroke_width=7)
        m_dot = marker(M, CREAM, 0.06)
        m_lab = billboard(self, mono("M", color=CREAM, size=22)
                          .move_to(M + np.array([0.12, 0.0, 0.20])))

        narrate(
            self,
            "Take the line of the plate that happens to be horizontal: through A, "
            "level with A, cutting B C at a point we shall call M. Every plane holds "
            "a whole family of them, all parallel to one another.",
            Create(horiz), FadeIn(m_dot), FadeIn(m_lab),
            lag_ratio=0.3,
        )

        h_tv = Line(on_hp(pts["A"]), on_hp(M), color=TEAL, stroke_width=5)
        h_rays = VGroup(projector(pts["A"], on_hp(pts["A"]), TEAL),
                        projector(M, on_hp(M), TEAL))
        tl_mid = (on_hp(pts["A"]) + on_hp(M)) / 2
        tl_tag = billboard(self, mono("true length", color=TEAL, size=18)
                           .move_to(tl_mid - np.array([G["w"][0], G["w"][1], 0.0]) * 0.42))
        narrate(
            self,
            "Because A M is parallel to the horizontal plane, its top view is its "
            "true length and points in its true direction. That is the whole reason "
            "for choosing it: the top view now tells us exactly which way to look.",
            Create(h_rays), Create(h_tv), FadeIn(tl_tag),
            lag_ratio=0.3,
        )

        # ---- look along A M ------------------------------------------------
        u3 = np.array([G["u"][0], G["u"][1], 0.0])
        w3 = np.array([G["w"][0], G["w"][1], 0.0])
        sight = VGroup(*[DashedLine(pts[k] + u3 * 1.15, pts[k] - u3 * 0.75,
                                    color=SLATE, stroke_width=2.2, dash_length=0.1)
                         for k in KEYS])
        narrate(
            self,
            "These are the lines of sight: all parallel to A M, all running straight "
            "along the surface of the plate.",
            Create(sight),
            lag_ratio=0.2,
        )

        centroid = sum(pts[k] for k in KEYS) / 3.0
        theta_cam = math.atan2(u3[1], u3[0])
        fly_camera(
            self,
            "Now put your eye in line with them and look straight down A M. Watch "
            "what happens to the plate.",
            FadeOut(self.vp), FadeOut(self.tags[0]), FadeOut(sight),
            phi=90 * DEGREES, theta=theta_cam, zoom=1.7, focal_distance=60.0,
            frame_center=np.array([centroid[0], centroid[1], 0.85]),
        )

        # The exact edge view: the plate's plane cut by the plane through the
        # centroid perpendicular to the direction of sight. Every vertex lands on
        # this one line, which is why the plate shows as a line.
        proj = {k: pts[k] - u3 * float(np.dot(pts[k] - centroid, u3)) for k in KEYS}
        edge_dir = proj["B"] - proj["C"]
        edge_dir = edge_dir / np.linalg.norm(edge_dir)
        order = sorted(KEYS, key=lambda k: float(np.dot(proj[k] - centroid, edge_dir)))
        ends = (proj[order[0]] - edge_dir * 0.28, proj[order[-1]] + edge_dir * 0.28)
        edge = Line(*ends, color=GOLD, stroke_width=7)
        edots = VGroup(*[marker(proj[k], VCOL[k], 0.062) for k in KEYS])

        narrate(
            self,
            "There it is. Three corners, three different heights, and yet from here "
            "they are in a straight line. The plate has closed up: this is its edge "
            "view.",
            FadeOut(plate), FadeOut(dots), FadeOut(horiz), FadeOut(m_dot),
            FadeOut(m_lab), FadeOut(labs),
            # everything that has done its job goes, or it piles up on the
            # ground line now that the whole stage is seen edge on
            FadeOut(h_tv), FadeOut(h_rays), FadeOut(tl_tag),
            FadeOut(self.tags[2]), FadeOut(self.tags[3]),
            Create(edge), FadeIn(edots),
            lag_ratio=0.25,
        )

        # the angle the edge view makes with the horizontal, drawn in the plane
        # that is square to the camera, so it reads true on screen
        s = 1.0 if float(np.dot(edge_dir, w3)) >= 0 else -1.0
        if edge_dir[2] < 0:
            edge_dir, s = -edge_dir, -s
        base = proj[min(KEYS, key=lambda k: proj[k][2])]
        ang = math.atan2(float(edge_dir[2]), float(np.dot(edge_dir, s * w3)))
        assert abs(math.degrees(ang) - G["theta"]) < 1e-6, "the 3-D angle is not θH"

        ground = DashedLine(base, base + s * w3 * 1.5, color=SLATE,
                            stroke_width=2.6, dash_length=0.1)
        arc = Arc(radius=0.55, start_angle=0.0, angle=ang, color=GOLD, stroke_width=4)
        arc.apply_matrix(np.array([[s * w3[0], 0.0, s * u3[0]],
                                   [s * w3[1], 0.0, s * u3[1]],
                                   [0.0, 1.0, 0.0]]))
        arc.shift(base)
        # parked well out along the ground line, inside the wedge: at this
        # distance the angle has opened far enough for the label to sit clear of
        # both arms and of the arc
        arc_lab = billboard(self, mono(f"θH = {G['theta']:.1f}°", color=GOLD, size=24)
                            .move_to(base + s * w3 * 1.45 + OUT * 0.50))

        narrate(
            self,
            "And the horizontal plane is edge on as well - it is the line running "
            "along the bottom. So the angle between the two lines is the true "
            f"inclination of the plate to the horizontal plane: theta H, "
            f"{G['theta']:.1f} degrees. One line, and that question is answered "
            "outright.",
            Create(ground), Create(arc), FadeIn(arc_lab),
            lag_ratio=0.3,
        )

        note = hud(self, chip(
            "on paper:  X1Y1  ⊥  the TOP VIEW of the horizontal line",
            color=GOLD, size=21).to_edge(DOWN, buff=0.6))
        narrate(
            self,
            "Everything you have just watched happen in space is what the drawing "
            "does on paper. The direction of sight was along a horizontal line of "
            "the plate, so on the sheet the new reference line is drawn "
            "perpendicular to the top view of that line. Perpendicular, because we "
            "are looking straight along it.",
            FadeIn(note),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S03 - the strategy, and the chain of views behind it
# ==========================================================================
class S03_Strategy(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("The Four Steps", "edge view first, true shape second")
        self.add(bar)

        steps = [
            ("1", "draw a horizontal line of the plane",
             "in the front view, through a corner, parallel to XY", CREAM),
            ("2", "X1Y1  PERPENDICULAR to its top view",
             "you are looking along the line · carry HEIGHTS from the front view", TEAL),
            ("3", "the three points land in a line",
             "that is the edge view · its angle with X1Y1 is θH", GOLD),
            ("4", "X2Y2  PARALLEL to the edge view",
             "carry DISTANCES from X1Y1, measured in the top view → true shape", VIOLET),
        ]
        rows = VGroup()
        for num, headline, sub, colour in steps:
            n = mono(num, color=colour, size=26)
            h = caption(headline, color=colour, size=21)
            s = mono(sub, color=SLATE, size=15)
            text = VGroup(h, s).arrange(DOWN, buff=0.09, aligned_edge=LEFT)
            rows.add(VGroup(n, text).arrange(RIGHT, buff=0.32, aligned_edge=UP))
        rows.arrange(DOWN, buff=0.30, aligned_edge=LEFT).move_to(np.array([-0.35, 0.70, 0]))

        narrate(self, "Four steps, and the whole exercise is these four steps.",
                FadeIn(bar))
        for i, text in enumerate([
            "One. In the front view, draw a line through a corner parallel to X Y, "
            "cutting the opposite side. Parallel to X Y in the front view means "
            "parallel to the H P in space, so that line is horizontal, and its top "
            "view is true length.",

            "Two. Draw the new reference line, X one Y one, perpendicular to that "
            "top view, because we are going to look straight along it. Project the "
            "corners across, and step off each corner's height above the H P.",

            "Three. The three points come out in a straight line. That is the edge "
            "view, and the angle it makes with X one Y one is theta H, the true "
            "inclination of the plane to the horizontal plane.",

            "Four. Draw X two Y two parallel to the edge view. Project across again, "
            "and this time step off each corner's distance from X one Y one, taken "
            "from the top view. Join the three points: true shape, true size.",
        ]):
            narrate(self, text, FadeIn(rows[i], shift=RIGHT * 0.25))

        # ---- the chain of views: why a distance comes from where it does ----
        names = ["FRONT VIEW", "TOP VIEW", "EDGE VIEW", "TRUE SHAPE"]
        cols = [CORAL, TEAL, GOLD, VIOLET]
        boxes = VGroup(*[chip(t, color=c, size=16) for t, c in zip(names, cols)])
        boxes.arrange(RIGHT, buff=1.15).move_to(np.array([0, -1.85, 0]))

        joins = VGroup()
        for a, b, name in zip(boxes[:-1], boxes[1:], ["XY", "X1Y1", "X2Y2"]):
            arrow = Arrow(a.get_right(), b.get_left(), buff=0.12, color=SLATE,
                          stroke_width=2.4, max_tip_length_to_length_ratio=0.22)
            joins.add(VGroup(arrow, mono(name, color=SLATE, size=14)
                             .next_to(arrow, UP, buff=0.06)))

        def hop(a, b, text, colour, drop=1.15):
            start, end = a.get_bottom() + DOWN * 0.06, b.get_bottom() + DOWN * 0.06
            mid = (start + end) / 2 + DOWN * drop
            curve = VMobject(stroke_color=colour, stroke_width=2.6)
            curve.set_points_as_corners([start, mid, end]).make_smooth()
            tip = Triangle(fill_color=colour, fill_opacity=1, stroke_width=0)
            tip.scale(0.075).move_to(end)
            lab = mono(text, color=colour, size=16).move_to(mid + DOWN * 0.2)
            return VGroup(curve, tip, lab)

        carry_h = hop(boxes[0], boxes[2], "carry the HEIGHTS", CORAL, 0.80)
        carry_d = hop(boxes[1], boxes[3], "carry the DISTANCES", TEAL, 1.30)

        narrate(
            self,
            "Steps two and four are tied together by one rule, and it is the rule "
            "that students get wrong. Think of the views as a chain: front view, top "
            "view, edge view, true shape, each one made from the one before it "
            "across a reference line.",
            FadeIn(boxes), FadeIn(joins),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "The distance you step off in a new view always comes from the view two "
            "steps back, measured from the reference line in between. Heights come "
            "forward from the front view into the edge view. Distances come forward "
            "from the top view into the true shape. Never from the view next door.",
            Create(carry_h[0]), FadeIn(carry_h[1], carry_h[2]),
            Create(carry_d[0]), FadeIn(carry_d[1], carry_d[2]),
            lag_ratio=0.3,
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)


# ==========================================================================
#  S04 - the whole solution, with the camera following the pencil
#  (card_back, rail_focus, frame_target and look_at are shared series
#  furniture and live in ed_common.py)
# ==========================================================================
class S04_Construction(MovingCameraScene):
    def construct(self):
        self.camera.background_color = NAVY

        fv, tv, aux1, aux2 = G["fv"], G["tv"], G["aux1"], G["aux2"]
        u, w, p0, v, n2, q0 = G["u"], G["w"], G["p0"], G["v"], G["n2"], G["q0"]
        udir = np.array([u[0], u[1], 0.0])
        wdir = np.array([w[0], w[1], 0.0])
        vdir = np.array([v[0], v[1], 0.0])
        ndir = np.array([n2[0], n2[1], 0.0])

        # ---------------- the given views ------------------------------------
        left = min(P(tv[k])[0] for k in KEYS) - 0.5
        right = max(P(tv[k])[0] for k in KEYS) + 0.5
        xy = Line(np.array([left, 0, 0]), np.array([right, 0, 0]), color=INK,
                  stroke_width=2.8)
        xy_lab = VGroup(mono("X", color=INK, size=16).next_to(xy, LEFT, buff=0.1),
                        mono("Y", color=INK, size=16).next_to(xy, RIGHT, buff=0.1))
        proj = VGroup(*[DashedLine(P(fv[k]), P(tv[k]), color=VCOL[k], stroke_width=1.1,
                                   stroke_opacity=0.45, dash_length=0.05) for k in KEYS])
        fv_tri = tri(fv, CORAL, 3.2, 0.10)
        tv_tri = tri(tv, TEAL, 3.2, 0.10)
        vdots = VGroup(*[Dot(P(fv[k]), radius=0.042, color=VCOL[k]) for k in KEYS],
                       *[Dot(P(tv[k]), radius=0.042, color=VCOL[k]) for k in KEYS])
        def outward(point, cloud):
            """Unit vector from the middle of `cloud` towards `point` - labels
            hung this way always land OUTSIDE the triangle they belong to."""
            mid = sum(P(cloud[j]) for j in KEYS) / 3.0
            d = P(point) - mid
            return d / max(float(np.linalg.norm(d)), 1e-9)

        vlabs = VGroup()
        for k in KEYS:
            vlabs.add(mono(f"{k.lower()}′", color=VCOL[k], size=16)
                      .next_to(P(fv[k]), outward(fv[k], fv), buff=0.07))
            vlabs.add(mono(k.lower(), color=VCOL[k], size=16)
                      .next_to(P(tv[k]), outward(tv[k], tv), buff=0.07))
        given = VGroup(xy, xy_lab, proj, fv_tri, tv_tri, vdots, vlabs)

        # ---------------- step 2: the horizontal line -------------------------
        hz_fv = Line(P(fv["A"]), P(G["m_fv"]), color=CREAM, stroke_width=3.6)
        hz_drop = DashedLine(P(G["m_fv"]), P(G["m_tv"]), color=CREAM, stroke_width=1.1,
                             stroke_opacity=0.55, dash_length=0.05)
        hz_tv = Line(P(tv["A"]), P(G["m_tv"]), color=CREAM, stroke_width=3.6)
        m_labs = VGroup(
            mono("m′", color=CREAM, size=15)
            .next_to(P(G["m_fv"]), outward(G["m_fv"], fv), buff=0.06),
            mono("m", color=CREAM, size=15)
            .next_to(P(G["m_tv"]), outward(G["m_tv"], tv), buff=0.06))
        tl_tag = mono("true length", color=CREAM, size=13).move_to(
            (P(tv["A"]) + P(G["m_tv"])) / 2 + np.array([-w[0], -w[1], 0.0]) * 0.26)
        horiz_g = VGroup(hz_fv, hz_drop, hz_tv, m_labs, tl_tag)

        # ---------------- step 3: X1Y1 and the edge view ----------------------
        span1 = [np.dot(tv[k] - p0, w) for k in KEYS] + [np.dot(aux1[k] - p0, w) for k in KEYS]
        x1y1 = Line(P(p0 + w * (min(span1) - 14)), P(p0 + w * (max(span1) + 14)),
                    color=INK, stroke_width=2.6)
        x1_lab = mono("X1", color=INK, size=15).move_to(x1y1.get_start() - wdir * 0.24)
        y1_lab = mono("Y1", color=INK, size=15).move_to(x1y1.get_end() + wdir * 0.24)
        foot1 = {k: p0 + w * np.dot(tv[k] - p0, w) for k in KEYS}
        ra1 = right_angle(foot1["A"], -w, u, color=INK)

        rays1 = VGroup(*[DashedLine(P(tv[k]), P(aux1[k]), color=VCOL[k], stroke_width=1.1,
                                    stroke_opacity=0.5, dash_length=0.05) for k in KEYS])
        # A sits at the left-hand end of the figure and B at the right, so their
        # height dimensions are thrown outwards, away from the triangle; C's is
        # below it either way. (`offset` is measured 90° anticlockwise from the
        # dimension's own direction, so the signs are not interchangeable.)
        heights = VGroup(*[
            dim(np.array([fv[k][0], 0.0]), fv[k], f"{GIVEN[k]['h']:.0f}", VCOL[k],
                offset=off, gap=6.5)
            for k, off in zip(KEYS, (7.0, -7.0, -7.0))])
        carried1 = VGroup(*[
            dim(foot1[k], aux1[k], f"{GIVEN[k]['h']:.0f}", VCOL[k], offset=off, gap=6.0)
            for k, off in zip(KEYS, (-5.0, 5.0, -5.0))])

        edge = Line(P(aux1["C"] - v * 8), P(aux1["B"] + v * 8), color=GOLD, stroke_width=4.5)
        edots = VGroup(*[Dot(P(aux1[k]), radius=0.045, color=VCOL[k]) for k in KEYS])
        elabs = VGroup(*[mono(f"{k.lower()}1", color=VCOL[k], size=15)
                         .move_to(P(aux1[k]) + udir * 0.24) for k in KEYS])

        arm = DashedLine(P(aux1["C"]), P(aux1["C"] + w * 50), color=GOLD, stroke_width=1.4,
                         stroke_opacity=0.85, dash_length=0.05)
        vert = P(aux1["B"]) - P(aux1["C"])
        w_ang = math.atan2(w[1], w[0])
        edge_ang = math.atan2(vert[1], vert[0])
        a_arc = Arc(radius=0.40, start_angle=w_ang, angle=edge_ang - w_ang,
                    arc_center=P(aux1["C"]), color=GOLD, stroke_width=2.6)
        # on the bisector, far enough out that the wedge has opened wider than
        # the label - any nearer and the value sits on one of its own arms
        bisector = (w_ang + edge_ang) / 2.0
        a_lab = mono(f"θH = {G['theta']:.1f}°", color=GOLD, size=17).move_to(
            P(aux1["C"]) + 1.45 * np.array([math.cos(bisector), math.sin(bisector), 0.0]))
        aux1_g = VGroup(x1y1, x1_lab, y1_lab, ra1, rays1, carried1, edge, edots, elabs,
                        arm, a_arc, a_lab)

        # ---------------- step 4: X2Y2 and the true shape ---------------------
        span2 = [np.dot(aux1[k] - q0, v) for k in KEYS] + [np.dot(aux2[k] - q0, v) for k in KEYS]
        # stopped short at the X2 end: run it any further and it crosses X1Y1,
        # and the two reference lines end up labelled on top of one another
        x2y2 = Line(P(q0 + v * (min(span2) - 7)), P(q0 + v * (max(span2) + 14)),
                    color=INK, stroke_width=2.6)
        x2_lab = mono("X2", color=INK, size=15).move_to(
            x2y2.get_start() - vdir * 0.22 + ndir * 0.16)
        y2_lab = mono("Y2", color=INK, size=15).move_to(x2y2.get_end() + vdir * 0.24)
        par = VGroup(par_marks((aux1["A"] + aux1["B"]) / 2, v, GOLD),
                     par_marks(q0 + v * float(np.dot((aux1["A"] + aux1["B"]) / 2 - q0, v)),
                               v, GOLD))

        rays2 = VGroup(*[DashedLine(P(aux1[k]), P(aux2[k]), color=VCOL[k], stroke_width=1.1,
                                    stroke_opacity=0.5, dash_length=0.05) for k in KEYS])
        # these run back the other way along the projectors, so the signs are
        # mirrored to push each dimension off its neighbour, not onto it
        steps_src = VGroup(*[
            dim(foot1[k], tv[k], f"{G['step'][k]:.0f}", VCOL[k], offset=off, gap=6.0)
            for k, off in zip(KEYS, (5.0, -5.0, 5.0))])
        steps_dst = VGroup(*[
            dim(aux1[k] + n2 * GAP2, aux2[k], f"{G['step'][k]:.0f}", VCOL[k],
                offset=off, gap=6.0)
            for k, off in zip(KEYS, (-5.0, 5.0, -5.0))])

        ts = tri(aux2, GOLD, 4.5, 0.14)
        tdots = VGroup(*[Dot(P(aux2[k]), radius=0.05, color=VCOL[k]) for k in KEYS])
        tlabs = VGroup(*[mono(f"{k.lower()}2", color=VCOL[k], size=16)
                         .move_to(P(aux2[k]) + ndir * 0.24) for k in KEYS])
        tsp = mono("TRUE SHAPE", color=GOLD, size=15).move_to(
            P((aux2["A"] + aux2["B"] + aux2["C"]) / 3))

        def outside(p, q, other):
            a, b, c = aux2[p], aux2[q], aux2[other]
            d = b - a
            n = np.array([-d[1], d[0]]) / np.linalg.norm(d)
            return -9.0 if float(np.dot(c - a, n)) > 0 else 9.0
        side_dims = VGroup(*[
            dim(aux2[p], aux2[q], f"{G['sides'][(p, q)]:.1f}", GOLD, size=15,
                offset=outside(p, q, o), gap=6.5)
            for (p, q), o in zip(SIDES, ("C", "A", "B"))])
        aux2_g = VGroup(x2y2, x2_lab, y2_lab, par, rays2, steps_dst, ts, tdots, tlabs, tsp)

        sheet = VGroup(given, horiz_g, aux1_g, steps_src, heights, aux2_g, side_dims)

        # ---------------- the furniture, pinned to the screen ------------------
        centre, W = frame_target([given])
        self.camera.frame.set(width=W).move_to(centre)

        bar = pin_to_frame(self, card_back(title_bar(
            "Exercise 4 (Set A) · Q.6",
            "Figure P4.6 · true shape and θ with the HP")),
            corner=UP + LEFT, buff=0.30)
        rungs = VGroup(
            step_badge("1", "plot the given views", "front view above XY, top view below", SLATE),
            step_badge("2", "find a horizontal line", "a′m′ ∥ XY in the front view, then am", CREAM),
            step_badge("3", "make the edge view", "X1Y1 ⊥ am · carry the heights", GOLD),
            step_badge("4", "make the true shape", "X2Y2 ∥ edge view · carry the distances", VIOLET),
        ).arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        for rung in rungs:
            rung.set_opacity(0.26)
        rail = card_back(rungs)
        rail.levels = [0.26, 0.26, 0.26, 0.26]
        pin_to_frame(self, rail, corner=UP + RIGHT, buff=0.35)

        data_rows = VGroup(
            mono("GIVEN (mm)", color=SLATE, size=15),
            mono("        height   depth      x", color=SLATE, size=13),
            mono("  A        47       8       0", color=CORAL, size=15),
            mono("  B        62      33      76", color=TEAL, size=15),
            mono("  C        13      58      42", color=VIOLET, size=15),
        ).arrange(DOWN, buff=0.11, aligned_edge=LEFT)
        data = VGroup(SurroundingRectangle(data_rows, color=SLATE, buff=0.22,
                                           corner_radius=0.1, stroke_width=1.2,
                                           fill_color=NAVY, fill_opacity=0.85),
                      data_rows)
        pin_to_frame(self, data, corner=DOWN + RIGHT, buff=0.45)

        self.add(bar, rail)

        # ------------------------------ animate --------------------------------
        narrate(
            self,
            "Question six. The front view and the top view of a triangular plate are "
            "given, and we are asked for its true shape and its inclination to the "
            "horizontal plane.",
            FadeIn(bar), FadeIn(data),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "Set the question down first. A is forty-seven above the H P and eight in "
            "front of the V P. B is sixty-two and thirty-three. C is thirteen and "
            "fifty-eight. Their projectors stand at zero, seventy-six and forty-two "
            "along X Y.",
            rail_focus(rail, rungs, 0),
            Create(xy), FadeIn(xy_lab), Create(proj), FadeIn(vdots),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Join the three points above X Y, and the three below. There is the given "
            "figure - and remember, neither of those triangles is the true shape.",
            Create(fv_tri), Create(tv_tri), FadeIn(vlabs),
            lag_ratio=0.25,
        )

        narrate(
            self,
            "Step two. In the front view, draw a line through a prime parallel to X Y, "
            "cutting b prime c prime at m prime. Parallel to X Y in the front view "
            "means level in space, so A M is a horizontal line of the plate.",
            rail_focus(rail, rungs, 1),
            look_at(self, [given, horiz_g]),
            Create(hz_fv), FadeIn(m_labs[0]),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Drop m prime onto b c to get m, and join a to m. That top view is the "
            "true length of the horizontal line, and it points in its true direction.",
            Create(hz_drop), Create(hz_tv), FadeIn(m_labs[1]), FadeIn(tl_tag),
            lag_ratio=0.28,
        )

        narrate(
            self,
            "Step three. Draw the new reference line, X one Y one, perpendicular to a "
            "m. Perpendicular, because the way to make the plate close up is to look "
            "straight along that horizontal line.",
            rail_focus(rail, rungs, 2),
            look_at(self, [tv_tri, hz_tv, x1y1, ra1]),
            Create(x1y1), FadeIn(x1_lab), FadeIn(y1_lab), Create(ra1),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Now for the transfer, and this is where the rule earns its keep. Go two "
            "views back, to the front view, and measure the height of each corner "
            "above X Y: forty-seven, sixty-two, thirteen.",
            look_at(self, [fv_tri, heights], right=0.34),
            Create(heights),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project a, b and c across, square to X one Y one, and carry those same "
            "three heights over. Each corner keeps its own measurement - watch the "
            "colours.",
            look_at(self, [fv_tri, tv_tri, aux1_g]),
            Create(rays1),
            *[TransformFromCopy(heights[i], carried1[i]) for i in range(3)],
            lag_ratio=0.2,
        )
        narrate(
            self,
            "And the three points land in a straight line. They have to: we are "
            "looking along the plate. That line is the edge view.",
            look_at(self, [aux1_g]),
            FadeIn(edots), FadeIn(elabs), Create(edge),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "The angle it makes with X one Y one is theta H, the true inclination of "
            f"the plate to the horizontal plane: {G['theta']:.1f} degrees. Half the "
            "question is answered, and we have not measured a single length yet.",
            Create(arm), Create(a_arc), FadeIn(a_lab),
            lag_ratio=0.3,
        )

        narrate(
            self,
            "Step four. Draw X two Y two parallel to the edge view. Parallel this "
            "time, because a plane parallel to a plane that is seen edge on is "
            "parallel to the plate itself - and that is the plane the true shape "
            "appears on.",
            rail_focus(rail, rungs, 3),
            look_at(self, [aux1_g, x2y2]),
            # the heights have done their work in both views now; clearing them
            # keeps the edge view, the angle and the new reference line from
            # competing with old dimensions
            FadeOut(heights), FadeOut(carried1),
            Create(x2y2), FadeIn(x2_lab), FadeIn(y2_lab), FadeIn(par),
            lag_ratio=0.22,
        )
        narrate(
            self,
            "Two views back from here is the top view. So return to it, and measure "
            "how far a, b and c each stand from X one Y one. In the drawing office "
            "you would step these off with dividers; the numbers are here only so "
            "you can see which goes where.",
            look_at(self, [tv_tri, x1y1, steps_src], right=0.34),
            Create(steps_src),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Project the edge view across, square to X two Y two, and set off those "
            "same three distances. Every distance lands on the projector it came "
            "from.",
            look_at(self, [tv_tri, aux1_g, aux2_g]),
            Create(rays2),
            *[TransformFromCopy(steps_src[i], steps_dst[i]) for i in range(3)],
            lag_ratio=0.2,
        )
        narrate(
            self,
            "Join a two, b two, c two. That is the true shape of the plate, and "
            "because the plane of projection is parallel to it, it is also the true "
            "size: every side on the paper is the side itself.",
            look_at(self, [aux2_g]),
            FadeIn(tdots), FadeIn(tlabs), Create(ts), FadeIn(tsp),
            lag_ratio=0.25,
        )
        narrate(
            self,
            "Measure them and you get eighty-one point four, sixty-four point seven "
            "and seventy-three point six millimetres - which is exactly what the "
            "three space distances come to.",
            Create(side_dims),
            lag_ratio=0.3,
        )

        ans_rows = VGroup(
            mono(f"θ with the HP   {G['theta']:.1f}°", color=GOLD, size=20),
            mono(f"AB {G['sides'][('A', 'B')]:.1f}    BC {G['sides'][('B', 'C')]:.1f}"
                 f"    CA {G['sides'][('C', 'A')]:.1f}   mm", color=SLATE, size=15),
        ).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        ans = VGroup(SurroundingRectangle(ans_rows, color=GOLD, buff=0.24,
                                          corner_radius=0.1, stroke_width=1.6,
                                          fill_color=NAVY, fill_opacity=0.9),
                     ans_rows)
        pin_to_frame(self, ans, corner=DOWN + RIGHT, buff=0.45)

        narrate(
            self,
            "Clear away the working and look at the sheet as a whole: four views, "
            "three reference lines, and every one of them earning its place.",
            look_at(self, [sheet], right=0.26, top=0.10),
            FadeOut(steps_src), FadeOut(steps_dst), FadeOut(data),
            lag_ratio=0.15,
        )
        narrate(
            self,
            f"The plate is inclined to the horizontal plane at {G['theta']:.1f} "
            "degrees, and the triangle at the far end is its true shape and true "
            "size. Both answers came out of the same two auxiliary views.",
            FadeIn(ans),
            rail_focus(rail, rungs, -1, dim_level=0.5),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.4)


# ==========================================================================
#  S05 - recap
# ==========================================================================
class S05_Recap(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        bar = title_bar("Recap", "edge view, then true shape")
        self.add(bar)

        # the finished sheet in miniature, so the words have something to point at
        fv, tv, aux1, aux2 = G["fv"], G["tv"], G["aux1"], G["aux2"]
        u, w, v, p0, q0 = G["u"], G["w"], G["v"], G["p0"], G["q0"]
        span1 = [np.dot(tv[k] - p0, w) for k in KEYS] + [np.dot(aux1[k] - p0, w) for k in KEYS]
        span2 = [np.dot(aux1[k] - q0, v) for k in KEYS] + [np.dot(aux2[k] - q0, v) for k in KEYS]

        mini_fv = tri(fv, CORAL, 2.6, 0.10)
        mini_tv = tri(tv, TEAL, 2.6, 0.10)
        mini_am = Line(P(tv["A"]), P(G["m_tv"]), color=CREAM, stroke_width=2.6)
        mini_xy = Line(P(np.array([-16.0, 0.0])), P(np.array([94.0, 0.0])),
                       color=INK, stroke_width=2.0)
        mini_x1 = Line(P(p0 + w * (min(span1) - 12)), P(p0 + w * (max(span1) + 12)),
                       color=INK, stroke_width=1.8)
        mini_edge = Line(P(aux1["C"] - v * 6), P(aux1["B"] + v * 6), color=GOLD,
                         stroke_width=3.4)
        mini_x2 = Line(P(q0 + v * (min(span2) - 12)), P(q0 + v * (max(span2) + 12)),
                       color=INK, stroke_width=1.8)
        mini_ts = tri(aux2, GOLD, 3.4, 0.16)
        mini = VGroup(mini_xy, mini_fv, mini_tv, mini_am, mini_x1, mini_edge,
                      mini_x2, mini_ts)
        mini.scale(0.48).move_to(np.array([3.7, 0.35, 0]))

        lines = VGroup(
            mono("EDGE VIEW", color=GOLD, size=22),
            mono("  X1Y1  ⊥  the top view of a", color=SLATE, size=17),
            mono("         HORIZONTAL line of the plane", color=SLATE, size=17),
            mono("  carry the HEIGHTS from the front view", color=CORAL, size=17),
            mono("TRUE SHAPE", color=VIOLET, size=22),
            mono("  X2Y2  ∥  the edge view", color=SLATE, size=17),
            mono("  carry the DISTANCES from the top view", color=TEAL, size=17),
        ).arrange(DOWN, buff=0.19, aligned_edge=LEFT).move_to(np.array([-3.6, 0.55, 0]))

        narrate(self, "Two auxiliary views, one after the other, and that is all.",
                FadeIn(bar), FadeIn(mini), lag_ratio=0.4)
        narrate(
            self,
            "The first looks along a horizontal line of the plane. Its reference line "
            "is perpendicular to the top view of that line, the heights come across "
            "from the front view, and it gives you the edge view and the inclination "
            "with the H P.",
            FadeIn(lines[0]), FadeIn(lines[1]), FadeIn(lines[2]), FadeIn(lines[3]),
            Indicate(mini_edge, color=GOLD, scale_factor=1.15),
            lag_ratio=0.3,
        )
        narrate(
            self,
            "The second is parallel to that edge view. The distances come across from "
            "the top view, and it gives you the true shape and the true size.",
            FadeIn(lines[4]), FadeIn(lines[5]), FadeIn(lines[6]),
            Indicate(mini_ts, color=GOLD, scale_factor=1.12),
            lag_ratio=0.3,
        )

        swap_rows = VGroup(
            mono("inclination with the VP?", color=GOLD, size=19),
            mono("start from a line PARALLEL TO THE VP, found in the TOP view,",
                 color=SLATE, size=16),
            mono("and drive the first auxiliary off the FRONT view", color=SLATE, size=16),
        ).arrange(DOWN, buff=0.12)
        swap = VGroup(SurroundingRectangle(swap_rows, color=GOLD, buff=0.26,
                                           corner_radius=0.1, stroke_width=1.5,
                                           fill_color=NAVY, fill_opacity=0.9),
                      swap_rows).to_edge(DOWN, buff=0.45)
        narrate(
            self,
            "Question seven asks for the inclination with the vertical plane instead. "
            "Everything mirrors. Begin with a line of the plane parallel to the V P, "
            "which you find in the top view, and drive the first auxiliary off the "
            f"front view. For this plate that angle comes to {G['theta_v']:.1f} "
            "degrees - try it and see.",
            FadeIn(swap),
        )
        narrate(
            self,
            "Work question six through on paper before the next lecture, and check "
            "your edge view honestly. If those three points do not fall in one "
            "straight line, your X one Y one was not perpendicular to the top view of "
            "the horizontal line. That is nearly always the mistake.",
            Indicate(mini_x1, color=INK, scale_factor=1.05),
        )

        finish_audio(self)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.5)


# ==========================================================================
#  Marking scheme: run the file directly and it prints the answers it is about
#  to animate, so the video can be checked against a worked solution before a
#  single frame is rendered.
#
#      py -3.11 ed06_true_shape.py
# ==========================================================================
if __name__ == "__main__":
    print("Exercise 4 (Set A) Q.6 - Figure P4.6")
    print(f"  horizontal line a′m′ at height {GIVEN['A']['h']:.0f} mm, "
          f"m at x = {G['m_tv'][0]:.1f} mm")
    print(f"  θ with the HP            {G['theta']:.2f}°")
    print(f"  θ with the VP (Q.7)      {G['theta_v']:.2f}°")
    for p_, q_ in SIDES:
        print(f"  {p_}{q_}   true {G['sides'][(p_, q_)]:7.2f} mm"
              f"   front view {G['fv_sides'][(p_, q_)]:7.2f}"
              f"   top view {G['tv_sides'][(p_, q_)]:7.2f}")
    print("  distances carried from the top view into the true shape:")
    for k in KEYS:
        print(f"    {k}  {G['step'][k]:7.2f} mm from X1Y1")
