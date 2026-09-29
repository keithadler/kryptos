"""Resolve random-ciphertext timeouts for QIV under a guess: how often does random text satisfy it?
usage: KRYPTOS_GUESS=61:THE python3 calib_guess.py PERIOD [N] [LIMIT]"""
import random, sys
import quag34
from kryptos import AZ, GUESS
assert GUESS
per = int(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 3_000_000
real = quag34.K4
rnd = random.Random(7000 + per)
res = []
for i in range(n):
    quag34.K4 = "".join(rnd.choice(AZ) for _ in range(97))
    r = quag34.solve("IV", per, "vig", limit=limit)[0]
    res.append(r)
    print(f"random {i}: {r}", flush=True)
quag34.K4 = real
print(f"QIV period {per} under guess: random SAT {res.count(True)}/{n}, UNSAT {res.count(False)}, timeout {res.count(None)}")
print("K4:", quag34.solve("IV", per, "vig", limit=limit)[0])
