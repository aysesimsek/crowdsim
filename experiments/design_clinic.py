"""Affect-field design clinic: evaluate a layout and recommend safety improvements.

Usage:  python experiments/design_clinic.py [ScenarioName]   (default: Bottleneck)

Prints a safety report (egress, exit balance, congestion hotspots from the affect-field risk map) and an
A/B-tested, ranked list of design interventions. Writes a figure with the risk heatmap + the ranked
interventions. This is the MVP of the "upload-your-design" framework: layout in -> diagnosis + solutions out.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")     # Windows consoles default to cp1252
except Exception:
    pass
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from crowdsim.scenarios import SCENARIOS
from crowdsim.recommend import recommend

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures"); os.makedirs(FIG, exist_ok=True)


def draw_layout(ax, sc):
    for (cx, cz, sx, sz) in sc.walls:
        ax.add_patch(Rectangle((cx - sx / 2, cz - sz / 2), sx, sz, color="#444", zorder=3))
    ex = np.array(sc.exits, float)
    ax.scatter(ex[:, 0], ex[:, 1], marker="*", s=180, color="#11d011", edgecolor="k", zorder=5)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "Bottleneck"
    sc = SCENARIOS[name]
    print("=" * 70); print(f"AFFECT-FIELD DESIGN CLINIC  -  {name}: {sc.note}"); print("=" * 70)
    base, recs = recommend(sc)

    print(f"\n  BASELINE  evacuated={base['evacuated']:.1f}/{base['n']}  "
          f"t50={base['t50']:.1f}s  peakDensity={base['peak_density']:.2f}  MoranI={base['morans_i']:.2f}")
    if len(sc.exits) > 1:
        print(f"            exit usage={[round(u,2) for u in base['exit_usage']]}  "
              f"binding exit #{base['binding_exit']}  imbalance={base['exit_imbalance']:.2f}")
    print(f"            congestion hotspots (x,z,severity): "
          f"{[(round(x,1),round(z,1),round(s,2)) for x,z,s in base['hotspots']]}")

    print("\n  RECOMMENDATIONS (A/B-tested, best first):")
    for i, r in enumerate(recs, 1):
        dt = f"{r['d_t50']:+.1f}s" if r["d_t50"] is not None else "n/a"
        print(f"   {i}. {r['label']:28s} evacuated {base['evacuated']:.1f} -> {r['metrics']['evacuated']:.1f} "
              f"(d{r['d_evac']:+.1f})   t50 d{dt}   imbalance d{r['d_imbalance']:+.2f}")
    win = recs[0]
    verdict = (f"adopt '{win['label']}' (+{win['d_evac']:.1f} evacuated)"
               if win["d_evac"] > 0.5 else "baseline already near-best among tested interventions")
    print(f"\n  -> VERDICT: {verdict}")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
    risk = base["risk"].T
    a1.imshow(risk, origin="lower", extent=[-sc.width/2, sc.width/2, -sc.height/2, sc.height/2],
              cmap="inferno", aspect="equal")
    draw_layout(a1, sc)
    for x, z, s in base["hotspots"]:
        a1.add_patch(plt.Circle((x, z), 0.8, fill=False, color="cyan", lw=2, zorder=6))
    a1.set_title("Affect-field risk map + congestion hotspots"); a1.set_xlabel("x"); a1.set_ylabel("z")

    labels = ["baseline"] + [r["label"].replace(" ", "\n") for r in recs]
    vals = [base["evacuated"]] + [r["metrics"]["evacuated"] for r in recs]
    cols = ["#C9C9C9"] + ["#2E6FB7"] * len(recs)
    cols[1] = "#11a011"   # highlight the winner (recs sorted best-first)
    a2.bar(range(len(vals)), vals, color=cols)
    a2.set_xticks(range(len(vals))); a2.set_xticklabels(labels, fontsize=8)
    a2.set_ylabel(f"evacuated in {50}s (of {base['n']})"); a2.set_title("Intervention A/B test (best = green)")
    fig.suptitle(f"Design clinic: {name}", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(FIG, f"design_clinic_{name}.png")
    fig.savefig(out, dpi=140)
    print(f"  -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
