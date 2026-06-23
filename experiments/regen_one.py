# -*- coding: utf-8 -*-
"""Run one experiment with the bilingual savefig patch installed -> writes EN + _tr.png figures.
Usage: python experiments/regen_one.py <experiment_module_name>"""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from experiments import _figlang
_figlang.install()
mod = importlib.import_module("experiments." + sys.argv[1])
mod.main()
