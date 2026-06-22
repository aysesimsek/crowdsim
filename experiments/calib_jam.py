"""Calibrate contact_friction so the FD develops a proper jamming branch (v->0 near rho~5, matching
Weidmann's rho_max=5.4) WITHOUT disturbing the already-calibrated low/mid-density branch (rho<=3)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
from crowdsim import Config, Simulation
from experiments.validation_suite import weidmann

RHOS = np.array([1.0, 2.0, 3.0, 4.0, 5.0])


def fd_speed(rho, cf, jd, seed=0, side=10.0):
    n = max(6, int(rho * side * side))
    cfg = Config(width=side, height=side, boundary="torus", base_speed=1.34, stressed_speed=1.34,
                 field_gain=0.0, field_deposit_gain=0.0, w_sep=2.0, ps_base=0.7,
                 contact_friction=cf, friction_range=1.5, jam_density=jd)
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
    print("=" * 74); print("Contact-friction calibration (jamming branch)"); print("=" * 74)
    print("  Weidmann: " + "  ".join(f"ρ{RHOS[i]:.0f}={wd[i]:.2f}" for i in range(len(RHOS))))
    for jd in (3.0, 3.5, 4.0):
        for cf in (0.0, 1.0, 1.8, 3.0, 5.0):
            v = np.array([fd_speed(r, cf, jd) for r in RHOS])
            rmse_lowmid = float(np.sqrt(np.mean((v[:3] - wd[:3]) ** 2)))  # rho<=3 must stay matched
            jam = v[-1] < 0.15                                            # rho=5 -> jammed?
            jmax = float((RHOS * v).max())
            tag = " <== jams + low/mid kept" if (jam and rmse_lowmid < 0.12 and 1.2 <= jmax <= 1.8) else ""
            print(f"  jam_d={jd:.1f} cf={cf:.1f}  v=[" + " ".join(f"{x:.2f}" for x in v) +
                  f"]  RMSE(ρ≤3)={rmse_lowmid:.3f}  Jmax={jmax:.2f}  jam@5={'Y' if jam else 'n'}{tag}")
    print("\n  pick the smallest cf that jams (v(ρ5)<0.15) while RMSE(ρ≤3)<0.12 and Jmax in 1.2-1.8")


if __name__ == "__main__":
    main()
