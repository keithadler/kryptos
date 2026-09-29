"""Periodic key with an ARBITRARY unknown alphabet on one side (all 26! of them), solved exactly.

Quagmire I  (plaintext alphabet x unknown, ciphertext alphabet y in {AZ, KA}):
    vig:  k = y(C) - x(P)  => for cribs i, j on the same key residue:  x(P_i) - x(P_j) = y(C_i) - y(C_j)
    beau: k = y(C) + x(P)  =>                                           x(P_i) - x(P_j) = y(C_j) - y(C_i)
Quagmire II (ciphertext alphabet y unknown, x in {AZ, KA}): same with the roles swapped.

This is "mask the plaintext with any simple substitution, then a periodic tableau cipher" (QI) and
"periodic tableau cipher, then any simple substitution of the output" (QII).

Each equation is a difference constraint mod 26 between two letters. Weighted union-find merges
them; a contradiction is a cycle with a nonzero sum or two different letters pinned to the same
value. Surviving systems are then checked for an injective assignment across components.
We report the number of cycle-closing (genuinely constraining) equations for every survivor.
"""
import itertools
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA

KNOWN = {"AZ": {c: i for i, c in enumerate(AZ)}, "KA": {c: i for i, c in enumerate(KA)}}


class DUF:
    """Union-find with offsets: val[a] = val[root] + off[a] (mod 26)."""

    def __init__(self):
        self.p, self.o = {}, {}

    def find(self, a):
        if a not in self.p:
            self.p[a], self.o[a] = a, 0
        if self.p[a] == a:
            return a, 0
        r, off = self.find(self.p[a])
        self.p[a], self.o[a] = r, (self.o[a] + off) % 26
        return r, self.o[a]

    def union(self, a, b, d):
        """Impose val[a] - val[b] = d. Returns 'merge', 'cycle-ok' or 'conflict'."""
        ra, oa = self.find(a)
        rb, ob = self.find(b)
        if ra == rb:
            return "cycle-ok" if (oa - ob) % 26 == d % 26 else "conflict"
        # val[a] = val[ra] + oa, val[b] = val[rb] + ob;  val[ra] = val[rb] + ob + d - oa
        self.p[ra], self.o[ra] = rb, (ob + d - oa) % 26
        return "merge"


def injective(duf, letters):
    comps = {}
    for L in letters:
        r, o = duf.find(L)
        comps.setdefault(r, []).append(o)
    for offs in comps.values():
        if len(set(offs)) < len(offs):
            return False
    # place components with independent shifts so all values are distinct (backtracking)
    groups = sorted(comps.values(), key=len, reverse=True)
    used = set()

    def place(k):
        if k == len(groups):
            return True
        for s in range(26):
            vals = {(o + s) % 26 for o in groups[k]}
            if not vals & used:
                used.update(vals)
                if place(k + 1):
                    return True
                used.difference_update(vals)
        return False

    return place(0)


def run(unknown_side, kind, known_alpha, per):
    ka = KNOWN[known_alpha]
    duf = DUF()
    first = {}
    cycles = 0
    for p in CRIB_POS:
        r = p % per
        if r not in first:
            first[r] = p
            continue
        q = first[r]
        Pp, Pq, Cp, Cq = CRIBS[p], CRIBS[q], K4[p], K4[q]
        if unknown_side == "plain":      # x unknown, y known
            d = (ka[Cp] - ka[Cq]) if kind == "vig" else (ka[Cq] - ka[Cp])
            a, b = Pp, Pq
        else:                            # y unknown, x known
            d = (ka[Pp] - ka[Pq]) if kind == "vig" else (ka[Pq] - ka[Pp])
            a, b = Cp, Cq
        if a == b:
            if d % 26:
                return False, cycles
            cycles += 1
            continue
        res = duf.union(a, b, d)
        if res == "conflict":
            return False, cycles
        if res == "cycle-ok":
            cycles += 1
    letters = {CRIBS[p] for p in CRIB_POS} if unknown_side == "plain" else {K4[p] for p in CRIB_POS}
    return injective(duf, letters), cycles


def main():
    print("Quagmire I/II with any alphabet on the unknown side, periodic key, periods 1-26")
    for side, kind, ka in itertools.product(("plain", "cipher"), ("vig", "beau"), ("AZ", "KA")):
        surv = []
        for per in range(1, 27):
            ok, cyc = run(side, kind, ka, per)
            if ok:
                surv.append((per, cyc))
        label = f"{'QI  plaintext' if side == 'plain' else 'QII ciphertext'} alphabet unknown, {kind}, other side {ka}"
        print(f"  {label:58} survivors (period, cycle constraints): {surv or 'none'}")


if __name__ == "__main__":
    main()
