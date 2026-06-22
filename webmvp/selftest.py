"""Quick self-test of the running MVP server (python webmvp/selftest.py)."""
import json, urllib.request

BASE = "http://localhost:8000"


def post(path, obj):
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def get(path):
    return json.loads(urllib.request.urlopen(BASE + path, timeout=30).read())


lib = get("/api/scenarios")
print(f"/api/scenarios OK: {len(lib)} presets")
for name in ("Bottleneck", "NearFar", "MultiExit"):
    s = lib[name]
    pl = {"width": s["width"], "height": s["height"], "n": 45, "walls": s["walls"],
          "spawns": s["spawns"], "exits": s["exits"], "goals": s["goals"]}
    r = post("/api/analyze", pl)
    m = r["metrics"]
    print(f"  analyze {name:10s} evac={m['evacuated']}/45  t50={m['t50']}  imbalance={m['exit_imbalance']}  "
          f"hotspots={len(m['hotspots'])}  png={'yes' if r['risk_png'].startswith('data:image') else 'NO'}")
s = lib["NearFar"]
rec = post("/api/recommend", {"width": s["width"], "height": s["height"], "n": 45, "walls": s["walls"],
                              "spawns": s["spawns"], "exits": s["exits"], "goals": s["goals"]})
print(f"  recommend NearFar: baseline={rec['baseline_evac']}  best={rec['recommendations'][0]['label']} "
      f"({rec['recommendations'][0]['evac']}, d{rec['recommendations'][0]['delta']:+})")
s = lib["Bottleneck"]
sim = post("/api/simulate", {"width": s["width"], "height": s["height"], "n": 45, "walls": s["walls"],
                             "spawns": s["spawns"], "exits": s["exits"], "goals": s["goals"]})
print(f"  simulate Bottleneck: frames={len(sim['frames'])}  agents={len(sim['frames'][0])}  "
      f"peak={sim['peak']}  evac={sim['evacuated']}/{sim['n']}  dt={sim['dt']}")
assert len(sim["frames"]) > 5 and len(sim["dens"]) == len(sim["frames"]) and len(sim["evac_frame"]) == sim["n"]
print("SELFTEST PASS")
