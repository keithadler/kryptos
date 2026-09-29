"""Planted Quagmire ciphertext from real English (Carter vol 1), cribs overwritten in place.
usage: plant_sa.py MODE PERIOD SEED  -> prints ciphertext on line 1, plaintext on line 2"""
import os as _os, sys as _sys
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _ROOT); _os.chdir(_ROOT)   # run from anywhere; paths are repo-relative
import random, sys, pathlib
from runkey import load
from kryptos import AZ, KA, CRIBS
mode, per, seed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
rnd = random.Random(seed)
t = load(pathlib.Path("data/running_keys/carter_vol1.txt"))
o = rnd.randrange(20000, len(t) - 200)
pt = [AZ[c] for c in t[o:o + 97]]
for p, ch in CRIBS.items(): pt[p] = ch
def perm():
    l = list(AZ); rnd.shuffle(l); return "".join(l)
X = perm() if mode in (1, 3, 4) else AZ
Y = {1: KA, 2: perm(), 3: X, 4: perm()}[mode]
key = [rnd.randrange(26) for _ in range(per)]
print("".join(Y[(X.index(p) + key[i % per]) % 26] for i, p in enumerate(pt)))
print("".join(pt))
