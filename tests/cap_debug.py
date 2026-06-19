import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crowdsim.evaluate import evaluate_layout
from experiments.capacity_design import room

for nd, w in [(1, 1.6), (2, 1.6)]:
    for N in (30, 60, 90):
        r = evaluate_layout(room(nd, w), n=N, seeds=(0,), maxsec=80, inflate=0.2)
        print(f"{nd}door {w}m N={N}: evac={r['evacuated']:.0f}/{N}  t50={r['t50']:.1f}  t80={r['t80']:.1f}  t90={r['t90']:.1f}")
