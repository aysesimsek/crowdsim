"""Can the door specific flow (2.12, a bit above Seyfried's 1.9) be brought into band WITHOUT hurting the
corridor FD? Body size (contact_radius) sets how many bodies fit through a door but barely touches the
mid-density FD (where nobody is in contact). Sweep contact_radius; report door flow + FD-RMSE + jam."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
from crowdsim import Config, Simulation, NavField
from experiments.capacity_design import room
from experiments.validation_suite import weidmann

RHOS = np.array([1.0, 2.0, 3.0, 5.0])


def fd_speed(rho, cr, seed=0, side=10.0):
    n = max(6, int(rho * side * side))
    cfg = Config(width=side, height=side, boundary="torus", base_speed=1.34, stressed_speed=1.34,
                 field_gain=0.0, field_deposit_gain=0.0, contact_radius=cr)   # w_sep/ps_base/friction = calibrated defaults
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng)
    lim = side / 2 - 0.5
    sim.spawn(rng.uniform(-lim, lim, (n, 2)))
    sp = []
    for t in range(200):
        sim.set_targets(sim.pos + np.array([50.0, 0.0])); sim.step()
        if t > 110:
            sp.append(np.linalg.norm(sim.vel, axis=1).mean())
    return float(np.mean(sp))


def bottleneck(door_w, seed, cr, N=160, MAXSEC=60.0):
    sc = room(1, door_w)
    cfg = Config(width=sc.width, height=sc.height, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7, contact_radius=cr)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng); sim.set_walls(sc.walls)
    x0, x1, z0, z1 = sc.spawns[0]
    sim.spawn(np.c_[rng.uniform(x0, x1, N), rng.uniform(z0, z1, N)])
    nav = NavField(cfg, sc.walls, sc.exits, inflate=0.2); sim.nav = nav
    evac = np.zeros(N, bool); hw, hh = sc.width / 2, sc.height / 2; parked = 0; cum = []
    for t in range(int(MAXSEC / cfg.dt)):
        sim.step()
        d = nav.dist_at(sim.pos)
        for i in np.where((d < 0.6) & (~evac))[0]:
            evac[i] = True
            sim.pos[i] = [-hw + 0.5 + (parked % 18) * 0.45, -hh + 0.4 + (parked // 18) * 0.45]
            sim.vel[i] = 0.0; sim.load[i] = 0.0; parked += 1
        cum.append(int(evac.sum()))
    cum = np.array(cum); tt = np.arange(len(cum)) * cfg.dt
    m = (tt >= 8.0) & (tt <= 28.0) & (cum < N - 3)
    if m.sum() < 5:
        m = (tt >= 4) & (cum < N - 3)
    return np.polyfit(tt[m], cum[m], 1)[0] / door_w


def main():
    wd = weidmann(RHOS)
    print("=" * 70); print("Door-flow vs body size (contact_radius)"); print("=" * 70)
    print(f"  target: door ~1.9 (Seyfried), FD-RMSE(ρ≤3)<0.10, jam (v@5<0.15)")
    for cr in (0.22, 0.24, 0.26):
        v = np.array([fd_speed(r, cr) for r in RHOS])
        rmse = float(np.sqrt(np.mean((v[:3] - wd[:3]) ** 2)))
        jam = v[-1] < 0.15
        door = float(np.mean([bottleneck(2.0, s, cr) for s in (0, 1)]))
        ok = (door <= 2.0) and (rmse < 0.10) and jam
        tag = " <== door in band + FD kept + jams" if ok else ""
        print(f"  cr={cr:.2f} (Ø{2*cr:.2f}m)  door={door:.2f}  FD-RMSE={rmse:.3f}  v@5={v[-1]:.2f} jam={'Y' if jam else 'n'}{tag}")


if __name__ == "__main__":
    main()
