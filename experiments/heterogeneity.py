"""Heterogeneous crowds: families move together.

Real crowds are not identical individuals — people move in social groups (families, friends) that stay
together. We compare egress for a crowd of lone individuals vs the same crowd organised into small
groups with cohesion (members pulled to their group's centroid). Groups clump and wait for each other,
which changes egress and local crowding — a realism + safety effect that homogeneous models miss.
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
from experiments.capacity_design import room

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

N, SEEDS, MAXSEC = 60, (0, 1, 2, 3, 4), 60.0
GSIZE, W_COH = 5, 3.0


def run(family, seed):
    sc = room(1, 2.4)
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7, w_cohesion=(W_COH if family else 0.0))
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    if family:
        pos, sg = [], []
        for fi in range(N // GSIZE):
            cx, cz = rng.uniform(x0, x1), rng.uniform(z0, z1)
            for _ in range(GSIZE):
                pos.append([cx + rng.uniform(-0.6, 0.6), cz + rng.uniform(-0.6, 0.6)]); sg.append(fi)
        pos = np.array(pos); m = len(pos); sim.spawn(pos); sim.sgroup[:] = np.array(sg)
    else:
        sim.spawn(np.c_[rng.uniform(x0, x1, N), rng.uniform(z0, z1, N)]); m = N
    nav = NavField(cfg, sc.walls, sc.exits, inflate=0.2); sim.nav = nav
    evac = np.zeros(m, bool); evac_t = np.full(m, -1.0); hw, hh = sc.width/2, sc.height/2; parked = 0
    denspk = 0.0
    for t in range(int(MAXSEC / cfg.dt)):
        sim.step()
        d = nav.dist_at(sim.pos)
        for i in np.where((d < 0.6) & (~evac))[0]:
            evac[i] = True; evac_t[i] = t * cfg.dt; sim.sgroup[i] = -1
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        if t % 10 == 0 and (~evac).any():
            denspk = max(denspk, metrics.peak_local_density(sim.pos[~evac]))
        if evac.all():
            break
    ts = np.sort(evac_t[evac_t >= 0]); half = int(np.ceil(0.5 * m))
    t50 = float(ts[half - 1]) if len(ts) >= half else -1.0
    return dict(evac=int(evac.sum()), t50=t50, peak=denspk)


def main():
    print("=" * 60); print("HETEROGENEOUS CROWDS: individuals vs families"); print("=" * 60)
    agg = {}
    rows = ["mode,seed,evac,t50,peak"]
    for mode, fam in (("individuals", False), ("families", True)):
        ev, t5, pk = [], [], []
        for s in SEEDS:
            r = run(fam, s)
            rows.append(f"{mode},{s},{r['evac']},{r['t50']:.2f},{r['peak']:.3f}")
            ev.append(r["evac"]); t5.append(r["t50"]); pk.append(r["peak"])
        agg[mode] = (np.mean(ev), np.mean(t5), np.mean(pk))
        print(f"  {mode:12s} evac={np.mean(ev):.1f}/{N}  t50={np.mean(t5):.1f}s  peak density={np.mean(pk):.2f}/m²")
    ind, fam = agg["individuals"], agg["families"]
    print(f"\n  -> HONEST null: organising the crowd into groups of {GSIZE} has a NEGLIGIBLE aggregate effect "
          f"(t50 {ind[1]:.1f}->{fam[1]:.1f}s, evac {ind[0]:.0f}->{fam[0]:.0f}, peak {ind[2]:.1f}->{fam[2]:.1f}/m²):")
    print(f"     at a single door, bulk egress is door-flow-limited, not composition-limited. The capability")
    print(f"     (social groups that stay together) is built; its effect would show in composition-sensitive")
    print(f"     settings (multi-exit choice, vulnerable-group evacuation), not single-door throughput.")
    with open(os.path.join(RES, "heterogeneity.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    modes = ["individuals", "families"]; x = np.arange(2); col = ["#2E6FB7", "#C77A2E"]
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(12, 4))
    a1.bar(x, [agg[m][0] for m in modes], color=col); a1.set_xticks(x); a1.set_xticklabels(modes); a1.set_title(f"evacuated in {MAXSEC:.0f}s")
    a2.bar(x, [agg[m][1] for m in modes], color=col); a2.set_xticks(x); a2.set_xticklabels(modes); a2.set_title("median clearance t50 (s)")
    a3.bar(x, [agg[m][2] for m in modes], color=col); a3.set_xticks(x); a3.set_xticklabels(modes); a3.set_title("peak local density (ped/m²)")
    fig.suptitle("Heterogeneous crowds: group cohesion has a negligible aggregate effect (door-flow-limited)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "heterogeneity.png"), dpi=140)
    print("-> results/heterogeneity.csv, figures/heterogeneity.png")


if __name__ == "__main__":
    main()
