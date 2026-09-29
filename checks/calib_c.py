"""Random-ciphertext calibration with the C solver (quag3), parallel, per-instance time limit.
usage: python3 calib_c.py KIND PERIOD N SECONDS [KGUESS]"""
import os as _os, sys as _sys
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _ROOT); _os.chdir(_ROOT)   # run from anywhere; paths are repo-relative
import random, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
kind, per, n, secs = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
env = dict(os.environ)
if len(sys.argv) > 5: env["KGUESS"] = sys.argv[5]
rnd = random.Random(9100 + int(per))
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
cts = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(n)]
if os.environ.get("REPEAT"):   # control: copy K4's one repeat (same letter at 1-based 28 and 66, both plaintext R)
    cts = [c[:65] + c[27] + c[66:] for c in cts]
def one(ct):
    try:
        out = subprocess.run(["bin/quag3", kind, per, ct], capture_output=True, text=True, timeout=secs, env=env).stdout
        return "SAT" if " SAT" in out else "UNSAT"
    except subprocess.TimeoutExpired:
        return "timeout"
with ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, cts))
k4 = subprocess.run(["bin/quag3", kind, per], capture_output=True, text=True, env=env).stdout.strip()
print(f"{'[R->P repeat planted] ' if os.environ.get('REPEAT') else ''}{kind} period {per} guess={env.get('KGUESS','-')}: random SAT {res.count('SAT')}/{n}, UNSAT {res.count('UNSAT')}, timeout {res.count('timeout')}  |  K4: {k4}")
