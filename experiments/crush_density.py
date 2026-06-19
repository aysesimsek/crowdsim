"""Crush-density: the real lethal limit. People die in crowds from compressive asphyxia at high local
density (~5-6 ped/m^2: Hillsborough, Love Parade), not from slow egress. So the binding safety limit is
often a DENSITY limit, not a time limit. We sweep occupancy for several door designs and record the peak
local density, and read off the crush-limited capacity (where peak density crosses a danger threshold).
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
from crowdsim.evaluate import evaluate_layout
from experiments.capacity_design import room

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

NS = [60, 120, 180, 240, 320, 400]
SEEDS = (0, 1)
MAXSEC = 45.0
D_DANGER, D_CRUSH = 4.0, 5.0       # ped/m^2: 4 = dangerous crowding, 5 = crush/asphyxia risk


def cross(ns, dens, thr):
    ns = np.array(ns, float)
    if (dens < thr).all():
        return None
    if (dens >= thr).all():
        return float(ns[0])
    i = int(np.argmax(dens >= thr))
    if i == 0:
        return float(ns[0])
    x0, x1, y0, y1 = ns[i-1], ns[i], dens[i-1], dens[i]
    return float(x0 + (thr - y0) * (x1 - x0) / (y1 - y0)) if y1 != y0 else float(x0)


def main():
    print("=" * 66); print("CRUSH-DENSITY: the lethal limit (peak ped/m^2 vs occupancy)"); print("=" * 66)
    designs = [("1 door, 1.6 m", 1, 1.6), ("1 door, 2.4 m", 1, 2.4),
               ("1 door, 3.2 m", 1, 3.2), ("2 doors, 1.6 m", 2, 1.6)]
    rows = ["design,crush_capacity_5pm2," + ",".join(f"peakD_N{n}" for n in NS)]
    curves = {}
    for label, nd, w in designs:
        sc = room(nd, w)
        peaks = [np.mean([evaluate_layout(sc, seeds=(s,), n=N, maxsec=MAXSEC, inflate=0.2)["peak_density"]
                          for s in SEEDS]) for N in NS]
        peaks = np.array(peaks)
        cap = cross(NS, peaks, D_CRUSH)
        curves[label] = peaks
        rows.append(f"{label},{('%.0f' % cap) if cap else '>%d' % NS[-1]}," + ",".join(f"{p:.2f}" for p in peaks))
        caps = f"{cap:.0f}" if cap else f">{NS[-1]}"
        print(f"  {label:16s} peak density {peaks.min():.1f}->{peaks.max():.1f}/m²   "
              f"crush-limited capacity (5/m²) ≈ {caps}")
    with open(os.path.join(RES, "crush_density.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    fig, ax = plt.subplots(figsize=(10, 5.2))
    cols = ["#C9A14A", "#E0552B", "#2E6FB7", "#1d7a37"]
    for (label, _, _), c in zip(designs, cols):
        ax.plot(NS, curves[label], "-o", color=c, label=label)
    ax.axhspan(D_CRUSH, 8, color="#C0392B", alpha=0.08)
    ax.axhline(D_DANGER, color="#C77A2E", ls=":", lw=1.3); ax.text(NS[0], D_DANGER + .08, "dangerous (4/m²)", color="#C77A2E", fontsize=9)
    ax.axhline(D_CRUSH, color="#C0392B", ls="--", lw=1.5); ax.text(NS[0], D_CRUSH + .08, "crush / asphyxia risk (5/m²)", color="#C0392B", fontsize=9)
    ax.set_xlabel("occupancy (number of people)"); ax.set_ylabel("peak local density (ped/m²)")
    ax.set_title("Crush-density: the lethal limit (peak crowding vs occupancy & door design)")
    ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "crush_density.png"), dpi=140)
    print("-> results/crush_density.csv, figures/crush_density.png")


if __name__ == "__main__":
    main()
