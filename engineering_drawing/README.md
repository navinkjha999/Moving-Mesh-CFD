# Engineering Drawing I — Sheet 4, *Basic Descriptive Geometry II*

Manim CE 0.20.1 source for eleven YouTube lessons:

* **Episode 06 — Edge View, True Shape and True Size of an Oblique Plane**
  (Exercise 4, Set A, Q.6), about eleven minutes.
* **Episode 07 — Where a Line Pierces a Plane**: the piercing point, the
  hidden stretch, and the true angle (Exercise 4, Set A, Q.11), about
  thirteen minutes.
* **Episode 08 — The True Angle Between Two Planes**: the dihedral angle
  (Exercise 4, Set A, Q.12), about eight minutes.
* **Episode 09 — The Shortest Distance Between Two Skew Lines** (§4.10), and
  the common perpendicular put back on the given views, about eleven minutes.
* **Episode 10 — Section, True Shape and Development** (Sheet 8, §9):
  Exercise 7 (Set A) Q.2(a), a cylinder cut by a 45° plane, about nine minutes.
* **Episode 11 — The Cone: True Length and Development** (Sheet 8, §9):
  Exercise 7 (Set A) Q.2(e), a cone cut by two planes at once, about nine minutes.
* **Episode 12 — Prisms: a Corner With No Edge** (Sheet 8, §9):
  Exercise 7 (Set A) Q.2(b), (c) and (d) — which completes Q.2 — about seven
  minutes.
* **Episode 13 — Points on the Surface of a Solid** (Sheet 8, §6):
  Exercise 7 (Set A) Q.1 — which completes the exercise — about nine minutes.
* **Episode 14 — Oblique Solids: Development by Triangulation** (Sheet 8, §10):
  Exercise 8 (Set A) Q.3(a) and Q.3(b) — an oblique cone and an oblique
  pyramid, both cut — about twelve minutes.
* **Episode 15 — Points on the Surface of an Oblique Solid** (Sheet 8, §10):
  Exercise 8 (Set A) Q.1 — the same two helper lines as episode 13, drawn where
  the solid has actually gone — about nine and a half minutes.
* **Episode 16 — The Right Section** (Sheet 8, §10): developing an oblique
  prism and an oblique cylinder, the one case none of episodes 10–14 covers —
  about seven minutes.

```
ed06_true_shape.py      episode 06: five scenes, all the narration, all the geometry
ed07_piercing_point.py  episode 07: six scenes
ed08_dihedral_angle.py  episode 08: four scenes
ed09_skew_lines.py      episode 09: five scenes
ed10_development.py     episode 10: five scenes  (Sheet 8)
ed11_cone.py            episode 11: five scenes  (Sheet 8)
ed12_prisms.py          episode 12: four scenes  (Sheet 8)
ed13_points.py          episode 13: four scenes  (Sheet 8)
ed14_oblique.py         episode 14: five scenes  (Sheet 8)
ed15_surface_points.py  episode 15: four scenes  (Sheet 8)
ed16_right_section.py   episode 16: four scenes  (Sheet 8)
ed_stage.py             the shared 3-D stage (HP, VP, XY, the four quadrants)
ed_common.py            thin shim over cfd_common: narration, HUD and camera helpers
cfd_common.py           the series infrastructure (voice, cache, loudnorm, fonts)
render_ed06.bat         renders episode 06 in running order at 1080p60
render_ed07.bat         renders episode 07 in running order at 1080p60
render_ed08.bat         renders episode 08 in running order at 1080p60
render_ed09.bat         renders episode 09 in running order at 1080p60
render_ed10.bat         renders episode 10 in running order at 1080p60
render_ed11.bat         renders episode 11 in running order at 1080p60
render_ed12.bat         renders episode 12 in running order at 1080p60
render_ed13.bat         renders episode 13 in running order at 1080p60
render_ed14.bat         renders episode 14 in running order at 1080p60
render_ed15.bat         renders episode 15 in running order at 1080p60
render_ed16.bat         renders episode 16 in running order at 1080p60
```

---

### Render

```bat
render_ed06.bat                              REM all five scenes, 1080p60
render_ed07.bat                              REM all six scenes
render_ed08.bat                              REM all four scenes
render_ed09.bat                              REM all five scenes
render_ed10.bat                              REM all five scenes
render_ed11.bat                              REM all five scenes
render_ed12.bat                              REM all four scenes
render_ed13.bat                              REM all four scenes
render_ed14.bat                              REM all five scenes
render_ed15.bat                              REM all four scenes
render_ed16.bat                              REM all four scenes
render_ed08.bat S03                          REM just that one scene
py -3.11 -m manim -qh ed06_true_shape.py S04_Construction
py -3.11 -m manim -ql ed07_piercing_point.py S02_CuttingPlane   REM quick look
```

Render **one scene at a time**. Manim writes its rendered glyphs into a shared
`media/texts/` cache, and two renders of the same file at once will now and
then delete each other's temporary SVG mid-read; the batch files are
sequential for that reason.

Needs `manim==0.20.1`, `edge-tts`, and `ffmpeg` on the PATH. The fonts are
Bahnschrift and Cascadia Mono, both shipped with Windows; on another machine
change `H_FONT` / `M_FONT` in `cfd_common.py` or Manim will quietly substitute
something proportional for the measurement labels.

Set `EFS_SILENT=1` to render with silence instead of speech. The scene timings
are unchanged (they come from a word-count estimate), so it is the fast way to
check layout and pacing. Narration is cached under `media/narration/<Scene>/`,
so a re-render never re-synthesises a line you have not edited.

### Check the answers before rendering

```bat
py -3.11 ed06_true_shape.py
py -3.11 ed07_piercing_point.py
py -3.11 ed08_dihedral_angle.py
py -3.11 ed09_skew_lines.py
py -3.11 ed10_development.py
py -3.11 ed11_cone.py
py -3.11 ed12_prisms.py
py -3.11 ed13_points.py
```

Each prints the worked solution its animation is about to draw. Episode 06:

```
  θ with the HP            52.55°
  θ with the VP (Q.7)      44.71°
  AB   true    81.40 mm   front view   77.47   top view   80.01
  BC   true    64.67 mm   front view   59.64   top view   42.20
  CA   true    73.62 mm   front view   54.04   top view   65.30
```

Nothing in the drawing is placed by eye. `construction()` derives every point
from the five given dimensions and asserts, before a frame is rendered, that

* the three points of the first auxiliary really are collinear (it is an edge
  view, not nearly an edge view),
* the angle that line makes with X1Y1 equals the inclination computed from the
  space coordinates, and
* each side of the true shape equals the true distance between the space points.

`S02_EdgeViewIdea` makes the same check in three dimensions: the angle it draws
on screen is asserted equal to θH before the arc is built.

Episode 07 prints, and asserts, the same way:

```
  piercing point P   x 49.5   38.5 in front of the VP   44.1 above the HP
  true angle DE ^ ABC   23.29°
  front view: hidden from t = 0.472 to 0.792   (nearer = more depth)
  top view:   hidden from t = 0.472 to 0.673   (nearer = more height)
  DE measures: front 109.2  top 110.7  aux1 83.6  aux2 105.3  aux3 114.7 (true)
```

`solve()` checks that the piercing point lies on the plane and inside the
triangle, that the cut line passes through it, that each auxiliary view does
its job, and that the angle read off the finished drawing equals the angle
computed from the plane's normal.

Episode 08 likewise:

```
  hinge BC:  front view  49.68   top view  39.29   TRUE LENGTH  50.68 mm
  at the point view:  a2 49.16 mm   d2 51.24 mm   a2-d2 62.72 mm
  TRUE DIHEDRAL ANGLE  θ = 77.28°   (77° 17')
```

Its `solve()` asserts that the first auxiliary shows BC at true length, that
the second reduces it to a single point, that folding one face about the hinge
by θ lays it exactly on the other, and that the angle read at the point view
equals the one computed from the space coordinates — by two independent routes,
the perpendicular components about the hinge and the two face normals.

Episode 09:

```
  the lines cross in the front view at x 81 (41 mm apart in depth)
  and in the top view at x 24 (48 mm apart in height)  ->  SKEW
  AB:  front  93.94   top  98.62   TRUE LENGTH 106.42 mm
  it measures  front 20.09   top 23.65   aux1 21.15
  SHORTEST DISTANCE  30.71 mm   (true only in aux 2)
```

Its `solve()` asserts that the lines really are skew — non-parallel, and a
clear gap at each of the two apparent crossings — that the link it draws is
perpendicular to both of them, that no sampled link anywhere on the two
segments is shorter, that the second auxiliary reduces AB to a point, and that
the right angle at M projects true in the first auxiliary, which is the step
that lets the common perpendicular be drawn there at all.

---

### Episode 06 — the five scenes

| Scene | ≈ | What it does |
|---|---|---|
| `S01_WhyBothViewsLie` | 2:10 | The plate in the first angle, tilted to both planes. Both views are projected onto the planes, then one side — AB — is measured three times: 81.4 mm in space, 77.5 in the front view, 80.0 in the top view. Foreshortening stops being a word and becomes a number. Ends on the rule: true shape needs a plane of projection **parallel** to the plane. |
| `S02_EdgeViewIdea` | 2:30 | A sheet of paper is turned until it is edge on and becomes a line. Then the same is done to the plate: a horizontal line of the plate is drawn, its top view shown to be true length, and **the camera swings round to look along it** — the plate closes up into its edge view on screen, and the angle with the (now edge-on) HP is θH = 52.5°. |
| `S03_Strategy` | 1:45 | The four steps, then the chain of views — front → top → edge → true shape — with the two "carry it forward" arcs that show why heights come from the front view and distances from the top view. |
| `S04_Construction` | 3:50 | Q.6 solved on one sheet. The camera follows the pencil, zooming into whichever view is being drawn, and every transferred dimension physically flies from the view it was measured in to the view it lands in, each corner keeping its own colour. |
| `S05_Recap` | 1:15 | The two rules against a miniature of the finished sheet, the mirror-image method for the inclination with the VP (44.7° for this plate — Q.7), and the one check that catches the usual mistake. |

Total 11:08.

### Episode 07 — the six scenes

| Scene | ≈ | What it does |
|---|---|---|
| `S01_ThePiercingPoint` | 2:15 | The figure standing in space. One point belongs to the line and the plate at once — and from that moment half the line is hidden. Both observers' rays of sight are followed in: each meets the plate before it meets the line, at a different place, and the camera then moves to each observer's own position to show the view he draws, dashes and all. |
| `S02_CuttingPlane` | 2:30 | The method built in space before it is used on paper. A sheet of glass is stood through the line, slicing the plate along 1–2; the camera looks at the glass **face on** (two lines in one plane must cross — there is the piercing point), then from **straight above**, where the glass collapses onto the top view of the line. That is why the cutting plane never has to be drawn. |
| `S03_Piercing` | 3:20 | Q.11 part one on the sheet: the crossings 1 and 2, carried up and joined, p′ and p. Then visibility settled the way it should be — at each crossing the two candidates are compared in the *other* view, heights for the top view and depths for the front view, with the verdict marked. |
| `S04_TrueAngleA` | 1:35 | Why the angle is awkward: it needs one view with the plate edge-on **and** the line true length. The horizontal line that aims X1Y1, then auxiliary 1 (edge view) and auxiliary 2 (true shape). |
| `S05_TrueAngleB` | 1:15 | X3Y3 drawn parallel to the line's image, and both things happen at once: the plate closes up again, and the line comes out at 114.7 mm — its true length, longer than in any earlier view. The angle is then measured: 23.3°. |
| `S06_Recap` | 1:35 | Three jobs, three tools, drawn as one chain: the cutting plane branch needs no auxiliary at all; the angle branch needs three. |

Total ≈ 12–13 minutes.

### Episode 08 — the four scenes

| Scene | ≈ | What it does |
|---|---|---|
| `S01_Dihedral` | 2:20 | The two faces in space, hinged on the edge they share. The far face is folded shut onto the near one and opened again — that swing *is* the angle, and `solve()` asserts that folding by θ closes the book exactly. Then the camera goes and stands at the end of the hinge: B and C line up into one point, both faces flatten into lines, and the angle is there to read. Step off that line and it distorts again. |
| `S02_Strategy` | 1:30 | Why the order is fixed: a line reaches a point view only from a view that already shows it true length. A generic line is put through both auxiliaries at the side of the screen — a real construction at small scale, asserted true length and asserted point view, not a sketch. |
| `S03_Construction` | 3:10 | Q.12 on one sheet, the camera following the chain down it: X1Y1 ∥ bc with the heights carried across and flown into place, bc measured at 50.7 mm true length against 49.7 and 39.3 in the given views, then X2Y2 ⊥ b₁c₁ with the distances carried from two views back, b₂c₂ closing to a point, and the angle read at 77.3°. |
| `S04_Recap` | 1:15 | The method in four lines and one chain, with the three numbers to check yourself against. |

Total ≈ 8 minutes.

### Episode 09 — the five scenes

| Scene | ≈ | What it does |
|---|---|---|
| `S01_TheyDoNotMeet` | 3:00 | The two lines in space. The camera goes and stands where the front view is taken from — they cross. Step aside and that one crossing point comes apart into two, 41 mm apart in depth. The same again from above: a second crossing, elsewhere, 48 mm apart in height. That is what skew means, watched rather than asserted. Then the common perpendicular against three other links, and the camera moves to the end of AB, where AB is a point and the link lies flat across the view at its full 30.7 mm. |
| `S02_Strategy` | 1:54 | Why the point view answers it: from there the distance on the paper to any point of CD is the true perpendicular distance from the line AB to that point, so you see all of them at once and the least is the perpendicular. The small drawing beside the words is the real second auxiliary at small scale, not a sketch of one. |
| `S03_Construction` | 2:50 | The sheet. Both views, with the two crossings marked to show they miss. X1Y1 ∥ ab, the heights carried and flown into place, ab at 106.4 mm true length against 93.9 and 98.6 in the given views. Then X2Y2 ⊥ a₁b₁, the distances carried from two views back, AB closing to a point, and the perpendicular onto c₂d₂: 30.7 mm. |
| `S04_BackToTheViews` | 2:09 | Where the link actually is. n₂ back along its own projector onto c₁d₁; then the one piece of reasoning — AB is true length in aux 1, so the right angle projects true there, so m₁ is found square to a₁b₁. Back to the top view, up to the front, and the same link then measured in all four: 20.1, 23.7, 21.1 and 30.7. Three of those four are wrong. |
| `S05_Recap` | 1:15 | The method in four lines and one chain, the number to check yourself against, and §4.11 — the true angle between skew lines — as the companion problem. |

Total 11:08.

### Episode 10 — the five scenes

Sheet 8 this time, not Sheet 4: development of surfaces, and the first of the
Exercise 7 (Set A) Q.2 solids. The figure has a detail worth keeping — 42 ×
tan 45° is 42 and only 30 of height remains above the cut, so the plane leaves
through the **top face** 30 along. That is why the section is only part of an
ellipse, why the top view needs a chord, and why the development's top edge
has two corners with a flat stretch between them.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_Unroll` | 1:26 | What a development *is*. The cylinder's lateral surface unrolls in front of you into a plain rectangle, πD by 50 — and it unrolls properly: the surface is bent to a curvature running from 1/R down to 0, so arc length is preserved in every frame rather than lerped flat. It bends about the generator opposite the seam, which centres the pattern and puts the join on the shortest generator, where the convention wants it. |
| `S02_TheCut` | 2:05 | The 45° plane goes through, the top lifts away, and two facts appear: the section is an ellipse seen edge-on in the front view, and every generator now ends at a different height. Unroll it again and the top edge is a curve — with a flat stretch in the middle where the plane had already left the cylinder. |
| `S03_TrueShape` | 2:32 | The sheet. Twelve divisions numbered from the seam, the chord marked where the plane runs out through the top face, each generator carried up to the cut, and then X1Y1 parallel to the cut with the widths brought from the top view: the true shape. 42 across the slope, 42.43 up it. |
| `S04_Development` | 2:01 | The pattern. A base line πD = 131.95 long, twelve divisions of 10.996, each generator's own height stepped off and flown across from the front view, and a smooth curve through the tops — dead straight between the two breaks. |
| `S05_Recap` | 1:09 | The method in four lines, and the two traps: πD is the diameter of the **base**, and everything stepped off must be a true length. |

Total 9:12.

### Episode 11 — the five scenes

The other solid in Q.2 that is worth a film of its own. Note that Q.2 has no
pyramid in it — (b) and (c) are triangular prisms and (d) is a **pentagonal
prism** — so the cone is the one solid in the exercise needing the true-length
construction, and the pyramid is covered in the recap, where the method is
identical.

The cone is cut by **two planes at once**, meeting on the axis 25 above the
base: horizontal across the left half, 30° rising to the right. So the section
is in two pieces — a half-circle, already true in the top view because a
horizontal face always is, and a half-ellipse that needs an auxiliary.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_TheCone` | 1:42 | The cone, its twelve generators, the slant height 54.23, and the two planes. The waste lifts off and leaves the two section faces meeting on one diameter. |
| `S02_TrueLength` | 2:08 | The whole difficulty in one scene. Generators 7 and 4 are the same length in space; from the front view 7 measures 27.12 and 4 measures 25.00. The fix — swing the point about the axis until it lands on the outline, where its height and its distance from the apex are both unchanged — is watched in space before it is ever drawn. |
| `S03_Sheet` | 1:44 | The orthographic drawing, the twelve cut points, and the twelve true lengths lifted off by rotation. There are only four different answers: the seven level-cut generators all give 27.12, and symmetry pairs the rest. |
| `S04_Development` | 2:03 | The sector: radius 54.23, angle 360 R/L = 139.40°, twelve divisions of 11.6170°, and each true length stepped off from the apex. The inner curve runs as an arc at both ends — equal distances from the apex is an arc, not a straight line. |
| `S05_Recap` | 1:34 | The method, the two traps, and the pyramid: the same problem, since a cone is only a pyramid with a great many very thin faces. |

Total 9:11.

### Episode 12 — the four scenes

The three prisms, which finishes Q.2. All three are solved by one function
and drawn by one sheet builder, so the episode works (b) in full and then
shows (c) and (d) as variations rather than as three separate drawings.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_FoldItOut` | 1:47 | A prism is *folded* out, not rolled: each face hinges flat about the edge it shares with the last one, by α times the exterior angle, so the side lengths hold at every frame and the trace closes exactly at α = 1. Three rectangles, 120 across — the perimeter — where the cylinder had πD. |
| `S02_SheetB` | 1:45 | Q.2(b) in full. The middle line of the front view is not a fold in the drawing but the third edge of the prism pointing at you. Three edge heights read straight off the front view — no rotation, because a vertical edge is never foreshortened there — and the tops joined with **straight** lines, since a flat face cut by a flat plane meets it in a straight line. |
| `S03_TwoPlanes` | 2:09 | Q.2(c) and (d), and the point of the episode. Where two cutting planes meet, their line of intersection crosses a **face**, not an edge — the back face in (c), the front face in (d) — so the development needs a point there. Miss it and you draw one straight line where there should be two. A corner in the pattern where the solid has no edge at all. |
| `S04_Recap` | 1:17 | Prisms against cylinders, and the number people get wrong: the width is the perimeter of the **base**, measured in the top view where the sides are true length. |

Total 6:58.

### Episode 13 — the four scenes

Q.1, which completes Exercise 7 (Set A). Q.1(a) the cylinder and Q.1(d) the
square pyramid are worked in full, and between them they are the whole
method; the other three solids of Figure P7.1 — hexagonal prism, cone,
frustum — are the same two rules again.

The views are read in **first angle**, as the rest of the series is: top view
below, left-hand side view on the right. In that side view the observer
stands at −x looking along +x with z up, so screen-right is −y — what is
further *in front* is drawn further to the *right*. The 45° mitre
construction and the side view then agree for all six points, which is the
check that the handedness is right, and `solve()` asserts it.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_OnTheSurface` | 2:48 | What "on the surface" buys you: the point is stuck to the solid, so one view fixes it. Two helper lines cover every solid on the sheet — a **generator** where the sides run straight up, a **level section** where the solid tapers. Seen in space on the cylinder and then the pyramid. |
| `S02_Cylinder` | 2:42 | Q.1(a). Three points, each given in one view and carried into the other two, with the depth going round through the 45° line. The brackets do real work here: a point on the curved surface is *not* fixed by its top view at all, since every generator shows as the same point on that circle whatever its height — what puts point a at 50 is that it is unbracketed, and the rim you see from above is the top one. |
| `S03_Pyramid` | 2:24 | Q.1(d). On a pyramid the top view fixes a surface point completely, because the level section and the height are locked together. Then the front-view outline, which is not one edge but two slant edges projecting onto the same line — so two candidates, and the brackets choose. |
| `S04_Recap` | 1:18 | One rule per solid, and what each view hides: the front view what is behind, the top view what is underneath, the left side view what is to the right. |

Total 9:12.

### Episode 14 — the five scenes

Exercise 8 (Set A) Q.3, the first of the oblique-solid questions: Q.3(b) an
oblique square pyramid and Q.3(a) an oblique cone, each cut by a plane at 30°
and each developed. Sheet 8 §9 did the right solids, where a cone's
development is a sector and a pyramid's is a fan of identical triangles.
None of that survives the apex moving sideways, and this episode is about
what replaces it.

The whole method is one idea: **a triangle with three true sides has exactly
one shape.** Every face is a triangle, its base edge is true in the top view,
and its two slant edges come off a single right-angled diagram — plan length
along the bottom, height up the side, hypotenuse the true length. The cut is
then marked not at the height the front view shows but at its own true
distance from the apex, read off the same diagram by sliding each point
sideways onto its own hypotenuse.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_WhatIsOblique` | 1:36 | A right pyramid in space, all four slant edges 55.79 — then the apex pushed ten past the right-hand corner, same base and same height, and the four edges come out 77.72, 65.73, 50.99, 65.73. Three lengths where there was one. No slant height, so no sector and no πD⁄L: what is left is triangulation, which never needed either. |
| `S02_Triangulation` | 1:46 | The method, and the one construction under it. Neither view shows a slant edge true — the top view gives its plan length, the front view the height it climbs, never both, because the edge leans in two directions. Those two are the sides of a right-angled triangle whose hypotenuse is what we want, so one diagram drawn once reads off all four. |
| `S03_SheetB` | 2:34 | Q.3(b) in full. In the front view the cutting plane is one line, and where it crosses each slant edge is a corner of the section: 6, 27, 34.43, 27 — and 2′ and 4′ fall together, because those two edges coincide in that view. Carried down to the plan, then turned square-on for the true shape, 56.86 × 22.77: widths were never foreshortened, lengths are the plan divided by cos 30°. |
| `S04_DevelopmentB` | 2:22 | The pattern, face by face: two radii from the apex and a 35 chord fix each corner, which is a pair of compasses doing what the cosine rule does. Seam on edge 3, the shortest. Then the point of the episode — a cut point is **not** at the height you see in the front view, it is at its own true distance from the apex: 68.39, 30.23, 15.88, and the true-length diagram gives those too. |
| `S05_ConeAndRecap` | 3:08 | Q.3(a), the oblique cone. A cone has no edges, so twelve generators stand in for the surface; on a right cone all twelve are equal, here they run 72.81 down to 52.74. Same diagram, same method, twelve triangles instead of four — and the laid-out base is a curve, not a circular arc. Plus the recap. |

Total 11:26.

### Episode 15 — the four scenes

Exercise 8 (Set A) Q.1. Episode 13 gave two helper lines for finding a point on
a solid's surface — a **generator** where the sides run straight up, a **level
section** where the solid tapers. Both survive the axis leaning over; neither
stays where it was, and that is the whole episode.

| what | on a right solid | on an oblique one |
|---|---|---|
| the generator | vertical, so its plan is one point *on the base circle* | parallel to the **axis**, so its plan is a **line** 30 long |
| a surface point's depth | read off the base circle at the point's own x | read off the base circle where its **generator starts** |
| the level section | the base figure shrunk, concentric with the base | the base figure shrunk, **slid along the axis** |

Figure P8.1(a) is the book's solid — an oblique cylinder, Ø40, axis 60 long at
60°. Its lettered points were not available, so a, b and c exercise one rule
each. Parts (b) to (d) are stood in for by the oblique cone and the oblique
pyramid of Q.3, whose dimensions are the figure's and which episode 14 already
develops.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_WhatMoves` | 2:15 | In space, both helper lines before and after the lean. A point 0.7 of the way up one generator has its plan **on** the base circle while the cylinder is right; lean the axis and the same point's plan is 5.79 from the centre of a circle of radius 20 — most of the way in towards the middle. Then the level section: still a circle, still the same size for its height, but its centre has gone along the axis. |
| `S02_ObliqueCylinder` | 4:00 | Q.1(a) in full. **a′** given in the front view: its generator runs back to the base at 11.52, and the depth comes off the circle *there* — at a′'s own x of 30 the base circle is not there at all, it stopped at 20. **b** given in the top view: exactly two generators cross that plan point, so two heights, 46.77 and 5.20, and unbracketed takes the upper. **(c)** sits *on* the base circle in plan and still is not a base point until the bracket says so. |
| `S03_ConeAndPyramid` | 2:02 | The tapering pair. The oblique cone's level circle at 24 up is R 11.30 centred 13.86 *along the axis* — the size a right cone would give, in the place the lean put it. Then the check that costs one line: apex to d′, down to the base, depth off the base circle, back up to the apex in plan — the generator runs straight through d. The pyramid is the same with corners, where the depth is a subtraction rather than a square root. |
| `S04_Recap` | 1:07 | Two columns — what episode 13 still gives you, and the three things the lean moves — and the five points with the reason each came out as it did. |

Total 9:25.

### Episode 16 — the four scenes

The one empty cell in Sheet 8's matrix. Episodes 10 and 12 rolled right prisms
and cylinders along their bases; 11 opened a right cone into a sector; 14
triangulated oblique cones and pyramids. An oblique **prismatic** solid fits
none of them.

| solid | its generators | stretch-out line | ep. |
|---|---|---|---|
| right prism · cylinder | parallel **and** square to the base | the base — perimeter or πD | 10·12 |
| right cone · pyramid | all meet the apex, all equal | a sector, 360 R/L | 11 |
| oblique cone · pyramid | meet the apex, all different | none — triangulate face by face | 14 |
| oblique prism · cylinder | parallel, **not** square to the base | the **right section** | 16 |

A right prism rolls along its base only because the base is square to the
generators. Lean the axis and that angle is gone — 69.3°, not 90° — so the base
wanders off the line and its perimeter is the wrong width for the pattern. The
cure is to make a base that *is* square to the generators: slice the solid
perpendicular to the axis. That section, and only that section, rolls out
straight; everything else is then measured from it, above and below, signs and
all.

The arithmetic falls out clean, because a right-section point is just the base
point with its x foreshortened by sin(lean) and its depth untouched.

| Scene | ≈ | What it does |
|---|---|---|
| `S01_RollItFlat` | 1:34 | In space: a base edge meets a vertical generator at 90°, which is the only reason episode 10 worked. Lean the axis and it is 69.3°. Then the right section appears, with a right-angle mark on every generator — and the aside that explains episode 10 in one line: on a right solid the base *already is* a right section, so the question never came up. |
| `S02_ObliquePrism` | 2:35 | An oblique square prism, 30 side on its diagonals, cut at 30°. The right section's true shape is **not** a square — a rhombus 36.74 × 42.43, four sides of 28.06, giving a stretch-out of **112.25** where the base perimeter is 120. Then the pattern: the base 19.4 to 40.6 *below* the line, the top the same amounts above, the cut +33.82 at corner 3 and −29.82 at corner 1. |
| `S03_ObliqueCylinder` | 1:43 | The book's cylinder from P8.1(a), twelve generators. The right section is an ellipse, 40 deep by 34.64 across — the diameter untouched, and the diameter times sin 60°. The twelve chords are not equal (9.07 to 10.27) and total **116.06**, against a πD of 125.66 — the number the whole method exists to stop you using. |
| `S04_Recap` | 1:19 | The table above, and the check that saves you: on any prism or cylinder, right or oblique, base to top is the same distance on **every** generator. Here, 60. |

Total 7:11.

### Stitching the clips

Each scene renders to its own file under
`media\videos\<episode>\1080p60\`. Concatenate them in running order —
`-c copy`, because they share one encoder setting and there is nothing to
re-encode. Run each block from inside that folder.

**Episode 06**

```bat
(echo file 'S01_WhyBothViewsLie.mp4' & echo file 'S02_EdgeViewIdea.mp4' & echo file 'S03_Strategy.mp4' & echo file 'S04_Construction.mp4' & echo file 'S05_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed06_true_shape.mp4
```

**Episode 07**

```bat
(echo file 'S01_ThePiercingPoint.mp4' & echo file 'S02_CuttingPlane.mp4' & echo file 'S03_Piercing.mp4' & echo file 'S04_TrueAngleA.mp4' & echo file 'S05_TrueAngleB.mp4' & echo file 'S06_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed07_piercing_point.mp4
```

**Episode 08**

```bat
(echo file 'S01_Dihedral.mp4' & echo file 'S02_Strategy.mp4' & echo file 'S03_Construction.mp4' & echo file 'S04_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed08_dihedral_angle.mp4
```

**Episode 09**

```bat
(echo file 'S01_TheyDoNotMeet.mp4' & echo file 'S02_Strategy.mp4' & echo file 'S03_Construction.mp4' & echo file 'S04_BackToTheViews.mp4' & echo file 'S05_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed09_skew_lines.mp4
```

**Episode 10**

```bat
(echo file 'S01_Unroll.mp4' & echo file 'S02_TheCut.mp4' & echo file 'S03_TrueShape.mp4' & echo file 'S04_Development.mp4' & echo file 'S05_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed10_development.mp4
```

**Episode 11**

```bat
(echo file 'S01_TheCone.mp4' & echo file 'S02_TrueLength.mp4' & echo file 'S03_Sheet.mp4' & echo file 'S04_Development.mp4' & echo file 'S05_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed11_cone.mp4
```

**Episode 12**

```bat
(echo file 'S01_FoldItOut.mp4' & echo file 'S02_SheetB.mp4' & echo file 'S03_TwoPlanes.mp4' & echo file 'S04_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed12_prisms.mp4
```

**Episode 13**

```bat
(echo file 'S01_OnTheSurface.mp4' & echo file 'S02_Cylinder.mp4' & echo file 'S03_Pyramid.mp4' & echo file 'S04_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed13_points.mp4
```

**Episode 14**

```bat
(echo file 'S01_WhatIsOblique.mp4' & echo file 'S02_Triangulation.mp4' & echo file 'S03_SheetB.mp4' & echo file 'S04_DevelopmentB.mp4' & echo file 'S05_ConeAndRecap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed14_oblique.mp4
```

**Episode 15**

```bat
(echo file 'S01_WhatMoves.mp4' & echo file 'S02_ObliqueCylinder.mp4' & echo file 'S03_ConeAndPyramid.mp4' & echo file 'S04_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed15_surface_points.mp4
```

**Episode 16**

```bat
(echo file 'S01_RollItFlat.mp4' & echo file 'S02_ObliquePrism.mp4' & echo file 'S03_ObliqueCylinder.mp4' & echo file 'S04_Recap.mp4') > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy ed16_right_section.mp4
```

Suggested chapters for the descriptions. The narration is timed from a word
count, so these are close but not exact — read the real boundaries off the
rendered clips with

```bat
for %%F in (S0*.mp4) do @ffprobe -v error -show_entries format=duration -of csv=p=0 %%F
```

Episode 06:

```
00:00  Why neither view is the true shape
02:10  Look along the plane: the edge view
04:40  The four steps, and the rule students get wrong
06:25  Q.6 worked: edge view, θ with the HP, true shape
10:15  Recap, and the same trick for the VP
```

Episode 07:

```
00:00  The piercing point, and why half the line goes hidden
02:15  The cutting plane, seen face on and from above
04:45  Q.11 worked: the crossings, p′ and p, and visibility
08:05  Why the true angle needs an edge view first
09:40  Auxiliary 3: the line at 114.7 mm, the angle at 23.3°
10:55  Recap: three jobs, three tools
```

Episode 08, off the rendered clips (137.3 s, 86.9 s, 189.3 s, 77.1 s):

```
00:00  What the angle between two planes is: the book and its hinge
02:17  Two auxiliaries, and why the order is fixed
03:44  Q.12 worked: BC true length, BC as a point, θ = 77.3°
06:53  Recap, and the three numbers to check yourself against
```

Episode 09, off the rendered clips (179.7 s, 114.1 s, 169.9 s, 129.3 s, 75.2 s):

```
00:00  Two lines that cross twice and never meet
03:00  Why the point view answers it
04:54  The sheet: AB true length, AB as a point, 30.7 mm
07:44  Where the link really is, and what it measures elsewhere
09:53  Recap, and the true angle between skew lines
```

Episode 10, off the rendered clips (85.7 s, 125.4 s, 151.5 s, 120.8 s, 68.8 s):

```
00:00  What a development is: the surface, unrolled
01:26  The cut, and what it does to the pattern
03:31  The sheet: twelve generators, and the true shape
06:03  The development: πD, twelve heights, one curve
08:04  Recap, and the two traps
```

Episode 11, off the rendered clips (102.0 s, 128.0 s, 104.1 s, 123.0 s, 94.3 s):

```
00:00  The cone, and the two planes that cut it
01:42  Why a generator lies, and how to make it talk
03:50  The sheet: twelve cut points, four true lengths
05:34  The development: a sector of 139.40°
07:37  Recap, the traps, and the pyramid
```

Episode 12, off the rendered clips (106.9 s, 104.9 s, 129.0 s, 77.1 s):

```
00:00  Folding a prism out: the perimeter, not πD
01:46  Q.2(b): three edge heights, three straight lines
03:31  Q.2(c) and (d): a corner where there is no edge
05:40  Recap, and the number people get wrong
```

Episode 13, off the rendered clips (167.6 s, 161.9 s, 144.0 s, 78.3 s):

```
00:00  What "on the surface" gives you: two helper lines
02:48  Q.1(a): the cylinder, and what the brackets decide
05:30  Q.1(d): the pyramid, where one view is enough
07:54  Recap: one rule per solid, and what each view hides
```

Episode 14, off the rendered clips (96.0 s, 105.6 s, 154.1 s, 141.7 s, 188.1 s):

```
00:00  What "oblique" costs you: three lengths where there was one
01:36  Triangulation, and the true-length diagram
03:21  Q.3(b): the cut, the four points, and the true shape
05:55  Q.3(b): the development, and where the cut really falls
08:17  Q.3(a): the oblique cone, and the recap
```

Episode 15, off the rendered clips (135.2 s, 240.6 s, 122.3 s, 67.3 s):

```
00:00  Both helper lines, before and after the lean
02:15  Q.1(a): the generator, and the depth that is not where you look
06:16  The cone and the pyramid: the section slides along the axis
08:18  Recap: what moved, what did not, and all five points
```

Episode 16, off the rendered clips (94.3 s, 155.0 s, 103.3 s, 78.5 s):

```
00:00  Why rolling an oblique prism on its base fails
01:34  The prism: right section, true shape, stretch-out
04:09  The cylinder: an elliptical right section, and πD is wrong
05:52  Four solids, four patterns — and the check
```

---

### Conventions the episodes keep

* **Colour is meaning, and it never changes mid-episode.** Coral is the vertical
  plane and the front view, teal the horizontal plane and the top view, cream the
  construction lines that only exist to get you there. What gold marks is
  whatever the episode is chasing: in 06 the plate and its answers, in 07 the
  line DE, in 08 the hinge BC, in 09 the line AB that goes to a point
  view — with the answer itself, the common perpendicular, in coral. Within an episode every object keeps one colour
  through every view — in 06 the corners (A coral, B teal, C violet), in 07 the
  plate violet against the gold line, in 08 the two faces (ABC violet, DBC
  coral), in 09 the two lines (AB gold, CD violet) — so one thing can be
  followed by eye from the given views all the way into the last auxiliary.
* **One figure throughout.** The solid that tilts in space in the opening scenes
  is built from the same given dimensions as the sheet solved later, only at a
  different scale. The 3-D picture and the drawing are the same problem, not an
  illustration of it.
* **Nothing is placed by eye.** Every point comes out of the episode's `solve()`
  or `construction()`, which asserts what the narration is about to claim —
  that the edge view really is collinear, that the auxiliary really is true
  length, that the point view really is one point. A wrong number stops the
  render instead of reaching YouTube.
* **No LaTeX.** Every glyph is Unicode `Text()`, so the files render on a machine
  with no TeX installed.
