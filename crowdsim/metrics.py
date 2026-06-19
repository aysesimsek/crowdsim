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


def close_pairs(pos, dist=0.45):
    if len(pos) < 2:
        return 0
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    iu = np.triu_indices(len(pos), 1)
    return int((d[iu] < dist).sum())
