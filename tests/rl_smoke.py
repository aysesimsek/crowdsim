import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from crowdsim.rl import CrowdEnv, train, policy_controller

e = CrowdEnv(n=12, seed=0)
o = e.obs()
print("obs", o.shape, o.dtype)
assert o.shape == (12, 11)
no, r, d = e.step(np.zeros((12, 3), np.float32))
print("step ok, reward shape", r.shape, "mean %.3f" % r.mean())
net, curve = train(iters=3, T=48, n=12, log=lambda *a: None)
print("train ok, curve", ["%.3f" % x for x in curve])
ctrl = policy_controller(net)
f, lr = ctrl(e)
print("controller ok, force", f.shape, "lambda_raw", lr.shape)
print("SMOKE PASS")
