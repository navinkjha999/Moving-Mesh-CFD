"""
mm_common.py -- shared infrastructure for the Moving Mesh From Scratch series.

Self-contained on purpose: it does not import cfd_common, so this episode runs
standalone. If you'd rather fold it into cfd_common.py, the only things this
module owns that you don't already have are `line_band()` and `code_block()` --
everything else mirrors your existing pattern.

Narration contract
------------------
`narrate()` is the ONLY timing primitive. Never call self.play() or self.wait()
directly in a scene; hand the animations to narrate() and let audio length drive
the runtime. Scenes inherit from NarratedScene.

    class S01_Foo(NarratedScene):
        def construct(self):
            t = title("Hello")
            self.narrate("Spoken line here.", Create(t))
            self.finish_audio()
            self.play(FadeOut(t))

Environment switches
--------------------
    NARR_SILENT=1   skip TTS entirely, estimate durations from word count
                    (use for every draft render -- it is ~40x faster)
    NARR_STRICT=0   downgrade synthesis failure from a crash to a warning
                    (default is STRICT=1: fail loudly rather than ship a
                     silent video, which is the failure mode that bites)
    NARR_VOICE      override the voice id

Render
------
    manim -ql mm01_scenes.py S01_Roadmap        # draft
    manim -qh mm01_scenes.py S01_Roadmap        # final
Never -qk: Cairo runs out of memory on the code-heavy scenes.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from manim import *

# =====================================================================
# 1. BRAND
# =====================================================================
NAVY = "#0B1221"
TEAL = "#2DD4BF"
GOLD = "#F5B642"
CORAL = "#FF6F61"
SLATE = "#334155"
PAPER = "#E2E8F0"
MUTED = "#94A3B8"

config.background_color = NAVY


def _font_or_fallback(preferred: str, fallback: str) -> str:
    """Fonts differ between your machine and a CI box. Degrade, don't crash."""
    try:
        import manimpango

        if preferred in manimpango.list_fonts():
            return preferred
    except Exception:
        pass
    return fallback


FONT_SANS = _font_or_fallback("Space Grotesk", "DejaVu Sans")
FONT_MONO = _font_or_fallback("JetBrains Mono", "DejaVu Sans Mono")

# Text reveal style lives in ONE place so the whole episode stays consistent.
# Create() on a Paragraph draws glyph outlines, which reads badly for code;
# Write() is used for text-like mobjects and Create() for geometry.
USE_WRITE_FOR_TEXT = True


# =====================================================================
# 2. NARRATION
# =====================================================================
VOICE = os.environ.get("NARR_VOICE", "en-US-GuyNeural")
RATE = "-3%"      # guy_low preset: slightly slower than default
PITCH = "-8Hz"    # and slightly deeper -- won the A/B test
SILENT = os.environ.get("NARR_SILENT", "0") == "1"
STRICT = os.environ.get("NARR_STRICT", "1") == "1"

CACHE_ROOT = Path("media") / "narration"
WORDS_PER_SEC = 2.6   # only used when SILENT=1


def _cache_path(scene_name: str, text: str) -> Path:
    """MD5 over the text AND the voice settings, namespaced per scene class.

    Namespacing per scene is not optional. Two scenes that share a line of
    narration will otherwise collide in the cache and you will ship the wrong
    audio under the wrong animation.
    """
    key = f"{VOICE}|{RATE}|{PITCH}|{text}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
    d = CACHE_ROOT / scene_name
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{digest}.wav"


def _synthesize(text: str, wav_path: Path) -> None:
    """edge-tts -> mp3 -> ffmpeg -> wav.

    edge-tts writes MP3 data regardless of the extension you give it. Asking it
    for a .wav yields a file that is really an MP3, which Manim's add_sound
    accepts without complaint and then plays as silence. Always synthesize to
    .mp3 and convert explicitly.
    """
    import asyncio

    import edge_tts

    mp3_path = wav_path.with_suffix(".mp3")

    async def _run():
        comm = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await comm.save(str(mp3_path))

    asyncio.run(_run())

    if not mp3_path.exists() or mp3_path.stat().st_size < 512:
        raise RuntimeError(f"edge-tts produced no usable audio for: {text[:60]!r}")

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3_path),
         "-ar", "44100", "-ac", "1", str(wav_path)],
        check=True,
    )
    mp3_path.unlink(missing_ok=True)


def _wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _estimate(text: str) -> float:
    return max(1.2, len(text.split()) / WORDS_PER_SEC)


class NarratedScene(Scene):
    """Scene base class where narration drives all timing."""

    def setup(self):
        super().setup()
        self._audio_tail = 0.0
        self._elapsed = 0.0

    # -- the sole timing primitive ------------------------------------
    def narrate(self, text: str, *anims, hold: float = 0.35, lag: float = 0.0,
                anim_time: float | None = None):
        """Speak `text` while playing `anims`, stretched to the audio length.

        anims     : Animation objects, or an AnimationGroup. Multiple animations
                    are wrapped in AnimationGroup(lag_ratio=lag).
        hold      : dead air after the animations finish, in seconds.
        anim_time : play the animations over this many seconds instead of
                    stretching them across the whole line, then hold still for
                    the remainder. Use it for highlight boxes and pointer moves
                    -- a box that takes twelve seconds to slide down four lines
                    reads as lag, not emphasis. Leave it None for reveals that
                    genuinely should unfold as you talk.
        """
        duration = self._audio_for(text)
        anims = [a for a in anims if a is not None]

        play_time = max(0.4, duration - hold)
        if anim_time is not None:
            play_time = max(0.3, min(anim_time, play_time))

        if anims:
            group = (anims[0] if len(anims) == 1
                     else AnimationGroup(*anims, lag_ratio=lag))
            self.play(group, run_time=play_time)
        else:
            self.wait(play_time)

        remainder = duration - play_time - hold
        if remainder > 0:
            self.wait(remainder)
        if hold > 0:
            self.wait(hold)
        self._elapsed += duration
        return duration

    def _audio_for(self, text: str) -> float:
        if SILENT:
            return _estimate(text)

        wav = _cache_path(type(self).__name__, text)
        if not wav.exists():
            try:
                _synthesize(text, wav)
            except Exception as exc:  # noqa: BLE001
                msg = (f"\n{'!'*70}\nNARRATION FAILED for {type(self).__name__}\n"
                       f"  text: {text[:70]!r}\n  error: {exc}\n{'!'*70}\n")
                if STRICT:
                    raise RuntimeError(msg) from exc
                print(msg, file=sys.stderr)
                return _estimate(text)

        dur = _wav_duration(wav)
        self.add_sound(str(wav))
        self._audio_tail = dur
        return dur

    def finish_audio(self):
        """Call before the final FadeOut so the last line is not clipped."""
        self.wait(0.6)


# =====================================================================
# 3. TEXT + LAYOUT HELPERS
# =====================================================================
def reveal(m: Mobject, **kw) -> Animation:
    """One place that decides how things appear."""
    is_texty = isinstance(m, (Text, Paragraph, MarkupText, MathTex, Tex, Code))
    if is_texty and USE_WRITE_FOR_TEXT:
        return Write(m, **kw)
    return Create(m, **kw)


def title(txt: str, size: float = 44, color: str = PAPER) -> Text:
    return Text(txt, font=FONT_SANS, font_size=size, color=color, weight=BOLD)


def body(txt: str, size: float = 30, color: str = PAPER) -> Text:
    return Text(txt, font=FONT_SANS, font_size=size, color=color)


def mono(txt: str, size: float = 26, color: str = TEAL) -> Text:
    return Text(txt, font=FONT_MONO, font_size=size, color=color)


def eq(tex: str, size: float = 44, color: str = PAPER) -> MathTex:
    return MathTex(tex, font_size=size, color=color)


def bullets(lines, size: float = 28, buff: float = 0.42) -> VGroup:
    g = VGroup(*[body(t, size=size) for t in lines])
    g.arrange(DOWN, aligned_edge=LEFT, buff=buff)
    return g


def stack_below(m: Mobject, ref: Mobject, buff: float = 0.6,
                x: float = 0.0) -> Mobject:
    """Place `m` under `ref` but re-centre it horizontally.

    next_to() copies the reference's horizontal centre. Because step_header()
    is pinned to the left edge, anything chained under it inherits that offset
    and walks off the left of the frame. Always route through this.
    """
    m.next_to(ref, DOWN, buff=buff)
    m.set_x(x)
    return m


def fit_frame(m: Mobject, max_w: float = 12.4, max_h: float = 5.9) -> Mobject:
    """Shrink `m` until it fits inside the safe area. Never enlarges."""
    if m.width <= 1e-9 or m.height <= 1e-9:
        return m
    s = min(max_w / m.width, max_h / m.height, 1.0)
    if s < 1.0:
        m.scale(s)
    return m


def banner(txt: str, color: str = GOLD, size: float = 26) -> VGroup:
    """A small labelled chip -- used for step counters."""
    t = Text(txt, font=FONT_MONO, font_size=size, color=NAVY, weight=BOLD)
    box = RoundedRectangle(
        corner_radius=0.12, width=t.width + 0.45, height=t.height + 0.3,
        fill_color=color, fill_opacity=1.0, stroke_width=0,
    )
    return VGroup(box, t)


# =====================================================================
# 4. CODE DISPLAY
# =====================================================================
def code_block(src: str, size: float = 20, line_numbers: bool = True,
               width: float | None = None) -> Code:
    """Manim CE 0.20.1 Code mobject with the series styling.

    0.20 renamed the constructor args (code_string=, formatter_style=) and
    exposes the rendered lines as `.code_lines`, which `line_band()` uses.
    """
    c = Code(
        code_string=src.strip("\n"),
        language="python",
        formatter_style="monokai",
        background="window",
        add_line_numbers=line_numbers,
        paragraph_config={"font": FONT_MONO, "font_size": size,
                          "line_spacing": 0.55},
        background_config={"stroke_color": SLATE, "fill_color": "#0F1729"},
    )
    if width is not None:
        c.set(width=width)
    return c


def _line_geometry(code: Code):
    """Return (y_of_line_0, line_height) in scene units.

    Derived from the line-number column when it exists, because every entry
    there is non-empty and evenly spaced. Measuring the code glyphs instead
    gives you the ink bounding box -- blank lines contribute nothing and
    descenders skew the bottom, which lands highlights half a line off.
    """
    ruler = getattr(code, "line_numbers", None)
    if ruler is not None and len(ruler) >= 2:
        y0 = ruler[0].get_center()[1]
        y1 = ruler[len(ruler) - 1].get_center()[1]
        return y0, (y0 - y1) / (len(ruler) - 1)

    # fallback: fit through the code lines that actually carry glyphs
    lines = code.code_lines
    known = [(i, ln.get_center()[1]) for i, ln in enumerate(lines)
             if len(ln.family_members_with_points()) > 0]
    if len(known) >= 2:
        (i0, y0), (i1, y1) = known[0], known[-1]
        lh = (y0 - y1) / max(1, (i1 - i0))
        return y0 + i0 * lh, lh

    top, bottom = lines.get_top()[1], lines.get_bottom()[1]
    n = max(1, len(lines))
    lh = (top - bottom) / n
    return top - lh / 2, lh


def line_band(code: Code, first: int, last: int | None = None,
              color: str = GOLD, opacity: float = 0.16) -> Rectangle:
    """Highlight rectangle spanning source lines `first`..`last` (0-indexed).

    Built geometrically rather than with SurroundingRectangle(code_lines[i]) --
    blank lines contain no points and would raise.
    """
    last = first if last is None else last
    y0, lh = _line_geometry(code)

    y_hi = (y0 - first * lh) + lh / 2
    y_lo = (y0 - last * lh) - lh / 2

    left = code.get_left()[0] + 0.12
    right = code.get_right()[0] - 0.12

    r = Rectangle(
        width=right - left,
        height=max(0.12, y_hi - y_lo),
        stroke_color=color, stroke_width=2.0,
        fill_color=color, fill_opacity=opacity,
    )
    r.move_to([(left + right) / 2, (y_hi + y_lo) / 2, 0])
    return r


# =====================================================================
# 5. PLOT HELPERS
# =====================================================================
def dark_axes(x_range, y_range, x_length=8.0, y_length=4.0,
              x_label=None, y_label=None,
              y_decimals: int | None = None,
              x_decimals: int | None = None) -> VGroup:
    """Axes in the series palette.

    y_decimals / x_decimals: pass an int to switch on tick numbers with that
    many decimal places. A density axis spanning 0.996 to 1.004 is meaningless
    without them -- the viewer cannot tell whether the wobble is 0.2% or 20%.
    """
    ax = Axes(
        x_range=x_range, y_range=y_range,
        x_length=x_length, y_length=y_length,
        axis_config={"color": MUTED, "stroke_width": 2,
                     "include_tip": False,
                     "font_size": 22},
        x_axis_config=(
            {"include_numbers": True,
             "decimal_number_config": {"num_decimal_places": x_decimals}}
            if x_decimals is not None else {}
        ),
        y_axis_config=(
            {"include_numbers": True,
             "decimal_number_config": {"num_decimal_places": y_decimals}}
            if y_decimals is not None else {}
        ),
        tips=False,
    )
    ax.set_color(MUTED)
    labels = VGroup()
    if x_label:
        labels.add(body(x_label, size=22, color=MUTED).next_to(ax.x_axis, DOWN, buff=0.28))
    if y_label:
        labels.add(body(y_label, size=22, color=MUTED)
                   .rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.28))
    return VGroup(ax, labels)


def mesh_strip(x_nodes, values, y_center=0.0, height=0.9,
               x_span=(-5.6, 5.6), vmin=None, vmax=None,
               low=TEAL, mid=SLATE, high=CORAL) -> VGroup:
    """Draw a 1D mesh as coloured cells with node lines on top.

    x_nodes : array of N+1 node positions in problem coordinates
    values  : array of N cell values used for the fill colour
    """
    import numpy as np

    x_nodes = np.asarray(x_nodes, dtype=float)
    values = np.asarray(values, dtype=float)
    x0, x1 = float(x_nodes[0]), float(x_nodes[-1])
    span = max(1e-12, x1 - x0)

    def to_screen(x):
        f = (x - x0) / span
        return x_span[0] + f * (x_span[1] - x_span[0])

    if vmin is None:
        vmin = float(values.min())
    if vmax is None:
        vmax = float(values.max())
    rng = max(1e-14, vmax - vmin)

    cells = VGroup()
    for i, v in enumerate(values):
        xl, xr = to_screen(x_nodes[i]), to_screen(x_nodes[i + 1])
        f = (v - vmin) / rng
        col = (interpolate_color(ManimColor(low), ManimColor(mid), f * 2)
               if f < 0.5 else
               interpolate_color(ManimColor(mid), ManimColor(high), (f - 0.5) * 2))
        cells.add(Rectangle(
            width=max(1e-3, xr - xl), height=height,
            stroke_width=0, fill_color=col, fill_opacity=1.0,
        ).move_to([(xl + xr) / 2, y_center, 0]))

    grid = VGroup(*[
        Line([to_screen(x), y_center - height / 2, 0],
             [to_screen(x), y_center + height / 2, 0],
             stroke_color=PAPER, stroke_width=1.1, stroke_opacity=0.5)
        for x in x_nodes
    ])
    return VGroup(cells, grid)


def require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found -- narration conversion will fail.")
