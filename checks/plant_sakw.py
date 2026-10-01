"""Planted keyword-alphabet Quagmire from real English (K2/K3 plaintext), clue words in place.
usage: plant_sakw.py MODE PERIOD SEED [MAXKW] [beau]  -> ciphertext on line 1, plaintext on line 2, keywords on line 3
The keywords are random letter strings (4 to MAXKW different letters), not dictionary words."""
import os as _os, sys as _sys
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _ROOT)
import random
from kryptos import AZ, CRIBS, K2_PT, K3_PT
from attacks import keyed
mode, per, seed = int(_sys.argv[1]), int(_sys.argv[2]), int(_sys.argv[3])
maxkw = int(_sys.argv[4]) if len(_sys.argv) > 4 else 9
rnd = random.Random(seed * 1000 + per)
text = K2_PT + K3_PT
o = rnd.randrange(len(text) - 97)
pt = list(text[o:o + 97])
for p, ch in CRIBS.items():
    pt[p] = ch
kw = ["".join(rnd.sample(AZ, rnd.randint(4, maxkw))) for _ in range(2)]
X = keyed(kw[0])
Y = X if mode == 3 else keyed(kw[1])
key = [rnd.randrange(26) for _ in range(per)]
beau = "beau" in _sys.argv
print("".join(Y[((key[i % per] - X.index(p)) if beau else (X.index(p) + key[i % per])) % 26] for i, p in enumerate(pt)))
print("".join(pt))
print(kw[0], kw[0] if mode == 3 else kw[1])
