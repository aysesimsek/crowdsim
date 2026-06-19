import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crowdsim.evaluate import evaluate_layout
from crowdsim.scenarios import SCENARIOS

for name in ("Bottleneck", "MultiExit", "NearFar"):
    r = evaluate_layout(SCENARIOS[name], seeds=(0, 1))
    print(f"\n{name}: evac={r['evacuated']:.1f}/{r['n']}  t50={r['t50']:.1f}  t90={r['t90']:.1f}  "
          f"peakDens={r['peak_density']:.2f}  MoranI={r['morans_i']:.2f}")
    print(f"   exit usage={[round(u,2) for u in r['exit_usage']]}  binding={r['binding_exit']}  "
          f"imbalance={r['exit_imbalance']:.2f}")
    print(f"   risk grid {r['risk'].shape} max={r['risk'].max():.2f}  hotspots="
          f"{[(round(x,1),round(z,1),round(s,2)) for x,z,s in r['hotspots']]}")
print("\nEVAL SMOKE PASS")
