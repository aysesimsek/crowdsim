"""Collective panic as a PHASE TRANSITION on the affect field (template experiment).

A venue-style square (torus, so density is uniform) of milling agents. We sweep crowd density (agent
count) and the field->affect feedback gain, and measure the order parameter (steady-state mean affective
load), a susceptibility (temporal fluctuation of the mean), the fraction panicked, and the field Moran's I.
A baseline calming (familiarity) gives headroom so a calm->panic transition is visible. Reproduces the
Unity PhaseTransitionExperiment result in pure Python (seconds).
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

SIDE = 18.0
WARMUP, MEASURE = 18.0, 12.0     # seconds
RETARGET = 3.0
FAM = 0.6                        # baseline calming (stabiliser) -> headroom for a visible transition


def steady(n, field_gain, seed):
    cfg = Config(width=SIDE, height=SIDE, boundary="torus", max_value=5.0, decay=0.35,
                 field_gain=field_gain, hard_contact=True)
    rng = np.random.default_rng(seed)
    sim = Simulation(cfg, rng)
    lim = SIDE / 2 - 0.8
    pos = rng.uniform(-lim, lim, size=(n, 2))
    sim.spawn(pos, fam=FAM)
    sim.set_targets(rng.uniform(-lim, lim, size=(n, 2)))
    steps_w = int(WARMUP / cfg.dt); steps_m = int(MEASURE / cfg.dt)
    rt = int(RETARGET / cfg.dt)
    series = []
    for t in range(steps_w + steps_m):
        if t % rt == 0:
            sim.set_targets(rng.uniform(-lim, lim, size=(n, 2)))
        sim.step()
        if t >= steps_w:
            series.append(sim.load.mean())
    series = np.array(series)
    return dict(M=float(series.mean()), chi=float(n * series.var()),
                frac=float((sim.load > 0.5).mean()), moran=sim.field.morans_i())


def main():
    print("=" * 60); print("PHASE TRANSITION (2D python core)"); print("=" * 60)
    rows = ["mode,control,n,density,M,chi,frac,moran"]
    seeds = (0, 1, 2)

    # density sweep
    counts = [10, 20, 35, 55, 80, 110, 145, 180]
    dens_M, dens_chi, dens_rho = [], [], []
    for n in counts:
        rs = [steady(n, 1.10, s) for s in seeds]
        M = np.mean([r["M"] for r in rs]); chi = np.mean([r["chi"] for r in rs])
        fr = np.mean([r["frac"] for r in rs]); mo = np.mean([r["moran"] for r in rs])
        rho = n / (SIDE * SIDE)
        dens_M.append(M); dens_chi.append(chi); dens_rho.append(rho)
        rows.append(f"density,{rho:.4f},{n},{rho:.4f},{M:.4f},{chi:.4f},{fr:.4f},{mo:.4f}")
    rho_c = dens_rho[int(np.argmax(dens_chi))]
    print(f"density sweep: M {min(dens_M):.3f}->{max(dens_M):.3f}; susceptibility peak at rho*={rho_c:.3f} ped/m^2")

    # feedback-gain sweep (fixed density)
    gains = [0.0, 0.4, 0.8, 1.2, 1.6, 2.2, 3.0, 4.0]
    g_M, g_chi = [], []
    for g in gains:
        rs = [steady(70, g, s) for s in seeds]
        M = np.mean([r["M"] for r in rs]); chi = np.mean([r["chi"] for r in rs])
        g_M.append(M); g_chi.append(chi)
        rows.append(f"gain,{g:.2f},70,{70/(SIDE*SIDE):.4f},{M:.4f},{chi:.4f},0,0")
    print(f"gain sweep: M {min(g_M):.3f}->{max(g_M):.3f}")

    with open(os.path.join(RES, "phase_transition.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.plot(dens_rho, dens_M, "-o", color="#2E6FB7", label="mean load $M$")
    a1.axvline(rho_c, color="#888", ls=":", lw=1)
    a1b = a1.twinx(); a1b.plot(dens_rho, np.array(dens_chi) / max(max(dens_chi), 1e-9), "-", color="#2BA84A")
    a1b.set_ylabel("susceptibility (norm.)", color="#2BA84A")
    a1.set_xlabel("density (ped/m$^2$)"); a1.set_ylabel("$M$"); a1.set_title(f"density: calm->panic ($\\rho*$={rho_c:.2f})")
    a1.legend(fontsize=8)
    a2.plot(gains, g_M, "-o", color="#2E6FB7"); a2.set_xlabel("field->affect gain"); a2.set_ylabel("$M$")
    a2.set_title("feedback gain: calm->panic")
    fig.suptitle("Collective panic phase transition (2D python)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(FIG, "phase_transition.png"), dpi=150)
    print("-> results/phase_transition.csv, figures/phase_transition.png")


if __name__ == "__main__":
    main()
