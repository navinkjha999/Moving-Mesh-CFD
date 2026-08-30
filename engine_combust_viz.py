"""
engine_combust_viz.py -- post-processor-grade animation for engine_combust.py

The physics module is deliberately plotting-free. Everything on screen here is
read back out of the arrays simulate() already records; nothing is re-derived,
smoothed or invented for the picture. What the animation adds is the *geometry*
the solver only ever held implicitly:

  * the slider-crank, drawn in its own schematic panel from the same closed
    form the solver integrates, so the piston in the picture is the piston in
    the equations (verify_kinematics() checks the drawn conrod never stretches
    off its length `l`),
  * the ALE mesh, stretched over the instantaneous chamber height, which is the
    same logical->physical map ale_piston_viz.py uses,
  * the flame front as the analytic circle of radius r_f about the spark plug,
    clipped by the bore -- the identical geometry burned_area()/flame_arc() use.

Panels
------
  upper left   cut plane through the cylinder axis and the spark plug:
               temperature field on the deforming ALE mesh, plus the piston
  lower left   the slider-crank, laid on its side, charge tinted by mean T
  centre       plan view of the pancake chamber -- the flame front eating into
               the end gas -- over a solver-monitor readout and a knock meter
  right        pressure, zone temperatures, burn rate, p-V loop, each with a
               live cursor locked to the frame
  bottom       crank-angle scrubber marked with spark, CA10/50/90 and knock

Outputs
-------
  engine_combust.mp4   (or .gif when ffmpeg is not available)
  VTK time series      optional, --vtk DIR, for ParaView / Tecplot / EnSight

Run
---
  python3 engine_combust_viz.py                    # write engine_combust.mp4
  python3 engine_combust_viz.py --interactive      # scrub it in a window
  python3 engine_combust_viz.py --field c          # progress variable instead
  python3 engine_combust_viz.py --vtk vtk_out      # export for ParaView
  python3 engine_combust_viz.py --spark -34 --rpm 3000 --save mbt.mp4
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

import numpy as np

import matplotlib
if not os.environ.get("DISPLAY") and sys.platform not in ("darwin", "win32"):
    matplotlib.use("Agg")          # overridden below when --interactive is asked
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Circle, Polygon, Rectangle

import engine_combust as ec


# ---------------------------------------------------------------- palette
# Surfaces and hardware keep the repo's brand colours. The *data series*
# colours are a separate, validated set: three categorical slots inside the
# dark-mode OKLCH lightness band with adjacent-pair CVD separation well clear
# of the floor (deutan dE 14.1, tritan 11.4 -- checked, not eyeballed).
NAVY, TEAL, GOLD, CORAL = "#0B1221", "#2DD4BF", "#F5B642", "#FF6F61"
SLATE, PAPER = "#334155", "#E2E8F0"
INK, INK_DIM, INK_MUTE = "#E2E8F0", "#9AA7BC", "#64748B"

SERIES = ("#00A08C", "#9B7BEA", "#E4523E")     # fixed order, never cycled
ACCENT = "#F5B642"                             # lone-series accent (pressure)
GOOD, WARN, CRIT = "#34D399", "#FBBF24", "#F87171"   # reserved status colours

# Temperature ramp: multi-hue but monotone in OKLCH lightness (the CFD-field
# convention done the defensible way -- no rainbow, no lightness inversions).
CMAP_T = LinearSegmentedColormap.from_list(
    "flame", ["#070C16", "#123B52", TEAL, GOLD, CORAL, "#FFE9D6"])
# Progress variable is a magnitude -> one hue, dark to light.
CMAP_C = LinearSegmentedColormap.from_list(
    "burnt", ["#071A1D", "#0E4A46", "#12796F", TEAL, "#C9F5EE"])
for _cm in (CMAP_T, CMAP_C):        # outside the bore is chamber wall, not data
    _cm.set_bad(NAVY)

FLAME_THICK = 1.2e-3      # m, rendering width of the reaction zone (display only)
PISTON_H = 0.030          # m, crown to wrist pin -- drawing dimension only
SKIRT_H = 0.052           # m, crown to bottom of skirt


# ================================================================= helpers
def _style_axes(ax, title=None):
    ax.set_facecolor("#0E1729")
    for s in ax.spines.values():
        s.set_color(SLATE)
        s.set_linewidth(0.8)
    ax.tick_params(colors=INK_MUTE, labelsize=8, length=3, width=0.8)
    ax.grid(True, color=SLATE, lw=0.5, alpha=0.35)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=10, pad=6, loc="left")


def _bare(ax):
    ax.set_facecolor(NAVY)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def _running_imep(res, eng):
    """Cumulative integral of p dV, normalised by displacement."""
    p, V = res["p"], res["V"]
    inc = 0.5 * (p[1:] + p[:-1]) * np.diff(V)
    return np.concatenate([[0.0], np.cumsum(inc)]) / eng.V_d


def _ca(res, frac):
    """Crank angle at which the mass fraction burned first reaches frac."""
    x = res["x"]
    if x.max() < frac:
        return None
    return float(res["theta"][int(np.searchsorted(x, frac))])


def _display_ceiling(res):
    """Colour-scale top.

    Right at kernel ignition the two-zone volume closure divides the leftover
    volume by a near-zero burned mass, so T_b spikes to values the model does
    not mean. That is an artefact of the closure, not of the combustion, so the
    scale is set from the burned gas once the kernel has grown (x > 2%) and the
    field is clipped to it for display.
    """
    m = res["x"] > 0.02
    if not m.any():
        return 2500.0
    top = np.percentile(res["T_b"][m], 99.0)
    return float(np.ceil(top / 100.0) * 100.0)


def _resolve_ffmpeg():
    """matplotlib's rcParam -> PATH -> the imageio-ffmpeg wheel."""
    for cand in (matplotlib.rcParams.get("animation.ffmpeg_path"), "ffmpeg"):
        if cand and (os.path.isfile(cand) or shutil.which(cand)):
            return shutil.which(cand) or cand
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


# ================================================================= the figure
class CycleAnimator:
    """Builds every artist once, then only pushes new numbers into them.

    Nothing is re-created per frame, so the per-frame update costs about 2 ms
    and interactive playback blits cleanly; when writing a file the cost is
    almost entirely matplotlib rasterising the figure, not this code.
    """

    def __init__(self, eng: ec.Engine, res, n_frames=480, field="T",
                 show_mesh=True, figsize=(16.0, 9.0), dpi=110):
        self.eng, self.res, self.field = eng, res, field
        self.show_mesh = show_mesh
        n_pts = res["theta"].size
        self.idx = np.unique(np.linspace(0, n_pts - 1, n_frames).astype(int))
        self.n_frames = self.idx.size

        # ---- derived series, computed once -------------------------------
        self.imep_run = _running_imep(res, eng)
        dth = float(np.mean(np.diff(res["theta"])))
        self.hrr = res["dQ"] / dth                       # J per crank degree
        self.hrr_max = max(self.hrr.max(), 1e-12)
        self.fps = 30
        self._hook = None    # optional per-frame callback (scrub bar)
        self.vmax = _display_ceiling(res) if field == "T" else 1.0
        self.vmin = 300.0 if field == "T" else 0.0
        self.ca10, self.ca50, self.ca90 = (_ca(res, f) for f in (0.1, 0.5, 0.9))

        # engine time base: dtheta degrees take dtheta / (6 * rpm) seconds
        self.t_ms = (res["theta"] - res["theta"][0]) / (6.0 * eng.rpm) * 1e3
        self.cycle_ms = float(self.t_ms[-1])

        self._build_figure(figsize, dpi)

    # ------------------------------------------------------------- geometry
    def _kinematics(self, theta_deg):
        """Piston-pin and crankpin positions, straight off the slider-crank.

        z = 0 is the fire deck. The crank centre sits wherever it must for the
        crown to be at -h(theta); because h = V_c/A_p + d(theta) that position
        is a constant, which is the check verify_kinematics() exploits.
        """
        e = self.eng
        th = np.radians(theta_deg)
        h = e.height(theta_deg)
        z_crown = -h
        z_pin = z_crown - PISTON_H
        z_c = -(e.V_c / e.A_p) - PISTON_H - (e.a + e.l)
        return z_crown, z_pin, (e.a * np.sin(th), z_c + e.a * np.cos(th)), z_c

    def _mesh_segments(self, h, nx=11, nz=7):
        """The ALE grid: a fixed logical mesh stretched over the live height."""
        R = self.eng.B / 2.0
        xs = np.linspace(-R, R, nx)
        etas = np.linspace(0.0, 1.0, nz)
        segs = [np.column_stack([[x, x], [-h, 0.0]]) for x in xs]
        segs += [np.column_stack([[-R, R], [-h * t, -h * t]]) for t in etas]
        return segs

    # -------------------------------------------------------------- fields
    def _field_side(self, r_f, T_u, T_b):
        """Cut through y = 0. The flame is a cylinder about the plug, so in
        this plane the burned gas is the slab |x - r_s| < r_f."""
        if r_f <= 0.0:                      # before the spark: all unburned
            c = np.zeros_like(self._xs)
        else:
            c = 0.5 * (1.0 - np.tanh((np.abs(self._xs - self.eng.r_s) - r_f)
                                     / FLAME_THICK))
        row = c if self.field == "c" else T_u + (min(T_b, self.vmax) - T_u) * c
        return np.tile(row, (self._nz_side, 1))

    def _field_top(self, r_f, T_u, T_b):
        c = (np.zeros_like(self._rho) if r_f <= 0.0 else
             0.5 * (1.0 - np.tanh((self._rho - r_f) / FLAME_THICK)))
        f = c if self.field == "c" else T_u + (min(T_b, self.vmax) - T_u) * c
        return np.ma.array(f, mask=self._outside)

    # ------------------------------------------------------------- figure
    def _build_figure(self, figsize, dpi):
        self.fig = plt.figure(figsize=figsize, dpi=dpi, facecolor=NAVY)
        gs = GridSpec(12, 16, figure=self.fig,
                      left=0.030, right=0.982, top=0.870, bottom=0.152,
                      wspace=2.4, hspace=2.4)

        self.ax_side = self.fig.add_subplot(gs[0:8, 0:5])
        self.ax_mech = self.fig.add_subplot(gs[8:12, 0:5])
        self.ax_top = self.fig.add_subplot(gs[0:6, 5:9])
        self.ax_hud = self.fig.add_subplot(gs[6:12, 5:9])
        self.ax_p = self.fig.add_subplot(gs[0:3, 9:16])
        self.ax_T = self.fig.add_subplot(gs[3:6, 9:16])
        self.ax_b = self.fig.add_subplot(gs[6:9, 9:16])
        self.ax_pv = self.fig.add_subplot(gs[9:12, 9:16])
        self.ax_bar = self.fig.add_axes([0.030, 0.052, 0.952, 0.046])

        self._header()
        self._build_side()
        self._build_mech()
        self._build_top()
        self._build_hud()
        self._build_traces()
        self._build_scrubber()
        self._footer()

    def _header(self):
        e = self.eng
        self.fig.text(0.030, 0.960, "SPARK-IGNITION CYCLE  —  flame "
                      "propagation, pressure and knock",
                      color=INK, fontsize=17, fontweight="bold", va="center")
        spec = (f"bore {e.B*1e3:.0f} × stroke {e.L*1e3:.0f} mm   "
                f"CR {e.CR:.1f}   {e.rpm:.0f} rpm   "
                f"ϕ {e.phi:.2f}   RON {e.octane:.0f}   "
                f"spark {e.th_spark:+.0f}°   "
                f"IVC {e.th_ivc:+.0f}° → EVO {e.th_evo:+.0f}°")
        self.fig.text(0.030, 0.929, spec, color=INK_DIM, fontsize=10.5,
                      va="center")

    # ---------------------------------------------------------- side view
    def _build_side(self):
        e = self.eng
        ax = self.ax_side
        _bare(ax)
        R = e.B / 2.0
        z_bot = -(e.height(180.0) + SKIRT_H) - 0.006
        ax.set_xlim(-R * 1.30, R * 1.30)
        ax.set_ylim(z_bot, 0.026)
        ax.set_aspect("equal", adjustable="box")
        ax.autoscale(False)          # set_extent must never move the view
        ax.set_title("cut plane through the cylinder axis and the spark plug",
                     color=INK, fontsize=10, pad=6, loc="left")

        self._nz_side = 40
        self._xs = np.linspace(-R, R, 260)
        self.im_side = ax.imshow(np.zeros((self._nz_side, self._xs.size)),
                                 extent=(-R, R, -e.height(0.0), 0.0),
                                 origin="lower", aspect="auto",
                                 cmap=CMAP_T if self.field == "T" else CMAP_C,
                                 vmin=self.vmin, vmax=self.vmax,
                                 interpolation="bilinear", zorder=2)

        self.mesh = LineCollection([], colors="#94A3B8", linewidths=0.6,
                                   alpha=0.45, zorder=3)
        ax.add_collection(self.mesh)
        self.mesh.set_visible(self.show_mesh)
        self.front_side, = ax.plot([], [], color="#FFE9D6", lw=1.8,
                                   alpha=0.95, zorder=4)

        # --- hardware ---------------------------------------------------
        ax.add_patch(Rectangle((-R * 1.22, 0.0), 2 * R * 1.22, 0.014,
                               facecolor="#1B2740", edgecolor=SLATE, lw=1.2,
                               zorder=5))
        for sgn in (-1, 1):
            ax.add_patch(Rectangle((sgn * R, z_bot), sgn * R * 0.22,
                                   -z_bot, facecolor="#1B2740",
                                   edgecolor=SLATE, lw=1.2, zorder=5))
        for xv in (-R * 0.46, R * 0.46):   # valves: shut for the whole window
            ax.plot([xv, xv], [0.0, 0.0135], color=SLATE, lw=3.0, zorder=6)
            ax.plot([xv - R * 0.20, xv + R * 0.20], [0.0, 0.0],
                    color=SLATE, lw=4.0, solid_capstyle="round", zorder=6)
        ax.text(-R * 0.46, 0.0165, "intake", color=INK_MUTE, fontsize=7.5,
                ha="center", va="bottom")
        ax.text(R * 0.46, 0.0165, "exhaust", color=INK_MUTE, fontsize=7.5,
                ha="center", va="bottom")
        ax.text(0.0, 0.0225, "valves shut (IVC → EVO)", color=INK_MUTE,
                fontsize=7.5, ha="center", va="bottom")

        ax.plot([e.r_s], [0.0], marker="v", ms=9, color=GOLD, zorder=7)
        self.spark_glow, = ax.plot([], [], marker="*", ms=24, color="#FFF3E0",
                                   alpha=0.0, zorder=8)

        self.piston = Polygon(np.zeros((4, 2)), closed=True,
                              facecolor="#243352", edgecolor=INK_DIM, lw=1.1,
                              zorder=6)
        ax.add_patch(self.piston)
        self.rings = LineCollection([], colors=INK_DIM, linewidths=1.4,
                                    zorder=7)
        ax.add_collection(self.rings)
        self.h_label = ax.text(0.0, 0.0, "", color=INK_DIM, fontsize=8.5,
                               ha="center", va="center", zorder=8)

    # ------------------------------------------------------- slider-crank
    def _build_mech(self):
        """The mechanism, laid on its side so it fits a wide, short panel.

        Same closed form as the solver: the crank angle drives the crankpin,
        the conrod closes onto the wrist pin, and the crown lands exactly at
        -V(theta)/A_p. verify_kinematics() checks the rod never stretches.
        """
        e = self.eng
        ax = self.ax_mech
        _bare(ax)
        R = e.B / 2.0
        _, _, _, z_c = self._kinematics(0.0)
        ax.set_xlim(z_c - e.a * 1.45, 0.022)
        ax.set_ylim(-R * 1.5, R * 1.5)
        ax.set_aspect("equal", adjustable="box")
        ax.autoscale(False)
        ax.set_title("slider-crank (schematic, cylinder axis horizontal)",
                     color=INK, fontsize=10, pad=6, loc="left")

        ax.plot([0.0, 0.0], [-R * 1.25, R * 1.25], color=SLATE, lw=3.0)
        for sgn in (-1, 1):
            ax.plot([z_c + e.a * 1.25, 0.0], [sgn * R, sgn * R],
                    color=SLATE, lw=2.0)
        ax.add_patch(Circle((z_c, 0.0), e.a, facecolor="none", edgecolor=SLATE,
                            lw=0.9, ls=(0, (4, 4))))
        ax.add_patch(Circle((z_c, 0.0), e.a * 0.09, facecolor=NAVY,
                            edgecolor=INK_DIM, lw=1.3, zorder=6))
        ax.text(z_c, -R * 1.32, "crank", color=INK_MUTE, fontsize=7.5,
                ha="center", va="top")
        ax.text(0.0, R * 1.32, "TDC", color=INK_MUTE, fontsize=7.5,
                ha="center", va="bottom")

        self.m_gas = Rectangle((0, -R), 0, 2 * R, facecolor=CORAL, alpha=0.85,
                               edgecolor="none", zorder=1)
        ax.add_patch(self.m_gas)
        self.m_piston = Polygon(np.zeros((4, 2)), closed=True,
                                facecolor="#243352", edgecolor=PAPER, lw=1.2,
                                zorder=4)
        ax.add_patch(self.m_piston)
        self.m_rod, = ax.plot([], [], color=PAPER, lw=3.0,
                              solid_capstyle="round", zorder=3)
        self.m_crank, = ax.plot([], [], color=INK_DIM, lw=4.0,
                                solid_capstyle="round", zorder=2)
        self.m_pin = Circle((0, 0), e.a * 0.085, facecolor=NAVY,
                            edgecolor=PAPER, lw=1.2, zorder=5)
        ax.add_patch(self.m_pin)
        self.m_cpin = Circle((0, 0), e.a * 0.085, facecolor=NAVY,
                             edgecolor=INK_DIM, lw=1.2, zorder=5)
        ax.add_patch(self.m_cpin)

    # ----------------------------------------------------------- top view
    def _build_top(self):
        e = self.eng
        ax = self.ax_top
        _bare(ax)
        R = e.B / 2.0
        ax.set_xlim(-R * 1.12, R * 1.12)
        ax.set_ylim(-R * 1.12, R * 1.12)
        ax.set_aspect("equal", adjustable="box")
        ax.autoscale(False)
        ax.set_title("flame front in the pancake chamber (plan view)",
                     color=INK, fontsize=10, pad=6, loc="left")

        n = 240
        g = np.linspace(-R, R, n)
        X, Y = np.meshgrid(g, g)
        self._rho = np.hypot(X - e.r_s, Y)
        self._outside = (X ** 2 + Y ** 2) > R ** 2

        self.im_top = ax.imshow(np.zeros((n, n)), extent=(-R, R, -R, R),
                                origin="lower",
                                cmap=CMAP_T if self.field == "T" else CMAP_C,
                                vmin=self.vmin, vmax=self.vmax,
                                interpolation="bilinear", zorder=2)
        ax.add_patch(Circle((0, 0), R, facecolor="none", edgecolor=PAPER,
                            lw=2.0, zorder=5))
        self.front_top, = ax.plot([], [], color="#FFE9D6", lw=2.0, zorder=6)
        ax.plot([e.r_s], [0.0], marker="o", ms=7, color=GOLD, zorder=7)
        ax.text(e.r_s, R * 0.10, "spark", color=GOLD, fontsize=8,
                ha="center", va="bottom", zorder=7)
        self.endgas, = ax.plot([], [], color=CRIT, lw=2.4, alpha=0.0, zorder=6)
        self.knock_banner = ax.text(
            0.0, R * 1.045, "END-GAS AUTOIGNITION — KNOCK", color=CRIT,
            fontsize=9.5, fontweight="bold", ha="center", va="center",
            alpha=0.0, zorder=8)

        bt, bh = ax.get_position(), self.ax_hud.get_position()
        cax = self.fig.add_axes([bt.x0 + 0.012, bh.y1 + 0.034,
                                 bt.width - 0.024, 0.013])
        cb = self.fig.colorbar(self.im_top, cax=cax, orientation="horizontal")
        cb.outline.set_edgecolor(SLATE)
        cb.ax.tick_params(colors=INK_MUTE, labelsize=8, length=3)
        cb.set_label("temperature (K)" if self.field == "T"
                     else "progress variable c (–)",
                     color=INK_DIM, fontsize=9, labelpad=2)

    # ---------------------------------------------------------------- HUD
    def _build_hud(self):
        ax = self.ax_hud
        _bare(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.add_patch(Rectangle((0.0, 0.0), 1.0, 1.0, facecolor="#0E1729",
                               edgecolor=SLATE, lw=0.8, zorder=1))
        self.hud = ax.text(0.055, 0.955, "", color=INK, fontsize=9.6,
                           family="monospace", va="top", ha="left",
                           linespacing=1.55, zorder=3)
        self.knock_bar = Rectangle((0.055, 0.075), 0.0, 0.052,
                                   facecolor=GOOD, zorder=3)
        ax.add_patch(self.knock_bar)
        ax.add_patch(Rectangle((0.055, 0.075), 0.46, 0.052, facecolor="none",
                               edgecolor=SLATE, lw=0.8, zorder=3))
        ax.text(0.515, 0.055, "1.0", color=INK_MUTE, fontsize=7.5,
                ha="center", va="top", zorder=4)
        self.knock_txt = ax.text(0.55, 0.101, "", color=GOOD, fontsize=9.5,
                                 family="monospace", va="center", zorder=4)

    # ------------------------------------------------------------ traces
    def _build_traces(self):
        res, e = self.res, self.eng
        th = res["theta"]

        # pressure: a lone series, so the title names it and no legend is drawn
        ax = self.ax_p
        _style_axes(ax, "cylinder pressure (bar)")
        ax.plot(th, res["p"] / 1e5, color=ACCENT, lw=1.0, alpha=0.20)
        self.l_p, = ax.plot([], [], color=ACCENT, lw=2.0)
        self.d_p, = ax.plot([], [], marker="o", ms=6, color=ACCENT,
                            mec=NAVY, mew=1.2)
        ax.set_xlim(th[0], th[-1])
        ax.set_ylim(0, res["p"].max() / 1e5 * 1.14)
        self._mark_events(ax)

        # zone temperatures: three series in the same unit -> one axis.
        # Each zone is drawn only while it exists: no burned gas before the
        # kernel, no unburned gas once the flame has consumed the charge.
        ax = self.ax_T
        _style_axes(ax, "zone temperatures (K)")
        alive_u = res["x"] < 0.999
        alive_b = res["x"] > 0.02
        T_cap = self.vmax if self.field == "T" else 4000.0
        self.l_T = []
        for key, lab, col, alive in (("T_u", "unburned", SERIES[0], alive_u),
                                     ("T", "mass-mean", SERIES[1], None),
                                     ("T_b", "burned", SERIES[2], alive_b)):
            y = np.clip(res[key], 0.0, T_cap)
            if alive is not None:
                y = np.where(alive, y, np.nan)
            ax.plot(th, y, color=col, lw=1.0, alpha=0.20)
            ln, = ax.plot([], [], color=col, lw=2.0, label=lab)
            self.l_T.append((ln, y))
        ax.set_xlim(th[0], th[-1])
        ax.set_ylim(0, T_cap * 1.30)
        leg = ax.legend(loc="upper left", fontsize=8, frameon=False, ncol=3,
                        handlelength=1.3, columnspacing=1.0, borderpad=0.1)
        for t in leg.get_texts():
            t.set_color(INK_DIM)
        self._mark_events(ax)

        # burn rate: two quantities of very different scale, so both are
        # normalised onto one axis and the heat-release peak is direct-labelled
        ax = self.ax_b
        _style_axes(ax, "burn rate (normalised)")
        ax.plot(th, res["x"], color=SERIES[0], lw=1.0, alpha=0.20)
        ax.plot(th, self.hrr / self.hrr_max, color=SERIES[1], lw=1.0, alpha=0.20)
        self.l_x, = ax.plot([], [], color=SERIES[0], lw=2.0,
                            label="mass fraction burned")
        self.l_q, = ax.plot([], [], color=SERIES[1], lw=2.0,
                            label="heat release")
        th_peak = float(th[int(np.argmax(self.hrr))])
        ax.annotate(f"peak {self.hrr_max:.1f} J/deg", xy=(th_peak, 1.0),
                    xytext=(th_peak + 14, 1.17), color=SERIES[1], fontsize=8,
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=SERIES[1], lw=0.9))
        ax.set_xlim(th[0], th[-1])
        ax.set_ylim(-0.05, 1.30)
        leg = ax.legend(loc="upper left", fontsize=8, frameon=False, ncol=2,
                        handlelength=1.3, columnspacing=1.0, borderpad=0.1)
        for t in leg.get_texts():
            t.set_color(INK_DIM)
        ax.set_xlabel("crank angle (deg ATDC)", color=INK_DIM, fontsize=9,
                      labelpad=1)
        self._mark_events(ax)

        # p-V loop
        ax = self.ax_pv
        _style_axes(ax, "p–V loop (IVC → EVO)")
        ax.plot(res["V"] * 1e6, res["p"] / 1e5, color=ACCENT, lw=1.0, alpha=0.20)
        self.l_pv, = ax.plot([], [], color=ACCENT, lw=2.0)
        self.d_pv, = ax.plot([], [], marker="o", ms=6, color=ACCENT,
                             mec=NAVY, mew=1.2)
        ax.set_xlim(0, res["V"].max() * 1e6 * 1.05)
        ax.set_ylim(0, res["p"].max() / 1e5 * 1.14)
        ax.set_xlabel("volume (cm³)", color=INK_DIM, fontsize=9, labelpad=1)
        ax.set_ylabel("p (bar)", color=INK_DIM, fontsize=9, labelpad=1)

    def _mark_events(self, ax):
        e, res = self.eng, self.res
        ax.axvline(e.th_spark, color=GOLD, lw=1.0, ls=(0, (3, 3)), alpha=0.65)
        ax.axvline(0.0, color=INK_MUTE, lw=0.9, alpha=0.5)
        if res["knock_theta"] is not None:
            ax.axvline(res["knock_theta"], color=CRIT, lw=1.0,
                       ls=(0, (2, 3)), alpha=0.7)

    # ---------------------------------------------------------- scrubber
    def _build_scrubber(self):
        res, e = self.res, self.eng
        ax = self.ax_bar
        _bare(ax)
        th = res["theta"]
        ax.set_xlim(th[0], th[-1])
        ax.set_ylim(0, 1)
        ax.plot([th[0], th[-1]], [0.74, 0.74], color=SLATE, lw=3.0,
                solid_capstyle="butt")
        self.bar_done, = ax.plot([], [], color=ACCENT, lw=3.0,
                                 solid_capstyle="butt")
        self._bar_y = 0.74
        events = [(th[0], "IVC", INK_MUTE), (e.th_spark, "spark", GOLD),
                  (0.0, "TDC", INK_DIM), (th[-1], "EVO", INK_MUTE)]
        for lab, val, col in (("CA10", self.ca10, SERIES[0]),
                              ("CA50", self.ca50, SERIES[1]),
                              ("CA90", self.ca90, SERIES[2])):
            if val is not None:
                events.append((val, lab, col))
        if res["knock_theta"] is not None:
            events.append((res["knock_theta"], "knock", CRIT))
        # alternate the label rows so neighbouring events cannot collide
        for row, (x, lab, col) in enumerate(sorted(events)):
            lo = 0.40 if row % 2 == 0 else 0.04
            ax.plot([x, x], [lo + 0.22, 0.88], color=col, lw=1.4)
            ax.text(x, lo, lab, color=col, fontsize=7.5, ha="center",
                    va="bottom")
        self.bar_dot, = ax.plot([], [], marker="o", ms=9, color=PAPER,
                                mec=NAVY, mew=1.4)

    def _footer(self):
        self.fig.text(
            0.030, 0.006,
            "two-zone model — uniform pressure, adiabatic walls, no "
            "dissociation; the flame is the analytic circle used by "
            "burned_area()/flame_arc(); the grid is the ALE map; field values "
            "are clipped to the colour scale for display only.",
            color=INK_MUTE, fontsize=8, va="bottom")

    # --------------------------------------------------------------- draw
    def draw(self, k):
        """Push frame k into the artists. Returns everything that moved."""
        e, res = self.eng, self.res
        i = int(self.idx[k])
        th = float(res["theta"][i])
        h = float(res["V"][i]) / e.A_p
        r_f = float(res["r_f"][i])
        T_u, T_b = float(res["T_u"][i]), float(res["T_b"][i])
        R = e.B / 2.0

        # -- fields ------------------------------------------------------
        self.im_side.set_data(self._field_side(r_f, T_u, T_b))
        self.im_side.set_extent((-R, R, -h, 0.0))
        self.im_top.set_data(self._field_top(r_f, T_u, T_b))
        if self.show_mesh:
            self.mesh.set_segments(self._mesh_segments(h))

        # -- flame front, exactly the geometry the solver integrates ------
        if r_f > 0.0:
            fx, fz = [], []
            for x in (e.r_s - r_f, e.r_s + r_f):
                if -R < x < R:
                    fx += [x, x, np.nan]
                    fz += [-h, 0.0, np.nan]
            self.front_side.set_data(fx, fz)
            psi = np.linspace(0.0, 2 * np.pi, 401)
            cx, cy = e.r_s + r_f * np.cos(psi), r_f * np.sin(psi)
            inside = (cx ** 2 + cy ** 2) <= R ** 2
            self.front_top.set_data(np.where(inside, cx, np.nan),
                                    np.where(inside, cy, np.nan))
        else:
            self.front_side.set_data([], [])
            self.front_top.set_data([], [])

        d_spark = th - e.th_spark
        if 0.0 <= d_spark < 2.0:
            self.spark_glow.set_data([e.r_s], [0.0])
            self.spark_glow.set_alpha(float(1.0 - d_spark / 2.0))
        else:
            self.spark_glow.set_alpha(0.0)

        # -- piston, in both views ---------------------------------------
        z_crown, z_pin, (cpx, cpz), z_c = self._kinematics(th)
        w = R * 0.985
        self.piston.set_xy([(-w, z_crown), (w, z_crown),
                            (w, z_crown - SKIRT_H), (-w, z_crown - SKIRT_H)])
        self.rings.set_segments([
            np.column_stack([[-w, w], [z_crown - dz, z_crown - dz]])
            for dz in (0.005, 0.009, 0.013)])
        self.h_label.set_position((0.0, z_crown - SKIRT_H * 0.5))
        self.h_label.set_text(f"h = {h*1e3:.1f} mm")

        # schematic: same numbers, x and y swapped
        self.m_gas.set_bounds(z_crown, -w, -z_crown, 2 * w)
        T_mean = float(res["T"][i])
        self.m_gas.set_facecolor(CMAP_T((T_mean - 300.0)
                                        / max(self.vmax - 300.0, 1.0)))
        self.m_piston.set_xy([(z_crown, -w), (z_crown, w),
                              (z_crown - SKIRT_H, w), (z_crown - SKIRT_H, -w)])
        self.m_pin.set_center((z_pin, 0.0))
        self.m_cpin.set_center((cpz, cpx))
        self.m_rod.set_data([z_pin, cpz], [0.0, cpx])
        self.m_crank.set_data([z_c, cpz], [0.0, cpx])

        # -- traces ------------------------------------------------------
        s = slice(0, i + 1)
        self.l_p.set_data(res["theta"][s], res["p"][s] / 1e5)
        self.d_p.set_data([th], [res["p"][i] / 1e5])
        for ln, y in self.l_T:
            ln.set_data(res["theta"][s], y[s])
        self.l_x.set_data(res["theta"][s], res["x"][s])
        self.l_q.set_data(res["theta"][s], self.hrr[s] / self.hrr_max)
        self.l_pv.set_data(res["V"][s] * 1e6, res["p"][s] / 1e5)
        self.d_pv.set_data([res["V"][i] * 1e6], [res["p"][i] / 1e5])
        self.bar_done.set_data([res["theta"][0], th],
                               [self._bar_y, self._bar_y])
        self.bar_dot.set_data([th], [self._bar_y])

        # -- readout -----------------------------------------------------
        slow = (self.n_frames / self.fps) / max(self.cycle_ms * 1e-3, 1e-12)
        stage = ("compression" if th < e.th_spark else
                 "burning" if res["x"][i] < 0.999 else "expansion")
        T_b_show = min(T_b, self.vmax) if res["x"][i] > 0.0 else float("nan")
        self.hud.set_text(
            f"crank      {th:+8.1f}° ATDC\n"
            f"time       {self.t_ms[i]:8.2f} ms\n"
            f"phase      {stage:>12s}\n"
            f"pressure   {res['p'][i]/1e5:8.2f} bar\n"
            f"T unburned {T_u:8.0f} K\n"
            f"T burned   {T_b_show:8.0f} K\n"
            f"burned     {res['x'][i]*100:8.1f} %\n"
            f"flame r_f  {r_f*1e3:8.1f} mm\n"
            f"S_L / S_T  {res['S_L'][i]:.2f} / {res['S_T'][i]:.2f} m/s\n"
            f"work/V_d   {self.imep_run[i]/1e5:8.2f} bar\n"
            f"slow motion{slow:8.0f} ×")

        ki = float(res["knock"][i])
        col = CRIT if ki >= 1.0 else WARN if ki >= 0.6 else GOOD
        lab = "KNOCK" if ki >= 1.0 else "MARGINAL" if ki >= 0.6 else "SAFE"
        self.knock_bar.set_width(0.46 * min(ki, 1.0))
        self.knock_bar.set_facecolor(col)
        self.knock_txt.set_text(f"knock {ki:4.2f} {lab}")
        self.knock_txt.set_color(col)
        knocking = ki >= 1.0 and r_f > 0.0
        self.endgas.set_alpha(0.85 if knocking else 0.0)
        self.knock_banner.set_alpha(1.0 if knocking else 0.0)
        if knocking:
            self.endgas.set_data(*self.front_top.get_data())

        if self._hook is not None:
            self._hook(k)

        return [self.im_side, self.im_top, self.mesh, self.front_side,
                self.front_top, self.spark_glow, self.piston, self.rings,
                self.h_label, self.m_gas, self.m_piston, self.m_pin,
                self.m_cpin, self.m_rod, self.m_crank,
                self.l_p, self.d_p, self.l_x, self.l_q, self.l_pv, self.d_pv,
                self.bar_done, self.bar_dot, self.hud, self.knock_bar,
                self.knock_txt, self.endgas, self.knock_banner
                ] + [ln for ln, _ in self.l_T]

    # ------------------------------------------------------------ drivers
    def make_animation(self, fps=30, blit=True):
        self.fps = fps
        return FuncAnimation(self.fig, self.draw, frames=self.n_frames,
                             interval=1000.0 / fps, blit=blit, repeat=True)

    def save(self, path, fps=30, dpi=None):
        self.fps = fps
        ani = self.make_animation(fps=fps, blit=False)
        ext = os.path.splitext(path)[1].lower()
        if ext in (".mp4", ".mov", ".mkv"):
            exe = _resolve_ffmpeg()
            if exe is None:
                path = os.path.splitext(path)[0] + ".gif"
                ext = ".gif"
                print("  ffmpeg not found -> falling back to", path)
            else:
                matplotlib.rcParams["animation.ffmpeg_path"] = exe
        if ext == ".gif":
            writer = PillowWriter(fps=fps)
        else:
            writer = FFMpegWriter(fps=fps, bitrate=-1, codec="libx264",
                                  extra_args=["-pix_fmt", "yuv420p",
                                              "-preset", "medium", "-crf", "20"])
        n = self.n_frames
        ani.save(path, writer=writer, dpi=dpi or self.fig.dpi,
                 savefig_kwargs={"facecolor": NAVY},
                 progress_callback=lambda i, _n: (
                     print(f"\r  frame {i+1}/{n}", end="", flush=True)))
        print()
        return path

    def show(self, fps=30):
        """Interactive playback: scrub bar, space to pause, arrows to step."""
        from matplotlib.widgets import Slider
        self.fps = fps
        ani = self.make_animation(fps=fps, blit=False)
        sax = self.fig.add_axes([0.20, 0.005, 0.60, 0.020], facecolor="#1B2740")
        slider = Slider(sax, "", 0, self.n_frames - 1, valinit=0, valstep=1,
                        color=ACCENT, initcolor="none")
        slider.valtext.set_visible(False)
        slider.label.set_color(INK_MUTE)
        state = {"running": True, "k": 0, "guard": False}

        def on_slide(val):
            if state["guard"]:
                return
            ani.event_source.stop()
            state["running"] = False
            state["k"] = int(val)
            self.draw(state["k"])
            self.fig.canvas.draw_idle()

        slider.on_changed(on_slide)

        def follow(k):
            state["k"] = k
            state["guard"] = True
            slider.set_val(k)
            state["guard"] = False

        self._hook = follow

        def on_key(ev):
            if ev.key == " ":
                if state["running"]:
                    ani.event_source.stop()
                else:
                    ani.event_source.start()
                state["running"] = not state["running"]
            elif ev.key in ("left", "right"):
                ani.event_source.stop()
                state["running"] = False
                step = 1 if ev.key == "right" else -1
                state["k"] = (state["k"] + step) % self.n_frames
                on_slide(state["k"])
            elif ev.key == "r":
                state["k"] = 0
                on_slide(0)
                ani.event_source.start()
                state["running"] = True

        self.fig.canvas.mpl_connect("key_press_event", on_key)
        self.fig.text(0.035, 0.022, "space pause · ←→ step "
                      "· r restart", color=INK_MUTE, fontsize=8)
        plt.show()
        return ani


# ================================================================= VTK out
def export_vtk(eng: ec.Engine, res, outdir, n_frames=60, nx=48, ny=48, nz=24):
    """Write a .vts time series + .pvd collection.

    This is the same reconstruction the animation draws, on a real 3D grid, so
    the cycle can be replayed and probed in ParaView, Tecplot or EnSight rather
    than only in matplotlib. The grid deforms with the piston -- that is the
    moving mesh, written out honestly instead of faked with a clip plane.
    """
    os.makedirs(outdir, exist_ok=True)
    R = eng.B / 2.0
    vmax = _display_ceiling(res)
    idx = np.unique(np.linspace(0, res["theta"].size - 1, n_frames).astype(int))

    g = np.linspace(-R, R, nx)
    X, Y = np.meshgrid(g, g, indexing="ij")           # (nx, ny)
    rho = np.hypot(X - eng.r_s, Y)
    in_bore = (X ** 2 + Y ** 2) <= R ** 2
    eta = np.linspace(0.0, 1.0, nz)

    files = []
    for f, i in enumerate(idx):
        h = float(res["V"][i]) / eng.A_p
        r_f = float(res["r_f"][i])
        T_u, T_b = float(res["T_u"][i]), min(float(res["T_b"][i]), vmax)

        c2 = 0.5 * (1.0 - np.tanh((rho - r_f) / FLAME_THICK)) if r_f > 0 \
            else np.zeros_like(rho)
        T2 = T_u + (T_b - T_u) * c2

        # VTK structured grid wants i fastest, then j, then k
        pts = np.empty((nz, ny, nx, 3), dtype=np.float32)
        pts[..., 0] = X.T[None, :, :]
        pts[..., 1] = Y.T[None, :, :]
        pts[..., 2] = (-h * eta)[:, None, None]
        c3 = np.broadcast_to(c2.T[None, :, :], (nz, ny, nx))
        T3 = np.broadcast_to(T2.T[None, :, :], (nz, ny, nx))
        m3 = np.broadcast_to(in_bore.T[None, :, :], (nz, ny, nx))

        name = f"cycle_{f:04d}.vts"
        with open(os.path.join(outdir, name), "w") as fh:
            ext = f"0 {nx-1} 0 {ny-1} 0 {nz-1}"
            fh.write('<?xml version="1.0"?>\n'
                     '<VTKFile type="StructuredGrid" version="0.1" '
                     'byte_order="LittleEndian">\n'
                     f'  <StructuredGrid WholeExtent="{ext}">\n'
                     f'    <Piece Extent="{ext}">\n'
                     '      <Points>\n'
                     '        <DataArray type="Float32" NumberOfComponents="3" '
                     'format="ascii">\n')
            np.savetxt(fh, pts.reshape(-1, 3), fmt="%.6g")
            fh.write('        </DataArray>\n      </Points>\n'
                     '      <PointData Scalars="temperature">\n')
            for arr, aname, dtype, fmt in ((T3, "temperature", "Float32", "%.4g"),
                                          (c3, "progress", "Float32", "%.4g"),
                                          (m3, "in_bore", "Int8", "%d")):
                fh.write(f'        <DataArray type="{dtype}" Name="{aname}" '
                         'format="ascii">\n')
                np.savetxt(fh, np.ascontiguousarray(arr).reshape(1, -1), fmt=fmt)
                fh.write('        </DataArray>\n')
            fh.write('      </PointData>\n    </Piece>\n'
                     '  </StructuredGrid>\n</VTKFile>\n')
        files.append((float(res["theta"][i]), name))

    with open(os.path.join(outdir, "cycle.pvd"), "w") as fh:
        fh.write('<?xml version="1.0"?>\n<VTKFile type="Collection" '
                 'version="0.1" byte_order="LittleEndian">\n  <Collection>\n')
        for t, name in files:
            fh.write(f'    <DataSet timestep="{t:.4f}" part="0" '
                     f'file="{name}"/>\n')
        fh.write('  </Collection>\n</VTKFile>\n')
    return os.path.join(outdir, "cycle.pvd"), len(files)


# ============================================================ verification
def verify_kinematics(eng: ec.Engine, anim: CycleAnimator, n=721):
    """The drawn conrod must be exactly `l` long at every crank angle.

    If the picture and the solver ever disagreed about where the piston is,
    this is where it would show up -- the rod would stretch.
    """
    err = 0.0
    for th in np.linspace(-180.0, 180.0, n):
        _, z_pin, (cpx, cpz), _ = anim._kinematics(th)
        err = max(err, abs(np.hypot(cpx - 0.0, cpz - z_pin) - eng.l))
    return err


def verify_flame_geometry(eng: ec.Engine, res):
    """The drawn burned area must reproduce the burned volume the solver used."""
    R = eng.B / 2.0
    n = 1200
    g = np.linspace(-R, R, n)
    X, Y = np.meshgrid(g, g)
    rho = np.hypot(X - eng.r_s, Y)
    in_bore = (X ** 2 + Y ** 2) <= R ** 2
    cell = (2 * R / (n - 1)) ** 2

    worst = 0.0
    m = np.where(res["x"] > 0.02)[0]
    for i in m[:: max(1, m.size // 120)]:
        r_f = float(res["r_f"][i])
        A_exact = ec.burned_area(r_f, R, eng.r_s)
        A_num = np.count_nonzero((rho <= r_f) & in_bore) * cell
        worst = max(worst, abs(A_num - A_exact) / max(A_exact, 1e-12))
    return worst


# ==================================================================== main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--save", default="engine_combust.mp4",
                    help="output file (.mp4 or .gif); '' to skip writing")
    ap.add_argument("--interactive", action="store_true",
                    help="open a scrubable window instead of writing a file")
    ap.add_argument("--frames", type=int, default=480)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--field", choices=("T", "c"), default="T",
                    help="temperature field or progress variable")
    ap.add_argument("--no-mesh", action="store_true",
                    help="hide the ALE grid overlay")
    ap.add_argument("--dtheta", type=float, default=0.05)
    ap.add_argument("--rpm", type=float, default=None)
    ap.add_argument("--spark", type=float, default=None)
    ap.add_argument("--phi", type=float, default=None)
    ap.add_argument("--octane", type=float, default=None)
    ap.add_argument("--vtk", default=None, metavar="DIR",
                    help="also write a .vts/.pvd time series for ParaView")
    ap.add_argument("--vtk-frames", type=int, default=60)
    ap.add_argument("--verify", action="store_true",
                    help="check the drawing against the solver and exit")
    args = ap.parse_args(argv)

    kw = {}
    if args.rpm is not None:
        kw["rpm"] = args.rpm
    if args.spark is not None:
        kw["theta_spark"] = args.spark
    if args.phi is not None:
        kw["phi"] = args.phi
    if args.octane is not None:
        kw["octane"] = args.octane
    eng = ec.Engine(**kw)

    print("solving the cycle ...")
    res = ec.simulate(eng, dtheta=args.dtheta)
    print(f"  p_max {res['p'].max()/1e5:.2f} bar   "
          f"IMEP {ec.imep(res, eng)/1e5:.2f} bar   "
          f"CA50 {_ca(res, 0.5)}   knock {res['knock_int']:.2f}")

    if args.interactive:
        for backend in ("QtAgg", "TkAgg", "MacOSX"):
            try:
                matplotlib.use(backend, force=True)
                break
            except Exception:
                continue

    anim = CycleAnimator(eng, res, n_frames=args.frames, field=args.field,
                         show_mesh=not args.no_mesh, dpi=args.dpi)

    if args.verify:
        print("\nDRAWING vs SOLVER")
        print(f"  conrod length error   = {verify_kinematics(eng, anim):.3e} m")
        print(f"  burned-area agreement = {verify_flame_geometry(eng, res):.3e}"
              "  (relative, vs the analytic lens)")
        return 0

    if args.vtk:
        print("writing VTK time series ...")
        pvd, n = export_vtk(eng, res, args.vtk, n_frames=args.vtk_frames)
        print(f"  {n} steps -> {pvd}")

    if args.interactive:
        anim.show(fps=args.fps)
    elif args.save:
        print(f"rendering {anim.n_frames} frames ...")
        out = anim.save(args.save, fps=args.fps, dpi=args.dpi)
        print(f"  wrote {out}  "
              f"({anim.n_frames/args.fps:.1f} s at {args.fps} fps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
