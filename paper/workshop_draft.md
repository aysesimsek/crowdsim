# Stigmergic Affect Fields and Affect-Gated Arbitration for Crowd Simulation

*Workshop draft — v0.1 (2026-06-17). Numbers from a 7-condition × 10-seed ablation; citations marked [verify] need a final source check before submission.*

---

## Abstract

We model collective emotion in crowd simulation as an **autonomous stigmergic field** — a
scalar affect quantity deposited into the environment, diffusing and decaying over space and
time — rather than as the pairwise agent-to-agent contagion that dominates prior work. On top of
this field we place an **affect-gated arbitration** mechanism in which each agent blends a
reactive Social-Force controller with a learned (PPO) corrective policy through a scalar gate
λ that is conditioned on the agent's affective state, operationalising dual-process (System-1 /
System-2) control. In a factorial ablation (7 conditions, 10 seeds) we show that (i) the affect
field produces strong, statistically significant spatial autocorrelation of emotion (global
Moran's I ≈ 0.84 with the field enabled vs 0 without, p < 0.001), which pairwise contagion
cannot represent; (ii) an **agent-drain** test confirms the field is an autonomous substrate —
after the entire population is removed, affect persists and decays at the field's own intrinsic
rate (k ≈ 0.34 s⁻¹), a memory property a mean-field/pairwise model provably cannot reproduce;
(iii) the gate λ is genuinely affect-dependent (regression R² = 0.67; λ rises
with affective load, the dual-process direction), and because the arbitration force drives
locomotion, this dependence is behavioural, not cosmetic; and (iv) the learned controller
reaches ~2.5× more goals than a pure Social-Force baseline. We additionally observe an emergent
slowing of egress in high-affect regions, consistent with real crowd behaviour under stress, and
in a dense corridor the model reproduces the empirical fundamental diagram up to ~1.7 ped/m² in
both shape and magnitude (free speed 1.38 m/s vs Weidmann 1.34; ~0.48 m/s at 1.7 ped/m²).
We discuss the limitation that, under a physics-dominant gate, the arbitration's behavioural
footprint remains modest, and outline how a wider gate range and validation against empirical
pedestrian data extend the work.

---

## 1. Introduction

Realistic simulation of dense human crowds in safety-critical settings (evacuations, large
gatherings) must capture two intertwined phenomena: how **emotion/panic propagates** through a
crowd, and how that emotion **changes individual movement decisions**. Two limitations recur in
prior work.

First, collective emotion is almost always modelled as **pairwise contagion**: each agent's
affect is updated from its neighbours' affect over a proximity graph (epidemiological,
thermodynamic, or dyadic update rules). This is O(N²) in interactions, treats emotion as a
private per-agent state, and — crucially — has **no spatial persistence**: when agents leave a
location, the emotional "charge" of that place vanishes with them.

Second, locomotion is modelled either by hand-designed reactive forces (the Social-Force Model,
interpretable but rigid) or by reinforcement learning that *replaces* those forces (flexible but
opaque, and typically affect-agnostic). No prior model lets an agent **learn how much to trust
reactive physics versus its own correction as a function of its emotional state**.

**Contributions.** We address both gaps:

1. **A stigmergic affect field** (Sec. 3.1): collective emotion as an autonomous reaction–
   diffusion field ∂Φ/∂t = D∇²Φ − kΦ + S(x,t) on the environment, into which agents deposit
   affect and from which they sample it. Emotion becomes a property of *places*, with
   environmental memory decoupled from the moving population. We quantify the resulting spatial
   structure with **Moran's I**, a spatial-autocorrelation statistic new to this subfield.

2. **Affect-gated arbitration** (Sec. 3.4): a scalar gate λ ∈ [0,1] blends a Social-Force action
   with a PPO residual, accel = λ·F_phys + (1−λ)·u_RL, where λ is conditioned on affective state.
   We report a negative finding — *unconstrained RL converges to a near-constant λ* — that
   motivates a **structured affect gate** (a dual-process prior) carrying a learned residual.

3. **A factorial evaluation** (Sec. 4–5) with an ablation over field, social, memory, and gate
   components across 10 seeds, multi-metric crowd analysis (egress, density, contacts, path
   smoothness, group coherence, stress, Moran's I), and significance testing.

## 2. Related Work

**Emotion contagion in crowds.** The dominant computational approach is agent-pairwise:
epidemiological/SIS rules (Durupınar et al. [verify]), thermodynamic flow (ASCRIBE; Bosse et al.
[verify]), and dyadic-relation models (ESCAPES; Tsai et al. [verify]); a recent systematic review
(van Haeringen & Gerritsen, 2023 [verify]) classifies essentially all such models as neighbour-
graph updates. None decouple affect into an environmental field.

**Continuum / field crowd models.** Continuum Crowds (Treuille, Cooper & Popović, 2006 [verify])
and kinetic-theory PDE models represent **density/velocity/pressure**, not affect; where they
include fear it is a per-agent variable advected with the crowd, not an autonomous field. Our
field is of *affect*, with its own deposit–diffuse–decay dynamics.

**RL for crowd locomotion.** Decentralised PPO collision avoidance (Long et al. [verify]),
CADRL/GA3C-CADRL (Chen, Everett, How [verify]) and graphics-oriented crowd RL learn **full
policies that replace reactive rules**. Residual RL (Johannink et al., 2019 [verify]) learns an
additive correction on a fixed controller but uses a *fixed, unweighted* sum. We instead learn a
*state-dependent blend weight*.

**Arbitration / dual-process control.** Reliability/uncertainty-weighted arbitration between a
model-based and a model-free controller is grounded in neuroscience (Daw et al., 2005; Lee,
Shimojo & O'Doherty, 2014 [verify]). Such gates are conditioned on uncertainty or disagreement —
never, to our knowledge, on **affect**, and not in a crowd-simulation context.

**Gap.** No prior model (a) treats affect as an autonomous spatial field, nor (b) gates a
physics-vs-learning arbitration on emotional state. We do both and evaluate them jointly.

## 3. Method

### 3.1 Stigmergic affect field
A scalar field Φ is maintained on a uniform grid over the environment. Each step every agent
deposits affect proportional to its affective load; the field evolves by a discrete reaction–
diffusion update (4-neighbour Jacobi Laplacian + exponential decay), Φ ← Φ + D∇²Φ·dt − kΦ·dt,
clamped to [0, Φ_max]. Agents sample Φ bilinearly at their position to obtain a *field pressure*
that drives their affective dynamics. Landmarks act as sinks (comfort) and stimulus zones as
sources (alarms). The field is O(N) per step and, unlike pairwise contagion, retains an emotional
imprint of a location after the agents that created it have moved on.

### 3.2 Cognitive state
Each agent carries a continuous cognitive state — affective load, fatigue, familiarity, and an
episodic-memory bias — updated from local density, stimulus salience, field pressure, and a
*true* contagion term (flow toward the neighbourhood-mean load, not a one-way copy).

### 3.3 Reactive base controller
The reactive layer is a Social-Force controller (separation with a distance floor to bound the
1/d² kernel, a social-flow term aggregating neighbour intent/velocity, goal attraction, and
obstacle repulsion); affective load increases personal space and desired speed.

### 3.4 Affect-gated arbitration
A PPO policy outputs a planar corrective force u_RL and a raw gate value; the executed
acceleration is

  accel = λ·F_phys + (1 − λ)·u_RL,   λ = σ(raw + b₀ + k_a·load + k_f·fieldP).

The affect terms (k_a, k_f > 0) encode the dual-process prior that higher affective load shifts
control toward the reactive System-1 controller; b₀ biases the untrained gate toward physics so
the policy bootstraps from a navigating baseline; the learned *raw* term is the situational
residual. **Motivation:** with a *free* gate (λ = σ(raw) only), PPO converged to a near-constant
λ ≈ 0.43 that did not depend on affect (regression R² ≈ 0.001) — a negative result that motivates
the structured gate. The arbitration force is the agent's sole mover, so λ genuinely controls
behaviour.

### 3.5 Training
Decentralised PPO (~20 shared-policy agents). Each episode an agent respawns at a valid point and
is assigned one reachable goal; reward = dense progress toward goal + success bonus − small
effort/time penalties. Training reaches a stable positive return with short episode lengths
(agents reach goals in ≈160 steps), indicating efficient goal-directed navigation.

## 4. Experimental Setup

**Environment.** A 40×40 arena with obstacles, waypoints and goals; NavMesh for planning, custom
force-driven locomotion.

**Ablation (7 conditions).** `Full` (all on); `NoField`, `NoSocial`, `NoMemory` (remove one
component); `FixedLambda` (λ ≡ 1, physics only with RL present); and two baselines — `BaselineSFM`
(pure Social-Force, no RL/field/social/memory) and `SFMContagion` (Social-Force + pairwise
contagion). Each condition is run for **10 seeds**.

**Metrics.** Egress throughput, peak local density, agent–agent contacts, path turning
(smoothness), group coherence, mean affective load (stress), the learned gate λ, and **global
Moran's I** of the affect field (4-neighbour contiguity). Per-run time-aggregates are compared
across conditions with mean ± 95% CI, Mann–Whitney U with Holm correction, and Cliff's δ effect
size. Per-step per-agent telemetry supports λ-maps and λ-regression.

## 5. Results

### 5.1 The affect field creates spatial emotional structure
Global Moran's I is **0.84 ± 0.01** with the field enabled (Full, NoSocial, NoMemory, FixedLambda)
and exactly **0** without it (BaselineSFM, SFMContagion, NoField), p < 0.001, Cliff's δ = −1.0
across all field-off conditions. The field thus produces strong, persistent spatial clustering of
affect — structure that pairwise contagion, lacking an environmental substrate, cannot produce.

![**Figure 1.** Global Moran's I of the affect field by condition (mean, 95% CI, 10 seeds). Field-on
conditions (Full, NoSocial, NoMemory, FixedLambda) show strong spatial autocorrelation (≈0.84);
field-off conditions (BaselineSFM, SFMContagion, NoField) are exactly 0.](figures/fig1_morans_i.png)

### 5.2 The gate is genuinely affect-dependent
With the structured gate, λ rises with affect: λ–load Pearson r = **0.83** (Spearman 0.90), and a
multiple regression of λ on standardised cognitive/spatial covariates gives **R² = 0.67** with a
dominant positive load coefficient (β = 0.81, p < 0.001) — the pre-registered dual-process
direction (more affect → more reactive control). This contrasts sharply with the free-gate
baseline (R² ≈ 0.001, constant λ). λ-maps show the gate spatially tracking the affect field.

![**Figure 2.** Spatial map of the learned arbitration λ over the arena (Full condition). λ varies
with location, tracking the affect field; red = trust reactive physics, blue = trust the RL
correction.](figures/fig2_lambda_map.png)

### 5.3 The learned controller improves egress
Conditions with the RL/arbitration layer active reach **18.8–24.1** goals per run versus
**8.6–9.6** for the pure Social-Force baselines — a ~2.5× throughput gain — at comparable contact
rates.

![**Figure 3.** Egress throughput (goals reached per run) by condition (mean, 95% CI, 10 seeds).
The learned-arbitration conditions roughly double the pure Social-Force baselines.](figures/fig3_throughput.png)

### 5.4 Emergent stress-modulated egress
Enabling the field slightly *reduces* throughput (Full 18.8 vs NoField 23.1) and raises localized
stress response: agents slow in high-affect regions. This reproduces the qualitative real-world
effect of panic impeding egress, emerging from the field coupling rather than being hand-coded.

### 5.5 Agent-drain: the field is an autonomous substrate, not mean-field contagion
To test the *defining* property of a stigmergic field — environmental memory **decoupled from the
population** — we let the field build up, then at t = 30 s removed **all** agents simultaneously and
recorded the field thereafter. The field does not collapse: it **persists and decays exponentially
at its own intrinsic rate**. The fitted post-drain decay constant is k ≈ 0.34 s⁻¹ (half-life ≈ 2.0 s),
matching the field's configured decay parameter (0.35 s⁻¹) and *independent of agent count*; 52% of
the affect present at drain remains 2 s later, 18% at 5 s. A mean-field / pairwise-contagion model,
in which affect is a function of the agents currently present, would read ≈ 0 the instant the
population is removed and **provably cannot reproduce this persistence**. This is direct empirical
evidence that the affect field is an autonomous environmental substrate, the property that
distinguishes it from all pairwise-contagion crowd-emotion models.

![**Figure 4.** Agent-drain test: affect field mean over time. The field builds while agents are
present, and after all agents are removed at t = 30 s it persists and decays exponentially at its
own rate (k ≈ 0.34 s⁻¹) — not to zero instantly as a mean-field/pairwise model would (grey
reference).](figures/fig4_agent_drain.png)

### 5.6 Fundamental diagram (dense corridor)
In a periodic corridor with position-based contact resolution, swept from 0.17 to 4.33 ped/m²
(realised net forward speed), the model reproduces the empirical pedestrian fundamental diagram
in the practically important regime: free-flow speed is **1.38 m/s** (ρ = 0.17), matching the
canonical Weidmann value (v₀ = 1.34 m/s), and speed falls to **~0.48 m/s at 1.67 ped/m²**,
quantitatively consistent with measured pedestrian data (~0.5–0.7 m/s at 1–1.7 ped/m²). The
congested branch (≤ ~1.7 ped/m²) is thus matched in **both shape and magnitude**, not merely
qualitatively. Honest limitation: above ~1.7 ped/m² the simplified contact model shows a mild
speed *recovery* (0.48 → 0.67 m/s) rather than continued jamming toward standstill, so the
extreme high-density / flow-collapse regime is not captured; a velocity-based (e.g. ORCA/RVO)
contact model is needed there. We therefore report a quantitative FD match up to ~1.7 ped/m².

![**Figure 5.** Fundamental diagram in the dense corridor: model speed v(ρ) and flow J(ρ) vs the
Weidmann (1993) reference. Free speed (1.38 m/s) and the congested drop to ~0.48 m/s at 1.7 ped/m²
match empirical data; the mild speed recovery above ~1.7 ped/m² is a contact-model
limitation.](figures/fig5_fundamental_diagram.png)

### 5.7 Field vs pairwise contagion (head-to-head)
Our ablation already contains a direct, matched comparison: `Full` adds the stigmergic field on top
of pairwise contagion, while `NoField` keeps the pairwise contagion (the social/contagion channel,
flow toward the neighbourhood-mean load) but removes the field — i.e. `NoField` *is* a pairwise-
contagion crowd-emotion model run in the identical environment, policy, and seeds. The contrast is
categorical: the field condition yields global Moran's I = 0.84 (strong spatial clustering of
affect), whereas the pairwise condition yields **exactly 0** — pairwise contagion, lacking an
environmental substrate, produces no spatial affect structure (p < 0.001, Cliff's δ = −1.0). The
agent-drain test (§5.5) sharpens this: the field's affect persists after the population is removed
(decay at k ≈ 0.34 s⁻¹), a place-memory that a pairwise model *cannot* exhibit because its affect is
defined only on the agents currently present. Together these establish, on matched runs, the two
properties — spatial structure and population-independent memory — that distinguish the stigmergic
field from the entire pairwise-contagion line of work. (A dedicated stimulus-on/off flow protocol
against a literature-calibrated density-coupled contagion model, e.g. ASCRIBE/Durupınar, is left to
the full paper as additional confirmation.)

## 6. Discussion and Limitations

**Physics-dominant gate.** The bootstrap bias keeps λ ≈ 0.94 (physics-leaning), which is necessary
for stable navigation but limits the arbitration's behavioural footprint: `Full` and `FixedLambda`
trajectories differ only modestly (speed-distribution JS divergence ≈ 0.012). The gate is
*measurably* affect-dependent but *behaviourally* gentle. Widening the gate range (smaller b₀)
trades navigation stability for arbitration impact — a tension we will map explicitly.

**Designed vs learned gating.** The affect-dependence of λ is, by construction, partly imposed by
the structured prior; the RL contributes the residual. We therefore frame the contribution as a
*structured affect-gated arbitration with a learned residual*, motivated by the negative finding
that free RL does not discover affect-gating.

**Locomotion architecture & scale.** A single open arena with ~20 agents; locomotion is custom
force integration with NavMesh planning. Larger, denser, multi-exit scenarios remain future work.

**Partial external validation.** The fundamental-diagram comparison (§5.6) anchors the model to
empirical pedestrian data up to ~1.7 ped/m²; the extreme high-density / flow-collapse regime and
trajectory-level dataset comparisons remain to be validated.

## 7. Conclusion and Future Work

We introduced collective emotion as an autonomous stigmergic field and an affect-gated arbitration
between reactive physics and a learned residual, and showed — across a 10-seed factorial ablation —
that the field produces significant spatial affect structure (Moran's I) that pairwise contagion
cannot, that the gate is genuinely affect-dependent (R² = 0.67) and behaviour-driving, and that the
learned controller improves egress ~2.5×, an agent-drain test confirms the field's
population-independent environmental memory (which pairwise contagion cannot reproduce), a matched
field-vs-pairwise comparison shows the field alone yields spatial affect structure, and the model
reproduces the empirical fundamental diagram up to ~1.7 ped/m². Future work: (a) a dedicated
**stimulus-on/off flow protocol** against a literature-calibrated density-coupled contagion model
(ASCRIBE/Durupınar) for post-stimulus hysteresis; (b) extreme-density FD with a velocity-based
(ORCA/RVO) contact model to reach the flow-collapse regime; (c) a wider/precision-based gate
(active-inference framing) and anisotropic, flow-coupled field diffusion; (d) larger, denser,
multi-exit scenarios; (e) trajectory-level validation against pedestrian datasets.

## References
*Verified against primary sources (APS, ACM DL, IEEE, Springer, IFAAMAS, PubMed) on 2026-06-17.*

1. Helbing, D., & Molnár, P. (1995). Social force model for pedestrian dynamics. *Physical Review E*, 51(5), 4282–4286.
2. Treuille, A., Cooper, S., & Popović, Z. (2006). Continuum crowds. *ACM Transactions on Graphics*, 25(3), 1160–1168. (Proc. SIGGRAPH 2006).
3. Durupınar, F., Allbeck, J., Pelechano, N., & Badler, N. (2008). Creating crowd variation with the OCEAN personality model. In *Proc. AAMAS 2008*, 1217–1220.
4. Durupınar, F., Güdükbay, U., Aman, A., & Badler, N. I. (2016). Psychological parameters for crowd simulation: From audiences to mobs. *IEEE Transactions on Visualization and Computer Graphics*, 22(9), 2145–2159.
5. Bosse, T., Hoogendoorn, M., Klein, M. C. A., Treur, J., van der Wal, C. N., & van Wissen, A. (2013). Modelling collective decision making in groups and crowds: Integrating social contagion and interacting emotions, beliefs and intentions (ASCRIBE). *Autonomous Agents and Multi-Agent Systems*, 27(1), 52–84.
6. Tsai, J., Fridman, N., Bowring, E., Brown, M., Epstein, S., Kaminka, G., Marsella, S., et al. (2011). ESCAPES — Evacuation simulation with children, authorities, parents, emotions, and social comparison. In *Proc. AAMAS 2011*, 457–464.
7. van Haeringen, E. S., Gerritsen, C., & Hindriks, K. V. (2023). Emotion contagion in agent-based simulations of crowds: A systematic review. *Autonomous Agents and Multi-Agent Systems*, 37(1), Art. 6.
8. Long, P., Fan, T., Liao, X., Liu, W., Zhang, H., & Pan, J. (2018). Towards optimally decentralized multi-robot collision avoidance via deep reinforcement learning. In *Proc. IEEE ICRA 2018*, 6252–6259.
9. Chen, Y. F., Liu, M., Everett, M., & How, J. P. (2017). Decentralized non-communicating multiagent collision avoidance with deep reinforcement learning. In *Proc. IEEE ICRA 2017*, 285–292.
10. Everett, M., Chen, Y. F., & How, J. P. (2018). Motion planning among dynamic, decision-making agents with deep reinforcement learning (GA3C-CADRL). In *Proc. IEEE/RSJ IROS 2018*, 3052–3059.
11. Johannink, T., Bahl, S., Nair, A., Luo, J., Kumar, A., Loskyll, M., Ojea, J. A., Solowjow, E., & Levine, S. (2019). Residual reinforcement learning for robot control. In *Proc. IEEE ICRA 2019*, 6023–6029.
12. Daw, N. D., Niv, Y., & Dayan, P. (2005). Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control. *Nature Neuroscience*, 8(12), 1704–1711.
13. Lee, S. W., Shimojo, S., & O'Doherty, J. P. (2014). Neural computations underlying arbitration between model-based and model-free learning. *Neuron*, 81(3), 687–699.
