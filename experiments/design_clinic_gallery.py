"""Design-clinic gallery: for a set of real layouts, produce a working architectural prescription.

For each scenario the recommender diagnoses the crush-risk map, A/B-tests candidate interventions
(widen the binding exit, add an offset flow-pillar, affect-field exit guidance) and prescribes the
winner. The figure is a gallery: each panel is the affect-field RISK MAP with the congestion hotspot
ringed, titled with the prescribed fix and the measured improvement (extra people evacuated). This is
the "layout in -> architectural solution out" tool, demonstrated end-to-end.
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
from matplotlib.patches import Rectangle, Circle
from crowdsim.scenarios import SCENARIOS
from crowdsim.recommend import recommend

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

NAMES = ["Bottleneck", "MultiExit", "NearFar", "StadiumFunnel", "ParallelBottlenecks", "TwoRooms"]
SEEDS = (0, 1, 2)


def draw(ax, sc, base):
    risk = base["risk"].T
    ax.imshow(risk, origin="lower", extent=[-sc.width/2, sc.width/2, -sc.height/2, sc.height/2],
              cmap="inferno", aspect="equal")
    for (cx, cz, s_x, s_z) in sc.walls:
        ax.add_patch(Rectangle((cx - s_x/2, cz - s_z/2), s_x, s_z, color="#3a3f4a", zorder=3))
    ex = np.array(sc.exits, float)
    ax.scatter(ex[:, 0], ex[:, 1], marker="*", s=90, color="#19e019", edgecolor="k", lw=.5, zorder=5)
    for x, z, s in base["hotspots"]:
        ax.add_patch(Circle((x, z), 0.9, fill=False, color="cyan", lw=1.6, zorder=6))
    ax.set_xticks([]); ax.set_yticks([])


def main():
    print("=" * 74); print("DESIGN-CLINIC GALLERY: architectural prescriptions for real layouts"); print("=" * 74)
    rows = ["scenario,baseline_evac,best_fix,best_evac,delta"]
    results = []
    for name in NAMES:
        sc = SCENARIOS[name]
        base, recs = recommend(sc, seeds=SEEDS)
        best = recs[0]
        results.append((name, sc, base, best))
        rows.append(f"{name},{base['evacuated']:.1f},{best['label']},{best['metrics']['evacuated']:.1f},{best['d_evac']:+.1f}")
        op = next((r for r in recs if r["label"] == "affect-field exit guidance"), None)
        print(f"\n  {name} ({sc.note}) — baseline evac {base['evacuated']:.1f}, "
              f"exit imbalance {base['exit_imbalance']:.2f}")
        for r in recs:
            star = "  <- prescribe (best)" if r is best else ""
            print(f"      {r['label']:28s} evac {r['metrics']['evacuated']:5.1f}  (Δ{r['d_evac']:+.1f}){star}")
        if op is not None and op is not best:
            print(f"      best zero-construction option: affect-field exit guidance (Δ{op['d_evac']:+.1f})")
    with open(os.path.join(RES, "design_clinic_gallery.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10.5))
    for ax, (name, sc, base, best) in zip(axes.ravel(), results):
        draw(ax, sc, base)
        rx = best["label"] if best["d_evac"] > 0.5 else "no change needed"
        gain = f"  (+{best['d_evac']:.0f} evacuated)" if best["d_evac"] > 0.5 else ""
        ax.set_title(f"{name}: {sc.note}\nRx: {rx}{gain}", fontsize=10)
    fig.suptitle("Affect-field design clinic — risk map (hotspots ringed) + prescribed architectural fix",
                 fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95], h_pad=3.0, w_pad=1.5)
    fig.savefig(os.path.join(FIG, "design_clinic_gallery.png"), dpi=130)
    print("\n-> results/design_clinic_gallery.csv, figures/design_clinic_gallery.png")


if __name__ == "__main__":
    main()
