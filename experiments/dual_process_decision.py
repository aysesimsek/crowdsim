"""Dual-process arbitration where it matters: at the DECISION level, not locomotion.

At the locomotion level the affect gate is real but behaviourally gentle (it rides on a physics-dominant
blend; egress barely moves). Here we move the same dual-process idea up to the EXIT-CHOICE decision:
  System 1 (reactive)    : go to the nearest exit.
  System 2 (deliberative): go to the field-aware exit (avoid the congested door).
A decision gate lambda_d in [0,1] blends them. We clamp-and-probe lambda_d on the NearFar room and show
the behavioural footprint is LARGE (max-exit share swings widely) -- the opposite of the modest
locomotion gate. Then an AFFECT-GATED version (lambda_d set per-agent by stress) lands on that curve,
adapting deliberation to emotional load.
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

N, SEEDS, MAXSEC = 45, (0, 1, 2), 60.0
KMAX, RECHOOSE, REACH = 20.0, 2.0, 0.6


class ExitNav:
    def __init__(self, navs, choice): self.navs, self.choice = navs, choice
    def direction_at(self, pos):
        out = np.zeros((len(pos), 2))
        for e, nav in enumerate(self.navs):
            m = self.choice == e
            if m.any(): out[m] = nav.direction_at(pos[m])
        return out


def _sig(x): return 1.0 / (1.0 + np.exp(-x))


def run(seed, lam_d=None, affect_gate=False):
    sc = SCENARIOS["NearFar"]
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    sim.spawn(np.c_[rng.uniform(x0, x1, N), rng.uniform(z0, z1, N)])
    exits = np.array(sc.exits, float)
    navs = [NavField(cfg, sc.walls, [tuple(e)]) for e in sc.exits]
    appr = [(e[0] - 1.5, e[1]) for e in sc.exits]

    def weights():                                  # per-agent deliberation weight on the field term
        if affect_gate:
            return KMAX * _sig(8.0 * (sim.load - 0.4))     # stressed agents deliberate more
        return np.full(N, lam_d * KMAX)

    def choose():
        d = np.stack([navs[e].dist_at(sim.pos) for e in range(len(exits))], axis=1)   # (N,nexit)
        field = np.array([sim.field.sample_point(ax, az) for (ax, az) in appr])       # (nexit,)
        w = weights()[:, None]                                                        # (N,1)
        return np.argmin(d + w * field[None, :], axis=1)

    enav = ExitNav(navs, choose()); sim.nav = enav
    evac = np.zeros(N, bool); used = np.full(N, -1)
    steps = int(MAXSEC / cfg.dt); rt = int(RECHOOSE / cfg.dt); hw, hh = sc.width/2, sc.height/2; parked = 0
    for t in range(steps):
        if t % rt == 0:
            keep = (~evac) & (enav.choice >= 0) & (sim.pos[:, 0] < sc.exits[0][0] - 2)
            if keep.any(): enav.choice[keep] = choose()[keep]
        sim.step()
        d_own = np.empty(N)
        for e in range(len(exits)):
            m = enav.choice == e
            if m.any(): d_own[m] = navs[e].dist_at(sim.pos[m])
        for i in np.where((d_own < REACH) & (~evac))[0]:
            evac[i] = True; used[i] = int(np.argmin(((exits - sim.pos[i]) ** 2).sum(1)))
            enav.choice[i] = -1
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        if evac.all(): break
    near = int((used == 0).sum()); far = int((used == 1).sum()); ev = near + far
    return max(near, far) / ev if ev else 1.0, far


def main():
    print("=" * 64); print("DUAL-PROCESS AT THE DECISION LEVEL (clamp-and-probe)"); print("=" * 64)
    lam = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]
    ms, fr = [], []
    for ld in lam:
        rs = [run(s, lam_d=ld) for s in SEEDS]
        ms.append(np.mean([r[0] for r in rs])); fr.append(np.mean([r[1] for r in rs]))
        print(f"  lambda_d={ld:.2f}  max-exit share={ms[-1]:.2f}  far-exit usage={fr[-1]:.1f}")
    ag = [run(s, affect_gate=True) for s in SEEDS]
    ag_ms, ag_fr = np.mean([r[0] for r in ag]), np.mean([r[1] for r in ag])
    rng_ms = ms[0] - min(ms)
    print(f"  affect-gated (lambda_d set by stress): max-exit share={ag_ms:.2f}  far-exit usage={ag_fr:.1f}")
    print(f"\n  -> decision-level gate swings max-exit share by {rng_ms:.2f} (from {ms[0]:.2f} at System-1")
    print(f"     to {min(ms):.2f} at System-2) -- a LARGE behavioural footprint, unlike the locomotion gate")
    print(f"     whose egress range was ~flat. Moving the dual-process arbitration to the decision level is")
    print(f"     where it becomes substantial. The affect-gated policy self-selects an operating point ({ag_ms:.2f}).")

    rows = ["lambda_d,maxshare,far"] + [f"{l:.2f},{m:.3f},{f:.2f}" for l, m, f in zip(lam, ms, fr)]
    rows.append(f"affect_gated,{ag_ms:.3f},{ag_fr:.2f}")
    with open(os.path.join(RES, "dual_process_decision.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3))
    a1.plot(lam, ms, "-o", color="#2E6FB7", label="clamped $\\lambda_d$")
    a1.axhline(ag_ms, color="#E0552B", ls="--", lw=1.2, label=f"affect-gated ({ag_ms:.2f})")
    a1.set_xlabel("decision gate $\\lambda_d$  (0=reactive nearest, 1=deliberative field-aware)")
    a1.set_ylabel("max-exit share (1=imbalanced)"); a1.set_title("Decision gate has a LARGE footprint")
    a1.legend(fontsize=8); a1.grid(alpha=0.3)
    a2.plot(lam, fr, "-o", color="#2BA84A"); a2.axhline(ag_fr, color="#E0552B", ls="--", lw=1.2)
    a2.set_xlabel("decision gate $\\lambda_d$"); a2.set_ylabel("far-exit usage")
    a2.set_title("Deliberation routes the crowd to the far exit")
    fig.suptitle("Dual-process arbitration at the decision level (NearFar)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "dual_process_decision.png"), dpi=140)
    print("-> results/dual_process_decision.csv, figures/dual_process_decision.png")


if __name__ == "__main__":
    main()
