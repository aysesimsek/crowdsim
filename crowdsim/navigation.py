"""Navigation (flow) field: Dijkstra distance-to-nearest-exit over free space, giving each cell a
direction toward the nearest reachable exit AROUND walls. This replaces straight-line goal seeking, so
agents route through doors / around corners (the global planning the Social-Force layer lacks).
"""
import heapq
import numpy as np


class NavField:
    def __init__(self, cfg, walls, exits, nav_cell=0.4, inflate=0.35):
        self.W, self.H = cfg.width, cfg.height
        self.minx, self.minz = -cfg.width / 2.0, -cfg.height / 2.0
        self.h = nav_cell
        self.nx = max(2, int(round(cfg.width / nav_cell)))
        self.nz = max(2, int(round(cfg.height / nav_cell)))
        xs = self.minx + (np.arange(self.nx) + 0.5) * self.h
        zs = self.minz + (np.arange(self.nz) + 0.5) * self.h
        self.gx, self.gz = np.meshgrid(xs, zs, indexing="ij")
        # blocked cells: centre inside any wall rect inflated by the agent radius
        self.blocked = np.zeros((self.nx, self.nz), bool)
        for (cx, cz, sx, sz) in walls:
            hx, hz = sx / 2 + inflate, sz / 2 + inflate
            self.blocked |= (np.abs(self.gx - cx) <= hx) & (np.abs(self.gz - cz) <= hz)
        self.dist = np.full((self.nx, self.nz), np.inf)
        self._dijkstra(exits)
        self._direction()

    def _cell(self, x, z):
        ix = int(np.clip((x - self.minx) / self.h, 0, self.nx - 1))
        iz = int(np.clip((z - self.minz) / self.h, 0, self.nz - 1))
        return ix, iz

    def _dijkstra(self, exits):
        pq = []
        for (ex, ez) in exits:
            ix, iz = self._cell(ex, ez)
            # nudge an exit that fell on a blocked cell to the nearest free neighbour
            if self.blocked[ix, iz]:
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        jx, jz = np.clip(ix + dx, 0, self.nx - 1), np.clip(iz + dz, 0, self.nz - 1)
                        if not self.blocked[jx, jz]:
                            ix, iz = jx, jz; break
            if self.dist[ix, iz] > 0:
                self.dist[ix, iz] = 0.0
                heapq.heappush(pq, (0.0, ix, iz))
        nbr = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
               (-1, -1, 1.41421356), (-1, 1, 1.41421356), (1, -1, 1.41421356), (1, 1, 1.41421356)]
        while pq:
            d, ix, iz = heapq.heappop(pq)
            if d > self.dist[ix, iz]:
                continue
            for dx, dz, w in nbr:
                jx, jz = ix + dx, iz + dz
                if 0 <= jx < self.nx and 0 <= jz < self.nz and not self.blocked[jx, jz]:
                    nd = d + w * self.h
                    if nd < self.dist[jx, jz]:
                        self.dist[jx, jz] = nd
                        heapq.heappush(pq, (nd, jx, jz))

    def _direction(self):
        # each free cell points toward the 8-neighbour with the smallest distance-to-exit
        self.dir = np.zeros((self.nx, self.nz, 2))
        big = np.where(np.isinf(self.dist), 1e12, self.dist)
        for ix in range(self.nx):
            for iz in range(self.nz):
                if self.blocked[ix, iz] or np.isinf(self.dist[ix, iz]):
                    continue
                best, bv = None, big[ix, iz]
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx == 0 and dz == 0:
                            continue
                        jx, jz = ix + dx, iz + dz
                        if 0 <= jx < self.nx and 0 <= jz < self.nz and big[jx, jz] < bv:
                            bv = big[jx, jz]; best = (dx, dz)
                if best is not None:
                    v = np.array([best[0], best[1]], float)
                    self.dir[ix, iz] = v / np.linalg.norm(v)

    def direction_at(self, pos):
        ix = np.clip(((pos[:, 0] - self.minx) / self.h).astype(int), 0, self.nx - 1)
        iz = np.clip(((pos[:, 1] - self.minz) / self.h).astype(int), 0, self.nz - 1)
        return self.dir[ix, iz]

    def dist_at(self, pos):
        ix = np.clip(((pos[:, 0] - self.minx) / self.h).astype(int), 0, self.nx - 1)
        iz = np.clip(((pos[:, 1] - self.minz) / self.h).astype(int), 0, self.nz - 1)
        d = self.dist[ix, iz]
        return np.where(np.isinf(d), 1e9, d)
