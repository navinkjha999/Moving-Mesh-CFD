# Engineering Drawing I — Sheet 4, *Basic Descriptive Geometry II*

Manim CE 0.20.1 source for four YouTube lessons:

* **Episode 06 — Edge View, True Shape and True Size of an Oblique Plane**
  (Exercise 4, Set A, Q.6), about eleven minutes.
* **Episode 07 — Where a Line Pierces a Plane**: the piercing point, the
  hidden stretch, and the true angle (Exercise 4, Set A, Q.11), about
  thirteen minutes.
* **Episode 08 — The True Angle Between Two Planes**: the dihedral angle
  (Exercise 4, Set A, Q.12), about eight minutes.
* **Episode 09 — The Shortest Distance Between Two Skew Lines** (§4.10), and
  the common perpendicular put back on the given views, about eleven minutes.

```
ed06_true_shape.py      episode 06: five scenes, all the narration, all the geometry
ed07_piercing_point.py  episode 07: six scenes
ed08_dihedral_angle.py  episode 08: four scenes
ed09_skew_lines.py      episode 09: five scenes
ed_stage.py             the shared 3-D stage (HP, VP, XY, the four quadrants)
ed_common.py            thin shim over cfd_common: narration, HUD and camera helpers
cfd_common.py           the series infrastructure (voice, cache, loudnorm, fonts)
render_ed06.bat         renders episode 06 in running order at 1080p60
render_ed07.bat         renders episode 07 in running order at 1080p60
render_ed08.bat         renders episode 08 in running order at 1080p60
render_ed09.bat         renders episode 09 in running order at 1080p60
```

---

### Render

```bat
render_ed06.bat                              REM all five scenes, 1080p60
render_ed07.bat                              REM all six scenes
render_ed08.bat                              REM all four scenes
render_ed09.bat                              REM all five scenes
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

Total ≈ 11 minutes.

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
| `S01_TheyDoNotMeet` | 2:40 | The two lines in space. The camera goes and stands where the front view is taken from — they cross. Step aside and that one crossing point comes apart into two, 41 mm apart in depth. The same again from above: a second crossing, elsewhere, 48 mm apart in height. That is what skew means, watched rather than asserted. Then the common perpendicular against three other links, and the camera moves to the end of AB, where AB is a point and the link lies flat across the view at its full 30.7 mm. |
| `S02_Strategy` | 1:50 | Why the point view answers it: from there the distance on the paper to any point of CD is the true perpendicular distance from the line AB to that point, so you see all of them at once and the least is the perpendicular. The small drawing beside the words is the real second auxiliary at small scale, not a sketch of one. |
| `S03_Construction` | 3:20 | The sheet. Both views, with the two crossings marked to show they miss. X1Y1 ∥ ab, the heights carried and flown into place, ab at 106.4 mm true length against 93.9 and 98.6 in the given views. Then X2Y2 ⊥ a₁b₁, the distances carried from two views back, AB closing to a point, and the perpendicular onto c₂d₂: 30.7 mm. |
| `S04_BackToTheViews` | 2:20 | Where the link actually is. n₂ back along its own projector onto c₁d₁; then the one piece of reasoning — AB is true length in aux 1, so the right angle projects true there, so m₁ is found square to a₁b₁. Back to the top view, up to the front, and the same link then measured in all four: 20.1, 23.7, 21.1 and 30.7. Three of those four are wrong. |
| `S05_Recap` | 1:20 | The method in four lines and one chain, the number to check yourself against, and §4.11 — the true angle between skew lines — as the companion problem. |

Total ≈ 11 minutes.

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

Episode 09:

```
00:00  Two lines that cross twice and never meet
02:40  Why the point view answers it
04:30  The sheet: AB true length, AB as a point, 30.7 mm
07:50  Where the link really is, and what it measures elsewhere
10:10  Recap, and the true angle between skew lines
```

---

### Conventions the four episodes keep

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
