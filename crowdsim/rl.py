"""Multi-agent PPO (parameter sharing) for the learned affect-gated arbitration -- the part that was
Unity/ML-Agents-only. One shared policy controls every agent; it outputs a corrective force u_rl and a
raw gate term that enters lambda = sigma(bias + k_a*load + k_f*fieldP + raw). Reward is minimal
(progress to goal + success - tiny control penalty), so any arbitration the policy learns is emergent.
Requires torch (CPU is fine). The trained policy is the 2D counterpart of the Unity ABC_Crowd model.
"""
import numpy as np
import torch
import torch.nn as nn

from .model import Config, Simulation

OBS_DIM = 11   # pos(2) vel(2) load fatigue fieldP goal-dir(2) goal-dist density
ACT_DIM = 3    # corrective force (2) + raw gate term (1)
RL_FORCE = 1.5      # corrective-force multiplier
RAW_SCALE = 2.0     # how far the policy can shift the gate


class ActorCritic(nn.Module):
    def __init__(self, obs=OBS_DIM, act=ACT_DIM, h=64):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act)
        self.log_std = nn.Parameter(-0.5 * torch.ones(act))
        self.v = nn.Linear(h, 1)

    def forward(self, x):
        t = self.trunk(x)
        return self.mu(t), self.log_std.exp(), self.v(t).squeeze(-1)

    def act(self, x):
        mu, std, v = self(x)
        d = torch.distributions.Normal(mu, std)
        a = d.sample()
        return a, d.log_prob(a).sum(-1), v

    def evaluate(self, x, a):
        mu, std, v = self(x)
        d = torch.distributions.Normal(mu, std)
        return d.log_prob(a).sum(-1), d.entropy().sum(-1), v


class CrowdEnv:
    """Cross-to-goal task; agents respawn with a new goal on arrival (continuous episodes).

    cross=False: open arena, random spawn+goal (physics alone is near-optimal here).
    cross=True : spawn LEFT, goal RIGHT, with a central wall+gap (walls). Straight-line physics jams
                 at the wall, so the policy must learn to detour through the gap -- this is where the
                 learned residual earns its keep (the Unity 'RL helps where physics fails' regime)."""
    def __init__(self, n=20, side=20.0, seed=0, field_on=True, walls=None, cross=False):
        self.n, self.side, self.cross = n, side, cross
        self.cfg = Config(width=side, height=side, boundary="walls", max_value=50.0,
                          field_gain=1.10 if field_on else 0.0,
                          field_deposit_gain=0.7 if field_on else 0.0)
        self.rng = np.random.default_rng(seed)
        self.sim = Simulation(self.cfg, self.rng)
        if walls:
            self.sim.set_walls(walls)
        self.vmax = self.cfg.stressed_speed
        self.reset()

    def _spawn(self, k):
        lim = self.side / 2 - 1.0
        if self.cross:
            return np.c_[self.rng.uniform(-lim, -3.0, k), self.rng.uniform(-lim, lim, k)]
        return self.rng.uniform(-lim, lim, size=(k, 2))

    def _goal(self, k):
        lim = self.side / 2 - 1.0
        if self.cross:
            return np.c_[self.rng.uniform(3.0, lim, k), self.rng.uniform(-lim, lim, k)]
        return self.rng.uniform(-lim, lim, size=(k, 2))

    def reset(self):
        self.sim.spawn(self._spawn(self.n), self._goal(self.n))
        self.prevd = np.linalg.norm(self.sim.pos - self.sim.target, axis=1)
        return self.obs()

    def obs(self):
        s = self.sim
        p = s.pos / (self.side / 2)
        v = s.vel / self.vmax
        fp = np.clip(s.field.sample(s.pos) / self.cfg.max_value, 0, 1)
        g = s.target - s.pos
        gd = np.linalg.norm(g, axis=1)
        gdir = g / np.maximum(gd[:, None], 1e-6)
        d = s.pos[:, None, :] - s.pos[None, :, :]
        dist = np.linalg.norm(d, axis=2); np.fill_diagonal(dist, np.inf)
        dens = np.clip((dist < self.cfg.sense_radius).sum(1) / self.cfg.dens_cap, 0, 1)
        return np.column_stack([p, v, s.load, s.fatigue, fp, gdir,
                                np.clip(gd / self.side, 0, 1), dens]).astype(np.float32)

    def step(self, act):
        s = self.sim
        force = np.clip(act[:, :2] * RL_FORCE, -3, 3)
        raw = np.clip(act[:, 2] * RAW_SCALE, -4, 4)
        s.set_rl(force, raw)
        s.step()
        d = np.linalg.norm(s.pos - s.target, axis=1)
        rew = (self.prevd - d) - 1e-3 * (force ** 2).sum(1)      # progress - control cost
        done = d < 1.0
        rew = rew + done * 1.0                                    # success bonus
        if done.any():                                            # respawn arrived agents
            k = int(done.sum())
            s.pos[done] = self._spawn(k)
            s.target[done] = self._goal(k)
            s.vel[done] = 0.0
            d[done] = np.linalg.norm(s.pos[done] - s.target[done], axis=1)
        self.prevd = d
        return self.obs(), rew.astype(np.float32), done


def train(iters=120, T=256, n=20, lr=3e-4, gamma=0.99, lam=0.95, clip=0.2, epochs=4, seed=0,
          env_kwargs=None, log=print):
    torch.manual_seed(seed)
    env = CrowdEnv(n=n, seed=seed, **(env_kwargs or {}))
    net = ActorCritic()
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env.obs()
    curve = []
    for it in range(iters):
        O, A, LP, R, V, D = [], [], [], [], [], []
        for _ in range(T):
            ot = torch.as_tensor(obs)
            with torch.no_grad():
                a, lp, v = net.act(ot)
            no, r, d = env.step(a.numpy())
            O.append(ot); A.append(a); LP.append(lp); R.append(torch.as_tensor(r)); V.append(v); D.append(torch.as_tensor(d.astype(np.float32)))
            obs = no
        with torch.no_grad():
            _, _, lastv = net(torch.as_tensor(obs))
        V.append(lastv)
        R = torch.stack(R); D = torch.stack(D); Vs = torch.stack(V)          # (T,n),(T,n),(T+1,n)
        adv = torch.zeros_like(R); gae = torch.zeros(n)
        for t in reversed(range(T)):
            nonterm = 1.0 - D[t]
            delta = R[t] + gamma * Vs[t + 1] * nonterm - Vs[t]
            gae = delta + gamma * lam * nonterm * gae
            adv[t] = gae
        ret = adv + Vs[:T]
        O = torch.stack(O).reshape(-1, OBS_DIM); A = torch.stack(A).reshape(-1, ACT_DIM)
        LP = torch.stack(LP).reshape(-1); adv = adv.reshape(-1); ret = ret.reshape(-1)
        adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        idx = np.arange(len(O))
        for _ in range(epochs):
            np.random.shuffle(idx)
            for b in range(0, len(idx), 1024):
                j = idx[b:b + 1024]
                nlp, ent, v = net.evaluate(O[j], A[j])
                ratio = (nlp - LP[j]).exp()
                pg = -torch.min(ratio * adv[j], torch.clamp(ratio, 1 - clip, 1 + clip) * adv[j]).mean()
                vl = ((v - ret[j]) ** 2).mean()
                loss = pg + 0.5 * vl - 0.01 * ent.mean()
                opt.zero_grad(); loss.backward(); opt.step()
        curve.append(float(R.mean()))
        if (it + 1) % 10 == 0:
            log(f"  iter {it+1:3d}/{iters}  mean step reward={np.mean(curve[-10:]):+.4f}")
    return net, curve


def policy_controller(net):
    """Deterministic controller (sim) -> (force, lambda_raw) for evaluation/inference."""
    def ctrl(env):
        with torch.no_grad():
            mu, _, _ = net(torch.as_tensor(env.obs()))
        a = mu.numpy()
        return np.clip(a[:, :2] * RL_FORCE, -3, 3), np.clip(a[:, 2] * RAW_SCALE, -4, 4)
    return ctrl
