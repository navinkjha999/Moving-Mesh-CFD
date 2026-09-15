"""
ed_common.py - Engineering Drawing series helpers.

This is a THIN SHIM over cfd_common.py. All narration, caching, voice profile,
loudnorm and the silence-fallback come straight from cfd_common - nothing is
duplicated or re-implemented here, so the audio behaves exactly as it does in
the CFD series. This module only adds what the drawing episodes need on top:

    hud()          pin a mobject to the camera frame in a ThreeDScene
    billboard()    labels that stay upright and readable as the camera moves
    half_turn()    a 180 degree camera orbit timed to the narration
    fly_camera()   a scripted 3-D camera move timed to the narration
    pin_to_frame() hold a mobject still on SCREEN in a MovingCameraScene
    frame_target() where the camera must sit for a group to be readable
    look_at()      the camera animation that gets it there
    card_back()    a dark backing card behind screen furniture
    rail_focus()   light one rung of a step rail and dim the rest
    title_bar()    the standing top-left caption
    chip()         a boxed callout tag
    caption()      heading-font text

Import ed_common in the episode file; it re-exports the cfd_common names so a
scene never has to import both.
"""

from __future__ import annotations

from manim import (
    BOLD,
    DOWN,
    LEFT,
    ORIGIN,
    PI,
    RIGHT,
    UP,
    Line,
    Rectangle,
    RoundedRectangle,
    Text,
    UpdateFromAlphaFunc,
    VGroup,
    config,
    interpolate,
)
import numpy as _np

# --------------------------------------------------------------------------
# Locate cfd_common.py
#
# Easiest setup: drop a copy of cfd_common.py in this folder. If you would
# rather keep one master copy with the CFD series, either set the environment
# variable ED_CFD_COMMON to the folder holding it, or add that folder to
# EXTRA_SEARCH_PATHS below - this module will put it on sys.path for you.
# --------------------------------------------------------------------------
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

EXTRA_SEARCH_PATHS = [
    # add your own absolute paths here, e.g.
    # r"C:\Users\Navin Jha\Desktop\youtubetoupload\CFD",
]


def _locate_cfd_common() -> None:
    """Put the folder containing cfd_common.py on sys.path, or explain why not."""
    candidates = []

    env = os.environ.get("ED_CFD_COMMON")
    if env:
        candidates.append(Path(env))

    candidates += [Path(p) for p in EXTRA_SEARCH_PATHS]
    candidates.append(_HERE)

    # walk up from this folder and look in every sibling directory - this finds
    # the CFD series folder when both live under one "youtubetoupload" root
    for level in (_HERE, *_HERE.parents[:3]):
        candidates.append(level)
        try:
            candidates.extend(child for child in level.iterdir() if child.is_dir())
        except OSError:
            pass

    seen = set()
    for folder in candidates:
        # a path may be given as the file itself rather than its folder
        if folder.is_file() and folder.name == "cfd_common.py":
            folder = folder.parent
        key = str(folder)
        if key in seen:
            continue
        seen.add(key)
        if (folder / "cfd_common.py").is_file():
            if key not in sys.path:
                sys.path.insert(0, key)
            return

    raise ModuleNotFoundError(
        "ed_common.py needs cfd_common.py and could not find it.\n"
        f"  Looked in {_HERE} and its sibling folders.\n"
        "  Fix it either way:\n"
        "    1. copy cfd_common.py into this folder, or\n"
        "    2. set ED_CFD_COMMON to the folder that holds it, e.g.\n"
        '       set ED_CFD_COMMON=C:\\Users\\Navin Jha\\Desktop\\youtubetoupload\\CFD'
    )


_locate_cfd_common()

# --- everything real comes from the working CFD infrastructure -------------
# Imported DEFENSIVELY: older copies of cfd_common.py do not define every
# name (CREAM, VIOLET, prewarm, ...), so anything optional falls back to a
# local default rather than blowing up the import. Only narrate() and
# finish_audio() are genuinely required.
import cfd_common  # noqa: E402

CFD_COMMON_PATH = getattr(cfd_common, "__file__", "<unknown>")

# If the copy in use is not the one next to this file, say so once - with two
# copies on disk it is otherwise invisible which one a render actually used.
if Path(CFD_COMMON_PATH).resolve().parent != _HERE:
    print(f"[ed_common] using cfd_common.py from {CFD_COMMON_PATH}")

for _required in ("narrate", "finish_audio"):
    if not hasattr(cfd_common, _required):
        raise ImportError(
            f"{CFD_COMMON_PATH} has no {_required}() - this looks like the wrong "
            "or a very old copy of cfd_common.py.\n"
            "  Copy your current cfd_common.py into this folder, or set "
            "ED_CFD_COMMON to the folder holding it."
        )

narrate = cfd_common.narrate
finish_audio = cfd_common.finish_audio

# Palette - defaults match the series brand if the loaded copy is missing one
NAVY = getattr(cfd_common, "NAVY", "#0B1221")
TEAL = getattr(cfd_common, "TEAL", "#2DD4BF")
GOLD = getattr(cfd_common, "GOLD", "#F5B642")
CORAL = getattr(cfd_common, "CORAL", "#FF6F61")
CREAM = getattr(cfd_common, "CREAM", "#FDF6E3")
SLATE = getattr(cfd_common, "SLATE", "#94A3B8")
VIOLET = getattr(cfd_common, "VIOLET", "#8B5CF6")

H_FONT = getattr(cfd_common, "H_FONT", "Space Grotesk")
M_FONT = getattr(cfd_common, "M_FONT", "JetBrains Mono")

VOICE = getattr(cfd_common, "VOICE", "en-US-GuyNeural")
RATE = getattr(cfd_common, "RATE", "-3%")
PITCH = getattr(cfd_common, "PITCH", "-8Hz")


def _fallback_synthesise(namespace: str, text: str):
    """Word-count duration estimate, used only if cfd_common has no synthesise()."""
    words = max(1, len(text.split()))
    return None, max(1.0, words / 152.0 * 60.0)


synthesise = getattr(cfd_common, "synthesise", _fallback_synthesise)
prewarm = getattr(cfd_common, "prewarm", None)


def _fallback_mono(text: str, size: int = 18, color: str = "#E7EDF3", **kw):
    return Text(text, font=M_FONT, font_size=size, color=color, **kw)


mono = getattr(cfd_common, "mono", _fallback_mono)
head = getattr(cfd_common, "head", None)
body = getattr(cfd_common, "body", None)
fade_all = getattr(cfd_common, "fade_all", None)


# Aliases so the episode file reads in drawing-room language
INK = "#E7EDF3"
MUTED = SLATE
TITLE_FONT = H_FONT
MONO_FONT = M_FONT


# --------------------------------------------------------------------------
# 3-D scene helpers
# --------------------------------------------------------------------------
def hud(scene, mob):
    """
    Pin `mob` to the camera frame, then take it back off the scene so it can
    still be introduced with a FadeIn instead of popping in. The camera keeps
    the fixed-in-frame flag in its own set, so removing it from the scene does
    not undo the pinning.
    """
    scene.add_fixed_in_frame_mobjects(mob)
    scene.remove(mob)
    return mob


def billboard(scene, *mobs):
    """
    Labels that stay upright and readable as the camera moves.

    IMPORTANT: Manim's 3-D camera only TRANSLATES fixed-orientation mobjects -
    it never re-orients their points. So never put one of these inside a
    Rotate(); rotate the geometry and move the label with .animate.move_to().
    """
    scene.add_fixed_orientation_mobjects(*mobs)
    for mob in mobs:
        scene.remove(mob)
    return mobs[0] if len(mobs) == 1 else VGroup(*mobs)


def half_turn(scene, text, *anims, turn=PI, **kwargs):
    """
    Narrate `text` while the camera swings a half turn around the arrangement,
    so the viewer is carried round to look at the projection face on.

    The duration is taken from the cached narration itself (synthesise() is
    memoised, so the narrate() call re-uses the same wav) - the orbit therefore
    lands exactly when the sentence ends, with no hand-tuned run_time.
    """
    _, dur = synthesise(type(scene).__name__, text)
    scene.begin_ambient_camera_rotation(rate=turn / max(dur, 0.5))
    narrate(scene, text, *anims, **kwargs)
    scene.stop_ambient_camera_rotation()
    return dur


def fly_camera(scene, text, *anims, hold: float = 0.0, **camera):
    """
    Narrate `text` while the 3-D camera TRAVELS to a named orientation.

    half_turn() spins; this one goes somewhere on purpose - phi, theta, zoom,
    focal_distance, frame_center are passed straight to ThreeDScene.move_camera,
    and `anims` ride along with the move. The run time is the length of the
    narration itself, so the camera arrives exactly as the sentence ends.

    Use a large focal_distance (say 60) for the shot where a plane has to close
    up into a line: Manim's 3-D camera is slightly perspective, and a long lens
    is what makes the collapse look exact rather than nearly exact.
    """
    ns = type(scene).__name__
    wav, dur = synthesise(ns, text)
    if wav is not None:
        scene.add_sound(str(wav))
    scene._audio_end = max(getattr(scene, "_audio_end", 0.0),
                           scene.renderer.time + dur)
    scene.move_camera(added_anims=list(anims),
                      run_time=max(dur - hold, 0.1), **camera)
    if hold > 0:
        scene.wait(hold)
    return dur


def pin_to_frame(scene, mob, corner=UP + LEFT, buff=0.42):
    """
    Hold `mob` still on the SCREEN while a MovingCameraScene pans and zooms.

    hud() only works in a ThreeDScene - "fixed in frame" is a feature of the
    3-D camera. A 2-D scene that moves its camera needs this instead: an
    updater re-hangs the mobject on the camera frame every frame and rescales
    it by the current zoom, so the caption, the step rail and the answer card
    never grow or drift while the drawing is being followed about the sheet.

    The updater runs AFTER each frame's animations, so it is safe to fade or
    recolour the pinned mobject while the camera is moving.
    """
    base_height = mob.height

    def _hang(m):
        frame = scene.camera.frame
        zoom = frame.height / config.frame_height
        if m.height > 1e-6:
            m.scale(base_height * zoom / m.height)
        pad = buff * zoom
        c = _np.array([float(corner[0]), float(corner[1]), 0.0])
        m.move_to(frame.get_corner(c)
                  - _np.array([c[0] * (pad + m.width / 2.0),
                               c[1] * (pad + m.height / 2.0), 0.0]))

    _hang(mob)
    mob.add_updater(_hang)
    return mob


def frame_target(mobs, pad=0.45, right=0.30, top=0.20):
    """
    Where the camera has to sit for `mobs` to be comfortably readable.

    The right-hand strip of the screen belongs to the step rail and the top
    strip to the caption, so the drawing is fitted into what is LEFT rather
    than into the whole frame - that is why a zoomed construction never ends up
    hiding behind the furniture. Returns (centre, width) for the camera frame.
    """
    aspect = config.frame_width / config.frame_height
    g = VGroup(*mobs)
    w, h = g.width + 2 * pad, g.height + 2 * pad
    width = float(max(w / (1.0 - right), (h / (1.0 - top)) * aspect, 5.0))
    height = width / aspect
    c = g.get_center()
    return _np.array([c[0] + right * width / 2.0,
                      c[1] + top * height / 2.0, 0.0]), width


def look_at(scene, mobs, **kw):
    """The camera animation that brings `mobs` into the clear part of the screen."""
    centre, width = frame_target(mobs, **kw)
    return scene.camera.frame.animate.set(width=width).move_to(centre)


def card_back(mob, pad=0.24, opacity=0.9, color=None):
    """
    A dark backing card behind a piece of screen furniture.

    A camera that roams over a sheet with drawing on all sides of it will
    sooner or later pass a projector or a triangle behind the caption. The card
    keeps the words readable when that happens, and costs nothing when it does
    not.
    """
    back = RoundedRectangle(width=mob.width + 2 * pad, height=mob.height + 2 * pad,
                            corner_radius=0.12, stroke_width=0,
                            fill_color=color or NAVY, fill_opacity=opacity)
    back.move_to(mob)
    return VGroup(back, mob)


def rail_focus(panel, rungs, active, dim_level=0.26):
    """
    Light the rung of the step rail we are on and dim the rest.

    One animation, on the WHOLE pinned panel, and it touches nothing but
    opacity. Both of those matter. Animating a single rung would make Manim add
    that rung to the scene in its own right, which quietly dismantles the VGroup
    around it - and that VGroup is what pin_to_frame() hangs on the camera, so
    the rail would stop following the camera and drift off the top of the
    screen. Touching only opacity keeps the animation clear of the same updater.

    `active` is the index to light, or a collection of indices; anything not in
    it is dimmed. `panel.levels` carries the current opacities between calls.
    """
    lit = set(active) if isinstance(active, (list, tuple, set, range)) else {active}
    starts = list(panel.levels)
    targets = [1.0 if i in lit else dim_level for i in range(len(rungs))]
    panel.levels = targets

    def _relight(mob, alpha):
        for rung, a, b in zip(rungs, starts, targets):
            rung.set_opacity(interpolate(a, b, alpha))

    return UpdateFromAlphaFunc(panel, _relight)



def settle(*anims, share: float = 0.2, lag: float = 0.12):
    """Land `anims` early in a narrate() span instead of over the whole of it.

    narrate() stretches whatever it is handed across the entire sentence. That
    is exactly right for a line being drawn as it is described, and exactly
    wrong for a caption: on a fifty-word sentence a FadeIn becomes a thirteen
    second creep which is fully lit only as the scene begins to fade out. With
    TAIL_PAD at 0.35 s, the closing line of a scene - the one a viewer would
    pause on - is legible for about a third of a second.

    Succession keeps the proportions between its parts when the outer play()
    rescales it, so pairing the animation with a Wait pins it to `share` of
    whatever the sentence turns out to last: the words land in the first fifth
    and stay lit for the rest, at any sentence length.
    """
    group = anims[0] if len(anims) == 1 else AnimationGroup(*anims, lag_ratio=lag)
    return Succession(group, Wait(group.run_time * (1.0 - share) / share))


# --------------------------------------------------------------------------
# Typography / furniture
# --------------------------------------------------------------------------
def caption(text: str, color=INK, size: int = 24, font=None):
    return Text(text, font=font or TITLE_FONT, color=color, font_size=size)


def title_bar(text: str, sub: str | None = None):
    """Standing top-left caption used on every scene of the series."""
    heading = Text(text, font=TITLE_FONT, weight=BOLD, color=INK, font_size=30)
    group = VGroup(heading)
    if sub:
        tail = Text(sub, font=MONO_FONT, color=TEAL, font_size=19)
        tail.next_to(heading, DOWN, aligned_edge=LEFT, buff=0.16)
        group.add(tail)
    rule = Line(ORIGIN, RIGHT * max(heading.width, group.width),
                color=TEAL, stroke_width=2)
    rule.next_to(group, DOWN, aligned_edge=LEFT, buff=0.14)
    group.add(rule)
    return group.to_corner(UP + LEFT, buff=0.42)


def chip(text: str, color=GOLD, size: int = 20, pad: float = 0.18):
    """Rounded tag used for quadrant and rule callouts."""
    label = Text(text, font=MONO_FONT, color=color, font_size=size)
    box = Rectangle(
        width=label.width + 2 * pad,
        height=label.height + 1.4 * pad,
        stroke_color=color,
        stroke_width=1.6,
        fill_color=NAVY,
        fill_opacity=0.82,
    ).move_to(label)
    return VGroup(box, label)
