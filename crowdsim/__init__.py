"""crowdsim2d — a compact 2D agent-based crowd simulator with a stigmergic affect field.

Pure-Python/numpy reimplementation of the Unity ML-Agents crowd-affect model, so every experiment
runs in seconds with no engine round-trips. Two contributions are reproduced:
  - a stigmergic AFFECT FIELD: collective emotion as an autonomous reaction-diffusion scalar field
    (deposited by agents, diffusing + decaying in the environment), not pairwise contagion;
  - AFFECT-GATED ARBITRATION: each agent blends a Social-Force controller with a (pluggable) corrective
    term through a scalar gate lambda conditioned on its affective state (dual-process).
"""
from .model import Config, AffectField, Simulation
from .navigation import NavField
from .evaluate import evaluate_layout
from .recommend import recommend
from . import metrics, scenarios

__all__ = ["Config", "AffectField", "Simulation", "NavField", "evaluate_layout", "recommend",
           "metrics", "scenarios"]
