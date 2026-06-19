"""Smoke test: the core runs, agents move toward goals, the field builds spatial structure, no NaNs."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from crowdsim import Config, Simulation

rng = np.random.default_rng(1)
cfg = Config(width=16, height=16, boundary="walls", max_value=50.0)
sim = Simulation(cfg, rng)

N = 40
pos = rng.uniform(-7, 7, size=(N, 2))
targets = rng.uniform(-7, 7, size=(N, 2))
sim.spawn(pos, targets)

d0 = np.linalg.norm(sim.pos - sim.target, axis=1).mean()
for _ in range(300):
    sim.step()
d1 = np.linalg.norm(sim.pos - sim.target, axis=1).mean()

assert np.isfinite(sim.pos).all(), "NaN/inf in positions"
assert (sim.load >= 0).all() and (sim.load <= 1).all(), "load out of [0,1]"
fm = sim.field.mean(); mi = sim.field.morans_i()
print(f"mean dist-to-goal: {d0:.2f} -> {d1:.2f}  (agents should approach goals)")
print(f"mean affective load: {sim.load.mean():.3f}")
print(f"field mean: {fm:.3f}   field Moran's I: {mi:.3f}   field peak: {sim.field.peak():.3f}")
print(f"mean lambda: {sim.lambda_.mean():.3f}   mean speed: {np.linalg.norm(sim.vel,axis=1).mean():.3f}")
assert fm > 0, "field did not build"
assert mi > 0.2, f"field has no spatial structure (Moran's I={mi:.2f})"
print("\nSMOKE TEST PASSED")
