"""Decrypt a columnar-transposition x periodic-KA-Vigenere survivor (as printed by bin/dfs), filling
only positions whose key residue the clues determine ('?' elsewhere). Used to read the width-14
survivors: English between the clue words would be a lead; gibberish means chance.
usage: python3 checks/decode_columnar.py < results/08_columnar_every_order_w12-14.txt"""
import os as _os, sys as _sys
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _ROOT); _os.chdir(_ROOT)
import re
from kryptos import K4, CRIBS, KA
ka = {c: i for i, c in enumerate(KA)}
N = 97
for line in _sys.stdin:
    m = re.match(r"SURVIVOR w=(\d+) dir=0 fam=vig-PKA-CKA order=([AB]) per=(\d+) checks=\d+ ord=([\d,]+)", line)
    if not m:
        continue
    W, orderB, PER, ordr = int(m[1]), m[2] == "B", int(m[3]), list(map(int, m[4].split(",")))
    rows, s, t = -(-N // W), [0] * N, 0
    for col in ordr:
        for r in range(rows if (N % W == 0 or col < N % W) else rows - 1):
            s[r * W + col] = t; t += 1
    key = {}
    for i, p in CRIBS.items():
        j = s[i]; idx = j if orderB else i
        key.setdefault(idx % PER, (ka[K4[j]] - ka[p]) % 26)
    pt = ["?"] * N
    for i in range(N):
        j = s[i]; idx = j if orderB else i
        if idx % PER in key:
            pt[i] = KA[(ka[K4[j]] - key[idx % PER]) % 26]
    print(f"w={W} order={m[2]} period={PER} ord={m[4]}  key residues known {len(key)}/{PER}")
    print("   " + "".join(pt))
