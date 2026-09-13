"""
cfd_common.py
Shared infrastructure for the Engineering From Scratch Manim series.
Manim CE 0.20.1 / Python 3.11.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import struct
import subprocess
import wave
from pathlib import Path

from manim import *

# ---------------------------------------------------------------------------
# Brand & Colors
# ---------------------------------------------------------------------------
NAVY = "#0B1221"
TEAL = "#2DD4BF"
GOLD = "#F5B642"
CORAL = "#FF6F61"
CREAM = "#FDF6E3"   
SLATE = "#94A3B8"   
VIOLET = "#8B5CF6"  

# Use fonts that are present in a standard Windows installation. This avoids
# Manim silently substituting a proportional fallback for measurement labels.
H_FONT = "Bahnschrift"
M_FONT = "Cascadia Mono"

config.background_color = NAVY

# ---------------------------------------------------------------------------
# Voice profile
# ---------------------------------------------------------------------------
VOICE = "en-US-GuyNeural"
RATE = "-3%"
PITCH = "-8Hz"

SAMPLE_RATE = 44100
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"

CACHE_ROOT = Path("media") / "narration"

LAG_DEFAULT = 0.35     
TAIL_PAD = 0.35        
WPM_ESTIMATE = 155.0   

# ---------------------------------------------------------------------------
# Cache + synthesis 
# ---------------------------------------------------------------------------
def _clean(text: str) -> str:
    return " ".join(text.split())

def cache_key(text: str, voice: str = VOICE, rate: str = RATE, pitch: str = PITCH) -> str:
    payload = f"{voice}|{rate}|{pitch}|{_clean(text)}".encode("utf-8")
    return hashlib.md5(payload).hexdigest()

def cache_path(namespace: str, text: str) -> Path:
    return CACHE_ROOT / namespace / f"{cache_key(text)}.wav"

def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())

def estimate_duration(text: str) -> float:
    words = len(_clean(text).split())
    return max(1.0, words / WPM_ESTIMATE * 60.0)

def write_silence(path: Path, seconds: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * SAMPLE_RATE)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(struct.pack("<h", 0) * frames)

async def _edge_save(text: str, mp3_path: Path) -> None:
    import edge_tts
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await comm.save(str(mp3_path))

def _mp3_to_wav(mp3_path: Path, wav_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(mp3_path),
           "-ac", "1", "-ar", str(SAMPLE_RATE)]
    if not os.environ.get("EFS_NO_NORM"):
        cmd += ["-af", LOUDNORM]
    cmd += ["-c:a", "pcm_s16le", str(wav_path)]
    subprocess.run(cmd, check=True)

def synthesise(namespace: str, text: str) -> tuple[Path, float]:
    text = _clean(text)
    wav = cache_path(namespace, text)
    if wav.exists():
        return wav, wav_duration(wav)

    wav.parent.mkdir(parents=True, exist_ok=True)

    if os.environ.get("EFS_SILENT"):
        write_silence(wav, estimate_duration(text))
        return wav, wav_duration(wav)

    mp3 = wav.with_suffix(".mp3")
    try:
        asyncio.run(_edge_save(text, mp3))
        if not mp3.exists() or mp3.stat().st_size < 512:
            raise RuntimeError("edge-tts produced an empty file")
        _mp3_to_wav(mp3, wav)
        mp3.unlink(missing_ok=True)
        return wav, wav_duration(wav)
    except Exception as exc:                                   
        mp3.unlink(missing_ok=True)
        write_silence(wav, estimate_duration(text))
        dur = wav_duration(wav)
        print(f"[cfd_common] TTS FAILED, using {dur:.1f}s silence: {exc}\n"
              f"             text: {text[:70]}...\n"
              f"             delete {wav} to retry.")
        return wav, dur

# ---------------------------------------------------------------------------
# Standalone Narration Functions 
# ---------------------------------------------------------------------------
def narrate(scene: Scene, text: str, *anims, hold: float = 0.0, **kwargs) -> float:
    """Speak `text` while playing `anims` stretched to fit the audio."""
    if not hasattr(scene, "_audio_end"):
        scene._audio_end = 0.0
        
    namespace = type(scene).__name__
    wav, dur = synthesise(namespace, text)
    scene.add_sound(str(wav))
    scene._audio_end = max(scene._audio_end, scene.renderer.time + dur)

    span = max(dur - hold, 0.1)
    if anims:
        # Safely extract lag_ratio from kwargs if it was passed by the scene
        lag = kwargs.pop("lag_ratio", LAG_DEFAULT)
        
        if len(anims) == 1:
            scene.play(anims[0], run_time=span, **kwargs)
        else:
            group = AnimationGroup(*anims, lag_ratio=lag)
            scene.play(group, run_time=span, **kwargs)
    else:
        scene.wait(span)

    if hold > 0:
        scene.wait(hold)
    return dur

def finish_audio(scene: Scene, pad: float = TAIL_PAD) -> None:
    """Hold until the queued narration has fully played out."""
    if not hasattr(scene, "_audio_end"):
        return
        
    remaining = scene._audio_end - scene.renderer.time
    if remaining > 0:
        scene.wait(remaining)
    if pad > 0:
        scene.wait(pad)


# ---------------------------------------------------------------------------
# Shared UI & Formatting Helpers
# ---------------------------------------------------------------------------
def mono(text: str, size: int = 18, color: str = "#E7EDF3", **kw) -> Text:
    return Text(text, font=M_FONT, font_size=size, color=color, **kw)

def head(text: str, size: int = 34, color: str = "#E7EDF3", **kw) -> Text:
    return Text(text, font=H_FONT, font_size=size, color=color, weight=BOLD, **kw)

def body(text: str, size: int = 24, color: str = CREAM, weight=NORMAL) -> Text:
    return Text(text, font=M_FONT, font_size=size, color=color, weight=weight)

def eq(tex: str, size: int = 36, color: str = CREAM) -> MathTex:
    return MathTex(tex, font_size=size, color=color)

def title_card(ep: str, main: str, sub: str) -> VGroup:
    return VGroup(
        Text(ep, font_size=24, color=SLATE),
        Text(main, font_size=48, color=CREAM, weight=BOLD),
        Text(sub, font_size=24, color=TEAL)
    ).arrange(DOWN, buff=0.3)

def phase_banner(num: int) -> VGroup:
    return VGroup(Text(f"PHASE {num}", font_size=20, color=SLATE)).to_corner(UL)

def section_title(num: int, title: str) -> VGroup:
    return VGroup(Text(f"Step {num}: {title}", font_size=34, color=GOLD, weight=BOLD))

def panel(obj: Mobject, label: str = "", color: str = TEAL, pad: float = 0.3) -> VGroup:
    rect = SurroundingRectangle(obj, color=color, buff=pad, corner_radius=0.1)
    lab = Text(label, font_size=20, color=color).next_to(rect, UP, aligned_edge=LEFT)
    return VGroup(rect, lab, obj)

def callout(text: str, color: str = TEAL, size: int = 24) -> Text:
    return Text(text, font_size=size, color=color)

def nepal_hook(text: str, size: int = 24) -> Text:
    return Text(text, font_size=size, color=CREAM)

def code_block(lines: list[str], size: int = 24, highlight: set = frozenset()) -> VGroup:
    g = VGroup()
    for i, l in enumerate(lines):
        col = GOLD if i in highlight else CREAM
        txt = Text(l, font=M_FONT, font_size=size, color=col)
        g.add(txt)
    return g.arrange(DOWN, aligned_edge=LEFT)

def fade_all(scene: Scene) -> AnimationGroup:
    return AnimationGroup(*[FadeOut(m) for m in scene.mobjects])

def prewarm(scene_cls, texts) -> None:
    ns = scene_cls if isinstance(scene_cls, str) else scene_cls.__name__
    for t in texts:
        _, d = synthesise(ns, t)
        print(f"  {d:5.1f}s  {_clean(t)[:60]}...")
        