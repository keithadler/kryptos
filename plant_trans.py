"""Build a planted ciphertext (columnar w=7 + KA Vigenere period 7, order A) for trans.c's self-test."""
import random
from kryptos import AZ, KA, CRIBS
rnd = random.Random(3)
pt = [rnd.choice(AZ) for _ in range(97)]
for p, ch in CRIBS.items(): pt[p] = ch
w, ordr = 7, [3, 0, 6, 1, 5, 2, 4]
rows = -(-97 // w); sigma = [0]*97; t = 0
for col in ordr:
    nrow = rows if col < 97 % w else rows - 1
    for r in range(nrow):
        sigma[r*w+col] = t; t += 1
kai = {c: i for i, c in enumerate(KA)}
key = [kai[c] for c in "PALIMPS"]
inter = [KA[(kai[p] + key[i % 7]) % 26] for i, p in enumerate(pt)]   # order A: substitute at plaintext index
ct = [None]*97
for i in range(97): ct[sigma[i]] = inter[i]
print("".join(ct))
