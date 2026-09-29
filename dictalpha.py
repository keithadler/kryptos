"""Periodic key (1..26) with a dictionary word as the keyed alphabet, vectorized.

Arrangements (x = plaintext alphabet, y = ciphertext alphabet, W = keyed(word)):
  Q1 x=W  y=AZ     Q2 x=AZ y=W     Q3 x=W y=W     KA-W x=KA y=W     W-KA x=W y=KA
each as Vigenere (y(C) = x(P) + k) and Beaufort (y(C) = k - x(P)).
"""
import re
import sys
import numpy as np
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA
from attacks import keyed

PL = np.array([ord(CRIBS[p]) - 65 for p in CRIB_POS])
CL = np.array([ord(K4[p]) - 65 for p in CRIB_POS])


def alphabet_index(alpha):
    """letter -> position in alpha"""
    out = np.empty(26, dtype=np.int16)
    for i, c in enumerate(alpha):
        out[ord(c) - 65] = i
    return out


def period_pairs():
    """For each period, (first, other) crib-index pairs within each residue class."""
    res = {}
    for per in range(1, 27):
        first, a, b = {}, [], []
        for j, p in enumerate(CRIB_POS):
            r = p % per
            if r in first:
                a.append(first[r]); b.append(j)
            else:
                first[r] = j
        res[per] = (np.array(a), np.array(b))
    return res


def main(words):
    alphas = sorted({keyed(w) for w in words})
    W = np.stack([alphabet_index(a) for a in alphas])          # (n, 26)
    AZi, KAi = alphabet_index(AZ), alphabet_index(KA)
    n = len(alphas)
    fixed = {"AZ": np.broadcast_to(AZi, W.shape), "KA": np.broadcast_to(KAi, W.shape)}
    arr = {"Q1": (W, fixed["AZ"]), "Q2": (fixed["AZ"], W), "Q3": (W, W),
           "KA-W": (fixed["KA"], W), "W-KA": (W, fixed["KA"])}
    pairs = period_pairs()
    total = 0
    print(f"{n} distinct keyed alphabets from {len(words)} words")
    for name, (X, Y) in arr.items():
        xv, yv = X[:, PL].astype(np.int16), Y[:, CL].astype(np.int16)
        for kind, v in (("vig", (yv - xv) % 26), ("beau", (yv + xv) % 26)):
            for per, (a, b) in pairs.items():
                if len(a) == 0:
                    continue
                ok = np.all(v[:, a] == v[:, b], axis=1)
                total += n
                for i in np.nonzero(ok)[0]:
                    print(f"SURVIVOR {name} {kind} period {per} checks {len(a)} alphabet {alphas[i]}")
    print(f"tested {total} (alphabet x arrangement x kind x period) combos")


if __name__ == "__main__":
    words = set()
    for f in ("/usr/share/dict/words", "/usr/share/dict/propernames"):
        for line in open(f):
            w = line.strip().upper()
            if re.fullmatch(r"[A-Z]+", w):
                words.add(w)
    words.update(sys.argv[1:])
    main(sorted(words))
