"""General egress runner: runs EVERY scenario in the library through the core (with navigation),
FIELD vs NOFIELD, and tabulates egress + field structure + congestion into one table + figure.

Routing uses the Dijkstra navigation field (per spawn-group goal set), so agents route around walls /
through doors in every layout. FIELD = affect field active; NOFIELD = matched no-field baseline
(field_gain=0, no deposit) -> Moran's I ~ 0.
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

N_AGENTS = 45
SEEDS = (0, 1, 2)
MAXSEC = 50.0
REACH = 0.6              # distance-to-exit at which an agent has evacuated


class GroupNav:
    """Dispatches navigation per spawn group (group -1 = evacuated/parked -> no drive)."""
    def __init__(self, navs, group):
        self.navs, self.group = navs, group

    def direction_at(self, pos):
        out = np.zeros((len(pos), 2))
        for g, nav in enumerate(self.navs):
            m = self.group == g
            if m.any():
                out[m] = nav.direction_at(pos[m])
        return out

    def dist_at(self, pos):
        out = np.full(len(pos), 1e9)
        for g, nav in enumerate(self.navs):
            m = self.group == g
            if m.any():
                out[m] = nav.dist_at(pos[m])
        return out


def build_navs(cfg, sc):
    """One NavField per spawn group, from that group's goal exits (or all exits if goals is None)."""
    navs = []
    for i in range(len(sc.spawns)):
        if sc.goals is None:
            ex = sc.exits
        else:
            ex = [sc.exits[k] for k in sc.goals[i]]
        navs.append(NavField(cfg, sc.walls, ex))
    return navs


def spawn_groups(sc, n, rng):
    """Distribute n agents across spawn rectangles (group = rect index)."""
    areas = np.array([(x1 - x0) * (z1 - z0) for (x0, x1, z0, z1) in sc.spawns], float)
    counts = np.maximum(1, np.round(n * areas / areas.sum()).astype(int))
    pos, grp = [], []
    for i, (x0, x1, z0, z1) in enumerate(sc.spawns):
        k = counts[i]
        pos.append(np.c_[rng.uniform(x0, x1, k), rng.uniform(z0, z1, k)])
        grp.append(np.full(k, i))
    return np.vstack(pos), np.concatenate(grp)


def run(sc, field_on, seed):
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10 if field_on else 0.0,
                 field_deposit_gain=0.7 if field_on else 0.0)
    rng = np.random.default_rng(seed)
    sim = Simulation(cfg, rng)
    sim.set_walls(sc.walls)
    pos, grp = spawn_groups(sc, N_AGENTS, rng)
    n = len(pos)
    sim.spawn(pos)
    navs = build_navs(cfg, sc)
    gnav = GroupNav(navs, grp.copy())
    sim.nav = gnav

    evac = np.zeros(n, bool); evac_t = np.full(n, -1.0)
    steps = int(MAXSEC / cfg.dt); samp = int(0.5 / cfg.dt)
    hw, hh = sc.width / 2, sc.height / 2
    denspk = 0.0; spd_sum = 0.0; spd_n = 0; mor_sum = 0.0; fm_sum = 0.0; msamp = 0
    parked = 0
    for t in range(steps):
        sim.step()
        d = gnav.dist_at(sim.pos)
        newly = (d < REACH) & (~evac)
        for i in np.where(newly)[0]:
            evac[i] = True; evac_t[i] = t * cfg.dt
            gnav.group[i] = -1                                  # stop driving it
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        if t % samp == 0:
            act = ~evac
            if act.any():
                denspk = max(denspk, metrics.peak_local_density(sim.pos[act]))
                spd_sum += np.linalg.norm(sim.vel[act], axis=1).sum(); spd_n += act.sum()
            mor_sum += sim.field.morans_i(); fm_sum += sim.field.mean(); msamp += 1
        if evac.all():
            break

    ev = int(evac.sum())
    ts = np.sort(evac_t[evac_t >= 0])
    need = int(np.ceil(0.5 * n))
    t50 = float(ts[need - 1]) if len(ts) >= need else -1.0
    return dict(n=n, evacuated=ev, t50=t50, peak_density=denspk,
                mean_speed=(spd_sum / max(1, spd_n)), morans_i=mor_sum / max(1, msamp),
                field_mean=fm_sum / max(1, msamp))


def main():
    print("=" * 78); print("GENERAL EGRESS RUNNER (all scenarios, FIELD vs NOFIELD)"); print("=" * 78)
    rows = ["scenario,condition,seed,n,evacuated,t50,peak_density,mean_speed,morans_i,field_mean"]
    names = list(SCENARIOS.keys())
    agg = {}
    for name in names:
        sc = SCENARIOS[name]
        agg[name] = {}
        for cond, on in (("FIELD", True), ("NOFIELD", False)):
            evs, mors = [], []
            for s in SEEDS:
                r = run(sc, on, s)
                rows.append(f"{name},{cond},{s},{r['n']},{r['evacuated']},{r['t50']:.2f},"
                            f"{r['peak_density']:.3f},{r['mean_speed']:.3f},{r['morans_i']:.4f},{r['field_mean']:.4f}")
                evs.append(r["evacuated"]); mors.append(r["morans_i"])
            agg[name][cond] = (np.mean(evs), np.mean(mors))
        fE, mE = agg[name]["FIELD"]; fN, mN = agg[name]["NOFIELD"]
        print(f"  {name:16s} evac F={fE:4.1f} N={fN:4.1f}   Moran's I F={mE:.2f} N={mN:.2f}")
    with open(os.path.join(RES, "egress_runner.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    x = np.arange(len(names)); w = 0.4
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(15, 8))
    a1.bar(x - w / 2, [agg[n]["FIELD"][1] for n in names], w, label="FIELD", color="#2E6FB7")
    a1.bar(x + w / 2, [agg[n]["NOFIELD"][1] for n in names], w, label="NOFIELD", color="#C9C9C9")
    a1.set_ylabel("affect-field Moran's $I$"); a1.set_title("Field spatial structure across all scenarios")
    a1.set_xticks(x); a1.set_xticklabels(names, rotation=40, ha="right", fontsize=8); a1.legend()
    a2.bar(x - w / 2, [agg[n]["FIELD"][0] for n in names], w, label="FIELD", color="#2E6FB7")
    a2.bar(x + w / 2, [agg[n]["NOFIELD"][0] for n in names], w, label="NOFIELD", color="#C9C9C9")
    a2.set_ylabel(f"evacuated in {MAXSEC:.0f}s (of {N_AGENTS})"); a2.set_title("Egress across all scenarios")
    a2.set_xticks(x); a2.set_xticklabels(names, rotation=40, ha="right", fontsize=8); a2.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "egress_runner.png"), dpi=140)
    print("\n-> results/egress_runner.csv, figures/egress_runner.png")


if __name__ == "__main__":
    main()
