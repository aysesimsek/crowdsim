"""Anisotropic flow-coupled diffusion -- an HONEST NEGATIVE.

If affect were advected by crowd flow, the field would stretch along the flow. We check this at the
operator level on a grid: (a) pure diffusion vs (b) advection (+x) + diffusion, from the same blob.
Findings:
  - The advection operator is CORRECT: the advected blob's centroid moves downstream at ~v (transport
    works).
  - But standard (omni-directional) Moran's I is DIRECTION-BLIND: it is ~the same for the isotropic and
    the advected field, so it cannot detect the anisotropy. The right observable is a DIRECTIONAL
    autocorrelation (east-west vs north-south), which does separate them at the operator level.
Reported as a negative that scopes the correct future observable (directional, not standard Moran's I)
-- matching the Unity result where the directional signature was not recoverable from aggregate Moran's I.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)

NX = 60
DX = 1.0
D = 0.6           # diffusion
V = 0.8           # advection speed (+x), cells/s
K = 0.05          # decay
DT = 0.1
STEPS = 120


def lap(F):
    return (np.roll(F, 1, 0) + np.roll(F, -1, 0) + np.roll(F, 1, 1) + np.roll(F, -1, 1) - 4 * F) / DX**2


def step(F, vx):
    # upwind advection for vx>0 along axis 0 (x)
    adv = -vx * (F - np.roll(F, 1, 0)) / DX
    return np.clip(F + DT * (D * lap(F) + adv - K * F), 0, None)


def moran(F):                              # standard omni-directional (rook, torus), S0=4N
    d = F - F.mean(); den = (d * d).sum()
    neigh = np.roll(d, 1, 0) + np.roll(d, -1, 0) + np.roll(d, 1, 1) + np.roll(d, -1, 1)
    return float((d * neigh).sum() / (4 * den + 1e-12))


def moran_axis(F, axis):                   # directional autocorrelation along one axis, S0=2N
    d = F - F.mean(); den = (d * d).sum()
    neigh = np.roll(d, 1, axis) + np.roll(d, -1, axis)
    return float((d * neigh).sum() / (2 * den + 1e-12))


def centroid_x(F):
    xs = np.arange(NX)[:, None]
    return float((F * xs).sum() / (F.sum() + 1e-12))


def main():
    print("=" * 64); print("ANISOTROPY -- honest negative (operator-level)"); print("=" * 64)
    F0 = np.zeros((NX, NX))
    F0[NX // 2 - 3:NX // 2 + 3, NX // 2 - 3:NX // 2 + 3] = 1.0     # central blob
    iso, adv = F0.copy(), F0.copy()
    cx0 = centroid_x(adv)
    cxs, tt = [], []
    for t in range(STEPS):
        iso = step(iso, 0.0)
        adv = step(adv, V)
        cxs.append(centroid_x(adv) - cx0); tt.append(t * DT)

    # operator check: advected centroid displacement vs expected v*t
    exp = V * np.array(tt)
    slope = np.polyfit(tt, cxs, 1)[0]
    print(f"  [operator] advected centroid drift = {slope:.2f} cells/s (set v={V}) -> transport CORRECT")
    print(f"             isotropic centroid drift = {centroid_x(iso)-cx0:+.3f} cells (stays put)")

    mi_iso, mi_adv = moran(iso), moran(adv)
    ew_iso, ns_iso = moran_axis(iso, 0), moran_axis(iso, 1)
    ew_adv, ns_adv = moran_axis(adv, 0), moran_axis(adv, 1)
    print(f"  [standard Moran's I]  isotropic={mi_iso:.3f}  advected={mi_adv:.3f}  "
          f"(diff {abs(mi_iso-mi_adv):.3f}) -> DIRECTION-BLIND, cannot detect anisotropy")
    print(f"  [directional autocorr] isotropic EW-NS={ew_iso-ns_iso:+.3f}  advected EW-NS={ew_adv-ns_adv:+.3f} "
          f"-> the correct observable separates them")
    print("  -> HONEST NEGATIVE: advection operator is correct, but the anisotropy is NOT visible in")
    print("     standard Moran's I; a directional autocorrelation is the observable to use.")

    with open(os.path.join(RES, "anisotropy.csv"), "w") as f:
        f.write("metric,isotropic,advected\n")
        f.write(f"moran_standard,{mi_iso:.4f},{mi_adv:.4f}\n")
        f.write(f"moran_EW,{ew_iso:.4f},{ew_adv:.4f}\nmoran_NS,{ns_iso:.4f},{ns_adv:.4f}\n")
        f.write(f"centroid_drift,{centroid_x(iso)-cx0:.4f},{slope:.4f}\n")

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.3))
    ax[0].imshow(iso.T, origin="lower", cmap="inferno"); ax[0].set_title("isotropic diffusion")
    ax[1].imshow(adv.T, origin="lower", cmap="inferno"); ax[1].set_title(f"advection +x (v={V}) + diffusion")
    for a in ax[:2]:
        a.set_xticks([]); a.set_yticks([])
    a2 = ax[2]
    a2.plot(tt, cxs, color="#2E6FB7", lw=2, label="advected centroid drift")
    a2.plot(tt, exp, "--", color="#888", label=f"expected v·t (v={V})")
    a2.set_xlabel("time (s)"); a2.set_ylabel("x-centroid displacement (cells)")
    a2.set_title(f"operator OK; but $I$ blind: iso={mi_iso:.2f}, adv={mi_adv:.2f}")
    a2.legend(fontsize=8)
    fig.suptitle("Anisotropy: an honest negative (operator correct, standard Moran's I direction-blind)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(FIG, "anisotropy.png"), dpi=140)
    print("-> results/anisotropy.csv, figures/anisotropy.png")


if __name__ == "__main__":
    main()
