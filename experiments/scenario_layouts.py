"""Draw every scenario in the library as a schematic grid (auto-updates as scenarios are added)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
from crowdsim.scenarios import SCENARIOS

FIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")
os.makedirs(FIG, exist_ok=True)
WALL = "#5A5A5A"; SPAWN = "#2E6FB7"; EXIT = "#2BA84A"; FLOW = "#E8985E"


def draw(ax, s):
    hw, hd = s.width / 2, s.height / 2
    ax.add_patch(Rectangle((-hw, -hd), s.width, s.height, facecolor="#F4F4F2", edgecolor="#BBBBBB", zorder=0))
    for (cx, cz, sx, sz) in s.walls:
        ax.add_patch(Rectangle((cx - sx / 2, cz - sz / 2), sx, sz, facecolor=WALL, edgecolor="none", zorder=3))
    for (x0, x1, z0, z1) in s.spawns:
        ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, facecolor=SPAWN, alpha=0.30,
                               edgecolor=SPAWN, lw=1.0, zorder=2))
    for (x, z) in s.exits:
        ax.scatter([x], [z], s=70, marker="*", color=EXIT, edgecolor="white", lw=0.5, zorder=5)
    for (x, z, dx, dz) in s.arrows:
        ax.add_patch(FancyArrow(x, z, dx, dz, width=0.25, head_width=1.1, head_length=1.1,
                                length_includes_head=True, color=FLOW, alpha=0.9, zorder=4))
    m = max(hw, hd) + 1
    ax.set_xlim(-m, m); ax.set_ylim(-m, m)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{s.name}\n{s.note}", fontsize=9)


def main():
    items = list(SCENARIOS.values())
    ncol = 4
    nrow = math.ceil((len(items) + 1) / ncol)      # +1 cell for the legend
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.3 * ncol, 3.3 * nrow))
    axes = axes.ravel()
    for ax, s in zip(axes, items):
        draw(ax, s)
    # legend in the next free cell
    lg = axes[len(items)]; lg.axis("off")
    handles = [
        Rectangle((0, 0), 1, 1, facecolor=WALL, label="wall (obstacle)"),
        Rectangle((0, 0), 1, 1, facecolor=SPAWN, alpha=0.3, edgecolor=SPAWN, label="spawn zone"),
        plt.Line2D([0], [0], marker="*", color="w", markerfacecolor=EXIT, markersize=12, label="exit / door"),
        FancyArrow(0, 0, 1, 0, width=0.2, color=FLOW, label="intended flow"),
    ]
    lg.legend(handles=handles, loc="center", fontsize=11, frameon=False, title="legend")
    for ax in axes[len(items) + 1:]:
        ax.axis("off")
    fig.suptitle(f"crowdsim2d test scenarios ({len(items)} RiMEA-style pedestrian benchmarks)", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = os.path.join(FIG, "scenario_layouts.png")
    fig.savefig(out, dpi=140)
    print(f"{len(items)} scenarios -> {out}")


if __name__ == "__main__":
    main()
