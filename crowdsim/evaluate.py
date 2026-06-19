"""Layout evaluation — the core of the affect-field design clinic.

evaluate_layout(scenario) simulates a crowd (navigation-routed physics, optionally a learned RL policy)
and returns a safety report:
  - egress: evacuated, t50, t90
  - affect-field RISK MAP: the time-averaged field is a crush-risk / congestion heatmap (the novel
    diagnostic) -- high sustained field = sustained crowding pressure
  - hotspots: local maxima of the risk map (x, z, severity)
  - exit balance: per-exit usage share + the binding (most-loaded) exit
  - peak local density, Moran's I

This is the building block the recommender A/B-tests design modifications against.
"""
import numpy as np
from .model import Config, Simulation
from .navigation import NavField
from . import metrics

REACH = 0.6


class _GroupNav:
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


def _build_navs(cfg, sc, inflate=0.35, nav_cell=0.4):
    navs = []
    for i in range(len(sc.spawns)):
        ex = sc.exits if sc.goals is None else [sc.exits[k] for k in sc.goals[i]]
        navs.append(NavField(cfg, sc.walls, ex, inflate=inflate, nav_cell=nav_cell))
    return navs


def _spawn(sc, n, rng):
    areas = np.array([(x1 - x0) * (z1 - z0) for (x0, x1, z0, z1) in sc.spawns], float)
    counts = np.maximum(1, np.round(n * areas / areas.sum()).astype(int))
    pos, grp = [], []
    for i, (x0, x1, z0, z1) in enumerate(sc.spawns):
        k = counts[i]
        pos.append(np.c_[rng.uniform(x0, x1, k), rng.uniform(z0, z1, k)])
        grp.append(np.full(k, i))
    return np.vstack(pos), np.concatenate(grp)


def _policy_step(net, sim, cfg, nav, side):
    """Build the rl.OBS_DIM observation for an arbitrary layout and return (force, lambda_raw)."""
    import torch
    vmax = cfg.stressed_speed
    p = sim.pos / (side / 2)
    v = sim.vel / vmax
    fp = np.clip(sim.field.sample(sim.pos) / cfg.max_value, 0, 1)
    gdir = nav.direction_at(sim.pos)
    gd = np.clip(nav.dist_at(sim.pos) / side, 0, 1)
    d = sim.pos[:, None, :] - sim.pos[None, :, :]
    dist = np.linalg.norm(d, axis=2); np.fill_diagonal(dist, np.inf)
    dens = np.clip((dist < cfg.sense_radius).sum(1) / cfg.dens_cap, 0, 1)
    obs = np.column_stack([p, v, sim.load, sim.fatigue, fp, gdir, gd, dens]).astype(np.float32)
    with torch.no_grad():
        mu, _, _ = net(torch.as_tensor(obs))
    a = mu.numpy()
    return np.clip(a[:, :2] * 1.5, -3, 3), np.clip(a[:, 2] * 2.0, -4, 4)


def _hotspots(risk, cfg, sc, k=5, frac=0.55):
    """Local maxima of the risk grid above frac*max -> [(x, z, severity 0..1)]."""
    R = risk; mx = R.max()
    if mx <= 1e-9:
        return []
    nx, nz = R.shape
    cand = []
    for i in range(1, nx - 1):
        for j in range(1, nz - 1):
            v = R[i, j]
            if v < frac * mx:
                continue
            if v >= R[i-1:i+2, j-1:j+2].max() - 1e-9:
                x = -sc.width / 2 + (i + 0.5) * cfg.cell
                z = -sc.height / 2 + (j + 0.5) * cfg.cell
                cand.append((x, z, float(v / mx)))
    cand.sort(key=lambda t: -t[2])
    # suppress near-duplicates
    out = []
    for x, z, s in cand:
        if all((x - ox) ** 2 + (z - oz) ** 2 > 4.0 for ox, oz, _ in out):
            out.append((x, z, s))
        if len(out) >= k:
            break
    return out


def evaluate_layout(scenario, seeds=(0, 1, 2), n=45, maxsec=50.0, policy=None, field_on=True,
                    field_route=False, k_field=20.0, relax_drive=True, inflate=0.35, nav_cell=0.4):
    sc = scenario
    nexit = len(sc.exits)
    ev_l, t50_l, t80_l, t90_l, pk_l, mor_l = [], [], [], [], [], []
    use_acc = np.zeros(nexit)
    risk_acc = None
    rt = 40  # re-choose interval in steps (~2 s at dt=0.05)
    for seed in seeds:
        cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                     field_gain=1.10 if field_on else 0.0, field_deposit_gain=0.7 if field_on else 0.0,
                     relax_drive=relax_drive)
        rng = np.random.default_rng(seed)
        sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
        pos, grp = _spawn(sc, n, rng); m = len(pos); sim.spawn(pos)
        exits = np.array(sc.exits, float)
        if field_route:                      # affect-field exit guidance: per-exit navs, dynamic choice
            navs = [NavField(cfg, sc.walls, [tuple(e)], inflate=inflate, nav_cell=nav_cell) for e in sc.exits]
            appr = []
            for e in sc.exits:
                v = -np.array(e, float); nv = np.linalg.norm(v)
                v = v / nv if nv > 1e-6 else np.array([1.0, 0.0])
                appr.append((e[0] + 1.5 * v[0], e[1] + 1.5 * v[1]))

            def choose():
                dd = np.stack([navs[e].dist_at(sim.pos) for e in range(nexit)], axis=1)
                pen = np.array([k_field * sim.field.sample_point(ax, az) for (ax, az) in appr])
                return np.argmin(dd + pen[None, :], axis=1)
            gnav = _GroupNav(navs, choose())
        else:                                # nearest-exit routing (baseline)
            navs = _build_navs(cfg, sc, inflate, nav_cell); gnav = _GroupNav(navs, grp.copy())
        sim.nav = gnav
        evac = np.zeros(m, bool); evac_t = np.full(m, -1.0); used = np.full(m, -1)
        steps = int(maxsec / cfg.dt); hw, hh = sc.width / 2, sc.height / 2
        risk = np.zeros_like(sim.field.F); rs = 0; parked = 0; denspk = 0.0; mor = 0.0; ms = 0
        for t in range(steps):
            if field_route and t % rt == 0:
                keep = (~evac) & (gnav.group >= 0)
                if keep.any():
                    gnav.group[keep] = choose()[keep]
            if policy is not None:
                f, raw = _policy_step(policy, sim, cfg, gnav, sc.width)
                sim.set_rl(f, raw)
            sim.step()
            d = gnav.dist_at(sim.pos)
            for i in np.where((d < REACH) & (~evac))[0]:
                evac[i] = True; evac_t[i] = t * cfg.dt
                used[i] = int(np.argmin(((exits - sim.pos[i]) ** 2).sum(1)))
                gnav.group[i] = -1
                sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
                sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
            if t % 10 == 0:
                act = ~evac
                if act.any():
                    denspk = max(denspk, metrics.peak_local_density(sim.pos[act]))
                risk += sim.field.F; rs += 1
                mor += sim.field.morans_i(); ms += 1
            if evac.all():
                break
        ev_l.append(int(evac.sum()))
        ts = np.sort(evac_t[evac_t >= 0])
        t50_l.append(float(ts[int(np.ceil(0.5 * m)) - 1]) if len(ts) >= int(np.ceil(0.5 * m)) else -1.0)
        t80_l.append(float(ts[int(np.ceil(0.8 * m)) - 1]) if len(ts) >= int(np.ceil(0.8 * m)) else -1.0)
        t90_l.append(float(ts[int(np.ceil(0.9 * m)) - 1]) if len(ts) >= int(np.ceil(0.9 * m)) else -1.0)
        pk_l.append(denspk); mor_l.append(mor / max(1, ms))
        for e in range(nexit):
            use_acc[e] += int((used == e).sum())
        risk_acc = (risk / max(1, rs)) if risk_acc is None else risk_acc + risk / max(1, rs)
    risk_acc /= len(seeds)
    use = use_acc / max(1, use_acc.sum())
    binding = int(np.argmax(use_acc)) if nexit > 1 else 0
    balance = float(use.max()) if nexit > 1 else 1.0
    return dict(
        evacuated=float(np.mean(ev_l)), n=n, t50=float(np.mean(t50_l)),
        t80=float(np.mean(t80_l)), t90=float(np.mean(t90_l)),
        peak_density=float(np.mean(pk_l)), morans_i=float(np.mean(mor_l)),
        exit_usage=use.tolist(), binding_exit=binding, exit_imbalance=balance,
        hotspots=_hotspots(risk_acc, Config(width=sc.width, height=sc.height), sc),
        risk=risk_acc)
