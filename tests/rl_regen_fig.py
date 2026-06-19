"""Regenerate figures/rl_training.png from the saved policies (no retraining)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from crowdsim.rl import ActorCritic
from experiments.train_rl import rollout, CROSS_KW, MOD, FIG, RES

no = ActorCritic(); no.load_state_dict(torch.load(os.path.join(MOD, "policy_open.pt"))); no.eval()
nc = ActorCritic(); nc.load_state_dict(torch.load(os.path.join(MOD, "policy_cross.pt"))); nc.eval()
oa_p, ol_p, of_p, ol_hist = rollout(no, use_policy=True)
oa_b, ol_b, _, _ = rollout(no, use_policy=False)
ca_p, cl_p, cf_p, _ = rollout(nc, CROSS_KW, use_policy=True)
ca_b, cl_b, _, _ = rollout(nc, CROSS_KW, use_policy=False)
gain = ca_p / max(1, ca_b)
# learning curves from the csv
it, oc, cc = [], [], []
for ln in open(os.path.join(RES, "rl_training.csv")).read().splitlines()[1:]:
    a, b, c = ln.split(","); it.append(int(a)); oc.append(float(b)); cc.append(float(c))

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].plot(oc, color="#888", lw=1.2, label="open"); ax[0].plot(cc, color="#2E6FB7", lw=1.5, label="cross (wall+gap)")
ax[0].set_xlabel("PPO iteration"); ax[0].set_ylabel("mean step reward"); ax[0].set_title("Learning curves"); ax[0].legend(); ax[0].grid(alpha=0.3)
ax[1].hist(ol_hist, bins=40, color="#2E6FB7", alpha=0.85, label=f"learned (mean {ol_p:.2f})")
ax[1].axvline(ol_b, color="#aa3333", ls="--", lw=1.2, label=f"physics default {ol_b:.2f}")
ax[1].set_xlabel("arbitration gate  $\\lambda$"); ax[1].set_ylabel("count"); ax[1].set_title("OPEN: gate learns to trust physics"); ax[1].legend()
g = ["OPEN\ntrained", "OPEN\nphysics", "CROSS\ntrained", "CROSS\nphysics"]; vals = [oa_p, oa_b, ca_p, ca_b]
ax[2].bar(g, vals, color=["#2E6FB7", "#C9C9C9", "#2E6FB7", "#C9C9C9"])
verdict = "RL beats physics" if gain > 1.05 else ("tie" if gain > 0.95 else "RL below physics")
ax[2].set_ylabel("arrivals / 1500 steps"); ax[2].set_title(f"CROSS: learned residual x{gain:.2f} ({verdict})")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "rl_training.png"), dpi=140)
print(f"regen ok: OPEN lambda={ol_p:.3f} arr {oa_p}/{oa_b}; CROSS lambda={cl_p:.3f} arr {ca_p}/{ca_b} (x{gain:.2f})")
