"""Random-ciphertext calibration with the C solver (quag3), parallel, per-instance time limit.
usage: python3 calib_c.py KIND PERIOD N SECONDS [KGUESS]"""
import random, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
kind, per, n, secs = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
env = dict(os.environ)
if len(sys.argv) > 5: env["KGUESS"] = sys.argv[5]
rnd = random.Random(9100 + int(per))
AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
cts = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(n)]
def one(ct):
    try:
        out = subprocess.run(["./quag3", kind, per, ct], capture_output=True, text=True, timeout=secs, env=env).stdout
        return "SAT" if " SAT" in out else "UNSAT"
    except subprocess.TimeoutExpired:
        return "timeout"
with ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, cts))
k4 = subprocess.run(["./quag3", kind, per], capture_output=True, text=True, env=env).stdout.strip()
print(f"{kind} period {per} guess={env.get('KGUESS','-')}: random SAT {res.count('SAT')}/{n}, UNSAT {res.count('UNSAT')}, timeout {res.count('timeout')}  |  K4: {k4}")
