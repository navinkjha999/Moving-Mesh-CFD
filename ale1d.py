"""
ale1d.py  --  1D Arbitrary Lagrangian-Eulerian finite volume solver (Euler equations)

Purpose: demonstrate the Geometric Conservation Law (GCL / Space Conservation Law).

Two experiments:
  A) FREE-STREAM PRESERVATION.  Uniform flow, mesh wiggles internally, boundaries
     periodic.  Exact answer: nothing happens, forever.
       - grid velocity from DISCRETE node displacement  -> GCL satisfied -> exact
       - grid velocity from ANALYTIC dx/dt at t^n       -> GCL violated  -> garbage
     The counter-intuitive part: the *more accurate* grid velocity is the wrong one.

  B) PISTON COMPRESSION.  Moving wall, verify against isentropic p*V^gamma = const.

Run:  python3 ale1d.py
"""

import numpy as np

GAMMA = 1.4


# ----------------------------------------------------------------------
# state conversions
# ----------------------------------------------------------------------
def prim2cons(rho, u, p):
    E = p / (GAMMA - 1.0) + 0.5 * rho * u * u
    return np.vstack([rho, rho * u, E])


def cons2prim(U):
    rho = U[0]
    u = U[1] / rho
    p = (GAMMA - 1.0) * (U[2] - 0.5 * rho * u * u)
    return rho, u, p


def flux(U):
    rho, u, p = cons2prim(U)
    return np.vstack([rho * u, rho * u * u + p, u * (U[2] + p)])


# ----------------------------------------------------------------------
# ALE Rusanov flux.  xdot = grid velocity at the face.
#   F_ALE = F(U) - xdot * U   (relative-velocity form of the RTT)
# ----------------------------------------------------------------------
def rusanov_ale(UL, UR, xdot):
    rL, uL, pL = cons2prim(UL)
    rR, uR, pR = cons2prim(UR)
    aL = np.sqrt(GAMMA * pL / rL)
    aR = np.sqrt(GAMMA * pR / rR)
    s = np.maximum(np.abs(uL - xdot) + aL, np.abs(uR - xdot) + aR)
    FL = flux(UL) - xdot * UL
    FR = flux(UR) - xdot * UR
    return 0.5 * (FL + FR) - 0.5 * s * (UR - UL)


# ======================================================================
# EXPERIMENT A : free-stream preservation
# ======================================================================
def mesh_positions(X, t, A=0.05, f=1.0):
    """Interior nodes swim; the pattern is periodic in X so BCs stay periodic."""
    return X + A * np.sin(2 * np.pi * X) * np.sin(2 * np.pi * f * t)


def mesh_velocity_analytic(X, t, A=0.05, f=1.0):
    """dx/dt evaluated exactly at time t -- the 'obvious' choice."""
    return A * np.sin(2 * np.pi * X) * (2 * np.pi * f) * np.cos(2 * np.pi * f * t)


def free_stream_test(gcl=True, N=60, t_end=2.0, cfl=0.4,
                     rho0=1.0, u0=1.0, p0=1.0, A=0.05, f=1.0):
    X = np.linspace(0.0, 1.0, N + 1)          # reference node coords
    t = 0.0
    x = mesh_positions(X, t, A, f)
    V = np.diff(x)                             # cell volumes (lengths)

    U = prim2cons(np.full(N, rho0), np.full(N, u0), np.full(N, p0))
    worst = 0.0
    history = []

    while t < t_end - 1e-14:
        rho, u, p = cons2prim(U)
        a = np.sqrt(GAMMA * p / rho)
        xd_est = np.abs(mesh_velocity_analytic(X, t, A, f)).max()
        dt = cfl * V.min() / (np.abs(u).max() + a.max() + xd_est + 1e-30)
        dt = min(dt, t_end - t)

        x_new = mesh_positions(X, t + dt, A, f)
        V_new = np.diff(x_new)

        if gcl:
            # grid velocity DEFINED by the swept volume: xdot = (x^{n+1}-x^n)/dt
            xdot = (x_new - x) / dt
        else:
            # grid velocity from the analytic motion law at t^n
            xdot = mesh_velocity_analytic(X, t, A, f)

        # periodic halo
        UL = np.hstack([U[:, -1:], U])         # left state of each of N+1 faces
        UR = np.hstack([U, U[:, :1]])
        Fh = rusanov_ale(UL, UR, xdot)

        U = (V * U - dt * (Fh[:, 1:] - Fh[:, :-1])) / V_new

        x, V, t = x_new, V_new, t + dt
        err = np.abs(cons2prim(U)[0] - rho0).max()
        worst = max(worst, err)
        history.append((t, err))

    return worst, history


# ======================================================================
# EXPERIMENT B : piston compression, verified against p*V^gamma
# ======================================================================
def piston(N=200, L0=1.0, stroke=0.5, omega=0.5, t_end=None, cfl=0.4,
           rho0=1.0, p0=1.0):
    """Right wall sweeps in.  Slow enough to stay near-isentropic."""
    if t_end is None:
        t_end = np.pi / omega                  # half a cycle -> full compression

    def L(t):
        return L0 - 0.5 * stroke * (1.0 - np.cos(omega * t))

    def Ldot(t):
        return -0.5 * stroke * omega * np.sin(omega * t)

    Xi = np.linspace(0.0, 1.0, N + 1)          # normalised node coords
    t = 0.0
    x = Xi * L(t)
    V = np.diff(x)
    U = prim2cons(np.full(N, rho0), np.zeros(N), np.full(N, p0))

    pV0 = p0 * L0 ** GAMMA

    while t < t_end - 1e-14:
        rho, u, p = cons2prim(U)
        a = np.sqrt(GAMMA * p / rho)
        dt = cfl * V.min() / (np.abs(u).max() + a.max() + abs(Ldot(t)) + 1e-30)
        dt = min(dt, t_end - t)

        x_new = Xi * L(t + dt)
        V_new = np.diff(x_new)
        xdot = (x_new - x) / dt                # GCL-consistent by construction

        # moving-wall ghosts: u_ghost = 2*xdot_wall - u_interior
        rl, ul, pl = rho[0], 2 * xdot[0] - u[0], p[0]
        rr, ur, pr = rho[-1], 2 * xdot[-1] - u[-1], p[-1]
        UL = np.hstack([prim2cons(np.array([rl]), np.array([ul]), np.array([pl])), U])
        UR = np.hstack([U, prim2cons(np.array([rr]), np.array([ur]), np.array([pr]))])

        Fh = rusanov_ale(UL, UR, xdot)
        U = (V * U - dt * (Fh[:, 1:] - Fh[:, :-1])) / V_new
        x, V, t = x_new, V_new, t + dt

    rho, u, p = cons2prim(U)
    Lf = L(t_end)
    p_mean = np.sum(p * V) / np.sum(V)
    p_isen = p0 * (L0 / Lf) ** GAMMA
    return Lf, p_mean, p_isen, abs(p_mean - p_isen) / p_isen, pV0


# ======================================================================
if __name__ == "__main__":
    print("=" * 66)
    print("EXPERIMENT A -- free-stream preservation (uniform flow, wiggling mesh)")
    print("=" * 66)
    for gcl in (True, False):
        err, _ = free_stream_test(gcl=gcl)
        tag = "GCL SATISFIED (xdot = swept volume / dt)" if gcl else \
              "GCL VIOLATED  (xdot = analytic dx/dt)   "
        print(f"  {tag}   max|rho-1| = {err:.3e}")

    print("\n  grid refinement, GCL-violating scheme (does the error go away?)")
    for N in (30, 60, 120, 240):
        err, _ = free_stream_test(gcl=False, N=N)
        print(f"    N = {N:4d}   max|rho-1| = {err:.3e}")

    print("\n  amplitude sweep, GCL-violating scheme")
    for A in (0.01, 0.02, 0.05, 0.10):
        err, _ = free_stream_test(gcl=False, A=A)
        print(f"    mesh amplitude A = {A:.2f}   max|rho-1| = {err:.3e}")

    print("\n" + "=" * 66)
    print("EXPERIMENT B -- piston compression vs isentropic p*V^gamma")
    print("=" * 66)
    Lf, pm, pi, rel, _ = piston()
    print(f"  compression ratio      = {1.0/Lf:.3f}")
    print(f"  solver mean pressure   = {pm:.6f}")
    print(f"  isentropic prediction  = {pi:.6f}")
    print(f"  relative error         = {rel*100:.4f} %")
