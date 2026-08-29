"""
ale_piston_viz.py  --  moving-boundary animation: piston compressing a gas.

This is the case that *looks* like a moving mesh: the domain itself shrinks,
cells compress, and the solution is verified live against isentropic p*V^gamma.

Outputs
-------
  ale_piston.mp4        shrinking mesh + density field + live p-V curve
  ale_piston.npz        baked arrays for Manim (S11_Piston)

Run:  python3 ale_piston_viz.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.animation import FuncAnimation, FFMpegWriter

import os
import ale1d as ale

NAVY, TEAL, GOLD, CORAL = "#0B1221", "#2DD4BF", "#F5B642", "#FF6F61"
SLATE, PAPER = "#334155", "#E2E8F0"
CMAP = LinearSegmentedColormap.from_list("rho", [NAVY, TEAL, GOLD, CORAL])

N        = int(os.environ.get("ALE_N", 120))   # ALE_N=40 for video clarity
L0       = 1.0
STROKE   = 0.5          # -> compression ratio 2.0
OMEGA    = 0.5
CFL      = 0.4
RHO0, P0 = 1.0, 1.0
N_FRAMES = 160


def L(t):
    return L0 - 0.5 * STROKE * (1.0 - np.cos(OMEGA * t))


def Ldot(t):
    return -0.5 * STROKE * OMEGA * np.sin(OMEGA * t)


def simulate():
    t_end = np.pi / OMEGA
    frame_times = np.linspace(0.0, t_end, N_FRAMES)

    Xi = np.linspace(0.0, 1.0, N + 1)
    t = 0.0
    x = Xi * L(t)
    V = np.diff(x)
    U = ale.prim2cons(np.full(N, RHO0), np.zeros(N), np.full(N, P0))

    snaps = {"t": [], "x": [], "rho": [], "u": [], "p": [], "V": [], "pm": []}

    def record(tt, xx, UU, VV):
        rho, u, p = ale.cons2prim(UU)
        snaps["t"].append(tt)
        snaps["x"].append(xx.copy())
        snaps["rho"].append(rho.copy())
        snaps["u"].append(u.copy())
        snaps["p"].append(p.copy())
        snaps["V"].append(VV.sum())
        snaps["pm"].append(np.sum(p * VV) / VV.sum())

    record(t, x, U, V)
    nxt = 1

    while nxt < N_FRAMES:
        rho, u, p = ale.cons2prim(U)
        a = np.sqrt(ale.GAMMA * p / rho)
        dt = CFL * V.min() / (np.abs(u).max() + a.max() + abs(Ldot(t)) + 1e-30)
        dt = min(dt, frame_times[nxt] - t)

        x_new = Xi * L(t + dt)
        V_new = np.diff(x_new)
        xdot = (x_new - x) / dt                 # GCL-consistent by construction

        rl, ul, pl = rho[0],  2 * xdot[0]  - u[0],  p[0]
        rr, ur, pr = rho[-1], 2 * xdot[-1] - u[-1], p[-1]
        UL = np.hstack([ale.prim2cons(np.array([rl]), np.array([ul]), np.array([pl])), U])
        UR = np.hstack([U, ale.prim2cons(np.array([rr]), np.array([ur]), np.array([pr]))])

        Fh = ale.rusanov_ale(UL, UR, xdot)
        U = (V * U - dt * (Fh[:, 1:] - Fh[:, :-1])) / V_new
        x, V, t = x_new, V_new, t + dt

        if t >= frame_times[nxt] - 1e-12:
            record(t, x, U, V)
            nxt += 1

    return {k: (np.array(v) if k != "x" else np.array(v)) for k, v in snaps.items()}


def main():
    s = simulate()
    np.savez_compressed("ale_piston.npz", **s)
    print("wrote ale_piston.npz")

    Vs = s["V"]
    p_isen = P0 * (L0 / Vs) ** ale.GAMMA
    rel = np.abs(s["pm"] - p_isen) / p_isen

    fig = plt.figure(figsize=(11, 6.6), facecolor=NAVY)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0],
                          width_ratios=[1.35, 1.0], hspace=0.34, wspace=0.24,
                          left=0.07, right=0.965, top=0.87, bottom=0.11)
    axM = fig.add_subplot(gs[0, :])
    axPV = fig.add_subplot(gs[1, 0])
    axE = fig.add_subplot(gs[1, 1])

    fig.suptitle("Moving boundary: the mesh compresses with the gas",
                 color=PAPER, fontsize=15, fontweight="bold", y=0.955)

    # ---- mesh strip
    axM.set_facecolor(NAVY)
    axM.set_xlim(-0.03, 1.05); axM.set_ylim(0, 1)
    axM.set_yticks([]); axM.tick_params(colors=PAPER, labelsize=9)
    for sp in axM.spines.values():
        sp.set_color(SLATE)
    norm = Normalize(vmin=1.0, vmax=2.05)
    x0, r0 = s["x"][0], s["rho"][0]
    quads = axM.bar(x0[:-1], 1.0, width=np.diff(x0), align="edge",
                    color=CMAP(norm(r0)), linewidth=0)
    lines = [axM.axvline(xi, color=PAPER, lw=(0.5 if N > 60 else 1.0), alpha=(0.45 if N > 60 else 0.75)) for xi in x0]
    piston = axM.axvline(x0[-1], color=GOLD, lw=4.0)
    head = axM.text(0.5, 1.07, "", transform=axM.transAxes, color=PAPER,
                    fontsize=10.5, ha="center", family="monospace")

    # ---- p-V diagram
    axPV.set_facecolor(NAVY)
    axPV.set_xlim(0.45, 1.03); axPV.set_ylim(0.85, 2.85)
    axPV.tick_params(colors=PAPER, labelsize=9)
    for sp in axPV.spines.values():
        sp.set_color(SLATE)
    axPV.set_xlabel("volume  V", color=PAPER, fontsize=10)
    axPV.set_ylabel("pressure  p", color=PAPER, fontsize=10)
    Vg = np.linspace(0.5, 1.0, 200)
    axPV.plot(Vg, P0 * (L0 / Vg) ** ale.GAMMA, color=SLATE, lw=3.0,
              label=r"isentropic  $pV^{\gamma}$")
    (pv,) = axPV.plot([], [], color=TEAL, lw=2.0, label="ALE solver")
    (pvdot,) = axPV.plot([], [], "o", color=CORAL, ms=6)
    axPV.legend(loc="upper left", facecolor=NAVY, edgecolor=SLATE,
                labelcolor=PAPER, fontsize=9)

    # ---- error trace
    axE.set_facecolor(NAVY)
    axE.set_xlim(1.0, 2.05); axE.set_ylim(0, 0.045)
    axE.tick_params(colors=PAPER, labelsize=9)
    for sp in axE.spines.values():
        sp.set_color(SLATE)
    axE.set_xlabel("compression ratio", color=PAPER, fontsize=10)
    axE.set_ylabel("error vs isentropic  [%]", color=PAPER, fontsize=10)
    (er,) = axE.plot([], [], color=GOLD, lw=2.0)
    ertxt = axE.text(0.05, 0.86, "", transform=axE.transAxes, color=GOLD,
                     fontsize=10, family="monospace")

    def update(i):
        x, r = s["x"][i], s["rho"][i]
        w = np.diff(x)
        for k, patch in enumerate(quads):
            patch.set_x(x[k]); patch.set_width(w[k])
            patch.set_color(CMAP(norm(r[k])))
        for ln, xi in zip(lines, x):
            ln.set_xdata([xi, xi])
        piston.set_xdata([x[-1], x[-1]])
        head.set_text(f"t = {s['t'][i]:5.2f}     CR = {L0/Vs[i]:4.2f}"
                      f"     mean p = {s['pm'][i]:5.3f}")
        pv.set_data(Vs[:i + 1], s["pm"][:i + 1])
        pvdot.set_data([Vs[i]], [s["pm"][i]])
        cr = L0 / Vs[:i + 1]
        er.set_data(cr, rel[:i + 1] * 100)
        ertxt.set_text(f"error = {rel[i]*100:.4f} %")
        return []

    anim = FuncAnimation(fig, update, frames=len(s["t"]), interval=45, blit=False)
    anim.save("ale_piston.mp4", writer=FFMpegWriter(fps=24, bitrate=3200),
              dpi=130, savefig_kwargs={"facecolor": NAVY})
    print("wrote ale_piston.mp4")
    print(f"final CR = {L0/Vs[-1]:.3f}   solver p = {s['pm'][-1]:.6f}"
          f"   isentropic = {p_isen[-1]:.6f}   error = {rel[-1]*100:.4f} %")


if __name__ == "__main__":
    main()
