"""
engine_combust.py -- flame propagation and combustion in a piston-cylinder,
built from first principles.

Nothing here is a curve fit to a pressure trace. The burn rate comes out of
flame geometry multiplied by a flame speed; the pressure comes out of the first
law. The Wiebe function -- which most textbooks hand you as the starting point
-- is something this model REPRODUCES rather than assumes, and that is the
verification in verify_wiebe().

Model chain
-----------
  slider-crank      ->  V(theta), exact closed form
  pancake chamber   ->  flame front is a circle of radius r_f centred on the
                        spark plug, intersected with the bore circle.  Both the
                        burned area and the flame arc length are analytic.
  flame speed       ->  laminar (Metghalchi & Keck form) + turbulence
                        (Damkoehler) + a kernel development factor
  burn rate         ->  dm_b/dt = rho_u * A_flame * S_T
  pressure          ->  first law, ideal gas, temperature-dependent gamma
  knock             ->  Livengood-Wu integral with a Douaud-Eyzat delay

Correlation constants are quoted from the standard engine literature. Check them
against the original papers before putting them on screen -- I am reproducing
them from memory and cannot verify citations here.

Run:  python3 engine_combust.py

Animation lives in engine_combust_viz.py -- this module stays plotting-free so
the physics can be imported and verified without a display or matplotlib.
"""

from __future__ import annotations

import numpy as np

# np.trapz was renamed to np.trapezoid in NumPy 2.0.
_trapz = getattr(np, "trapezoid", None) or np.trapz

# =====================================================================
# Geometry and operating point
# =====================================================================
class Engine:
    def __init__(self,
                 bore=0.086,          # m
                 stroke=0.086,        # m
                 conrod=0.143,        # m
                 CR=10.5,             # compression ratio
                 rpm=2000.0,
                 spark_offset=0.0129,  # spark plug distance from cylinder axis, m
                 p_ivc=0.90e5,        # Pa, intake at valve closing
                 T_ivc=330.0,         # K
                 theta_ivc=-140.0,    # deg ATDC
                 theta_evo=+140.0,    # deg ATDC
                 theta_spark=-25.0,   # deg ATDC
                 phi=1.0,             # equivalence ratio
                 octane=95.0,         # RON
                 residual=0.05):
        self.B, self.L, self.l = bore, stroke, conrod
        self.a = stroke / 2.0                     # crank radius
        self.CR = CR
        self.rpm = rpm
        self.omega = 2 * np.pi * rpm / 60.0       # rad/s
        self.r_s = spark_offset
        self.p_ivc, self.T_ivc = p_ivc, T_ivc
        self.th_ivc, self.th_evo, self.th_spark = theta_ivc, theta_evo, theta_spark
        self.phi, self.octane, self.residual = phi, octane, residual

        self.A_p = np.pi * bore ** 2 / 4.0        # piston area
        self.V_d = self.A_p * stroke              # displaced volume
        self.V_c = self.V_d / (CR - 1.0)          # clearance volume

        self.R_gas = 287.0                        # J/kg-K
        self.LHV = 44.0e6                         # J/kg, gasoline
        self.AFR_s = 14.6                         # stoichiometric air-fuel ratio

    # -- slider-crank -------------------------------------------------
    def volume(self, theta_deg):
        """Exact slider-crank volume. theta measured from TDC firing."""
        th = np.radians(theta_deg)
        a, l = self.a, self.l
        # piston displacement below TDC
        d = a * (1.0 - np.cos(th)) + l - np.sqrt(l ** 2 - (a * np.sin(th)) ** 2)
        return self.V_c + self.A_p * d

    def dVdtheta(self, theta_deg):
        """Analytic derivative, per radian."""
        th = np.radians(theta_deg)
        a, l = self.a, self.l
        root = np.sqrt(l ** 2 - (a * np.sin(th)) ** 2)
        dddth = a * np.sin(th) + (a ** 2 * np.sin(th) * np.cos(th)) / root
        return self.A_p * dddth

    def height(self, theta_deg):
        """Pancake chamber height: instantaneous volume spread over the bore."""
        return self.volume(theta_deg) / self.A_p

    def mean_piston_speed(self):
        return 2.0 * self.L * self.rpm / 60.0


# =====================================================================
# Flame geometry: circle of radius r_f centred at distance d from the
# cylinder axis, clipped by the bore circle of radius R.
# Both quantities below are exact -- no discretisation anywhere.
# =====================================================================
def burned_area(r_f, R, d):
    """Area of the flame circle that lies inside the bore circle."""
    if r_f <= 0.0:
        return 0.0
    if d < 1e-12:
        return np.pi * min(r_f, R) ** 2
    if r_f <= R - d:
        return np.pi * r_f ** 2          # flame entirely within the bore
    if r_f >= R + d:
        return np.pi * R ** 2            # everything burned
    # circular lens
    c1 = (d * d + r_f * r_f - R * R) / (2.0 * d * r_f)
    c2 = (d * d + R * R - r_f * r_f) / (2.0 * d * R)
    c1 = np.clip(c1, -1.0, 1.0)
    c2 = np.clip(c2, -1.0, 1.0)
    tri = 0.5 * np.sqrt(max(0.0, (-d + r_f + R) * (d + r_f - R)
                            * (d - r_f + R) * (d + r_f + R)))
    return r_f ** 2 * np.arccos(c1) + R ** 2 * np.arccos(c2) - tri


def flame_arc(r_f, R, d):
    """Length of the flame circle that is still inside the bore.

    Once the flame touches the far wall this starts shrinking, which is why the
    burn rate falls off at the end of combustion without any tuning constant.
    """
    if r_f <= 0.0:
        return 0.0
    if d < 1e-12:
        return 2.0 * np.pi * r_f if r_f < R else 0.0
    k = (R * R - d * d - r_f * r_f) / (2.0 * d * r_f)
    if k >= 1.0:
        return 2.0 * np.pi * r_f
    if k <= -1.0:
        return 0.0
    psi0 = np.arccos(k)
    return 2.0 * r_f * (np.pi - psi0)


def invert_burned_area(A_target, R, d, r_max):
    """Find r_f such that burned_area(r_f) = A_target. Monotonic -> bisection."""
    if A_target <= 0.0:
        return 0.0
    lo, hi = 0.0, r_max
    if burned_area(hi, R, d) <= A_target:
        return hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if burned_area(mid, R, d) < A_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# =====================================================================
# Flame speed
# =====================================================================
def laminar_flame_speed(T_u, p, phi, residual):
    """Metghalchi & Keck power-law form for a gasoline-air mixture."""
    B_m, phi_m, B_phi = 0.305, 1.21, -0.549
    S_L0 = B_m + B_phi * (phi - phi_m) ** 2
    S_L0 = max(S_L0, 0.02)
    alpha = 2.18 - 0.8 * (phi - 1.0)
    beta = -0.16 + 0.22 * (phi - 1.0)
    S_L = S_L0 * (T_u / 298.0) ** alpha * (p / 101325.0) ** beta
    return max(0.01, S_L * (1.0 - 2.1 * residual))


def turbulent_flame_speed(S_L, u_prime, r_f, kernel_scale):
    """Damkoehler wrinkling, damped while the kernel is still small.

    A 1 mm kernel cannot feel eddies larger than itself, so it burns close to
    laminar. Without this factor the model lights off far too fast and the
    ignition delay is wrong by ten crank degrees.
    """
    develop = 1.0 - np.exp(-r_f / max(kernel_scale, 1e-6))
    return S_L + 1.0 * u_prime * develop


def gamma_of_T(T, constant=None):
    if constant is not None:
        return constant
    return float(np.clip(1.40 - 6.0e-5 * (T - 300.0), 1.24, 1.40))


def knock_delay_ms(p_pa, T_u, octane):
    """Douaud-Eyzat autoignition delay, milliseconds. p in atm."""
    p_atm = max(p_pa / 101325.0, 1e-6)
    return 17.68 * (octane / 100.0) ** 3.402 * p_atm ** (-1.7) * np.exp(3800.0 / T_u)


# =====================================================================
# The solver
# =====================================================================
def simulate(eng: Engine, dtheta=0.05, motored=False, gamma_const=None,
             kernel_scale=0.002, record=True):
    th = eng.th_ivc
    V = eng.volume(th)
    p = eng.p_ivc
    T = eng.T_ivc

    m_tot = p * V / (eng.R_gas * T)
    m_fuel = m_tot * (1.0 - eng.residual) / (1.0 + eng.AFR_s / eng.phi)
    Q_total = m_fuel * eng.LHV

    m_b = 0.0
    r_f = 0.0
    T_b = T
    r_kernel = 0.0005          # 0.5 mm spark kernel -- the flame needs a seed
    sparked = False
    knock_int = 0.0
    knock_theta = None
    p_ref, T_ref = p, T          # unburned isentrope anchor

    u_prime = 0.5 * eng.mean_piston_speed()
    R_bore = eng.B / 2.0
    dt = np.radians(dtheta) / eng.omega

    hist = {k: [] for k in ("theta", "V", "p", "T", "T_u", "T_b", "x", "r_f",
                            "A_f", "S_L", "S_T", "dQ", "knock")}

    while th < eng.th_evo:
        V = eng.volume(th)
        h = eng.height(th)
        T = p * V / (m_tot * eng.R_gas)

        # unburned zone follows its own isentrope from IVC
        gam_u = gamma_of_T(T, gamma_const)
        T_u = T_ref * (p / p_ref) ** ((gam_u - 1.0) / gam_u)

        # ---- burn rate from flame geometry ----------------------------
        S_L = S_T = 0.0
        A_f = 0.0
        dQ = 0.0
        x = m_b / m_tot if m_tot > 0 else 0.0

        if (not motored) and th >= eng.th_spark and x < 0.9995:
            if not sparked:
                r_f, sparked = r_kernel, True
            rho_u = p / (eng.R_gas * T_u)
            S_L = laminar_flame_speed(T_u, p, eng.phi, eng.residual)
            S_T = turbulent_flame_speed(S_L, u_prime, max(r_f, r_kernel), kernel_scale)
            arc = flame_arc(max(r_f, r_kernel), R_bore, eng.r_s)
            A_f = arc * h                      # flame surface = arc x chamber height
            dm_b = rho_u * A_f * S_T * dt
            dm_b = min(dm_b, m_tot - m_b)
            m_b += dm_b
            dQ = (dm_b / m_tot) * Q_total if m_tot > 0 else 0.0

        # ---- first law -> pressure ------------------------------------
        gam = gamma_of_T(T, gamma_const)
        dV = eng.dVdtheta(th) * np.radians(dtheta)
        dp = (gam - 1.0) / V * dQ - gam * p / V * dV
        p = max(p + dp, 1e3)

        # ---- flame radius consistent with the burned-zone volume ------
        # Two zones at a common pressure. The unburned zone volume follows
        # directly from its own mass and its isentropic temperature, so the
        # burned volume is whatever is left over. No expansion-ratio fudge.
        if m_b > 0.0:
            m_u = max(m_tot - m_b, 0.0)
            V_u = m_u * eng.R_gas * T_u / p
            V_b = float(np.clip(V - V_u, 0.0, V))
            r_f = invert_burned_area(V_b / h, R_bore, eng.r_s,
                                     R_bore + eng.r_s)
            T_b = p * V_b / (m_b * eng.R_gas) if V_b > 0 else T

        # ---- knock ----------------------------------------------------
        if (not motored) and x < 0.999 and th > eng.th_spark:
            tau_ms = knock_delay_ms(p, T_u, eng.octane)
            knock_int += (dt * 1000.0) / tau_ms
            if knock_int >= 1.0 and knock_theta is None:
                knock_theta = th

        if record:
            for k, v in (("theta", th), ("V", V), ("p", p), ("T", T),
                         ("T_u", T_u), ("T_b", T_b), ("x", x), ("r_f", r_f), ("A_f", A_f),
                         ("S_L", S_L), ("S_T", S_T), ("dQ", dQ),
                         ("knock", knock_int)):
                hist[k].append(v)
        th += dtheta

    out = {k: np.array(v) for k, v in hist.items()}
    out["m_tot"] = m_tot
    out["m_fuel"] = m_fuel
    out["Q_total"] = Q_total
    out["knock_theta"] = knock_theta
    out["knock_int"] = knock_int
    return out


def imep(res, eng: Engine):
    """Indicated mean effective pressure from the enclosed p-V area."""
    W = _trapz(res["p"], res["V"])
    return W / eng.V_d


# =====================================================================
# Verification
# =====================================================================
def verify_geometry(eng: Engine):
    """Volume at BDC/TDC must reproduce the compression ratio exactly."""
    v_tdc = eng.volume(0.0)
    v_bdc = eng.volume(180.0)
    return v_bdc / v_tdc, eng.CR


def verify_motored(eng: Engine):
    """No combustion, constant gamma, no heat loss -> pV^gamma is constant."""
    r = simulate(eng, motored=True, gamma_const=1.4)
    pv = r["p"] * r["V"] ** 1.4
    return pv.std() / pv.mean()


def wiebe(theta, th0, dur, a, n):
    z = np.clip((theta - th0) / dur, 0.0, 1.0)
    return 1.0 - np.exp(-a * z ** n)


def verify_wiebe(res, eng: Engine):
    """Fit a Wiebe function to the burn curve the physics produced."""
    th, x = res["theta"], res["x"]
    burning = (x > 0.001) & (x < 0.999)
    if burning.sum() < 20:
        return None
    if x.max() < 0.92:
        return {"incomplete": True, "x_final": float(x.max())}
    th0 = th[burning][0]
    th10 = th[min(np.searchsorted(x, 0.10), len(th) - 1)]
    th90 = th[min(np.searchsorted(x, 0.90), len(th) - 1)]
    dur = (th[burning][-1] - th0)

    best = None
    for a in np.linspace(2.0, 8.0, 61):
        for n in np.linspace(1.2, 4.0, 57):
            err = np.sqrt(np.mean((wiebe(th[burning], th0, dur, a, n)
                                   - x[burning]) ** 2))
            if best is None or err < best[0]:
                best = (err, a, n)
    return {"rmse": best[0], "a": best[1], "n": best[2],
            "th0": th0, "dur": dur,
            "d1090": th90 - th10, "th10": th10, "th90": th90}


# =====================================================================
if __name__ == "__main__":
    eng = Engine()
    print("=" * 68)
    print("GEOMETRY")
    print("=" * 68)
    ratio, CR = verify_geometry(eng)
    print(f"  V(BDC)/V(TDC) = {ratio:.6f}   specified CR = {CR}")
    print(f"  displacement  = {eng.V_d*1e6:.1f} cm^3    clearance = {eng.V_c*1e6:.2f} cm^3")
    print(f"  mean piston speed = {eng.mean_piston_speed():.2f} m/s")

    print("\n" + "=" * 68)
    print("MOTORED COMPRESSION  (should be isentropic)")
    print("=" * 68)
    print(f"  relative scatter in p*V^gamma = {verify_motored(eng):.3e}")

    print("\n" + "=" * 68)
    print("FIRED CYCLE")
    print("=" * 68)
    r = simulate(eng)
    i = int(np.argmax(r["p"]))
    print(f"  trapped mass    = {r['m_tot']*1e6:.2f} mg")
    print(f"  fuel mass       = {r['m_fuel']*1e6:.2f} mg")
    print(f"  fuel energy     = {r['Q_total']:.1f} J")
    print(f"  peak pressure   = {r['p'][i]/1e5:.2f} bar at {r['theta'][i]:+.1f} deg ATDC")
    print(f"  peak unburned T = {r['T_u'].max():.1f} K")
    print(f"  peak mean T     = {r['T'].max():.1f} K")
    print(f"  IMEP            = {imep(r, eng)/1e5:.2f} bar")
    print(f"  peak S_L        = {r['S_L'].max():.3f} m/s")
    print(f"  peak S_T        = {r['S_T'].max():.3f} m/s")
    print(f"  knock integral  = {r['knock_int']:.3f}"
          f"   onset = {r['knock_theta']}")

    print("\n" + "=" * 68)
    print("BURN RATE vs WIEBE  (physics reproducing the empirical fit)")
    print("=" * 68)
    w = verify_wiebe(r, eng)
    if w and w.get("incomplete"):
        print(f"  combustion INCOMPLETE -- x only reached {w['x_final']:.3f}")
        w = None
    if w:
        print(f"  best-fit Wiebe    a = {w['a']:.2f}   n = {w['n']:.2f}")
        print(f"  fit RMSE          = {w['rmse']:.4f} (mass fraction)")
        print(f"  10-90% burn dur   = {w['d1090']:.1f} deg CA")
        print(f"  CA10 = {w['th10']:+.1f}   CA90 = {w['th90']:+.1f}")

    print("\n" + "=" * 68)
    print("SPARK SWEEP  (looking for MBT)")
    print("=" * 68)
    best = None
    for sp in range(-40, -4, 3):
        e2 = Engine(theta_spark=float(sp))
        r2 = simulate(e2, dtheta=0.1)
        im = imep(r2, e2) / 1e5
        j = int(np.argmax(r2["p"]))
        print(f"  spark {sp:+4d} deg   IMEP {im:6.2f} bar   "
              f"p_max {r2['p'][j]/1e5:6.2f} bar at {r2['theta'][j]:+6.1f}   "
              f"knock {r2['knock_int']:.2f}")
        if best is None or im > best[0]:
            best = (im, sp, r2["theta"][j])
    print(f"  --> MBT at {best[1]:+d} deg, peak pressure at {best[2]:+.1f} deg ATDC")

    print("\n" + "=" * 68)
    print("ALTITUDE  (Kathmandu, 86 kPa ambient)")
    print("=" * 68)
    for label, p_amb in (("sea level 101.3 kPa", 101.3e3),
                         ("Kathmandu  86.0 kPa", 86.0e3)):
        e3 = Engine(p_ivc=0.89 * p_amb)
        r3 = simulate(e3, dtheta=0.1)
        print(f"  {label}:  IMEP {imep(r3, e3)/1e5:5.2f} bar   "
              f"p_max {r3['p'].max()/1e5:6.2f} bar   "
              f"knock integral {r3['knock_int']:.3f}")
