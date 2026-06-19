"""Fundamental diagram: speed vs density in a periodic arena (validates the locomotion layer).

Torus arena, every agent flows toward +x (uniform flow). Sweep density (agent count); measure
steady-state net-forward speed (mean v_x) and flow J = rho * v. Free-flow speed should approach the
Weidmann reference v0 ~ 1.34 m/s and fall with density.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim import Config, Simulation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

SIDE = 16.0
WARMUP, MEASURE = 6.0, 8.0
V0_WEIDMANN = 1.34


def mean_speed(n, seed):
    # FD validates the LOCOMOTION (congestion) layer, so we disable the affect arousal-speedup
    # (stressed_speed = base = Weidmann v0) and the field, isolating the pure speed--density relation.
    cfg = Config(width=SIDE, height=SIDE, boundary="torus", max_value=50.0, hard_contact=True,
                 base_speed=V0_WEIDMANN, stressed_speed=V0_WEIDMANN, field_gain=0.0)
    rng = np.random.default_rng(seed)
    sim = Simulation(cfg, rng)
    pos = rng.uniform(-SIDE / 2 + 0.5, SIDE / 2 - 0.5, size=(n, 2))
    sim.spawn(pos)
    sim.set_targets(pos + np.array([1000.0, 0.0]))     # far +x => uniform forward flow
    sw, sm = int(WARMUP / cfg.dt), int(MEASURE / cfg.dt)
    vx = []
    for t in range(sw + sm):
        sim.set_targets(sim.pos + np.array([1000.0, 0.0]))   # keep pulling +x as they wrap
        sim.step()
        if t >= sw:
            vx.append(sim.vel[:, 0].mean())                   # net forward speed (lateral averages out)
    return max(0.0, float(np.mean(vx)))


def main():
    print("=" * 56); print("FUNDAMENTAL DIAGRAM (2D python core)"); print("=" * 56)
    area = SIDE * SIDE
    counts = [4, 10, 25, 45, 70, 100, 140, 190, 250]
    rows = ["n,density,speed,flow"]
    rho, vs = [], []
    for n in counts:
        v = np.mean([mean_speed(n, s) for s in (0, 1)])
        d = n / area
        rho.append(d); vs.append(v)
        rows.append(f"{n},{d:.3f},{v:.3f},{d*v:.3f}")
        print(f"  n={n:4d}  rho={d:.3f} ped/m^2  v={v:.3f} m/s")
    print(f"\n  free-flow speed ~ {vs[0]:.2f} m/s (Weidmann v0={V0_WEIDMANN})")
    with open(os.path.join(RES, "fundamental_diagram.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.plot(rho, vs, "-o", color="#2E6FB7"); a1.axhline(V0_WEIDMANN, color="#aa3333", ls="--", lw=1, label="Weidmann $v_0$")
    a1.set_xlabel("density (ped/m$^2$)"); a1.set_ylabel("speed (m/s)"); a1.set_title("speed--density"); a1.legend(fontsize=8)
    a2.plot(rho, np.array(rho) * np.array(vs), "-o", color="#2BA84A")
    a2.set_xlabel("density (ped/m$^2$)"); a2.set_ylabel("flow (ped/m/s)"); a2.set_title("flow--density")
    fig.suptitle("Fundamental diagram (2D python)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(FIG, "fundamental_diagram.png"), dpi=150)
    print("-> results/fundamental_diagram.csv, figures/fundamental_diagram.png")


if __name__ == "__main__":
    main()
