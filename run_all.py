"""Run every experiment in sequence -> results/*.csv + figures/*.png."""
import os, sys, importlib, traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

EXPERIMENTS = [
    "scenario_layouts",      # draws the whole scenario library (figure only)
    "fundamental_diagram",
    "phase_transition",
    # added as ported:
    # "coordination", "actuator", "moran_generalization", "early_warning",
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
