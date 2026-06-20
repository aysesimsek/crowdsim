"""Shared statistics + crowd-metric helpers used across experiments."""
import numpy as np


def cliffs_delta(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    gt = sum(int((x > b).sum()) for x in a)
    lt = sum(int((x < b).sum()) for x in a)
    return (gt - lt) / (len(a) * len(b))


def mannwhitney(a, b, alternative="two-sided"):
    """Returns p-value; falls back to nan on degenerate input. Uses scipy if available."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    try:
        from scipy import stats
        return float(stats.mannwhitneyu(a, b, alternative=alternative).pvalue)
    except Exception:
        return float("nan")


def ci95(a):
    a = np.asarray(a, float)
    if len(a) < 2:
        return (float(a.mean()) if len(a) else float("nan")), 0.0
    return float(a.mean()), float(1.96 * a.std(ddof=1) / np.sqrt(len(a)))


def peak_local_density(pos, radius=1.5):
    """Max over agents of (neighbours within radius + 1) / disc area  -> ped/m^2."""
    if len(pos) == 0:
        return 0.0
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    near = (d < radius).sum(axis=1)
    return float((near + 1).max() / (np.pi * radius * radius))


def crowd_pressure(pos, vel, radius=1.5):
    """Helbing-style crowd 'pressure' = local density x local velocity variance (a crush predictor).
    Turbulent stop-go shoving (high local velocity variance) at high density is what kills in crushes;
    this rises even when static density saturates. Returns the peak over agents."""
    if len(pos) < 3:
        return 0.0
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    peak = 0.0
    for i in range(len(pos)):
        m = d[i] < radius                         # local cluster (includes self at d=0)
        if m.sum() >= 3:
            rho = m.sum() / (np.pi * radius * radius)
            v = vel[m]
            var = float(((v - v.mean(0)) ** 2).sum(1).mean())   # speed variance in the cluster
            peak = max(peak, rho * var)
    return float(peak)


def close_pairs(pos, dist=0.45):
    if len(pos) < 2:
        return 0
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    iu = np.triu_indices(len(pos), 1)
    return int((d[iu] < dist).sum())
