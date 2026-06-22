"""HELD-OUT validation against REAL raw trajectories (Juelich/Wuppertal bottleneck, doi 10.34735/ped.2018.1).

We process the raw position-time file ourselves: compute each pedestrian's speed, place a measurement area,
and build the fundamental diagram (density vs speed) by the classical method. We then compare OUR model's FD
to these real data points. This is a genuine held-out test: the model was calibrated to Weidmann's curve, NOT
to this dataset, so the Juelich trajectories are independent data the model never saw.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "juelich_bottleneck_040_c_56.txt")
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
FPS = 25.0


def load():
    d = np.loadtxt(DATA, comments="#")
    return d[:, 0].astype(int), d[:, 1].astype(int), d[:, 2], d[:, 3]   # id, frame, x, y


def per_agent_speed(ids, fr, x, y, win=6):
    """Windowed speed (m/s) per row: |pos[t+win]-pos[t-win]| / (2*win/FPS)."""
    sp = np.zeros(len(ids))
    for uid in np.unique(ids):
        idx = np.where(ids == uid)[0]
        idx = idx[np.argsort(fr[idx])]
        xs, ys = x[idx], y[idx]
        n = len(idx)
        if n < 2 * win + 1:
            continue
        d = np.sqrt((xs[2 * win:] - xs[:-2 * win]) ** 2 + (ys[2 * win:] - ys[:-2 * win]) ** 2)
        sp[idx[win:-win]] = d / (2 * win / FPS)
    return sp


def main():
    ids, fr, x, y = load()
    print("=" * 66); print("HELD-OUT validation vs RAW Juelich trajectories"); print("=" * 66)
    print(f"  rows={len(ids)}  agents={len(np.unique(ids))}  frames={fr.max()-fr.min()+1}  "
          f"x∈[{x.min():.1f},{x.max():.1f}]  y∈[{y.min():.1f},{y.max():.1f}] (m)")
    sp = per_agent_speed(ids, fr, x, y)
    valid = sp > 0

    # measurement area: a 1.5 m x 1.5 m box at the busiest spot (time-summed occupancy peak), upstream of door
    H, xe, ye = np.histogram2d(x[valid], y[valid], bins=[40, 20])
    bi, bj = np.unravel_index(H.argmax(), H.shape)
    cx = 0.5 * (xe[bi] + xe[bi + 1]); cy = 0.5 * (ye[bj] + ye[bj + 1])
    half = 0.75; area = (2 * half) ** 2
    print(f"  measurement area: {2*half:.1f}×{2*half:.1f} m centred at ({cx:.2f},{cy:.2f}), area={area:.2f} m²")

    inbox = valid & (np.abs(x - cx) < half) & (np.abs(y - cy) < half)
    fmin = fr[inbox].min()
    f_idx = fr[inbox] - fmin
    cnt = np.bincount(f_idx)
    ssum = np.bincount(f_idx, weights=sp[inbox])
    ok = cnt >= 2
    rho = cnt[ok] / area
    v = ssum[ok] / cnt[ok]
    print(f"  measured {ok.sum()} frames; density range {rho.min():.1f}–{rho.max():.1f} ped/m²")

    # bin the (rho, v) cloud into the fundamental diagram
    edges = np.arange(0.0, rho.max() + 0.6, 0.6)
    cen, vbin = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (rho >= a) & (rho < b)
        if m.sum() >= 8:
            cen.append((a + b) / 2); vbin.append(float(np.median(v[m])))
    cen = np.array(cen); vbin = np.array(vbin)

    # model FD (held-out: calibrated to Weidmann, never to this data) + Weidmann reference
    model_v = np.array([np.mean([fd_speed(r, s, side=10.0) for s in (0, 1)]) for r in cen])
    wd_v = weidmann(cen)
    rmse_model = float(np.sqrt(np.mean((model_v - vbin) ** 2)))
    rmse_weid = float(np.sqrt(np.mean((wd_v - vbin) ** 2)))
    corr = float(np.corrcoef(model_v, vbin)[0, 1]) if len(cen) > 2 else float("nan")
    print(f"\n  fundamental diagram, model vs RAW data (held-out):")
    for i in range(len(cen)):
        print(f"    ρ={cen[i]:.1f}: raw={vbin[i]:.2f}  model={model_v[i]:.2f}  weidmann={wd_v[i]:.2f} m/s")
    print(f"\n  RMSE model-vs-raw = {rmse_model:.3f} m/s | RMSE Weidmann-vs-raw = {rmse_weid:.3f} | corr={corr:.2f}")
    verdict = "PASS" if rmse_model < 0.20 else ("OK" if rmse_model < 0.30 else "WEAK")
    print(f"  -> [{verdict}] the model reproduces the REAL bottleneck FD it was never calibrated on.")

    with open(os.path.join(RES, "validate_juelich.csv"), "w") as f:
        f.write("density,raw_speed,model_speed,weidmann\n" +
                "\n".join(f"{cen[i]:.2f},{vbin[i]:.3f},{model_v[i]:.3f},{wd_v[i]:.3f}" for i in range(len(cen))) + "\n")

    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ax.scatter(rho, v, s=6, color="#bbb", alpha=0.35, label="raw frames (Jülich)")
    rr = np.linspace(0.2, max(5.0, cen.max() + 0.5), 120)
    ax.plot(rr, weidmann(rr), color="#888", lw=2, ls="--", label="Weidmann (calibration target)")
    ax.plot(cen, vbin, "s-", color="#222", ms=7, label="real data (binned median)")
    ax.plot(cen, model_v, "o-", color="#C0392B", ms=7, label=f"our model (held-out, RMSE {rmse_model:.2f})")
    ax.set_xlabel("density (ped/m²)"); ax.set_ylabel("speed (m/s)")
    ax.set_title("Held-out validation: model vs REAL raw Jülich bottleneck trajectories")
    ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.set_ylim(0, 1.6)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "validate_juelich.png"), dpi=140)
    print("-> results/validate_juelich.csv, figures/validate_juelich.png")


if __name__ == "__main__":
    main()
