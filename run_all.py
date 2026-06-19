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
    "design_clinic",         # evaluate a layout + A/B-test ranked safety interventions
    # added as ported:
    # "actuator", "early_warning", "anisotropy",
    # train_rl is intentionally omitted from run_all (slow torch training; run it directly)
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
