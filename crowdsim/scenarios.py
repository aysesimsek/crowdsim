"""A data-driven library of crowd test scenarios (RiMEA-style + real-life pedestrian benchmarks).

Each Scenario is pure geometry: arena size, axis-aligned wall rectangles, spawn rectangles, exit
points, and intended-flow arrows. Adding a scenario is one dict entry; the layout figure
(experiments/scenario_layouts.py) and any runner draw from this same library, so visuals stay in sync.
"""
from dataclasses import dataclass, field


@dataclass
class Scenario:
    name: str
    note: str
    width: float
    height: float
    walls: list = field(default_factory=list)     # (cx, cz, sx, sz) axis-aligned rectangles
    spawns: list = field(default_factory=list)     # (x0, x1, z0, z1) spawn rectangles
    exits: list = field(default_factory=list)      # (x, z) exit / door points
    arrows: list = field(default_factory=list)     # (x, z, dx, dz) intended flow


def vwall(x, zmin, zmax, gaps=(), gap_half=0.7, t=0.5):
    """Vertical wall at x over [zmin,zmax] with door gaps centred at `gaps` -> list of rects."""
    segs, cur = [], zmin
    for g in sorted(gaps):
        lo = g - gap_half
        if lo > cur:
            segs.append((x, (cur + lo) / 2.0, t, lo - cur))
        cur = g + gap_half
    if zmax > cur:
        segs.append((x, (cur + zmax) / 2.0, t, zmax - cur))
    return segs


def hwall(z, xmin, xmax, gaps=(), gap_half=0.7, t=0.5):
    """Horizontal wall at z over [xmin,xmax] with door gaps centred at `gaps` -> list of rects."""
    segs, cur = [], xmin
    for g in sorted(gaps):
        lo = g - gap_half
        if lo > cur:
            segs.append(((cur + lo) / 2.0, z, lo - cur, t))
        cur = g + gap_half
    if xmax > cur:
        segs.append(((cur + xmax) / 2.0, z, xmax - cur, t))
    return segs


def block(cx, cz, sx, sz):
    return (cx, cz, sx, sz)


def _build():
    S = {}

    S["OpenSquare"] = Scenario("OpenSquare", "open crossing (control)", 24, 24,
        spawns=[(-11, -9, -10, 10)], exits=[(11, 0)], arrows=[(-7, 0, 12, 0)])

    S["Corridor"] = Scenario("Corridor", "straight corridor", 24, 8,
        walls=[(0, 4, 24, 0.5), (0, -4, 24, 0.5)],
        spawns=[(-11, -7, -3, 3)], exits=[(11.5, 0)], arrows=[(-8, 0, 7, 0)])

    S["Bottleneck"] = Scenario("Bottleneck", "single 1.4 m door", 20, 16,
        walls=vwall(0, -8, 8, gaps=[0]), spawns=[(-9, -2, -7, 7)],
        exits=[(0, 0), (8, 0)], arrows=[(-5, 0, 6, 0)])

    S["WideDoor"] = Scenario("WideDoor", "single 3 m door", 20, 16,
        walls=vwall(0, -8, 8, gaps=[0], gap_half=1.5), spawns=[(-9, -2, -7, 7)],
        exits=[(0, 0), (8, 0)], arrows=[(-5, 0, 6, 0)])

    S["PillarBeforeDoor"] = Scenario("PillarBeforeDoor", "obstacle before exit (flow aid)", 20, 16,
        walls=vwall(0, -8, 8, gaps=[0]) + [block(-1.6, 0, 0.9, 0.9)],
        spawns=[(-9, -3, -7, 7)], exits=[(0, 0), (8, 0)], arrows=[(-5, 0, 6, 0)])

    S["MultiExit"] = Scenario("MultiExit", "two doors, nearest routing", 20, 16,
        walls=vwall(0, -8, 8, gaps=[4, -4]),
        spawns=[(-9, -2, 0.5, 7), (-9, -2, -7, -0.5)],
        exits=[(0, 4), (0, -4), (8, 4), (8, -4)], arrows=[(-5, 3, 5, 1), (-5, -3, 5, -1)])

    S["ThreeExit"] = Scenario("ThreeExit", "three doors", 24, 24,
        walls=vwall(0, -12, 12, gaps=[7, 0, -7]),
        spawns=[(-10, -3, 1, 11)], exits=[(0, 7), (0, 0), (0, -7)],
        arrows=[(-6, 4, 5, 0)])

    S["NearFar"] = Scenario("NearFar", "near + far exit (biased crowd)", 24, 20,
        walls=vwall(8, -10, 10, gaps=[3, -7]),
        spawns=[(-9, -3, 0, 8)], exits=[(8, 3), (8, -7)],
        arrows=[(-6, 4, 5, 1), (-6, 4, 5, -8)])

    S["DoubleBottleneck"] = Scenario("DoubleBottleneck", "two doors in series (vestibule)", 26, 16,
        walls=vwall(-4, -8, 8, gaps=[0]) + vwall(4, -8, 8, gaps=[0]),
        spawns=[(-12, -6, -7, 7)], exits=[(-4, 0), (4, 0), (12, 0)], arrows=[(-9, 0, 5, 0)])

    S["CounterFlow"] = Scenario("CounterFlow", "two opposing streams", 24, 6,
        walls=[(0, 3.25, 24, 0.5), (0, -3.25, 24, 0.5)],
        spawns=[(-11, -4, -2.3, 2.3), (4, 11, -2.3, 2.3)],
        exits=[(11.5, 0), (-11.5, 0)], arrows=[(-7, 1.2, 6, 0), (7, -1.2, -6, 0)])

    S["Corner"] = Scenario("Corner", "90-degree L-turn", 26, 26,
        walls=[(-5.25, -1.5, 13.5, 0.5), (-6.75, 1.5, 10.5, 0.5),
               (1.5, 5.25, 0.5, 13.5), (-1.5, 6.75, 0.5, 10.5)],
        spawns=[(-11, -7, -1.1, 1.1)], exits=[(0, 11)], arrows=[(-8, 0, 7, 0), (0, 2, 0, 7)])

    S["Crossing"] = Scenario("Crossing", "4-way intersection", 26, 26,
        walls=[block(7.25, 7.25, 11.5, 11.5), block(-7.25, 7.25, 11.5, 11.5),
               block(7.25, -7.25, 11.5, 11.5), block(-7.25, -7.25, 11.5, 11.5)],
        spawns=[(-12, -9, -1.1, 1.1), (-1.1, 1.1, -12, -9)],
        exits=[(12, 0), (0, 12)], arrows=[(-9, 0, 7, 0), (0, -9, 0, 7)])

    S["TJunction"] = Scenario("TJunction", "T-junction merge", 26, 18,
        walls=[block(0, 6.5, 26, 0.5)] +                                   # corridor ceiling
               hwall(1.5, -13, 13, gaps=[0], gap_half=1.75) +              # corridor floor w/ stem opening
               [block(-1.75, -5.6, 0.5, 7.7), block(1.75, -5.6, 0.5, 7.7)],  # stem walls
        spawns=[(-1.2, 1.2, -9, -6)], exits=[(12.5, 4), (-12.5, 4)],
        arrows=[(0, -7, 0, 7), (1, 4, 6, 0)])

    S["MergingLanes"] = Scenario("MergingLanes", "two lanes merge into one", 26, 16,
        walls=[(- 3, 0, 17, 0.5),                                          # central divider (left half)
               (0, 5.25, 26, 0.5), (0, -5.25, 26, 0.5)],                   # outer corridor walls
        spawns=[(-12, -8, 1.5, 4.5), (-12, -8, -4.5, -1.5)],
        exits=[(12.5, 0)], arrows=[(-9, 3, 9, -1.5), (-9, -3, 9, 1.5)])

    S["ObstacleField"] = Scenario("ObstacleField", "weave through pillars", 24, 18,
        walls=[block(-3, 3, 1.2, 1.2), block(-3, -3, 1.2, 1.2), block(2, 0, 1.2, 1.2),
               block(2, 6, 1.2, 1.2), block(2, -6, 1.2, 1.2), block(6, 3, 1.2, 1.2),
               block(6, -3, 1.2, 1.2)],
        spawns=[(-11, -9, -8, 8)], exits=[(11, 0)], arrows=[(-8, 0, 16, 0)])

    S["RoomToCorridor"] = Scenario("RoomToCorridor", "room -> door -> corridor", 28, 16,
        walls=vwall(-2, -8, 8, gaps=[0]) + [(7, 1.5, 18, 0.5), (7, -1.5, 18, 0.5)],
        spawns=[(-11, -5, -7, 7)], exits=[(-2, 0), (15.5, 0)], arrows=[(-8, 0, 6, 0), (2, 0, 12, 0)])

    S["TwoRooms"] = Scenario("TwoRooms", "two rooms via a door", 28, 18,
        walls=vwall(0, -9, 9, gaps=[0]),
        spawns=[(-12, -4, -8, 8)], exits=[(0, 0), (12, 0)], arrows=[(-7, 0, 6, 0)])

    S["StageEgress"] = Scenario("StageEgress", "crowd at a stage, side exits", 26, 22,
        walls=[block(0, 9.5, 22, 1.5)] +                                   # stage (top, impassable)
               vwall(-13, -11, 11, gaps=[5]) + vwall(13, -11, 11, gaps=[5]),  # side-wall exits
        spawns=[(-9, 9, -8, 4)], exits=[(-13, 5), (13, 5)],
        arrows=[(-6, 0, -6, 4), (6, 0, 6, 4)])

    S["StadiumFunnel"] = Scenario("StadiumFunnel", "wide stand -> narrow exit", 26, 22,
        walls=[block(-2.5, 6.5, 11, 0.5), block(-2.5, -6.5, 11, 0.5),     # converging upper/lower walls
               (4, 4, 0.5, 5.5), (4, -4, 0.5, 5.5)] + vwall(8, -8, 8, gaps=[0]),
        spawns=[(-11, -9, -9, 9)], exits=[(8, 0)], arrows=[(-8, 0, 15, 0)])

    return S


SCENARIOS = _build()
