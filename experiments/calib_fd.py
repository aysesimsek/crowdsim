"""Calibrate the separation force (w_sep, ps_base) so the corridor fundamental diagram matches the
empirical Weidmann curve (raises the over-congested mid-density branch into the 1.2-1.8 capacity band).
Sweeps a small grid, prints RMSE-vs-Weidmann + max specific flow, picks the best."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
from crowdsim import Config, Simulation
from experiments.validation_suite import weidmann

RHOS = np.array([0.5, 1.0, 1.5, 2.0, 2.5])


def fd_speed(rho, w_sep, ps_base, seed=0, side=10.0):
    n = max(6, int(rho * side * side))
    cfg = Config(width=side, height=side, boundary="torus", base_speed=1.34, stressed_speed=1.34,
                 field_gain=0.0, field_deposit_gain=0.0, w_sep=w_sep, ps_base=ps_base)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng)
    lim = side / 2 - 0.5
    sim.spawn(rng.uniform(-lim, lim, (n, 2)))
    sp = []
    for t in range(200):
        sim.set_targets(sim.pos + np.array([50.0, 0.0])); sim.step()
        if t > 110:
            sp.append(np.linalg.norm(sim.vel, axis=1).mean())
    return float(np.mean(sp))


def main():
    wd = weidmann(RHOS)
    print("=" * 70); print("FD calibration sweep (vs Weidmann)"); print("=" * 70)
    print(f"  Weidmann targets: " + "  ".join(f"ρ{RHOS[i]:.1f}={wd[i]:.2f}" for i in range(len(RHOS))))
    print(f"  current default w_sep=3.0 ps_base=0.90 ->")
    best = None
    for w_sep in (1.0, 1.5, 2.0, 2.5):
        for ps_base in (0.55, 0.70, 0.85):
            v = np.array([fd_speed(r, w_sep, ps_base) for r in RHOS])
            rmse = float(np.sqrt(np.mean((v - wd) ** 2)))
            jmax = float((RHOS * v).max())
            mono = bool(np.all(np.diff(v) <= 0.03))
            ok = (1.2 <= jmax <= 1.8) and mono
            tag = " <== candidate" if ok else ""
            print(f"  w_sep={w_sep:.1f} ps_base={ps_base:.2f}  RMSE={rmse:.3f}  Jmax={jmax:.2f}  mono={mono}{tag}")
            if ok and (best is None or rmse < best[0]):
                best = (rmse, w_sep, ps_base, jmax, v)
    if best:
        print(f"\n  BEST: w_sep={best[1]:.1f} ps_base={best[2]:.2f}  RMSE={best[0]:.3f}  Jmax={best[3]:.2f}")
        print(f"        speeds = " + "  ".join(f"{x:.2f}" for x in best[4]))
    else:
        print("\n  no combo hit Jmax in 1.2-1.8 + monotone; loosen grid")


if __name__ == "__main__":
    main()
