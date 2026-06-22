export const meta = {
  name: 'crowdsim-regression',
  description: 'Re-run every substantive experiment under the recalibrated core model and report whether each documented finding survives',
  phases: [{ title: 'Regression', detail: 'one agent per experiment: run it, compare to the documented claim' }],
}

// Each experiment + the claim the chapter currently makes about it (with OLD numbers where known).
const EXPERIMENTS = [
  { s: 'validation_suite.py', claim: 'FD tracks Weidmann (was RMSE 0.29 — after calibration should be much smaller, ~0.03-0.12); free-flow ~1.34 m/s; bottleneck specific flow in the 1.2-1.9 band; FD monotone decreasing.' },
  { s: 'validation.py', claim: 'bottleneck specific flow ~1.9 ped/m/s, within the empirical 1.2-1.9 band for door-limited widths (1.6-2.4 m).' },
  { s: 'coordination.py', claim: 'FieldRoute LOWERS the max-exit share vs Baseline (communication-free exit balancing); Cliff delta negative, p<0.05; far (wasted) exit used more under FieldRoute.' },
  { s: 'fundamental_diagram.py', claim: 'free-flow speed ~1.34 m/s (Weidmann vmax); speed decreases monotonically with density.' },
  { s: 'agent_drain.py', claim: 'the affect field shapes evacuation/drain dynamics (field-on differs from field-off).' },
  { s: 'anisotropy.py', claim: 'HONEST NEGATIVE: the advection operator is correct but the directional Moran-I prediction is falsified. It should REMAIN a negative result (that is the expected, correct outcome here).' },
  { s: 'phase_transition.py', claim: 'collective panic behaves as a phase transition with a critical density / feedback gain.' },
  { s: 'early_warning.py', claim: 'critical slowing down (ensemble susceptibility/variance) rises before the panic tipping point — a leading early-warning signal.' },
  { s: 'panic_prevention.py', claim: 'an early-warning-triggered calming intervention averts the tip (prevented run stays low while the un-prevented run tips over).' },
  { s: 'hysteresis.py', claim: 'ramp-up vs ramp-down shows a bistable hysteresis loop with nonzero area (~0.9).' },
  { s: 'mean_field_theory.py', claim: 'a mean-field reduction (effective coupling kappa) reproduces the transition curve; continuous crossover, not a sharp fold.' },
  { s: 'precision_gate.py', claim: 'the active-inference precision gate reduces stuck-states / uncertainty (~-24%) by deferring to RL when physics fails, at a modest speed cost.' },
  { s: 'dual_process_decision.py', claim: 'affect-gated arbitration blends physics and learned control; the lambda gate behaves as designed (physics-dominant by default).' },
  { s: 'actuator.py', claim: 'writing to the affect field STEERS the crowd (large effect delta ~1.0) but naive open-loop control OVER-steers (can be worse than self-organisation).' },
  { s: 'capacity_design.py', claim: 'median clearance t50 grows with crowd size and shrinks with door width — a monotone safe-capacity curve (e.g. 1.6 m door slower, wider doors faster).' },
  { s: 'crush_density.py', claim: 'peak crush density rises with crowding / narrower geometry.' },
  { s: 'crush_pressure.py', claim: 'crowd pressure keeps rising while density saturates; fewer/narrower doors give higher pressure; the 2-door layout is lowest.' },
  { s: 'case_study.py', claim: 'Itaewon-style alley: counter-flow GRIDLOCKS (few evacuate, ~14/70) while one-way flow evacuates far more (~64/70).' },
  { s: 'heterogeneity.py', claim: 'a vulnerable/slow subpopulation (20% at 0.4x speed) increases overall clearance time (~+15%).' },
  { s: 'optimize_design.py', claim: 'do not fragment the door budget — concentrating width beats splitting into narrow doors (~+62%).' },
  { s: 'sensitivity.py', claim: 'the headline results are robust to +/-40% variation in key parameters.' },
]

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    script: { type: 'string' },
    ran: { type: 'boolean', description: 'did the script run to completion without a Python error' },
    headline: { type: 'string', description: 'the exact key numbers it printed now (the summary line(s))' },
    verdict: { type: 'string', enum: ['survives', 'shifted', 'broken', 'error'], description: 'survives = qualitative claim holds with similar numbers; shifted = claim holds but numbers moved materially; broken = claim contradicted; error = did not run' },
    note: { type: 'string', description: 'one line: what changed vs the documented numbers, or the error' },
  },
  required: ['script', 'ran', 'headline', 'verdict', 'note'],
}

function promptFor(e) {
  return `You are verifying one experiment in the crowdsim2d repo after a CORE MODEL recalibration (separation force softened: w_sep 3.0->2.0, ps_base 0.9->0.7; new contact_friction for a realistic jamming branch). The model is now calibrated to real pedestrian data (Weidmann FD).

Run this experiment and capture its printed output:
  In the Bash tool run:  cd /d/Repo/crowdsim2d && python experiments/${e.s} 2>&1
It is a numpy simulation and MAY TAKE SEVERAL MINUTES — set the Bash timeout to the maximum (600000 ms) and wait for it to finish. Do not kill it early.

The chapter currently documents this claim about ${e.s}:
  "${e.claim}"

After it finishes, decide:
- ran: did it complete without a Python traceback?
- headline: copy the exact summary numbers it printed (the key result line(s) only).
- verdict: 'survives' if the qualitative claim still holds with similar numbers; 'shifted' if the claim direction holds but numbers moved materially (state old->new); 'broken' if the result now CONTRADICTS the claim; 'error' if it failed to run.
- note: one line on what changed vs the documented numbers (or the error message).

Be strictly honest — if a finding weakened or reversed, say 'broken' or 'shifted', do not round up to 'survives'. Return ONLY the structured object.`
}

phase('Regression')
log(`Re-running ${EXPERIMENTS.length} experiments under the recalibrated model...`)
const results = (await parallel(
  EXPERIMENTS.map(e => () => agent(promptFor(e), { label: `run:${e.s}`, phase: 'Regression', schema: SCHEMA }))
)).filter(Boolean)

const by = { survives: [], shifted: [], broken: [], error: [] }
for (const r of results) (by[r.verdict] || by.error).push(r)
log(`DONE: survives=${by.survives.length}  shifted=${by.shifted.length}  broken=${by.broken.length}  error=${by.error.length}`)
for (const r of results) log(`[${r.verdict}] ${r.script} — ${r.note}`)

return {
  counts: { survives: by.survives.length, shifted: by.shifted.length, broken: by.broken.length, error: by.error.length },
  results,
}
