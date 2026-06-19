"""Run the trained RL-combined agents across the scenario library (physics vs physics+learned policy).

Loads models/policy_cross.pt and evaluates each scenario with and without the learned residual. The
policy was trained on open/cross tasks, so applying it to corners/bottlenecks/rooms is an out-of-
distribution transfer test: does the learned arbitration help, hurt, or (as the physics-dominant gate
predicts) roughly match physics on unseen layouts?
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from crowdsim.evaluate import evaluate_layout
from crowdsim.scenarios import SCENARIOS
from crowdsim.rl import ActorCritic

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures"); MOD = os.path.join(ROOT, "models")

NAMES = ["OpenSquare", "Bottleneck", "WideDoor", "Corner", "Crossing", "TJunction",
         "RoomToCorridor", "StadiumFunnel"]


def main():
    net = ActorCritic(); net.load_state_dict(torch.load(os.path.join(MOD, "policy_cross.pt"))); net.eval()
    print("=" * 64); print("RL-COMBINED across scenarios (physics vs physics+policy)"); print("=" * 64)
    rows = ["scenario,physics_evac,rl_evac,physics_t50,rl_t50"]
    phys, rl = [], []
    for nm in NAMES:
        sc = SCENARIOS[nm]
        rp = evaluate_layout(sc, seeds=(0, 1, 2))
        rr = evaluate_layout(sc, seeds=(0, 1, 2), policy=net)
        phys.append(rp["evacuated"]); rl.append(rr["evacuated"])
        rows.append(f"{nm},{rp['evacuated']:.1f},{rr['evacuated']:.1f},{rp['t50']:.1f},{rr['t50']:.1f}")
        print(f"  {nm:16s} evac physics={rp['evacuated']:4.1f}  RL={rr['evacuated']:4.1f}  "
              f"(d{rr['evacuated']-rp['evacuated']:+.1f})")
    d = np.array(rl) - np.array(phys)
    print(f"\n  mean delta (RL - physics) = {d.mean():+.2f} evacuated/scenario  "
          f"-> {'RL helps' if d.mean()>1 else ('RL hurts' if d.mean()<-1 else 'matches physics (physics-dominant gate)')}")
    with open(os.path.join(RES, "rl_scenarios.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    x = np.arange(len(NAMES)); w = 0.4
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(x - w/2, phys, w, label="physics", color="#C9C9C9")
    ax.bar(x + w/2, rl, w, label="physics + learned policy", color="#2E6FB7")
    ax.set_xticks(x); ax.set_xticklabels(NAMES, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("evacuated in 50s (of 45)"); ax.legend()
    ax.set_title("RL-combined agents across scenarios (OOD transfer)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "rl_scenarios.png"), dpi=140)
    print("-> results/rl_scenarios.csv, figures/rl_scenarios.png")


if __name__ == "__main__":
    main()
