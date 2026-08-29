"""
ale1d_viz.py  --  moving-mesh visual layer for ale1d.py

Runs the free-stream test TWICE on an identical fixed time step -- once with the
GCL satisfied, once violated -- so the two runs stay frame-synchronised and the
only difference on screen is the grid-velocity definition.

Outputs
-------
  ale_freestream.mp4    side-by-side moving mesh + density, brand palette
  ale_snapshots.npz     baked arrays for the Manim cold open (S00_ColdOpen)

Arrays in the .npz (F = number of frames, N = cells):
  t        (F,)          frame times
  x_gcl    (F, N+1)      node positions      -- identical in both runs
  rho_gcl  (F, N)        density, GCL satisfied
  rho_bad  (F, N)        density, GCL violated
  u_bad    (F, N)        spurious velocity, GCL violated
  p_bad    (F, N)        pressure, GCL violated
  err_gcl  (F,)          max|rho-1| running
  err_bad  (F,)          max|rho-1| running

Run:  python3 ale1d_viz.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.animation import FuncAnimation, FFMpegWriter

import os
import ale1d as ale

# ---------------------------------------------------------------- brand
NAVY, TEAL, GOLD, CORAL = "#0B1221", "#2DD4BF", "#F5B642", "#FF6F61"
SLATE, PAPER = "#334155", "#E2E8F0"
CMAP = LinearSegmentedColormap.from_list("gcl", [TEAL, SLATE, CORAL])

# ---------------------------------------------------------------- config
N       = int(os.environ.get("ALE_N", 60))
T_END   = 2.0
A       = 0.05      # mesh oscillation amplitude
F_MESH  = 1.0       # mesh oscillation frequency
CFL     = 0.4
RHO0, U0, P0 = 1.0, 1.0, 1.0
N_FRAMES = 150
DEV_SCALE = 3.0e-3  # colour saturation for |rho - 1|


def fixed_dt():
    """One dt for both runs -> frames line up exactly, comparison is honest."""
    dx_min = (1.0 - 2 * np.pi * A) / N
    a0 = np.sqrt(ale.GAMMA * P0 / RHO0)
    xdot_max = 2 * np.pi * A * F_MESH
    return CFL * dx_min / (abs(U0) + a0 + xdot_max)


def run(gcl, dt, n_steps, frame_steps):
    X = np.linspace(0.0, 1.0, N + 1)
    t = 0.0
    x = ale.mesh_positions(X, t, A, F_MESH)
    V = np.diff(x)
    U = ale.prim2cons(np.full(N, RHO0), np.full(N, U0), np.full(N, P0))

    snaps = {"t": [], "x": [], "rho": [], "u": [], "p": [], "err": []}

    def record(tt, xx, UU):
        rho, u, p = ale.cons2prim(UU)
        snaps["t"].append(tt)
        snaps["x"].append(xx.copy())
        snaps["rho"].append(rho.copy())
        snaps["u"].append(u.copy())
        snaps["p"].append(p.copy())
        snaps["err"].append(np.abs(rho - RHO0).max())

    record(t, x, U)

    for step in range(1, n_steps + 1):
        x_new = ale.mesh_positions(X, t + dt, A, F_MESH)
        V_new = np.diff(x_new)

        if gcl:
            xdot = (x_new - x) / dt                          # swept volume / dt
        else:
            xdot = ale.mesh_velocity_analytic(X, t, A, F_MESH)  # analytic dx/dt

        UL = np.hstack([U[:, -1:], U])
        UR = np.hstack([U, U[:, :1]])
        Fh = ale.rusanov_ale(UL, UR, xdot)

        U = (V * U - dt * (Fh[:, 1:] - Fh[:, :-1])) / V_new
        x, V, t = x_new, V_new, t + dt

        if step in frame_steps:
            record(t, x, U)

    return {k: np.array(v) for k, v in snaps.items()}


def strip(ax, x, rho, label, badge, badge_col):
    """Draw one moving-mesh strip: cells filled by density, node lines on top."""
    ax.set_facecolor(NAVY)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xticks([])
    for s in ax.spines.values():
        s.set_color(SLATE)
    norm = TwoSlopeNorm(vmin=1 - DEV_SCALE, vcenter=1.0, vmax=1 + DEV_SCALE)
    quads = ax.bar(x[:-1], height=1.0, width=np.diff(x), align="edge",
                   color=CMAP(norm(rho)), linewidth=0)
    lines = [ax.axvline(xi, color=PAPER, lw=0.6, alpha=0.55) for xi in x]
    ax.text(0.012, 0.87, label, transform=ax.transAxes, color=PAPER,
            fontsize=10.5, fontweight="bold", family="monospace")
    txt = ax.text(0.988, 0.87, badge, transform=ax.transAxes, color=badge_col,
                  fontsize=10.5, ha="right", family="monospace")
    return quads, lines, txt, norm


def main():
    dt = fixed_dt()
    n_steps = int(np.ceil(T_END / dt))
    dt = T_END / n_steps
    frame_steps = set(np.unique(np.linspace(1, n_steps, N_FRAMES).astype(int)))
    print(f"dt = {dt:.3e}   steps = {n_steps}   frames = {len(frame_steps)+1}")

    good = run(True,  dt, n_steps, frame_steps)
    bad  = run(False, dt, n_steps, frame_steps)

    np.savez_compressed(
        "ale_snapshots.npz",
        t=good["t"], x_gcl=good["x"],
        rho_gcl=good["rho"], rho_bad=bad["rho"],
        u_bad=bad["u"], p_bad=bad["p"],
        err_gcl=good["err"], err_bad=bad["err"])
    print("wrote ale_snapshots.npz")

    # ------------------------------------------------------------ figure
    fig = plt.figure(figsize=(11, 7.2), facecolor=NAVY)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 1.35],
                          hspace=0.28, left=0.075, right=0.975,
                          top=0.885, bottom=0.085)
    axG, axB, axP = (fig.add_subplot(gs[i]) for i in range(3))

    fig.suptitle("Uniform flow.  The mesh moves.  Nothing else should.",
                 color=PAPER, fontsize=15, fontweight="bold", y=0.965)

    qG, lG, tG, norm = strip(axG, good["x"][0], good["rho"][0],
                             "GCL SATISFIED   xdot = (x^{n+1}-x^n)/dt", "", TEAL)
    qB, lB, tB, _    = strip(axB, bad["x"][0],  bad["rho"][0],
                             "GCL VIOLATED    xdot = analytic dx/dt", "", CORAL)

    axP.set_facecolor(NAVY)
    axP.set_xlim(0, 1)
    axP.set_ylim(1 - 3.4e-3, 1 + 3.4e-3)
    axP.axhline(1.0, color=SLATE, lw=1.0, ls="--")
    axP.tick_params(colors=PAPER, labelsize=9)
    for s in axP.spines.values():
        s.set_color(SLATE)
    axP.set_xlabel("x", color=PAPER, fontsize=10)
    axP.set_ylabel(r"density  $\rho$", color=PAPER, fontsize=10)

    xc0 = 0.5 * (good["x"][0][:-1] + good["x"][0][1:])
    (pG,) = axP.plot(xc0, good["rho"][0], color=TEAL,  lw=2.0, label="GCL satisfied")
    (pB,) = axP.plot(xc0, bad["rho"][0],  color=CORAL, lw=2.0, label="GCL violated")
    leg = axP.legend(loc="upper right", facecolor=NAVY, edgecolor=SLATE,
                     labelcolor=PAPER, fontsize=9)
    clock = axP.text(0.012, 0.055, "", transform=axP.transAxes, color=GOLD,
                     fontsize=10, family="monospace")
    mass = axP.text(0.012, 0.90, "", transform=axP.transAxes, color=PAPER,
                    fontsize=9.5, family="monospace")

    def update(i):
        x, rg, rb = good["x"][i], good["rho"][i], bad["rho"][i]
        w = np.diff(x)
        for k, patch in enumerate(qG):
            patch.set_x(x[k]); patch.set_width(w[k])
            patch.set_color(CMAP(norm(rg[k])))
        for k, patch in enumerate(qB):
            patch.set_x(x[k]); patch.set_width(w[k])
            patch.set_color(CMAP(norm(rb[k])))
        for ln, xi in zip(lG, x):
            ln.set_xdata([xi, xi])
        for ln, xi in zip(lB, x):
            ln.set_xdata([xi, xi])

        tG.set_text(f"max|rho-1| = {good['err'][i]:.2e}")
        tB.set_text(f"max|rho-1| = {bad['err'][i]:.2e}")

        xc = 0.5 * (x[:-1] + x[1:])
        pG.set_data(xc, rg)
        pB.set_data(xc, rb)
        clock.set_text(f"t = {good['t'][i]:5.3f}   mesh periods = {good['t'][i]*F_MESH:4.2f}")
        mG = np.sum(rg * w); mB = np.sum(rb * w)
        mass.set_text(f"total mass drift:  GCL {mG/1.0-1:+.1e}    violated {mB/1.0-1:+.1e}"
                      "     <- both conserved")
        return []

    n = len(good["t"])
    anim = FuncAnimation(fig, update, frames=n, interval=50, blit=False)
    writer = FFMpegWriter(fps=25, bitrate=3200,
                          metadata={"title": "ALE free-stream preservation"})
    anim.save("ale_freestream.mp4", writer=writer, dpi=130,
              savefig_kwargs={"facecolor": NAVY})
    print("wrote ale_freestream.mp4")

    print(f"\nfinal  GCL satisfied  max|rho-1| = {good['err'][-1]:.3e}")
    print(f"final  GCL violated   max|rho-1| = {bad['err'][-1]:.3e}")


if __name__ == "__main__":
    main()
