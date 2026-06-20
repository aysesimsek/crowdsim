# Crowd-Safety Design Clinic — web MVP

A minimal, self-contained web app for the **design-time** product: draw or load a floor plan, get a
crush-risk map, safe-occupancy metrics, and A/B-tested safety fixes. It wraps the `crowdsim2d` engine
(`evaluate_layout` + `recommend`) — **no extra dependencies** (Python stdlib `http.server` + the same
numpy/matplotlib the repo already uses).

## Run

```bash
python webmvp/server.py        # -> http://localhost:8000
```

Open **http://localhost:8000** in a browser. (Opening `index.html` as a file won't work — the API needs
the server.)

## Use

- **Load a preset** from the dropdown (28 built-in layouts) — the fastest way to see it work.
- Or **draw your own**: pick a tool and edit the canvas
  - **Wall** — drag a rectangle (obstacle / partition)
  - **Spawn** — drag a rectangle (where people start)
  - **Exit** — click to drop a door (green ★)
  - **Erase** — click an item to remove it
- Set the arena size and number of people, then:
  - **Analyze** → crush-risk heatmap + evacuated / median-clearance / peak-density / exit-imbalance + hotspots
  - **Suggest fixes** → interventions (widen the binding exit, add a flow-pillar, affect-field guidance),
    A/B-tested and ranked by people evacuated

## Endpoints

| method | path | body | returns |
|--------|------|------|---------|
| GET  | `/api/scenarios` | — | the built-in layout library |
| POST | `/api/analyze`   | `{width,height,n,walls,spawns,exits,goals}` | `{metrics, risk_png}` |
| POST | `/api/recommend` | same layout | `{baseline_evac, recommendations}` |

`walls` = `[cx,cz,sx,sz]` rectangles · `spawns` = `[x0,x1,z0,z1]` rectangles · `exits` = `[x,z]` points,
all in world metres centred at the arena centre.

## Scope / next

This is an MVP demonstrator. Toward production: validated engine (force-based crush + stairs + data
calibration — see `experiments/validation_suite.py`, `crush_pressure.py`), a real layout importer
(image/CAD), a continuous optimiser (`experiments/optimize_design.py` → CMA-ES), report export, and the
operations-time arm (live density → real-time risk + early warning).
