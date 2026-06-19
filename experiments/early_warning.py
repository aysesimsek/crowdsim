"""Early warning of the panic tipping point via CRITICAL SLOWING DOWN.

We slowly ramp the field->affect feedback gain through the phase transition (a torus crowd), in an
ensemble of runs. Near a tipping point a system recovers ever more slowly from fluctuations, so the
order parameter's rolling VARIANCE and lag-1 AUTOCORRELATION rise *before* it tips -- a generic
early-warning signal (Scheffer et al.). Honest: the agent transition is gradual, so this is a
proof-of-concept that the indicators lead the tip, not a dramatic fold catastrophe.
"""
import os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings("ignore", message="Mean of empty slice")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim import Config, Simulation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

SIDE, N, FAM = 18.0, 70, 0.6
G0, G1, RAMP = 0.3, 3.4, 44.0     # slow ramp of feedback gain through the transition
ENS = 8
SAMP = 4                          # sample order parameter every SAMP steps
WIN = 28                          # rolling window (~5.6 s of samples)


def run_ramp(seed):
    cfg = Config(width=SIDE, height=SIDE, boundary="torus", max_value=5.0, decay=0.35,
                 field_gain=G0, hard_contact=True)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng)
    lim = SIDE / 2 - 0.8
    sim.spawn(rng.uniform(-lim, lim, (N, 2)), fam=FAM)
    sim.set_targets(rng.uniform(-lim, lim, (N, 2)))
    total = int(RAMP / cfg.dt); rt = int(3.0 / cfg.dt)
    M, G = [], []
    for t in range(total):
        cfg.field_gain = G0 + (G1 - G0) * t / total
        if t % rt == 0:
            sim.set_targets(rng.uniform(-lim, lim, (N, 2)))
        sim.step()
        if t % SAMP == 0:
            M.append(sim.load.mean()); G.append(cfg.field_gain)
    return np.array(M), np.array(G)


def indicators(M, W):
    """Detrend with a centred rolling mean, then rolling variance + lag-1 autocorrelation of residuals."""
    k = np.ones(W) / W
    trend = np.convolve(M, k, mode="same")
    res = M - trend
    var = np.array([res[max(0, i - W):i + 1].var() for i in range(len(res))])
    ar1 = np.full(len(res), np.nan)
    for i in range(len(res)):
        w = res[max(0, i - W):i + 1]
        if len(w) > 4 and w.std() > 1e-9:
            ar1[i] = np.corrcoef(w[:-1], w[1:])[0, 1]
    return var, ar1


def main():
    print("=" * 60); print("EARLY WARNING (critical slowing down)"); print("=" * 60)
    Ms, As, G = [], [], None
    for s in range(ENS):
        M, G = run_ramp(s)
        _, a = indicators(M, WIN)
        Ms.append(M); As.append(a)
    L = min(len(m) for m in Ms)
    Marr = np.array([m[:L] for m in Ms])
    Mbar = Marr.mean(0)
    chi = Marr.var(0)                              # ensemble susceptibility (between-run variance)
    Abar = np.nanmean([a[:L] for a in As], 0)
    G = G[:L]; tt = np.arange(L) * SAMP * 0.05

    dM = np.gradient(Mbar)
    tip = int(np.argmax(dM))                        # tipping = steepest rise of the order parameter
    chi_peak = int(np.argmax(chi))
    lead = slice(max(0, tip - 2 * WIN), tip)
    base = slice(0, WIN)
    chi_rise = np.nanmean(chi[lead]) / max(1e-9, np.nanmean(chi[base]))
    a_rise = np.nanmean(Abar[lead]) - np.nanmean(Abar[base])
    print(f"  tipping at gain~{G[tip]:.2f} (t={tt[tip]:.1f}s), order parameter {Mbar[0]:.2f}->{Mbar[-1]:.2f}")
    print(f"  ensemble susceptibility peaks at t={tt[chi_peak]:.1f}s (gain~{G[chi_peak]:.2f})")
    print(f"  run-up to the tip: susceptibility x{chi_rise:.1f}, lag-1 AR(1) +{a_rise:.2f}")
    ok = chi_rise > 2.0 or a_rise > 0.1
    print(f"  -> {'critical slowing down LEADS the tip (early warning present)' if ok else 'weak CSD signal'}")

    with open(os.path.join(RES, "early_warning.csv"), "w") as f:
        f.write("t,gain,M,susceptibility,ar1\n")
        for i in range(L):
            f.write(f"{tt[i]:.2f},{G[i]:.3f},{Mbar[i]:.4f},{chi[i]:.6f},{Abar[i]:.4f}\n")

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(tt, Mbar, color="#2E6FB7", lw=2, label="order parameter $M$ (mean load)")
    ax.axvline(tt[tip], color="#aa3333", ls="--", lw=1.2, label=f"tipping (gain~{G[tip]:.1f})")
    ax.set_xlabel("time (s)"); ax.set_ylabel("$M$", color="#2E6FB7"); ax.legend(loc="upper left", fontsize=8)
    axb = ax.twinx()
    axb.plot(tt, chi / np.nanmax(chi), color="#2BA84A", lw=1.8, label="ensemble susceptibility (norm.)")
    axb.plot(tt, Abar, color="#E08A1E", lw=1.4, label="lag-1 autocorrelation")
    axb.set_ylabel("early-warning indicators"); axb.legend(loc="lower right", fontsize=8)
    ax.set_title("Critical slowing down: ensemble susceptibility rises into the panic tip")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "early_warning.png"), dpi=150)
    print("-> results/early_warning.csv, figures/early_warning.png")


if __name__ == "__main__":
    main()
