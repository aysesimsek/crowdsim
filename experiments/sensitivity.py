"""Sensitivity analysis: which parameters actually drive the predictions?

We vary each key affect-field parameter by ±40% around its baseline and measure the change in two outputs:
the field's spatial structure (Moran's I, pillar 1) and egress. A tornado chart shows which knobs matter
(robustness + which to calibrate first). Baseline outputs are reported with 95% CIs over seeds.
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
from crowdsim import Config, Simulation, NavField, metrics
from crowdsim.scenarios import SCENARIOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

SEEDS = (0, 1, 2)
PARAMS = ["field_gain", "decay", "diffusion", "deposit_gain", "contagion_gain", "calm_gain"]
BASE = dict(field_gain=1.10, decay=0.5, diffusion=1.0, deposit_gain=1.0, contagion_gain=0.35, calm_gain=0.45)


def run(overrides, seed):
    sc = SCENARIOS["Bottleneck"]
    kw = dict(width=sc.width, height=sc.height, boundary="walls", max_value=50.0, field_deposit_gain=0.7)
    kw.update(BASE); kw.update(overrides)
    cfg = Config(**{k: v for k, v in kw.items() if k in Config.__dataclass_fields__})
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    sim.spawn(np.c_[rng.uniform(x0, x1, 45), rng.uniform(z0, z1, 45)])
    nav = NavField(cfg, sc.walls, sc.exits, inflate=0.2); sim.nav = nav
    evac = np.zeros(45, bool); hw, hh = sc.width/2, sc.height/2; parked = 0; mor = 0.0; ms = 0
    for t in range(int(50 / cfg.dt)):
        sim.step()
        d = nav.dist_at(sim.pos)
        for i in np.where((d < 0.6) & (~evac))[0]:
            evac[i] = True; sim.pos[i] = [-hw+0.5+(parked % 18)*0.45, -hh+0.4+(parked//18)*0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        if t % 10 == 0:
            mor += sim.field.morans_i(); ms += 1
        if evac.all():
            break
    return mor / max(1, ms), int(evac.sum())


def main():
    print("=" * 60); print("SENSITIVITY ANALYSIS (±40% per parameter)"); print("=" * 60)
    bm = [run({}, s) for s in SEEDS]
    base_mor = np.array([b[0] for b in bm]); base_ev = np.array([b[1] for b in bm])
    m0, m0e = metrics.ci95(base_mor); e0, e0e = metrics.ci95(base_ev)
    print(f"  baseline: Moran's I = {m0:.3f} ± {m0e:.3f}   egress = {e0:.1f} ± {e0e:.1f}")
    rows = ["param,moran_low,moran_high,egress_low,egress_high"]; tor = []
    for p in PARAMS:
        lo, hi = BASE[p] * 0.6, BASE[p] * 1.4
        ml = np.mean([run({p: lo}, s)[0] for s in SEEDS]); mh = np.mean([run({p: hi}, s)[0] for s in SEEDS])
        el = np.mean([run({p: lo}, s)[1] for s in SEEDS]); eh = np.mean([run({p: hi}, s)[1] for s in SEEDS])
        rows.append(f"{p},{ml:.3f},{mh:.3f},{el:.1f},{eh:.1f}")
        tor.append((p, abs(mh - ml), abs(eh - el)))
        print(f"  {p:16s} Moran's I {ml:.2f}->{mh:.2f}   egress {el:.0f}->{eh:.0f}")
    tor.sort(key=lambda x: x[1])
    print(f"\n  -> most influential on field structure: {tor[-1][0]}; least: {tor[0][0]}. Outputs are "
          f"{'robust' if tor[-1][1] < 0.15 else 'moderately sensitive'} to ±40% parameter changes.")
    with open(os.path.join(RES, "sensitivity.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    names = [t[0] for t in tor]; mvals = [t[1] for t in tor]; evals = [t[2] for t in tor]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
    a1.barh(range(len(names)), mvals, color="#2E6FB7"); a1.set_yticks(range(len(names))); a1.set_yticklabels(names, fontsize=9)
    a1.set_xlabel("|Δ Moran's I| over ±40%"); a1.set_title("Sensitivity: field structure")
    order = np.argsort(evals)
    a2.barh(range(len(names)), [evals[i] for i in order], color="#C77A2E")
    a2.set_yticks(range(len(names))); a2.set_yticklabels([names[i] for i in order], fontsize=9)
    a2.set_xlabel("|Δ egress| over ±40%"); a2.set_title("Sensitivity: egress")
    fig.suptitle("Sensitivity analysis: which parameters drive the predictions (tornado)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "sensitivity.png"), dpi=140)
    print("-> results/sensitivity.csv, figures/sensitivity.png")


if __name__ == "__main__":
    main()
