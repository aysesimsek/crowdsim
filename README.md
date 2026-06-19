# crowdsim2d — stigmergic affect fields for crowd simulation (2D, pure Python)

A compact, fast, fully-reproducible **2D agent-based crowd simulator** built around a *stigmergic
affect field*. It is a pure-Python/numpy reimplementation of a Unity ML-Agents crowd-affect model, so
every experiment runs in **seconds with no engine round-trips**.

## The model (two contributions)

1. **Stigmergic affect field** — collective emotion is an autonomous scalar field on a grid that
   evolves by reaction–diffusion, `∂Φ/∂t = D∇²Φ − kΦ + S`. Agents *deposit* affect (∝ their stress)
   and *sample* a local "field pressure". Unlike pairwise contagion, emotion lives in the **environment**:
   it has spatial structure and persists after the agents that made it leave.
2. **Affect-gated arbitration** — each agent's acceleration blends a reactive Social-Force controller
   with a (pluggable) learned residual through a scalar gate `λ = σ(b₀ + kₐ·load + k_f·fieldP + raw)`,
   operationalising dual-process control. With no residual, `λ` scales the physics; affect also
   modulates desired speed, personal space, and herding.

The driving term is a Helbing velocity relaxation, so free-flow speed → the desired speed; locomotion
is validated against the empirical fundamental diagram (free-flow ≈ Weidmann's 1.34 m/s, monotone
slowdown with density).

## Layout

```
crowdsim/
  model.py      core: Config, AffectField, Simulation (vectorised numpy)
  navigation.py Dijkstra flow field -> route around walls / through doors to the nearest exit
  metrics.py    Moran's I helpers, Cliff's δ, Mann–Whitney, density/contacts
  scenarios.py  data-driven library of 23 RiMEA-style layouts (arena, walls, spawns, exits, flow)
experiments/    one runnable script per study (writes results/*.csv + figures/*.png)
tests/          smoke_test.py
run_all.py      run every experiment
```

## Scenario library

`crowdsim/scenarios.py` holds 23 pedestrian benchmarks as pure geometry (open square, corridor,
bottleneck, wide door, pillar-before-door, multi-exit, three-exit, near/far, double-bottleneck,
counter-flow, corner, 4-way crossing, T-junction, merging lanes, obstacle field, room→corridor,
two-rooms, stage egress, stadium funnel, four-rooms, zigzag, asymmetric-exits, wide counter-flow).
Adding one is a single dict entry; `experiments/scenario_layouts.py` draws them all into
`figures/scenario_layouts.png`, so the visual stays in sync as the library grows.

## Run

```bash
pip install -r requirements.txt
python tests/smoke_test.py          # sanity check the core
python run_all.py                   # run all experiments -> results/ + figures/
# or a single study:
python experiments/phase_transition.py
```

## Experiments

| script | reproduces | status |
|--------|-----------|--------|
| `scenario_layouts.py` | draws all 23 scenarios (auto-updates with the library) | ✅ |
| `egress_runner.py` | every scenario, FIELD vs NOFIELD: egress + Moran's I + density (navigation-routed) | ✅ |
| `fundamental_diagram.py` | speed–density vs Weidmann (locomotion validation) | ✅ |
| `phase_transition.py` | collective panic as a phase transition (critical density + feedback gain) | ✅ |
| `coordination.py` | communication-free exit redistribution (field-route vs nearest) | planned |
| `actuator.py` | affect field as an actuator; self-organisation beats naive central control | planned |
| `early_warning.py` | critical-slowing-down early warning of the panic tipping point | planned |

The egress runner confirms the field's spatial structure across **all 23 layouts** (Moran's I ≈ 0.87–0.93
with the field, exactly 0 without) — pillar-1 generalisation, reproduced in pure Python.

## Notes
- Boundary is `"walls"` (clamp + rectangular obstacles) or `"torus"` (periodic).
- The affect field can be disabled by setting `field_gain=0` and `field_deposit_gain=0` (the matched
  pairwise/no-field baseline → Moran's I ≈ 0).
- This Python model mirrors the Unity ML-Agents version; the genuine Unity-only part was training the
  PPO arbitration policy. Most experiments do not use the learned residual, so they port exactly.
