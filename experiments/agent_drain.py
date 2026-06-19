"""Agent-drain: the affect field is an AUTONOMOUS substrate.

Build the field with a milling crowd, then remove ALL agents at once and keep evolving the field. A
pairwise-contagion model would read ~0 instantly (affect is agent state); the stigmergic field instead
persists and decays at its own configured rate k (half-life ln2/k) -- spatial place-memory no
neighbour-graph model can hold. Reproduces the Unity agent-drain result in pure Python.
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
DECAY = 0.35
BUILD, OBSERVE = 25.0, 12.0


def main():
    print("=" * 56); print("AGENT-DRAIN (field autonomy)"); print("=" * 56)
    cfg = Config(width=SIDE, height=SIDE, boundary="torus", max_value=5.0, decay=DECAY)
    rng = np.random.default_rng(0)
    sim = Simulation(cfg, rng)
    n = 45
    lim = SIDE / 2 - 0.8
    sim.spawn(rng.uniform(-lim, lim, size=(n, 2)))
    sim.set_targets(rng.uniform(-lim, lim, size=(n, 2)))

    dt = cfg.dt
    rt = int(3.0 / dt)
    ts, fm = [], []
    bsteps, osteps = int(BUILD / dt), int(OBSERVE / dt)
    for t in range(bsteps):                      # build phase (agents deposit)
        if t % rt == 0:
            sim.set_targets(rng.uniform(-lim, lim, size=(n, 2)))
        sim.step()
    drain_val = sim.field.mean()
    drain_t = bsteps * dt
    sim.spawn(np.zeros((0, 2)))                   # DRAIN: remove all agents
    for t in range(osteps):                       # field evolves autonomously (decay only)
        sim.step()
        ts.append((bsteps + t) * dt); fm.append(sim.field.mean())

    ts = np.array(ts); fm = np.array(fm)
    # fit exponential decay rate from the post-drain field-mean
    rel = ts - drain_t
    mask = fm > 1e-6
    k_fit = float(-np.polyfit(rel[mask], np.log(fm[mask]), 1)[0]) if mask.sum() > 2 else float("nan")
    half = np.log(2) / k_fit if k_fit > 0 else float("nan")
    rem2 = float(fm[np.argmin(np.abs(rel - 2.0))] / drain_val)
    print(f"  field mean at drain (t={drain_t:.0f}s): {drain_val:.3f}")
    print(f"  fitted decay rate k = {k_fit:.3f} /s  (configured {DECAY})   half-life {half:.2f} s")
    print(f"  {rem2*100:.0f}% of drain-time affect remains 2 s after the crowd is gone "
          f"(a pairwise model would read 0)")

    with open(os.path.join(RES, "agent_drain.csv"), "w") as f:
        f.write("t,field_mean\n" + "\n".join(f"{a:.3f},{b:.4f}" for a, b in zip(ts, fm)) + "\n")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axvline(drain_t, color="#aa3333", ls="--", lw=1, label="all agents removed")
    ax.plot(ts, fm, color="#2E6FB7", lw=1.8, label="affect-field mean")
    ax.set_xlabel("time (s)"); ax.set_ylabel("field mean")
    ax.set_title(f"Agent-drain: field persists, decays at k={k_fit:.2f}/s (set {DECAY}), half-life {half:.1f}s")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "agent_drain.png"), dpi=150)
    print("-> results/agent_drain.csv, figures/agent_drain.png")


if __name__ == "__main__":
    main()
