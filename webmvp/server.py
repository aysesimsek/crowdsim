"""Crowd-safety design clinic — web MVP backend (zero extra dependencies; uses stdlib http.server).

Serves the single-page editor and two JSON endpoints:
  GET  /api/scenarios          -> the built-in layout library (for presets)
  POST /api/analyze   {layout} -> egress + risk map (PNG) + congestion hotspots + exit balance
  POST /api/recommend {layout} -> A/B-tested, ranked safety interventions

Run:  python webmvp/server.py     then open http://localhost:8000
"""
import os, sys, io, json, base64, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from http.server import BaseHTTPRequestHandler, HTTPServer

from crowdsim.scenarios import Scenario, SCENARIOS
from crowdsim.evaluate import evaluate_layout
from crowdsim.recommend import recommend

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = (0, 1)
NAGENTS = 45


def scenario_from(d):
    return Scenario("user", d.get("note", "user layout"),
                    float(d.get("width", 24)), float(d.get("height", 18)),
                    walls=[tuple(map(float, w)) for w in d.get("walls", [])],
                    spawns=[tuple(map(float, s)) for s in d.get("spawns", [])],
                    exits=[tuple(map(float, e)) for e in d.get("exits", [])],
                    goals=d.get("goals"))


def render_risk(sc, r):
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    risk = r["risk"].T
    ax.imshow(risk, origin="lower", extent=[-sc.width/2, sc.width/2, -sc.height/2, sc.height/2],
              cmap="inferno", aspect="equal")
    for (cx, cz, s_x, s_z) in sc.walls:
        ax.add_patch(Rectangle((cx - s_x/2, cz - s_z/2), s_x, s_z, color="#444", zorder=3))
    if sc.exits:
        ex = np.array(sc.exits, float)
        ax.scatter(ex[:, 0], ex[:, 1], marker="*", s=160, color="#19e019", edgecolor="k", lw=.5, zorder=5)
    for x, z, s in r["hotspots"]:
        ax.add_patch(Circle((x, z), 0.8, fill=False, color="cyan", lw=2, zorder=6))
    ax.set_title("Affect-field crush-risk map + hotspots", fontsize=11)
    ax.set_xlabel("x (m)"); ax.set_ylabel("z (m)")
    buf = io.BytesIO(); fig.tight_layout(); fig.savefig(buf, format="png", dpi=110); plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def analyze(layout):
    sc = scenario_from(layout)
    n = int(layout.get("n", NAGENTS))
    r = evaluate_layout(sc, seeds=SEEDS, n=n, inflate=0.2)
    return {
        "risk_png": render_risk(sc, r),
        "metrics": {
            "evacuated": round(r["evacuated"], 1), "n": n,
            "t50": round(r["t50"], 1), "t90": round(r["t90"], 1),
            "peak_density": round(r["peak_density"], 2), "morans_i": round(r["morans_i"], 2),
            "exit_imbalance": round(r["exit_imbalance"], 2), "binding_exit": r["binding_exit"],
            "exit_usage": [round(u, 2) for u in r["exit_usage"]],
            "hotspots": [[round(x, 1), round(z, 1), round(s, 2)] for x, z, s in r["hotspots"]],
        },
    }


def suggest(layout):
    sc = scenario_from(layout)
    n = int(layout.get("n", NAGENTS))
    base, recs = recommend(sc, seeds=SEEDS, n=n)
    out = [{"label": rr["label"], "evac": round(rr["metrics"]["evacuated"], 1),
            "delta": round(rr["d_evac"], 1)} for rr in recs]
    return {"baseline_evac": round(base["evacuated"], 1), "recommendations": out}


def library():
    lib = {}
    for name, sc in SCENARIOS.items():
        lib[name] = {"note": sc.note, "width": sc.width, "height": sc.height,
                     "walls": [list(w) for w in sc.walls], "spawns": [list(s) for s in sc.spawns],
                     "exits": [list(e) for e in sc.exits], "goals": sc.goals}
    return lib


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/api/scenarios":
            self._send(200, json.dumps(library()))
        elif self.path == "/viewer3d.html":
            p = os.path.join(HERE, "viewer3d.html")
            if os.path.exists(p):
                with open(p, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            else:
                self._send(404, json.dumps({"error": "run experiments/export_sim.py to build the 3D viewer"}))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/analyze":
                self._send(200, json.dumps(analyze(data)))
            elif self.path == "/api/recommend":
                self._send(200, json.dumps(suggest(data)))
            else:
                self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:
            traceback.print_exc()
            self._send(500, json.dumps({"error": str(e)}))

    def log_message(self, *a):
        pass


def main():
    port = int(os.environ.get("PORT", 8000))
    print(f"Crowd-safety design clinic MVP -> http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__":
    main()
