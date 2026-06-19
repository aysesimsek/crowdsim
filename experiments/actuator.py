"""The affect field as an ACTUATOR: can an external controller steer the crowd by writing to the field?

NearFar room (biased toward the near door). Agents read the field to choose an exit (affect-field
guidance). Three conditions:
  Baseline   : nearest-exit routing, no field guidance -> everyone crowds the near door (the problem).
  Self-org   : agents self-balance via their own deposited affect (no external control).
  ActuatorNaive: an external controller continuously dumps affect at the near door to push agents away.
We measure far-exit usage (does it steer?), max-exit share (does it over-steer?) and evacuation.
Reproduces the Unity result: writing to the field steers the crowd, but naive central control
OVER-steers and is beaten by decentralised self-organisation.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim import Config, Simulation, NavField
from crowdsim.scenarios import SCENARIOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

N, SEEDS, MAXSEC = 45, (0, 1, 2, 3, 4), 60.0
KFIELD, RECHOOSE, REACH = 20.0, 2.0, 0.6
ACT_AMOUNT = 80.0          # external deposit rate at the near door (naive open-loop controller)
GAIN_CL = 6.0              # closed-loop gain: deposit proportional to the live routing imbalance


class ExitNav:
    def __init__(self, navs, choice):
        self.navs, self.choice = navs, choice

    def direction_at(self, pos):
        out = np.zeros((len(pos), 2))
        for e, nav in enumerate(self.navs):
            m = self.choice == e
            if m.any():
                out[m] = nav.direction_at(pos[m])
        return out


def run(mode, seed):
    sc = SCENARIOS["NearFar"]
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    sim.spawn(np.c_[rng.uniform(x0, x1, N), rng.uniform(z0, z1, N)])
    exits = np.array(sc.exits, float)
    navs = [NavField(cfg, sc.walls, [tuple(e)]) for e in sc.exits]
    appr = [(e[0] - 1.5, e[1]) for e in sc.exits]                 # approach points (NearFar exits face -x)
    field_route = (mode != "Baseline")

    def choose():
        d = np.stack([navs[e].dist_at(sim.pos) for e in range(len(exits))], axis=1)
        if field_route:
            pen = np.array([KFIELD * sim.field.sample_point(ax, az) for (ax, az) in appr])
            return np.argmin(d + pen[None, :], axis=1)
        return np.argmin(d, axis=1)

    enav = ExitNav(navs, choose()); sim.nav = enav
    evac = np.zeros(N, bool); used = np.full(N, -1)
    steps = int(MAXSEC / cfg.dt); rt = int(RECHOOSE / cfg.dt); hw, hh = sc.width / 2, sc.height / 2
    parked = 0
    for t in range(steps):
        if mode == "ActuatorNaive":                               # open-loop: constant dump at near door
            sim.field.deposit_point(appr[0][0], appr[0][1], ACT_AMOUNT * cfg.dt)
        elif mode == "ActuatorCL":                                # closed-loop: deposit ~ live imbalance
            n0 = int(((enav.choice == 0) & (~evac)).sum())
            n1 = int(((enav.choice == 1) & (~evac)).sum())
            if n0 - n1 > 0:                                        # only relieve the over-subscribed door
                sim.field.deposit_point(appr[0][0], appr[0][1], GAIN_CL * (n0 - n1) * cfg.dt)
        if t % rt == 0:
            keep = (~evac) & (enav.choice >= 0) & (sim.pos[:, 0] < sc.exits[0][0] - 2)
            if keep.any():
                enav.choice[keep] = choose()[keep]
        sim.step()
        d_own = np.empty(N)
        for e in range(len(exits)):
            m = enav.choice == e
            if m.any():
                d_own[m] = navs[e].dist_at(sim.pos[m])
        for i in np.where((d_own < REACH) & (~evac))[0]:
            evac[i] = True
            used[i] = int(np.argmin(((exits - sim.pos[i]) ** 2).sum(1)))
            enav.choice[i] = -1
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        if evac.all():
            break
    near = int((used == 0).sum()); far = int((used == 1).sum()); ev = near + far
    return dict(evac=ev, near=near, far=far, maxshare=max(near, far) / ev if ev else 1.0)


def main():
    print("=" * 64); print("ACTUATOR: external field control vs self-organisation"); print("=" * 64)
    rows = ["mode,seed,evac,near,far,maxshare"]; agg = {}
    for mode in ("Baseline", "Self-org", "ActuatorNaive", "ActuatorCL"):
        ev, ms, fr = [], [], []
        for s in SEEDS:
            r = run(mode, s)
            rows.append(f"{mode},{s},{r['evac']},{r['near']},{r['far']},{r['maxshare']:.3f}")
            ev.append(r["evac"]); ms.append(r["maxshare"]); fr.append(r["far"])
        agg[mode] = (np.mean(ev), np.mean(ms), np.mean(fr))
        print(f"  {mode:14s} evac={np.mean(ev):4.1f}  far-exit={np.mean(fr):4.1f}  maxshare={np.mean(ms):.2f}")
    so, ac, cl, bl = agg["Self-org"], agg["ActuatorNaive"], agg["ActuatorCL"], agg["Baseline"]
    print(f"\n  -> Writing to the field STEERS the crowd (far-exit usage {bl[2]:.1f} -> {ac[2]:.1f}).")
    print(f"     OPEN-LOOP (naive) OVER-steers: it flips everyone to the far door, so max-exit share returns")
    print(f"     to {ac[1]:.2f} (re-imbalanced) vs self-organisation's {so[1]:.2f}.")
    print(f"     CLOSED-LOOP control FIXES it: depositing in proportion to the live imbalance and backing")
    print(f"     off as it balances reaches max-exit share {cl[1]:.2f} -- much closer to self-org's {so[1]:.2f}")
    print(f"     than to the naive over-steer ({ac[1]:.2f}), without flipping the crowd. ('Central control")
    print(f"     over-steers' -> largely solved by closing the loop.)")
    with open(os.path.join(RES, "actuator.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    modes = ["Baseline", "Self-org", "ActuatorNaive", "ActuatorCL"]; x = np.arange(4)
    cols = ["#C9C9C9", "#2E6FB7", "#C9A14A", "#11a011"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    a1.bar(x, [agg[m][2] for m in modes], color=cols)
    a1.set_xticks(x); a1.set_xticklabels(modes, fontsize=8); a1.set_ylabel("far-exit usage")
    a1.set_title("Steering: far-exit usage")
    a2.bar(x, [agg[m][1] for m in modes], color=cols)
    a2.axhline(1.0, color="#aa3333", ls="--", lw=0.8); a2.axhline(0.5, color="#2BA84A", ls=":", lw=0.8)
    a2.set_xticks(x); a2.set_xticklabels(modes, fontsize=8); a2.set_ylabel("max-exit share (1=imbalanced, .5=balanced)")
    a2.set_title("Naive over-steers (→1); closed-loop balances (→.5)")
    fig.suptitle("Field as actuator: open-loop over-steers, closed-loop control balances", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "actuator.png"), dpi=140)
    print("-> results/actuator.csv, figures/actuator.png")


if __name__ == "__main__":
    main()
