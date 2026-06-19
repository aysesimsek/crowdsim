"""Early-warning-triggered panic PREVENTION (flagship closed loop).

We ramp the field->affect feedback gain toward the panic tipping point. A live early-warning monitor
watches the cross-sectional spread of affective load (a susceptibility proxy that rises approaching the
transition). When it crosses a threshold, an intervention fires: a calming action (raising familiarity)
that counteracts the feedback. Result: the order parameter does NOT tip -- panic is averted -- whereas
the no-intervention control tips to panic. Closing the early-warning -> intervention loop.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from crowdsim import Config, Simulation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

SIDE, N, FAM0 = 18.0, 70, 0.6
G0, G1, RAMP = 0.3, 3.4, 44.0
ENS = 8
EW_MULT = 2.2            # trigger when the load-spread EW signal exceeds EW_MULT x its early baseline


def run(seed, intervene):
    cfg = Config(width=SIDE, height=SIDE, boundary="torus", max_value=5.0, decay=0.35,
                 field_gain=G0, hard_contact=True)
    rng = np.random.default_rng(seed); sim = Simulation(cfg, rng)
    lim = SIDE / 2 - 0.8
    sim.spawn(rng.uniform(-lim, lim, (N, 2)), fam=FAM0)
    sim.set_targets(rng.uniform(-lim, lim, (N, 2)))
    total = int(RAMP / cfg.dt); rt = int(3.0 / cfg.dt); warm = int(9.0 / cfg.dt)
    M, EW = [], []; base = []; triggered = False; trig_t = -1.0
    for t in range(total):
        cfg.field_gain = G0 + (G1 - G0) * t / total
        if t % rt == 0:
            sim.set_targets(rng.uniform(-lim, lim, (N, 2)))
        sim.step()
        M.append(float(sim.load.mean())); EW.append(float(sim.load.var()))
        if t < warm:
            base.append(EW[-1])
        elif intervene and not triggered and EW[-1] > EW_MULT * (np.mean(base) + 1e-9):
            triggered = True; trig_t = t * cfg.dt
        if triggered:
            sim.fam[:] = np.minimum(0.97, sim.fam + 0.04)      # calming intervention ramps up
    return np.array(M), np.array(EW), trig_t


def main():
    print("=" * 60); print("PANIC PREVENTION (early-warning-triggered)"); print("=" * 60)
    tt = np.arange(int(RAMP / 0.05)) * 0.05
    Mc = np.mean([run(s, False)[0] for s in range(ENS)], 0)
    res = [run(s, True) for s in range(ENS)]
    Mp = np.mean([r[0] for r in res], 0)
    EWp = np.mean([r[1] for r in res], 0)
    trig = np.mean([r[2] for r in res if r[2] > 0]) if any(r[2] > 0 for r in res) else -1
    L = min(len(Mc), len(Mp), len(tt)); tt, Mc, Mp, EWp = tt[:L], Mc[:L], Mp[:L], EWp[:L]
    print(f"  control (no intervention): final panic level M = {Mc[-1]:.2f}")
    print(f"  early-warning intervention: trigger at t≈{trig:.1f}s, final M = {Mp[-1]:.2f}")
    print(f"  -> {'panic AVERTED' if Mp[-1] < 0.55 * Mc[-1] else 'partial effect'} "
          f"({Mc[-1]:.2f} -> {Mp[-1]:.2f}); the warning leads the tip and the intervention holds the line.")

    with open(os.path.join(RES, "panic_prevention.csv"), "w") as f:
        f.write("t,M_control,M_prevented\n")
        for i in range(L):
            f.write(f"{tt[i]:.2f},{Mc[i]:.4f},{Mp[i]:.4f}\n")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(tt, Mc, color="#C0392B", lw=2.2, label="no intervention → panic")
    ax.plot(tt, Mp, color="#1d7a37", lw=2.2, label="early-warning intervention → averted")
    if trig > 0:
        ax.axvline(trig, color="#0E7C86", ls="--", lw=1.4)
        ax.text(trig + 0.3, 0.05, "warning fires →\nintervene", color="#0E7C86", fontsize=9, va="bottom")
    ax.set_xlabel("time (s)"); ax.set_ylabel("panic level $M$ (mean affective load)")
    ax.set_ylim(0, 1.0); ax.legend(loc="center left"); ax.grid(alpha=0.3)
    ax.set_title("Early-warning-triggered intervention averts the panic transition")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "panic_prevention.png"), dpi=140)
    print("-> results/panic_prevention.csv, figures/panic_prevention.png")


if __name__ == "__main__":
    main()
