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
  rl.py         multi-agent PPO (torch) for the learned affect-gated arbitration policy
  evaluate.py   evaluate_layout(): egress + affect-field risk map + hotspots + exit balance
  recommend.py  closed-loop design recommender: A/B-test interventions, ranked by safety
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
| `agent_drain.py` | field autonomy: persists + decays at its own rate after the crowd is removed | ✅ |
| `coordination.py` | communication-free exit redistribution (field-route vs nearest) | ✅ |
| `train_rl.py` | learned affect-gated arbitration (multi-agent PPO) — the part that was Unity-only | ✅ |
| `rl_scenarios.py` | run the trained RL-combined agents across the library (OOD transfer: ~matches physics) | ✅ |
| `rl_resolution.py` | explains Unity's 2.5× RL gain: a locomotion-baseline artifact, reproduced with NO RL | ✅ |
| `design_clinic.py` | evaluate a layout + A/B-test ranked safety interventions (the design framework) | ✅ |
| `actuator.py` | affect field as an actuator; self-organisation beats naive central control | planned |
| `early_warning.py` | critical-slowing-down early warning of the panic tipping point | planned |

The egress runner confirms the field's spatial structure across **all 23 layouts** (Moran's I ≈ 0.87–0.93
with the field, exactly 0 without) — pillar-1 generalisation, reproduced in pure Python.

## Design clinic (layout in → diagnosis + solutions out)

The stigmergic affect field is not just a model — its time-averaged value is a **crush-risk / congestion
map**, which turns the simulator into a layout-evaluation tool:

```python
from crowdsim import evaluate_layout, recommend
from crowdsim.scenarios import SCENARIOS

report = evaluate_layout(SCENARIOS["Bottleneck"])     # egress, risk map, hotspots, exit balance
base, ranked = recommend(SCENARIOS["Bottleneck"])     # A/B-tested interventions, best first
```

`evaluate_layout` returns evacuated / t50 / t90, the affect-field **risk grid**, congestion **hotspots**
(local maxima of the risk map), per-exit usage and the binding exit. `recommend` proposes interventions —
*widen the binding exit*, *add an offset flow-pillar*, *affect-field exit guidance* (operational, no
rebuild; backed by the coordination result) — simulates each, and ranks them by people evacuated.
`experiments/design_clinic.py [Scenario]` prints the report and draws the risk heatmap + the ranked A/B
test. This is the MVP of an "upload your floor-plan, get a safety diagnosis and ranked fixes" framework —
with the affect field as the novel design diagnostic. (`evaluate_layout(..., policy=net)` also runs the
learned RL agents on any layout.)

## Notes
- Boundary is `"walls"` (clamp + rectangular obstacles) or `"torus"` (periodic).
- The affect field can be disabled by setting `field_gain=0` and `field_deposit_gain=0` (the matched
  pairwise/no-field baseline → Moran's I ≈ 0).
- This Python model mirrors the Unity ML-Agents version. The previously Unity-only part — training the
  PPO arbitration policy — is now reproduced in pure torch (`experiments/train_rl.py`, `crowdsim/rl.py`,
  saved to `models/`). **Honest finding:** with a validated physics controller and a minimal reward, the
  learned gate becomes *physics-dominant* (λ → 0.97–0.98, above the 0.94 default) and the learned residual
  does **not** beat physics — a tie on the easy open task, and *worse* on a wall+gap task where the
  progress reward is deceptive (the policy backs off rather than discovering the detour). So pillar 2's
  value is conditional: the gate correctly defers to competent physics; RL would need reward shaping or a
  genuinely physics-unsolvable regime to earn its keep. Pillar 1 (the stigmergic field) is the strong,
  unconditional contribution.
- **Why the Unity paper saw a 2.5× RL egress gain but 2D does not** (`experiments/rl_resolution.py`):
  Unity's own clamp-probe already showed pure physics (λ=1) ≥ the learned gate, and the paper attributes
  the 2.5× to "the medium-horizon goal-seeking a purely local Social-Force controller lacks". We confirm
  it is a **baseline-locomotion artifact, not RL intelligence**: a *weak* constant-force controller
  (free-flow ≈ 0.8 m/s) vs the *strong* Helbing relaxation (free-flow ≈ 2.0) gives a **2.85× open-arena
  throughput gap with no RL at all** (and the weak one fails outright at bottlenecks). Unity's RL merely
  supplied the fast goal-seeking its BaselineSFM lacked; our physics has it natively (validated vs
  Weidmann), so RL adds nothing. The 2.5× was real but attributable to a weak baseline.
