"""An inference-time PRECISION GATE that cuts stuck-states.

In a dense bottleneck the reactive physics produces stuck states: an agent wants to move (far from its
exit) but is jammed and barely moving -- a high-'surprise' / low-precision situation. An active-inference
gate detects this (speed deficit) and, for those agents only, lowers lambda and injects a lateral escape
nudge (defer from the stalled physics to an exploratory action). We measure the stuck-state fraction over
the run with the gate off vs on. Reproduces the Unity precision-gate result (fewer stuck-states) in 2D.
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

N, SEEDS, MAXSEC = 60, (0, 1, 2, 3, 4), 45.0
STUCK_SPEED = 0.25        # below this (while far from exit) counts as stuck
NUDGE = 3.0               # lateral escape force magnitude
RAWGATE = -7.0            # strongly lower lambda for stuck agents so the escape action actually applies


def run(gate, seed):
    sc = SCENARIOS["Bottleneck"]
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    sim.spawn(np.c_[rng.uniform(x0, x1, N), rng.uniform(z0, z1, N)])
    nav = NavField(cfg, sc.walls, sc.exits); sim.nav = nav
    sign = np.where(rng.random(N) < 0.5, 1.0, -1.0)          # fixed lateral preference per agent
    evac = np.zeros(N, bool); hw, hh = sc.width / 2, sc.height / 2; parked = 0
    steps = int(MAXSEC / cfg.dt)
    stuck_series = []; ev_t = np.full(N, -1.0)
    for t in range(steps):
        d = nav.dist_at(sim.pos)
        spd = np.linalg.norm(sim.vel, axis=1)
        stuck = (~evac) & (d > 1.0) & (spd < STUCK_SPEED)
        if gate and stuck.any():
            ehat = nav.direction_at(sim.pos)
            perp = np.column_stack([-ehat[:, 1], ehat[:, 0]]) * sign[:, None]   # lateral to goal dir
            force = np.zeros((N, 2)); raw = np.zeros(N)
            force[stuck] = NUDGE * perp[stuck]; raw[stuck] = RAWGATE
            sim.set_rl(force, raw)
        else:
            sim.set_rl(np.zeros((N, 2)), np.zeros(N))
        sim.step()
        act = ~evac
        stuck_series.append(stuck.sum() / max(1, act.sum()))
        d = nav.dist_at(sim.pos)
        for i in np.where((d < 0.6) & (~evac))[0]:
            evac[i] = True; ev_t[i] = t * cfg.dt
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        if evac.all():
            break
    ts = np.sort(ev_t[ev_t >= 0]); half = int(np.ceil(0.5 * N))
    t50 = float(ts[half - 1]) if len(ts) >= half else -1.0
    return dict(stuck=float(np.mean(stuck_series)), evac=int(evac.sum()), t50=t50,
                series=np.array(stuck_series))


def main():
    print("=" * 60); print("PRECISION GATE: cutting stuck-states"); print("=" * 60)
    rows = ["mode,seed,stuck_frac,evac,t50"]; agg = {}; series = {}
    for mode, g in (("NoGate", False), ("PrecisionGate", True)):
        st, ev, series_runs = [], [], []
        for s in SEEDS:
            r = run(g, s)
            rows.append(f"{mode},{s},{r['stuck']:.4f},{r['evac']},{r['t50']:.2f}")
            st.append(r["stuck"]); ev.append(r["evac"]); series_runs.append(r["series"])
        agg[mode] = (np.mean(st), np.mean(ev))
        L = min(len(s) for s in series_runs)
        series[mode] = np.mean([s[:L] for s in series_runs], 0)
        print(f"  {mode:14s} mean stuck-fraction={np.mean(st):.3f}  evacuated={np.mean(ev):.1f}")
    ng, pg = agg["NoGate"], agg["PrecisionGate"]
    red = 100 * (ng[0] - pg[0]) / max(1e-9, ng[0])
    ecost = 100 * (ng[1] - pg[1]) / max(1e-9, ng[1])
    print(f"\n  -> precision gate reduces stuck-states by {red:.0f}% ({ng[0]:.3f} -> {pg[0]:.3f}) "
          f"at a modest egress cost ({ng[1]:.1f} -> {pg[1]:.1f}, -{ecost:.0f}%) -- it defers from the")
    print(f"     stalled physics to a lateral escape action, trading a little throughput for fewer jams.")

    with open(os.path.join(RES, "precision_gate.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    L = min(len(series["NoGate"]), len(series["PrecisionGate"]))
    tt = np.arange(L) * 0.05
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.plot(tt, series["NoGate"][:L], color="#C9A14A", lw=1.6, label="no gate")
    a1.plot(tt, series["PrecisionGate"][:L], color="#2E6FB7", lw=1.6, label="precision gate")
    a1.set_xlabel("time (s)"); a1.set_ylabel("stuck fraction"); a1.legend(); a1.set_title("Stuck-states over time")
    a2.bar(["no gate", "precision\ngate"], [ng[0], pg[0]], color=["#C9A14A", "#2E6FB7"])
    a2.set_ylabel("mean stuck fraction"); a2.set_title(f"Mean stuck-states ({red:.0f}% lower)")
    fig.suptitle("Precision gate: defer from stalled physics -> fewer stuck-states", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "precision_gate.png"), dpi=140)
    print("-> results/precision_gate.csv, figures/precision_gate.png")


if __name__ == "__main__":
    main()
