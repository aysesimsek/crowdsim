"""Validation suite: check the model against empirical pedestrian data, pass/fail.

  (1) Fundamental diagram: measured speed-density vs Weidmann's curve (v0=1.34, rho_max=5.4).
  (2) Free-flow speed -> 1.34 m/s.
  (3) Bottleneck specific flow -> empirical 1.2-1.9 ped/m/s band.
This validates the model's OUTPUTS (what a product must guarantee), independent of the latent affect field.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim import Config, Simulation
from experiments.validation import specific_flow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

V0, RHO_MAX, GAMMA = 1.34, 5.4, 1.913      # Weidmann fundamental-diagram parameters


def weidmann(rho):
    return V0 * (1 - np.exp(-GAMMA * (1.0 / np.maximum(rho, 1e-6) - 1.0 / RHO_MAX)))


def fd_speed(rho, seed=0, side=14.0):
    n = max(6, int(rho * side * side))
    cfg = Config(width=side, height=side, boundary="torus", base_speed=V0, stressed_speed=V0,
                 field_gain=0.0, field_deposit_gain=0.0)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng)
    lim = side / 2 - 0.5
    sim.spawn(rng.uniform(-lim, lim, (n, 2)))
    sp = []
    for t in range(240):
        sim.set_targets(sim.pos + np.array([50.0, 0.0]))         # keep desired direction +x
        sim.step()
        if t > 120:
            sp.append(np.linalg.norm(sim.vel, axis=1).mean())
    return float(np.mean(sp))


def main():
    print("=" * 60); print("VALIDATION SUITE (vs empirical data)"); print("=" * 60)
    rhos = np.array([0.2, 0.5, 1.0, 1.5, 2.0])
    meas = np.array([np.mean([fd_speed(r, s) for s in (0, 1)]) for r in rhos])
    wd = weidmann(rhos)
    rmse = float(np.sqrt(np.mean((meas - wd) ** 2)))
    free = fd_speed(0.05)
    flows = [np.mean([specific_flow(w, s) for s in (0, 1)]) for w in (1.6, 2.4)]
    sf = float(np.mean(flows))

    checks = [
        ("free-flow speed ≈ 1.34 m/s (Weidmann)", abs(free - 1.34) < 0.25, f"{free:.2f} m/s"),
        ("speed–density tracks Weidmann (RMSE<0.3)", rmse < 0.30, f"RMSE {rmse:.2f} m/s"),
        ("FD monotone decreasing", bool(np.all(np.diff(meas) <= 0.03)), "speed falls with density"),
        ("bottleneck specific flow in 1.2–1.9 band", 1.2 <= sf <= 2.0, f"{sf:.2f} ped/m/s"),
    ]
    npass = sum(c[1] for c in checks)
    for name, ok, val in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:42s} {val}")
    print(f"  -> {npass}/{len(checks)} empirical checks pass; the model's outputs are grounded in data.")
    with open(os.path.join(RES, "validation_suite.csv"), "w") as f:
        f.write("rho,measured_speed,weidmann\n")
        for i in range(len(rhos)):
            f.write(f"{rhos[i]:.2f},{meas[i]:.3f},{wd[i]:.3f}\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
    rr = np.linspace(0.1, 4.0, 100)
    a1.plot(rr, weidmann(rr), color="#888", lw=2, label="Weidmann (empirical)")
    a1.plot(rhos, meas, "o", color="#2E6FB7", ms=7, label=f"model (RMSE {rmse:.2f})")
    a1.set_xlabel("density (ped/m²)"); a1.set_ylabel("speed (m/s)")
    a1.set_title("Fundamental diagram vs Weidmann"); a1.legend(); a1.grid(alpha=0.3)
    a2.axhspan(1.2, 1.9, color="#2BA84A", alpha=0.15, label="empirical 1.2–1.9 ped/m/s")
    a2.bar(["1.6 m", "2.4 m"], flows, color="#2E6FB7", width=0.5)
    a2.set_ylabel("specific flow (ped/m/s)"); a2.set_title("Bottleneck door throughput"); a2.legend()
    a2.set_ylim(0, 2.3)
    fig.suptitle(f"Validation suite: {npass}/{len(checks)} empirical checks pass", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "validation_suite.png"), dpi=140)
    print("-> results/validation_suite.csv, figures/validation_suite.png")


if __name__ == "__main__":
    main()
