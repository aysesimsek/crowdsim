"""Core 2D crowd model: stigmergic affect field + Social-Force locomotion + affect-gated arbitration.

Vectorised numpy. Faithful to the Unity ML-Agents model's parameters and semantics so results match.
"""
from dataclasses import dataclass, field as _field
import numpy as np


@dataclass
class Config:
    # arena (metres) + field grid
    width: float = 24.0
    height: float = 24.0
    cell: float = 0.8
    boundary: str = "walls"          # "walls" (clamp + rect obstacles) or "torus" (periodic)
    # affect field (reaction-diffusion)
    diffusion: float = 1.0
    decay: float = 0.5               # field forgetting rate (paper uses 0.35; experiments may override)
    deposit_gain: float = 1.0
    field_deposit_gain: float = 0.7  # per-agent deposit weight
    max_value: float = 50.0          # high => avoid saturation (use 5.0 for the panic-dynamics regime)
    # cognition (affective load dynamics)
    field_gain: float = 1.10         # how strongly field pressure drives load
    decay_load: float = 0.18
    density_gain: float = 0.35
    contagion_gain: float = 0.35
    uncertainty_gain: float = 0.25
    calm_gain: float = 0.45          # familiarity-driven calming (the stabiliser)
    kappa: float = 0.5               # contagion/social kernel decay
    sense_radius: float = 3.0
    dens_cap: float = 12.0
    # Social-Force locomotion
    w_sep: float = 3.0
    w_goal: float = 1.6
    w_obs: float = 6.0
    w_soc: float = 1.2
    dist_floor: float = 0.4
    base_speed: float = 1.8
    stressed_speed: float = 2.6
    max_accel: float = 8.0
    tau: float = 0.5                 # velocity-relaxation time (Helbing driving term -> free-flow = vmax)
    # affect-gated arbitration: lambda = sigmoid(physics_bias + k_a*load + k_f*fieldP + raw)
    physics_bias: float = 2.0
    k_lambda_affect: float = 2.0
    k_lambda_field: float = 1.5
    # sim
    dt: float = 0.05
    contact_radius: float = 0.22
    hard_contact: bool = True


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class AffectField:
    """Scalar affect field on a grid: deposit-diffuse-decay reaction-diffusion (the stigmergic substrate)."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.nx = max(2, int(round(cfg.width / cfg.cell)))
        self.nz = max(2, int(round(cfg.height / cfg.cell)))
        self.minx = -cfg.width / 2.0
        self.minz = -cfg.height / 2.0
        self.F = np.zeros((self.nx, self.nz))

    def reset(self):
        self.F[:] = 0.0

    def _cells(self, pos):
        ix = np.clip(((pos[:, 0] - self.minx) / self.cfg.cell).astype(int), 0, self.nx - 1)
        iz = np.clip(((pos[:, 1] - self.minz) / self.cfg.cell).astype(int), 0, self.nz - 1)
        return ix, iz

    def step(self, dt):
        c = self.cfg
        F = self.F
        lap = (np.roll(F, 1, 0) + np.roll(F, -1, 0) + np.roll(F, 1, 1) + np.roll(F, -1, 1) - 4.0 * F)
        self.F = np.clip(F + c.diffusion * lap * dt - c.decay * F * dt, 0.0, c.max_value)

    def deposit(self, pos, amount):
        ix, iz = self._cells(pos)
        np.add.at(self.F, (ix, iz), self.cfg.deposit_gain * amount)
        np.clip(self.F, 0.0, self.cfg.max_value, out=self.F)

    def deposit_point(self, x, z, amount):
        self.deposit(np.array([[x, z]]), np.array([amount]))

    def calm_point(self, x, z, amount):
        ix, iz = self._cells(np.array([[x, z]]))
        self.F[ix[0], iz[0]] = max(0.0, self.F[ix[0], iz[0]] - amount)

    def sample(self, pos):
        """Bilinear sample at continuous positions -> raw field value array."""
        fx = (pos[:, 0] - self.minx) / self.cfg.cell
        fz = (pos[:, 1] - self.minz) / self.cfg.cell
        x0 = np.clip(np.floor(fx).astype(int), 0, self.nx - 1)
        z0 = np.clip(np.floor(fz).astype(int), 0, self.nz - 1)
        x1 = np.clip(x0 + 1, 0, self.nx - 1)
        z1 = np.clip(z0 + 1, 0, self.nz - 1)
        tx = np.clip(fx - x0, 0, 1)
        tz = np.clip(fz - z0, 0, 1)
        a = self.F[x0, z0]; b = self.F[x1, z0]; cc = self.F[x0, z1]; d = self.F[x1, z1]
        return (a * (1 - tx) + b * tx) * (1 - tz) + (cc * (1 - tx) + d * tx) * tz

    def sample_point(self, x, z):
        return float(self.sample(np.array([[x, z]]))[0])

    def mean(self):
        return float(self.F.mean())

    def peak(self):
        return float(self.F.max())

    def morans_i(self):
        # global Moran's I, 4-neighbour (rook) contiguity on the (periodic) grid.
        f = self.F - self.F.mean()
        denom = float((f * f).sum())
        if denom < 1e-12:
            return 0.0
        # num counts the +x and +z directed edges once; all four directions = 2*num by symmetry.
        num = float((f * np.roll(f, 1, 0)).sum() + (f * np.roll(f, 1, 1)).sum())
        N = self.F.size
        S0 = 4 * N                      # 4 neighbours per cell
        return (N / S0) * (2.0 * num / denom)


class Simulation:
    """Holds the affect field, the (vectorised) crowd, and axis-aligned rectangular walls.

    Walls are (cx, cz, sx, sz) rectangles on the obstacle layer. Goals/targets are per-agent points;
    set them with set_targets() (experiments do route choice by updating targets). The arbitration
    acceleration is the sole mover. A pluggable u_rl(sim)->(N,2) hook supplies a learned residual
    (default zero, matching the 'RL inactive' regime of most procedural experiments).
    """

    def __init__(self, cfg: Config, rng=None):
        self.cfg = cfg
        self.rng = rng if rng is not None else np.random.default_rng(0)
        self.field = AffectField(cfg)
        self.walls = []                      # list of (cx, cz, sx, sz)
        self.u_rl = None                     # optional callable(sim) -> (N,2)
        self._alloc(0)

    # ---- setup ----
    def _alloc(self, n):
        self.n = n
        self.pos = np.zeros((n, 2)); self.vel = np.zeros((n, 2))
        self.load = np.full(n, 0.02); self.fatigue = np.zeros(n); self.fam = np.zeros(n)
        self.target = np.zeros((n, 2)); self.group = np.zeros(n, int)
        self._stuck = np.zeros(n)

    def set_walls(self, walls):
        self.walls = [tuple(w) for w in walls]

    def spawn(self, positions, targets=None, fam=0.0):
        positions = np.asarray(positions, float)
        self._alloc(len(positions))
        self.pos[:] = positions
        self.fam[:] = fam
        self.target[:] = positions if targets is None else np.asarray(targets, float)

    def set_targets(self, targets):
        self.target[:] = np.asarray(targets, float)

    # ---- dynamics ----
    def _pairwise(self):
        d = self.pos[:, None, :] - self.pos[None, :, :]      # (N,N,2) from j to i
        dist = np.linalg.norm(d, axis=2)
        return d, dist

    def _social_force(self, dist, dvec):
        c = self.cfg
        N = self.n
        load = self.load
        ps = 0.9 + 0.5 * load                                # personal space expands with load
        beta = 1.0 + 0.6 * load                              # avoidance boost with stress
        gamma = 0.3 + 1.0 * load                             # herding (social-flow) gain with stress
        np.fill_diagonal(dist, np.inf)
        # separation: inverse-square repulsion within personal space, with a distance floor
        within = dist < ps[:, None]
        deff = np.maximum(dist, c.dist_floor)
        mag = np.where(within, 1.0 / (deff * deff), 0.0)
        unit = dvec / np.maximum(dist[:, :, None], 1e-6)     # from neighbour to agent
        sep = (mag[:, :, None] * unit).sum(axis=1)
        sep = c.w_sep * beta[:, None] * sep
        # social flow: kernel-weighted mean of neighbour velocities (alignment/herding)
        wk = np.exp(-c.kappa * np.where(np.isinf(dist), 1e9, dist))
        wk[np.isinf(dist)] = 0.0
        wsum = wk.sum(axis=1, keepdims=True)
        meanvel = (wk[:, :, None] * self.vel[None, :, :]).sum(axis=1) / np.maximum(wsum, 1e-9)
        soc = c.w_soc * gamma[:, None] * meanvel
        # obstacle repulsion from rectangular walls
        obs = np.zeros((N, 2))
        for (cx, cz, sx, sz) in self.walls:
            hx, hz = sx / 2.0, sz / 2.0
            qx = np.clip(self.pos[:, 0], cx - hx, cx + hx)
            qz = np.clip(self.pos[:, 1], cz - hz, cz + hz)
            ox = self.pos[:, 0] - qx; oz = self.pos[:, 1] - qz
            od = np.sqrt(ox * ox + oz * oz)
            near = (od < 1.2) & (od > 1e-6)
            m = np.where(near, 1.0 / np.maximum(od, c.dist_floor) ** 2, 0.0)
            obs[:, 0] += c.w_obs * beta * m * (ox / np.maximum(od, 1e-6))
            obs[:, 1] += c.w_obs * beta * m * (oz / np.maximum(od, 1e-6))
        # interaction forces only; the goal/driving term is a velocity relaxation added in step().
        return sep + soc + obs, wk, wsum

    def _cognition(self, dist, wk, wsum, dt):
        c = self.cfg
        np.fill_diagonal(dist, np.inf)
        neigh = (dist < c.sense_radius)
        dens = np.clip(neigh.sum(axis=1) / c.dens_cap, 0, 1)
        fieldraw = self.field.sample(self.pos)
        fieldp = np.clip(fieldraw / max(1e-6, c.max_value), 0, 1)
        # true contagion: flow toward kernel-weighted neighbourhood mean load
        nb_mean = (wk * self.load[None, :]).sum(axis=1) / np.maximum(wsum[:, 0], 1e-9)
        contagion = c.contagion_gain * (nb_mean - self.load)
        # uncertainty (stuckness): ramps while moving slowly
        speed = np.linalg.norm(self.vel, axis=1)
        self._stuck = np.where(speed < 0.15, self._stuck + dt, np.maximum(0.0, self._stuck - 2 * dt))
        unc = np.clip(self._stuck / 2.0, 0, 1)
        add = (c.density_gain * dens + c.field_gain * fieldp + c.uncertainty_gain * unc
               + contagion - c.calm_gain * self.fam)
        self.load = np.clip(self.load * (1 - c.decay_load * dt) + add * dt, 0, 1)
        return fieldp

    def step(self):
        c = self.cfg
        dt = c.dt
        if self.n == 0:
            self.field.step(dt); return
        dvec, dist = self._pairwise()
        interactions, wk, wsum = self._social_force(dist.copy(), dvec)
        fieldp = self._cognition(dist.copy(), wk, wsum, dt)
        # desired speed rises with load (arousal), falls with fatigue
        vmax = np.maximum(0.25, (c.base_speed + (c.stressed_speed - c.base_speed) * self.load) * (1 - 0.6 * self.fatigue))
        # Helbing driving term: relax velocity toward desired (vmax along the goal direction). This makes
        # free-flow speed approach vmax and supplies the damping, so no separate damping term is needed.
        g = self.target - self.pos
        gn = np.linalg.norm(g, axis=1, keepdims=True)
        ehat = np.where(gn > 1e-6, g / np.maximum(gn, 1e-6), 0.0)
        drive = (vmax[:, None] * ehat - self.vel) / c.tau
        F_phys = drive + interactions
        # affect-gated arbitration
        lam = _sigmoid(c.physics_bias + c.k_lambda_affect * self.load + c.k_lambda_field * fieldp)
        u_rl = self.u_rl(self) if self.u_rl is not None else 0.0
        accel = lam[:, None] * F_phys + (1.0 - lam[:, None]) * u_rl
        an = np.linalg.norm(accel, axis=1, keepdims=True)
        accel = np.where(an > c.max_accel, accel * c.max_accel / np.maximum(an, 1e-9), accel)
        self.vel += accel * dt
        sp = np.linalg.norm(self.vel, axis=1)
        self.vel = np.where(sp[:, None] > vmax[:, None], self.vel * (vmax / np.maximum(sp, 1e-9))[:, None], self.vel)
        # fatigue
        self.fatigue = np.clip(self.fatigue + 0.10 * (an[:, 0] / c.max_accel) ** 2 * dt
                               - 0.18 * (1 - self.load) * dt, 0, 1)
        # move + boundary
        self.pos += self.vel * dt
        self._boundary()
        if c.hard_contact:
            self._resolve_overlaps()
        # deposit affect into the field, then evolve the field
        self.field.deposit(self.pos, c.field_deposit_gain * self.load * dt)
        self.field.step(dt)
        self._lambda = lam

    def _boundary(self):
        c = self.cfg
        hx, hz = c.width / 2.0, c.height / 2.0
        if c.boundary == "torus":
            self.pos[:, 0] = (self.pos[:, 0] + hx) % c.width - hx
            self.pos[:, 1] = (self.pos[:, 1] + hz) % c.height - hz
        else:
            m = c.contact_radius
            np.clip(self.pos[:, 0], -hx + m, hx - m, out=self.pos[:, 0])
            np.clip(self.pos[:, 1], -hz + m, hz - m, out=self.pos[:, 1])

    def _resolve_overlaps(self):
        minD = 2 * self.cfg.contact_radius
        d = self.pos[:, None, :] - self.pos[None, :, :]
        dist = np.linalg.norm(d, axis=2)
        np.fill_diagonal(dist, np.inf)
        overlap = (dist < minD)
        if not overlap.any():
            return
        safe = np.where(overlap, dist, 1.0)                 # avoid inf*0 -> nan on non-overlap entries
        unit = d / safe[:, :, None]
        push = np.where(overlap[:, :, None], unit * ((minD - safe) * 0.25)[:, :, None], 0.0)
        self.pos += push.sum(axis=1)
        self._boundary()

    def run(self, steps):
        for _ in range(steps):
            self.step()

    @property
    def lambda_(self):
        return getattr(self, "_lambda", np.full(self.n, self.cfg.default_lambda if hasattr(self.cfg, "default_lambda") else 0.0))
