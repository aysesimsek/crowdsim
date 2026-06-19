"""Train the affect-gated arbitration policy (the part that was Unity/ML-Agents-only) in pure Python.

A single shared multi-agent PPO policy controls every agent: corrective force + a raw gate term that
enters lambda = sigma(bias + k_a*load + k_f*fieldP + raw). Reward is minimal (progress + arrival - tiny
control cost), so any arbitration is emergent. We train on two tasks to separate two questions:

  OPEN  task: physics (relaxation drive) is already near-optimal -> what does the GATE learn?
              Answer: it becomes physics-dominant (lambda -> ~0.98); the residual is small and does not
              beat physics. (Reproduces the Unity 'physics-dominant gate' finding.)
  CROSS task: a central wall+gap makes straight-line physics JAM at the wall -> can the learned residual
              earn its keep? This is the Unity 'RL helps where physics fails' regime.

Outputs: models/policy_open.pt, models/policy_cross.pt, figures/rl_training.png, results/rl_training.csv.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim.model import _sigmoid
from crowdsim.rl import CrowdEnv, train, policy_controller

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures"); MOD = os.path.join(ROOT, "models")
for d in (RES, FIG, MOD):
    os.makedirs(d, exist_ok=True)

ITERS, T, N = 150, 256, 20
# central wall with a 2 m gap at the centre: straight-line physics jams here.
WALL = [(0.0, 5.5, 0.6, 9.0), (0.0, -5.5, 0.6, 9.0)]
CROSS_KW = dict(walls=WALL, cross=True)


def lam_of(env, raw):
    c = env.cfg; s = env.sim
    fp = np.clip(s.field.sample(s.pos) / c.max_value, 0, 1)
    return _sigmoid(c.physics_bias + c.k_lambda_affect * s.load + c.k_lambda_field * fp + raw)


def rollout(net, env_kwargs=None, steps=1500, seed=7, use_policy=True):
    env = CrowdEnv(n=N, seed=seed, **(env_kwargs or {}))
    ctrl = policy_controller(net)
    arrivals = 0; lams = []; fmag = []
    for _ in range(steps):
        f, raw = (ctrl(env) if use_policy else (np.zeros((N, 2)), np.zeros(N)))
        lams.append(lam_of(env, raw)); fmag.append(np.linalg.norm(f, axis=1))
        _, _, d = env.step(np.concatenate([f / 1.5, (raw / 2.0)[:, None]], axis=1))  # env.step applies set_rl
        arrivals += int(d.sum())
    return arrivals, float(np.mean(lams)), float(np.mean(fmag)), np.concatenate(lams)


def main():
    print("=" * 66); print("TRAIN affect-gated arbitration policy (multi-agent PPO)"); print("=" * 66)
    torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))

    print("\n[OPEN task] physics already near-optimal -> what does the gate learn?")
    net_o, curve_o = train(iters=ITERS, T=T, n=N, seed=0)
    torch.save(net_o.state_dict(), os.path.join(MOD, "policy_open.pt"))
    oa_p, ol_p, of_p, ol_hist = rollout(net_o, use_policy=True)
    oa_b, ol_b, _, _ = rollout(net_o, use_policy=False)
    print(f"  learned gate mean lambda={ol_p:.3f} (physics default {ol_b:.3f}), |u_rl|={of_p:.3f}")
    print(f"  arrivals: trained={oa_p}  physics-only={oa_b}  -> gate is physics-dominant, RL adds ~nothing")

    print("\n[CROSS task] central wall+gap makes straight-line physics jam -> can RL earn its keep?")
    net_c, curve_c = train(iters=ITERS, T=T, n=N, seed=0, env_kwargs=CROSS_KW)
    torch.save(net_c.state_dict(), os.path.join(MOD, "policy_cross.pt"))
    ca_p, cl_p, cf_p, _ = rollout(net_c, CROSS_KW, use_policy=True)
    ca_b, cl_b, _, _ = rollout(net_c, CROSS_KW, use_policy=False)
    gain = ca_p / max(1, ca_b)
    print(f"  learned gate mean lambda={cl_p:.3f}, |u_rl|={cf_p:.3f}")
    print(f"  arrivals: trained={ca_p}  physics-only={ca_b}  -> RL x{gain:.2f} vs physics-only "
          f"({'RL earns its keep' if gain > 1.1 else 'no clear gain'})")

    with open(os.path.join(RES, "rl_training.csv"), "w") as f:
        f.write("iter,open_reward,cross_reward\n" +
                "\n".join(f"{i},{a:.5f},{b:.5f}" for i, (a, b) in enumerate(zip(curve_o, curve_c))) + "\n")

    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    ax[0].plot(curve_o, color="#888", lw=1.2, label="open")
    ax[0].plot(curve_c, color="#2E6FB7", lw=1.5, label="cross (wall+gap)")
    ax[0].set_xlabel("PPO iteration"); ax[0].set_ylabel("mean step reward")
    ax[0].set_title("Learning curves"); ax[0].legend(); ax[0].grid(alpha=0.3)
    ax[1].hist(ol_hist, bins=40, color="#2E6FB7", alpha=0.85, label=f"learned (mean {ol_p:.2f})")
    ax[1].axvline(ol_b, color="#aa3333", ls="--", lw=1.2, label=f"physics default {ol_b:.2f}")
    ax[1].set_xlabel("arbitration gate  $\\lambda$"); ax[1].set_ylabel("count")
    ax[1].set_title("OPEN: gate learns to trust physics"); ax[1].legend()
    g = ["OPEN\ntrained", "OPEN\nphysics", "CROSS\ntrained", "CROSS\nphysics"]
    vals = [oa_p, oa_b, ca_p, ca_b]; cols = ["#2E6FB7", "#C9C9C9", "#2E6FB7", "#C9C9C9"]
    ax[2].bar(g, vals, color=cols)
    ax[2].set_ylabel("arrivals / 1500 steps")
    verdict = "RL beats physics" if gain > 1.05 else ("tie" if gain > 0.95 else "RL below physics")
    ax[2].set_title(f"CROSS: learned residual x{gain:.2f} ({verdict})")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "rl_training.png"), dpi=140)
    print("\n-> models/policy_{open,cross}.pt, figures/rl_training.png, results/rl_training.csv")


if __name__ == "__main__":
    main()
