"""Run a scenario and emit a SELF-CONTAINED 3D playback (Three.js) at webmvp/viewer3d.html.

Showcase: the real-geometry Itaewon counter-flow crush (the validated case). Records agent positions +
per-agent local density per frame, then bakes them into a single HTML file that plays the crowd back in 3D
(orbit camera, agents coloured blue->red by local density, walls + floor). No install, no server needed.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
from crowdsim import Config, Simulation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "webmvp", "viewer3d.html")

W, H = 54.0, 12.0
ALLEY_LEN, ALLEY_W = 45.0, 3.2
HALF = ALLEY_W / 2.0
N_PER, SECS, EVERY = 110, 38.0, 3        # per-stream agents; record every EVERY steps (~0.15 s)


def local_density(pos, r=1.0):
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    return (d < r).sum(axis=1) / (np.pi * r * r)


def run_record():
    cfg = Config(width=W, height=H, boundary="walls", max_value=50.0,
                 field_gain=1.10, field_deposit_gain=0.7, w_compress=2.0, deformable=True)
    rng = np.random.default_rng(0); sim = Simulation(cfg, rng)
    walls = [(0.0, HALF + 0.25, ALLEY_LEN, 0.5), (0.0, -(HALF + 0.25), ALLEY_LEN, 0.5)]
    sim.set_walls(walls)
    zr = lambda k: rng.uniform(-HALF + 0.2, HALF - 0.2, k)
    posL = np.c_[rng.uniform(-22, -11, N_PER), zr(N_PER)]
    posR = np.c_[rng.uniform(11, 22, N_PER), zr(N_PER)]
    sim.spawn(np.vstack([posL, posR]))
    grpA = np.arange(2 * N_PER) < N_PER
    tgt = np.zeros((2 * N_PER, 2)); tgt[grpA] = [300, 0]; tgt[~grpA] = [-300, 0]
    edge = ALLEY_LEN / 2 + 2.0
    frames, dens, peak = [], [], 0.0
    for t in range(int(SECS / cfg.dt)):
        sim.set_targets(tgt); sim.step()
        outA = grpA & (sim.pos[:, 0] > edge); outB = (~grpA) & (sim.pos[:, 0] < -edge)
        if outA.any(): sim.pos[outA] = np.c_[rng.uniform(-22, -18, outA.sum()), zr(outA.sum())]; sim.vel[outA] = 0
        if outB.any(): sim.pos[outB] = np.c_[rng.uniform(18, 22, outB.sum()), zr(outB.sum())]; sim.vel[outB] = 0
        if t % EVERY == 0:
            ld = local_density(sim.pos, 1.0)
            peak = max(peak, float(ld.max()))
            frames.append([[round(float(x), 2), round(float(z), 2)] for x, z in sim.pos])
            dens.append([round(float(v), 1) for v in ld])
    return dict(walls=walls, w=W, h=H, alley=[ALLEY_LEN, ALLEY_W], group=int(N_PER),
                frames=frames, dens=dens), peak


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Crowd 3D — Itaewon crush</title>
<style>html,body{margin:0;height:100%;background:#0d1117;color:#e6edf3;font-family:system-ui,Segoe UI,sans-serif;overflow:hidden}
#hud{position:fixed;left:12px;top:12px;z-index:10;background:rgba(20,26,34,.82);padding:12px 14px;border-radius:10px;max-width:330px;font-size:13px;line-height:1.45}
#hud h1{font-size:15px;margin:0 0 6px} #hud b{color:#58a6ff}
#bar{position:fixed;left:0;right:0;bottom:0;z-index:10;background:rgba(20,26,34,.9);padding:10px 14px;display:flex;gap:12px;align-items:center}
#bar button{background:#238636;color:#fff;border:0;border-radius:6px;padding:7px 14px;font-size:14px;cursor:pointer}
#bar input[type=range]{flex:1} .leg{display:inline-block;width:12px;height:12px;border-radius:3px;margin:0 4px -1px 8px}
#t{min-width:120px;text-align:right;font-variant-numeric:tabular-nums}</style></head>
<body>
<div id="hud"><h1>Itaewon 2022 — counter-flow crush <span style="font-weight:400;color:#8b949e">(calibrated model, 3D)</span></h1>
Real alley geometry <b>45 m × 3.2 m</b>. Two crowds collide in the middle.<br>
Agents coloured by local density: <span class="leg" style="background:#2c7fb8"></span>low
<span class="leg" style="background:#7fcdbb"></span>· <span class="leg" style="background:#fec44f"></span>dense
<span class="leg" style="background:#e31a1c"></span>crush.<br>
<span style="color:#8b949e">drag = orbit · scroll = zoom · right-drag = pan</span><br>
peak density this run: <b id="pk">–</b> ped/m²</div>
<div id="bar"><button id="pp">⏸ Pause</button><input id="sl" type="range" min="0" value="0"><span id="t">0.0 s</span></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const SIM = __DATA__;
const PEAK = __PEAK__;
document.getElementById('pk').textContent = PEAK.toFixed(1);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0d1117);
scene.fog = new THREE.Fog(0x0d1117, 40, 110);
const cam = new THREE.PerspectiveCamera(55, innerWidth/innerHeight, 0.1, 500);
cam.position.set(0, 26, 30);
const ren = new THREE.WebGLRenderer({antialias:true});
ren.setSize(innerWidth, innerHeight); ren.setPixelRatio(Math.min(2,devicePixelRatio));
document.body.appendChild(ren.domElement);
const ctr = new THREE.OrbitControls(cam, ren.domElement); ctr.target.set(0,0,0); ctr.update();
scene.add(new THREE.AmbientLight(0xffffff, .65));
const dl = new THREE.DirectionalLight(0xffffff, .8); dl.position.set(20,40,15); scene.add(dl);
// floor
const floor = new THREE.Mesh(new THREE.PlaneGeometry(SIM.w, SIM.h),
  new THREE.MeshStandardMaterial({color:0x161b22}));
floor.rotation.x = -Math.PI/2; scene.add(floor);
const grid = new THREE.GridHelper(Math.max(SIM.w,SIM.h), Math.round(Math.max(SIM.w,SIM.h)), 0x30363d, 0x21262d);
scene.add(grid);
// walls
const wmat = new THREE.MeshStandardMaterial({color:0x586069});
SIM.walls.forEach(([cx,cz,sx,sz])=>{ const m=new THREE.Mesh(new THREE.BoxGeometry(sx,1.6,sz),wmat);
  m.position.set(cx,0.8,cz); scene.add(m); });
// agents (instanced)
const N = SIM.frames[0].length;
const geo = new THREE.CylinderGeometry(0.22,0.22,1.7,8);
const mat = new THREE.MeshStandardMaterial({});
const mesh = new THREE.InstancedMesh(geo, mat, N);
mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); scene.add(mesh);
const dummy = new THREE.Object3D(); const col = new THREE.Color();
// blue -> teal -> yellow -> red ramp by density (0..9)
function ramp(d){ const t=Math.max(0,Math.min(1,d/9));
  const stops=[[0.17,0.5,0.72],[0.5,0.8,0.73],[0.99,0.77,0.31],[0.89,0.10,0.11]];
  const x=t*3, i=Math.min(2,Math.floor(x)), f=x-i;
  return [stops[i][0]+(stops[i+1][0]-stops[i][0])*f, stops[i][1]+(stops[i+1][1]-stops[i][1])*f,
          stops[i][2]+(stops[i+1][2]-stops[i][2])*f]; }
function setFrame(k){
  const P=SIM.frames[k], D=SIM.dens[k];
  for(let i=0;i<N;i++){ dummy.position.set(P[i][0],0.85,P[i][1]); dummy.updateMatrix();
    mesh.setMatrixAt(i,dummy.matrix); const c=ramp(D[i]); col.setRGB(c[0],c[1],c[2]); mesh.setColorAt(i,col); }
  mesh.instanceMatrix.needsUpdate=true; if(mesh.instanceColor) mesh.instanceColor.needsUpdate=true;
  document.getElementById('t').textContent=(k*SIM.dt_play).toFixed(1)+' s';
}
SIM.dt_play = __DT__;
const sl=document.getElementById('sl'); sl.max=SIM.frames.length-1;
let frame=0, playing=true, acc=0, last=performance.now();
document.getElementById('pp').onclick=function(){ playing=!playing; this.textContent=playing?'⏸ Pause':'▶ Play'; };
sl.oninput=function(){ frame=+this.value; playing=false; document.getElementById('pp').textContent='▶ Play'; setFrame(frame); };
function loop(now){ requestAnimationFrame(loop); const dt=(now-last)/1000; last=now;
  if(playing){ acc+=dt; if(acc>=0.06){ acc=0; frame=(frame+1)%SIM.frames.length; sl.value=frame; setFrame(frame);} }
  ctr.update(); ren.render(scene,cam); }
setFrame(0); requestAnimationFrame(loop);
addEventListener('resize',()=>{ cam.aspect=innerWidth/innerHeight; cam.updateProjectionMatrix(); ren.setSize(innerWidth,innerHeight); });
</script></body></html>"""


def main():
    data, peak = run_record()
    print(f"recorded {len(data['frames'])} frames, {data['frames'][0].__len__()} agents, peak density {peak:.1f} ped/m²")
    html = (TEMPLATE.replace("__DATA__", json.dumps(data, separators=(",", ":")))
            .replace("__PEAK__", f"{peak:.1f}").replace("__DT__", f"{EVERY*0.05:.3f}"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(OUT) // 1024
    print(f"-> {OUT} ({kb} KB) — open in any browser (or http://localhost:8000/viewer3d.html)")


if __name__ == "__main__":
    main()
