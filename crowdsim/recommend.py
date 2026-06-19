"""Closed-loop design recommender.

Given a layout, propose architectural / operational interventions, A/B-test each against the baseline
with evaluate_layout, and rank them by safety (people evacuated, then egress time). Interventions:
  - widen the binding (most-loaded) exit
  - add an offset flow-pillar before the binding exit (a pillar can smooth a clogging door)
  - affect-field exit guidance (operational, no rebuild): agents read the field and self-balance across
    exits -- backed by our coordination result (this is where pillar 1 becomes a design tool).
"""
from dataclasses import replace
import numpy as np
from .evaluate import evaluate_layout


def widen_exit(sc, e, delta=0.9):
    ex, ez = sc.exits[e]
    walls = [list(w) for w in sc.walls]
    for w in walls:
        cx, cz, sx, sz = w
        if sx <= sz and abs(cx - ex) < 1.2:           # vertical wall on the exit's line
            zlo, zhi = cz - sz / 2, cz + sz / 2
            if zlo >= ez - 0.05:
                zlo = min(zhi - 0.4, zlo + delta)
            elif zhi <= ez + 0.05:
                zhi = max(zlo + 0.4, zhi - delta)
            else:
                continue
            w[1], w[3] = (zlo + zhi) / 2, zhi - zlo
        elif sz < sx and abs(cz - ez) < 1.2:           # horizontal wall on the exit's line
            xlo, xhi = cx - sx / 2, cx + sx / 2
            if xlo >= ex - 0.05:
                xlo = min(xhi - 0.4, xlo + delta)
            elif xhi <= ex + 0.05:
                xhi = max(xlo + 0.4, xhi - delta)
            else:
                continue
            w[0], w[2] = (xlo + xhi) / 2, xhi - xlo
    return replace(sc, walls=[tuple(w) for w in walls], name=sc.name + "+wider")


def add_pillar(sc, e):
    p = np.array(sc.exits[e], float)
    v = -p; nv = np.linalg.norm(v); v = v / nv if nv > 1e-6 else np.array([1.0, 0.0])
    perp = np.array([-v[1], v[0]])
    px, pz = p + 1.9 * v + 0.7 * perp
    return replace(sc, walls=list(sc.walls) + [(float(px), float(pz), 0.7, 0.7)], name=sc.name + "+pillar")


def recommend(scenario, seeds=(0, 1, 2), n=45, maxsec=50.0):
    base = evaluate_layout(scenario, seeds=seeds, n=n, maxsec=maxsec)
    e = base["binding_exit"]
    cands = [("widen binding exit", widen_exit(scenario, e), {}),
             ("offset flow-pillar", add_pillar(scenario, e), {})]
    if len(scenario.exits) > 1:
        cands.append(("affect-field exit guidance", scenario, dict(field_route=True)))
    out = []
    for label, sc2, kw in cands:
        r = evaluate_layout(sc2, seeds=seeds, n=n, maxsec=maxsec, **kw)
        out.append(dict(label=label, scenario=sc2, kw=kw, metrics=r,
                        d_evac=r["evacuated"] - base["evacuated"],
                        d_t50=(r["t50"] - base["t50"]) if (r["t50"] > 0 and base["t50"] > 0) else None,
                        d_imbalance=r["exit_imbalance"] - base["exit_imbalance"]))
    out.sort(key=lambda d: (-d["metrics"]["evacuated"], d["metrics"]["t50"] if d["metrics"]["t50"] > 0 else 1e9))
    return base, out
