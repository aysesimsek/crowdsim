"""Safe-capacity design tool: how many people can a venue safely hold, and how does the door design
(count / width) and a panic-prevention method change that?

For a parameterised room we sweep occupancy (agent count), measure the 90%-evacuation clearance time and
the peak crush density, and read off the MAX SAFE CAPACITY = the largest occupancy that still clears
within a safety time limit. We compare door designs (count x width) and a prevention method (affect-field
exit guidance). This reframes the affect-field model as an occupancy-certification / inverse-design tool.
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
from crowdsim.scenarios import Scenario, vwall

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

W, H = 26.0, 18.0
NS = [30, 60, 90, 120, 150, 180]
SEEDS = (0, 1)
MAXSEC = 80.0
T_SAFE = 25.0          # median-clearance-time limit (s) defining "safe"
D_CRUSH = 4.0          # peak local density (ped / m^2) above which crowding is dangerous


def room(n_doors, door_w):
    hh = H / 2
    centers = [0.0] if n_doors == 1 else list(np.linspace(-hh + 4, hh - 4, n_doors))
    walls = vwall(0.0, -hh, hh, gaps=centers, gap_half=door_w / 2)
    spawns = [(-W / 2 + 1, -2.0, -hh + 1, hh - 1)]
    exits = [(1.3, c) for c in centers]
    return Scenario("room", f"{n_doors}door x {door_w:.1f}m", W, H, walls=walls, spawns=spawns, exits=exits)


def capacity_curve(n_doors, door_w, field_route=False):
    # median (50%) clearance time: monotone in occupancy and robust to the model's low-N chronic-stuck
    # straggler fraction (the 80%/90%/full-clear metrics are brittle to it).
    ts, peaks = [], []
    sc = room(n_doors, door_w)
    for N in NS:
        r = evaluate_layout(sc, seeds=SEEDS, n=N, maxsec=MAXSEC, field_route=field_route, inflate=0.2)
        ts.append(r["t50"] if r["t50"] > 0 else MAXSEC)
        peaks.append(r["peak_density"])
    return np.array(ts), np.array(peaks)


def max_safe(ns, t90s):
    """Largest occupancy whose clearance time is within T_SAFE (linear interpolation on the crossing)."""
    ns = np.array(ns, float); ok = t90s <= T_SAFE
    if ok.all():
        return float(ns[-1])
    if not ok.any():
        return 0.0
    i = np.argmax(~ok)                                       # first unsafe index
    if i == 0:
        return 0.0
    x0, x1, y0, y1 = ns[i-1], ns[i], t90s[i-1], t90s[i]
    return float(x0 + (T_SAFE - y0) * (x1 - x0) / (y1 - y0)) if y1 != y0 else float(x0)


def main():
    print("=" * 70); print("SAFE-CAPACITY DESIGN TOOL (occupancy vs door design & prevention)"); print("=" * 70)
    # door widths >= 1.6 m: below ~1.5 m the position-based contact model under-flows (a stated limit)
    designs = [("1 door, 1.6 m", 1, 1.6, False),
               ("1 door, 2.4 m", 1, 2.4, False),
               ("1 door, 3.2 m", 1, 3.2, False),
               ("2 doors, 1.6 m", 2, 1.6, False),
               ("2 doors + field guidance", 2, 1.6, True)]
    rows = ["design,max_safe_capacity," + ",".join(f"t90_N{n}" for n in NS)]
    curves = {}
    for label, nd, w, fr in designs:
        ts, peaks = capacity_curve(nd, w, field_route=fr)
        cap = max_safe(NS, ts)
        curves[label] = (ts, cap)
        rows.append(f"{label},{cap:.0f}," + ",".join(f"{t:.1f}" for t in ts))
        print(f"  {label:28s} max safe capacity ≈ {cap:4.0f} people   (peak density up to {peaks.max():.1f}/m²)")
    with open(os.path.join(RES, "capacity_design.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    base = curves["1 door, 1.6 m"][1]
    print(f"\n  -> widening the door 1.6->2.4->3.2 m raises safe capacity {base:.0f} -> "
          f"{curves['1 door, 2.4 m'][1]:.0f} -> {curves['1 door, 3.2 m'][1]:.0f};")
    print(f"     a second 1.6 m door: {base:.0f} -> {curves['2 doors, 1.6 m'][1]:.0f};")
    print(f"     and a zero-construction prevention (field guidance) lifts the 2-door design "
          f"{curves['2 doors, 1.6 m'][1]:.0f} -> {curves['2 doors + field guidance'][1]:.0f}.")

    fig, ax = plt.subplots(figsize=(10, 5.4))
    cols = ["#C9A14A", "#E0552B", "#2E6FB7", "#1d7a37", "#7B4FB7"]
    for (label, _, _, _), c in zip(designs, cols):
        ts, cap = curves[label]
        ls = "--" if "guidance" in label else "-"
        ax.plot(NS, ts, ls + "o", color=c, label=f"{label}  (max safe ≈ {cap:.0f})")
    ax.axhline(T_SAFE, color="#aa3333", ls=":", lw=1.4)
    ax.text(NS[0], T_SAFE + 1, f"safety limit {T_SAFE:.0f}s", color="#aa3333", fontsize=9)
    ax.set_xlabel("occupancy (number of people)"); ax.set_ylabel("median (50%) clearance time (s)")
    ax.set_title("Safe capacity vs door design & prevention\n(where each curve crosses the limit = max safe occupancy)")
    ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "capacity_design.png"), dpi=140)
    print("-> results/capacity_design.csv, figures/capacity_design.png")


if __name__ == "__main__":
    main()
