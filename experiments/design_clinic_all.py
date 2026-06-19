"""Run the full design clinic for EVERY scenario in the library.

For each layout: diagnose (affect-field risk map + congestion hotspots), A/B-test the candidate
interventions, and write a per-scenario 2-panel report (risk map + ranked intervention bars) to
figures/clinic/<name>.png. Also writes a summary table of the prescribed fix and its measured gain.
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
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures", "clinic")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

SEEDS = (0, 1, 2)
MAXSEC = 50


def draw_layout(ax, sc):
    for (cx, cz, sx, sz) in sc.walls:
        ax.add_patch(Rectangle((cx - sx/2, cz - sz/2), sx, sz, color="#444", zorder=3))
    ex = np.array(sc.exits, float)
    ax.scatter(ex[:, 0], ex[:, 1], marker="*", s=170, color="#11d011", edgecolor="k", zorder=5)


def report(name):
    sc = SCENARIOS[name]
    base, recs = recommend(sc, seeds=SEEDS, maxsec=MAXSEC)
    best = recs[0]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
    a1.imshow(base["risk"].T, origin="lower",
              extent=[-sc.width/2, sc.width/2, -sc.height/2, sc.height/2], cmap="inferno", aspect="equal")
    draw_layout(a1, sc)
    for x, z, s in base["hotspots"]:
        a1.add_patch(Circle((x, z), 0.8, fill=False, color="cyan", lw=2, zorder=6))
    a1.set_title("Affect-field risk map + congestion hotspots"); a1.set_xlabel("x"); a1.set_ylabel("z")

    labels = ["baseline"] + [r["label"].replace(" ", "\n") for r in recs]
    vals = [base["evacuated"]] + [r["metrics"]["evacuated"] for r in recs]
    cols = ["#C9C9C9"] + ["#2E6FB7"] * len(recs)
    if best["d_evac"] > 0.5:
        cols[1] = "#11a011"
    a2.bar(range(len(vals)), vals, color=cols)
    a2.set_xticks(range(len(vals))); a2.set_xticklabels(labels, fontsize=8)
    a2.set_ylabel(f"evacuated in {MAXSEC}s (of {base['n']})")
    a2.set_title("Intervention A/B test (best = green)")
    fig.suptitle(f"Design clinic: {name} — {sc.note}", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(FIG, f"{name}.png"), dpi=130)
    plt.close(fig)
    return base, best


def main():
    print("=" * 76); print("DESIGN CLINIC — every scenario"); print("=" * 76)
    rows = ["scenario,baseline_evac,binding_exit,imbalance,best_fix,best_evac,delta"]
    names = list(SCENARIOS.keys())
    for i, name in enumerate(names, 1):
        sc = SCENARIOS[name]
        base, best = report(name)
        rx = best["label"] if best["d_evac"] > 0.5 else "no change needed"
        rows.append(f"{name},{base['evacuated']:.1f},{base['binding_exit']},{base['exit_imbalance']:.2f},"
                    f"{best['label']},{best['metrics']['evacuated']:.1f},{best['d_evac']:+.1f}")
        print(f"  [{i:2d}/{len(names)}] {name:18s} evac {base['evacuated']:4.1f}  "
              f"Rx: {rx:26s} (Δ{best['d_evac']:+.1f})")
    with open(os.path.join(RES, "design_clinic_all.csv"), "w") as f:
        f.write("\n".join(rows) + "\n")
    print(f"\n-> {len(names)} reports in figures/clinic/, summary in results/design_clinic_all.csv")


if __name__ == "__main__":
    main()
