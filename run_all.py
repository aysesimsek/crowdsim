"""Run every experiment in sequence -> results/*.csv + figures/*.png."""
import os, sys, importlib, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

EXPERIMENTS = [
    "scenario_layouts",      # draws the whole scenario library (figure only)
    "egress_runner",         # runs every scenario, FIELD vs NOFIELD -> table + figure
    "fundamental_diagram",
    "phase_transition",
    "agent_drain",           # field autonomy (persists + decays after the crowd is removed)
    "coordination",          # communication-free exit redistribution (field-route vs nearest)
    "actuator",              # field as actuator: steers but naive control over-steers (self-org wins)
    "precision_gate",        # inference-time gate cuts stuck-states (defer from stalled physics)
    "early_warning",         # critical slowing down: ensemble susceptibility leads the panic tip
    "anisotropy",            # honest negative: advection operator OK, standard Moran's I direction-blind
    "rl_resolution",         # the 2.5x RL gain is a baseline-locomotion artifact (no RL)
    "design_clinic",         # evaluate a layout + A/B-test ranked safety interventions
    # train_rl / rl_scenarios omitted from run_all (need torch / the trained policy; run directly)
]


def main():
    for name in EXPERIMENTS:
        print(f"\n########## {name} ##########")
        try:
            mod = importlib.import_module(f"experiments.{name}")
            mod.main()
        except Exception:
            print(f"!! {name} failed:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
