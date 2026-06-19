"""Communication-free exit coordination: does reading the affect field redistribute the crowd?

NearFar room (near + far exit), crowd biased toward the near door. Each exit has its own navigation
field (so route distance is the true path length around walls). Two conditions, field active in BOTH:
  Baseline  : each agent heads to its nearest-by-path exit.
  FieldRoute: each agent picks the exit minimising  path_dist + kField * affect_at_exit, re-choosing
              periodically -> agents avoid the high-affect (congested) door, with NO communication.
Reproduces the Unity coordination result (stigmergic exit balancing) in pure Python.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim import Config, Simulation, NavField, metrics
from crowdsim.scenarios import SCENARIOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

N = 45
SEEDS = tuple(range(10))
MAXSEC = 60.0
KFIELD = 20.0
RECHOOSE = 2.0
REACH = 0.6


class ExitNav:
    """Per-agent navigation: each agent follows the nav of its currently-chosen exit (group index)."""
    def __init__(self, navs, choice):
        self.navs, self.choice = navs, choice

    def direction_at(self, pos):
        out = np.zeros((len(pos), 2))
        for e, nav in enumerate(self.navs):
            m = self.choice == e
            if m.any():
                out[m] = nav.direction_at(pos[m])
        return out

    def dist_to(self, e, pos):
        return self.navs[e].dist_at(pos)


def run(field_route, seed):
    sc = SCENARIOS["NearFar"]
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7)         # field active in BOTH conditions
    rng = np.random.default_rng(seed)
    sim = Simulation(cfg, rng)
    sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    sim.spawn(np.c_[rng.uniform(x0, x1, N), rng.uniform(z0, z1, N)])
    exits = sc.exits                                              # [(8,3) near, (8,-7) far]
    navs = [NavField(cfg, sc.walls, [ex]) for ex in exits]
    choice = np.zeros(N, int)
    enav = ExitNav(navs, choice)
    sim.nav = enav

    def choose():
        d = np.stack([navs[e].dist_at(sim.pos) for e in range(len(exits))], axis=1)   # (N, nexit)
        if field_route:
            # sample affect at the APPROACH to each door (where the queue/congestion builds), not the
            # door gap itself (which agents pass through quickly).
            pen = np.array([KFIELD * sim.field.sample_point(ex[0] - 1.5, ex[1]) for ex in exits])
            score = d + pen[None, :]
        else:
            score = d
        return np.argmin(score, axis=1)

    enav.choice[:] = choose()
    evac = np.zeros(N, bool); used = np.full(N, -1)
    steps = int(MAXSEC / cfg.dt); rt = int(RECHOOSE / cfg.dt)
    hw, hh = sc.width / 2, sc.height / 2
    spd_sum = 0.0; spd_n = 0; parked = 0
    evac_t = np.full(N, -1.0)
    for t in range(steps):
        if t % rt == 0:
            keep = (~evac) & (sim.pos[:, 0] < sc.exits[0][0] - 2)
            nc = choose()
            enav.choice[keep] = nc[keep]
        sim.step()
        d_own = np.empty(N)
        for e in range(len(exits)):
            m = enav.choice == e
            if m.any():
                d_own[m] = navs[e].dist_at(sim.pos[m])
        for i in np.where((d_own < REACH) & (~evac))[0]:
            evac[i] = True; used[i] = enav.choice[i]; evac_t[i] = t * cfg.dt
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; enav.choice[i] = 0; parked += 1
        if t % 5 == 0:
            act = ~evac
            if act.any():
                spd_sum += np.linalg.norm(sim.vel[act], axis=1).sum(); spd_n += act.sum()
        if evac.all():
            break
    near = int((used == 0).sum()); far = int((used == 1).sum()); ev = near + far
    maxshare = max(near, far) / ev if ev else 1.0
    return dict(evac=ev, near=near, far=far, maxshare=maxshare, speed=spd_sum / max(1, spd_n))


def main():
    print("=" * 64); print("COORDINATION: communication-free exit redistribution"); print("=" * 64)
    rows = ["condition,seed,evacuated,near,far,maxshare,mean_speed"]
    agg = {}
    for cond, fr in (("Baseline", False), ("FieldRoute", True)):
        ev, ms, fars = [], [], []
        for s in SEEDS:
            r = run(fr, s)
            rows.append(f"{cond},{s},{r['evac']},{r['near']},{r['far']},{r['maxshare']:.3f},{r['speed']:.3f}")
            ev.append(r["evac"]); ms.append(r["maxshare"]); fars.append(r["far"])
        agg[cond] = (np.mean(ev), np.mean(ms), np.mean(fars))
        print(f"  {cond:10s} evac={np.mean(ev):.1f}  maxshare={np.mean(ms):.3f}  far-exit usage={np.mean(fars):.1f}")
    from crowdsim.metrics import mannwhitney, cliffs_delta
    bms = [float(r.split(",")[5]) for r in rows[1:] if r.startswith("Baseline")]
    fms = [float(r.split(",")[5]) for r in rows[1:] if r.startswith("FieldRoute")]
    print(f"  -> max-share FieldRoute<Baseline: p={mannwhitney(fms, bms, 'less'):.3g}, "
          f"delta={cliffs_delta(fms, bms):+.2f}  (lower = more balanced)")
    with open(os.path.join(RES, "coordination.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4))
    conds = ["Baseline", "FieldRoute"]; col = ["#C9C9C9", "#2E6FB7"]
    a1.bar(conds, [agg[c][1] for c in conds], color=col); a1.set_title("max-exit share (lower=balanced)")
    a1.axhline(1.0, color="#aa3333", ls="--", lw=0.8); a1.set_ylim(0, 1.1)
    a2.bar(conds, [agg[c][2] for c in conds], color=col); a2.set_title("far (wasted) exit usage")
    fig.suptitle("Communication-free affective coordination (NearFar)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "coordination.png"), dpi=150)
    print("-> results/coordination.csv, figures/coordination.png")


if __name__ == "__main__":
    main()
