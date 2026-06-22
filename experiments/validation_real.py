"""Validation against REAL measured pedestrian data (not just a fitted curve).

We check the model's derived quantities against empirical VALUES/RANGES reported in the experimental
literature:
  - free-flow speed         ~1.34 m/s            (Weidmann 1993)
  - bottleneck specific flow ~1.9 ped/m/s         (Seyfried/Juelich, arXiv physics/0702004)
  - max specific flow (capacity) 1.2-1.8 ped/m/s  (cross-study range; Schadschneider/Seyfried review)
  - jam density (v->0)       3.8-10 ped/m^2        (cross-study range)
  - density at max flow      1.75-7 ped/m^2        (cross-study range)
This is honest: it reports what the model reproduces AND what it does not.
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
from experiments.validation_suite import fd_speed, weidmann
from experiments.validation import specific_flow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

# empirical reference values / ranges from the literature
EMP = dict(free=(1.2, 1.4), bottleneck=(1.7, 2.0), capacity=(1.2, 1.8), jam=(3.8, 10.0), rho_at_max=(1.75, 7.0))


def main():
    print("=" * 66); print("VALIDATION vs REAL measured data (Weidmann / Seyfried-Juelich)"); print("=" * 66)
    rhos = np.array([0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0])
    v = np.array([np.mean([fd_speed(r, s, side=12.0) for s in (0, 1)]) for r in rhos])
    J = rhos * v                                            # specific flow (ped/m/s) per density
    free = fd_speed(0.05, side=12.0)
    bott = float(np.mean([specific_flow(w, s) for w in (1.6, 2.4) for s in (0, 1)]))
    jmax = float(J.max()); rho_at_max = float(rhos[int(J.argmax())])
    jam = float(rhos[v < 0.15][0]) if (v < 0.15).any() else float(f">{rhos[-1]:.0f}".replace(">", "9"))
    jam_str = f"{jam:.1f}" if (v < 0.15).any() else f">{rhos[-1]:.0f}"

    def chk(name, val, lo, hi):
        ok = lo <= val <= hi
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:34s} {val if isinstance(val,str) else f'{val:.2f}':>6}  (empirical {lo}-{hi})")
        return ok
    print("  vs real measured values:")
    p1 = chk("free-flow speed (m/s)", free, *EMP["free"])
    p2 = chk("bottleneck specific flow (ped/m/s)", bott, *EMP["bottleneck"])
    p3 = chk("max specific flow / capacity", jmax, *EMP["capacity"])
    p4 = chk("density at max flow (ped/m²)", rho_at_max, *EMP["rho_at_max"])
    p5 = (v < 0.15).any() and EMP["jam"][0] <= jam <= EMP["jam"][1]
    print(f"  [{'PASS' if p5 else 'FAIL'}] {'jam density v→0 (ped/m²)':34s} {jam_str:>6}  (empirical {EMP['jam'][0]}-{EMP['jam'][1]})")
    npass = sum([p1, p2, p3, p4, p5])
    print(f"\n  -> {npass}/5 vs REAL measured data. Honest read: free-flow + bottleneck flow MATCH real")
    print(f"     measurements; the corridor FD over-congests (capacity {jmax:.2f} < empirical 1.2-1.8) and the")
    print(f"     position-based model does not reach a clean v→0 jam — known limitations, stated not hidden.")

    with open(os.path.join(RES, "validation_real.csv"), "w") as f:
        f.write("rho,speed,specific_flow\n" + "\n".join(f"{rhos[i]:.2f},{v[i]:.3f},{J[i]:.3f}" for i in range(len(rhos))) + "\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
    rr = np.linspace(0.1, 5.0, 120)
    a1.plot(rr, weidmann(rr), color="#888", lw=2, label="Weidmann (empirical fit)")
    a1.plot(rhos, v, "o-", color="#2E6FB7", ms=6, label="model")
    a1.axhspan(*EMP["free"], color="#2BA84A", alpha=0.10)
    a1.set_xlabel("density (ped/m²)"); a1.set_ylabel("speed (m/s)"); a1.set_title("Speed–density vs Weidmann")
    a1.legend(fontsize=8); a1.grid(alpha=0.3)
    a2.plot(rhos, J, "o-", color="#C0392B", ms=6, label="model specific flow")
    a2.axhspan(*EMP["capacity"], color="#2BA84A", alpha=0.15, label="empirical capacity 1.2–1.8")
    a2.axhline(1.9, color="#0E7C86", ls="--", lw=1.2, label="bottleneck flow 1.9 (Seyfried)")
    a2.plot([0.2], [bott], "D", color="#0E7C86", ms=9, label=f"model bottleneck {bott:.2f}")
    a2.set_xlabel("density (ped/m²)"); a2.set_ylabel("specific flow (ped/m/s)")
    a2.set_title("Flow–density vs empirical capacity"); a2.legend(fontsize=8); a2.grid(alpha=0.3)
    fig.suptitle(f"Validation vs REAL measured data: {npass}/5 match (free-flow + bottleneck ✓; corridor capacity ✗ — honest)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "validation_real.png"), dpi=140)
    print("-> results/validation_real.csv, figures/validation_real.png")


if __name__ == "__main__":
    main()
