"""Planted double rotation (w1=24 cw, w2=8 cw, like K3) + KA Beaufort period 10, order B, for trans.c rot mode."""
import random
from kryptos import AZ, KA, CRIBS
N = 97
def rotation(w, ccw):
    rows = -(-N // w); sig = [0]*N; t = 0
    for k in range(w):
        col = w-1-k if ccw else k
        nrow = rows if (col < N % w or N % w == 0) else rows - 1
        for rr in range(nrow):
            r = rr if ccw else nrow-1-rr
            sig[r*w+col] = t; t += 1
    return sig
rnd = random.Random(5)
pt = [rnd.choice(AZ) for _ in range(N)]
for p, ch in CRIBS.items(): pt[p] = ch
s1, s2 = rotation(24, 0), rotation(8, 0)
sig = [s2[s1[i]] for i in range(N)]
inter = [None]*N
for i in range(N): inter[sig[i]] = pt[i]          # transpose first (order B)
kai = {c: i for i, c in enumerate(KA)}
key = [kai[c] for c in "ABSCISSAXY"]
print("".join(KA[(key[j % 10] - kai[inter[j]]) % 26] for j in range(N)))   # Beaufort
