"""Hill cipher with an added constant, and with different numberings on the two sides.

attacks.py tests C_block = M * P_block with A=0 (or K=0 in the KRYPTOS alphabet) on both sides.
A hand user is as likely to number A=1..Z=26, and that is a different cipher: it turns the Hill
into C_block = M * P_block + b. This tests every M and every b (so every starting number on either
side), with the plaintext and ciphertext numbered in A-Z or KRYPTOS order independently, in both
directions (C from P, and P from C). Each row of M is solved on its own: 26^(n+1) candidates
against one equation per fully known block.

n=2 has 11-12 known blocks and n=3 has 6-7, far more than the 3 or 4 unknowns per row. n=4 has
at most 5 blocks for 5 unknowns, so it cannot be tested this way.
"""
import itertools
import random
import numpy as np
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ, KA

ALPH = {"AZ": AZ, "KA": KA}


def blocks(ct, n, align, x, y):
    P, C = [], []
    for b in range(align, 97 - n + 1, n):
        if all(b + t in CRIBS for t in range(n)):
            P.append([x[CRIBS[b + t]] for t in range(n)])
            C.append([y[ct[b + t]] for t in range(n)])
    return np.array(P), np.array(C)


def rows_alive(src, dst, n):
    """For each output coordinate, how many (row of M, constant) reproduce every block."""
    cand = np.array(list(itertools.product(range(26), repeat=n + 1)), dtype=np.int32)    # row..., b
    pred = (cand[:, :n] @ src.T + cand[:, n:]) % 26                                       # (26^(n+1), blocks)
    return [int(np.all(pred == dst[:, r], axis=1).sum()) for r in range(n)]


def test(ct):
    """[(n, align, P numbering, C numbering, direction, blocks, candidates alive per row)] for every case."""
    out = []
    for n in (2, 3):
        for align in range(n):
            for xn, yn in itertools.product(ALPH, repeat=2):
                x, y = ({c: i for i, c in enumerate(ALPH[a])} for a in (xn, yn))
                P, C = blocks(ct, n, align, x, y)
                for direction, (s, d) in (("C=MP+b", (P, C)), ("P=MC+b", (C, P))):
                    out.append((n, align, xn, yn, direction, len(P), rows_alive(s, d, n)))
    return out


def main():
    res = test(kryptos.K4)
    alive = [r for r in res if 0 not in r[6]]
    for n in (2, 3):
        sub = [r for r in res if r[0] == n]
        print(f"n={n}: {len(sub)} cases (alignment x numberings x direction), {min(r[5] for r in sub)}-{max(r[5] for r in sub)} "
              f"known blocks each -> {sum(0 in r[6] for r in sub)} eliminated")
    print(f"K4 survivors: {alive or 'none'}")
    rnd = random.Random(2026)
    tot = sum(1 for _ in range(10) for r in test("".join(rnd.choice(AZ) for _ in range(97))) if 0 not in r[6])
    print(f"random ciphertexts x10: {tot} survivors of {10 * len(res)}")
    # plant: 3x3 Hill numbered A=1..Z=26
    pt = [rnd.choice(AZ) for _ in range(99)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    M = np.array([[6, 24, 1], [13, 16, 10], [20, 17, 15]])
    ct = "".join(AZ[(v - 1) % 26] for b in range(0, 99, 3)
                 for v in (M @ np.array([AZ.index(c) + 1 for c in pt[b:b + 3]])) % 26)[:97]
    got = [r[:5] for r in test(ct) if 0 not in r[6]]
    print(f"planted 3x3 Hill with A=1..Z=26: survivors {got}")


if __name__ == "__main__":
    main()
