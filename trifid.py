"""Trifid (3x3x3 cube, 27 symbols: 26 letters + '+') against the cribs, any cube, any period.

Encryption per group of g letters (period p, groups start at `off` mod p; the last is short):
write each plaintext letter's (layer,row,col) as a column, read the 3 rows in sequence, and cut
that 3g-trit stream into triples -> cipher letters. So trit t of cipher letter j in a group is
coordinate m // g of plaintext letter m % g, with m = 3j + t.
Each trit is a separate equality: coord t of C = coord (m//g) of P[m%g] whenever that P is a crib.

We merge equal trit variables (letter, coord), then backtrack over values 0..2 per class,
requiring all 27 cells distinct (26 letters distinct triples) and at most 9 letters per value per
coordinate. UNSAT means no cube works: period/offset eliminated. Calibrated against random
ciphertexts, since a SAT result with few equalities means nothing.
"""
import random
import sys
from kryptos import K4, CRIBS

AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def equalities(ct, per, off):
    eqs = []
    n = len(ct)
    starts = list(range(off - per if off else 0, n, per))
    for g0 in starts:
        g0c, g1 = max(g0, 0), min(g0 + per, n)
        g = g1 - g0c
        if g <= 0:
            continue
        for j in range(g):
            i = g0c + j
            for t in range(3):
                m = 3 * j + t
                src = g0c + m % g
                if src in CRIBS:
                    eqs.append(((ct[i], t), (CRIBS[src], m // g)))
    return eqs


def solve(eqs, limit=200000):
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in eqs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    letters = sorted({v[0] for e in eqs for v in e})
    # classes and which (letter, coord) belong to each
    cls = {}
    for L in letters:
        for t in range(3):
            cls.setdefault(find((L, t)), []).append((L, t))
    # a class spanning two coordinates of the same letter is fine; one spanning coord t of two
    # letters forces those letters equal on t. Identical triples -> UNSAT immediately.
    trip = {L: tuple(find((L, t)) for t in range(3)) for L in letters}
    if len(set(trip.values())) < len(trip):
        return False, len(eqs)
    order = sorted(cls, key=lambda c: -len(cls[c]))
    val = {}
    steps = [0]

    def consistent():
        seen = {}
        for L in letters:
            tv = tuple(val.get(trip[L][t]) for t in range(3))
            if None not in tv:
                if tv in seen:
                    return False
                seen[tv] = L
        for t in range(3):
            cnt = [0, 0, 0]
            for c, v in val.items():
                cnt[v] += sum(1 for (L, tt) in cls[c] if tt == t)
            if max(cnt) > 9:
                return False
        return True

    touched = [0, 0, 0]   # how many assigned classes touch each coordinate

    def bt(k):
        steps[0] += 1
        if steps[0] > limit:
            raise TimeoutError
        if k == len(order):
            return True
        c = order[k]
        coords = {t for (_, t) in cls[c]}
        # symmetry: values within one coordinate are interchangeable, so the first class touching
        # an untouched coordinate (and only that coordinate) may be fixed to 0
        choices = [0] if len(coords) == 1 and touched[next(iter(coords))] == 0 else [0, 1, 2]
        for t in coords:
            touched[t] += 1
        for v in choices:
            val[c] = v
            if consistent() and bt(k + 1):
                return True
            del val[c]
        for t in coords:
            touched[t] -= 1
        return False

    try:
        return bt(0), len(eqs)
    except TimeoutError:
        return None, len(eqs)


def encrypt(pt, per, cube):
    """cube: symbol -> (l, r, c). Groups from position 0."""
    inv = {v: k for k, v in cube.items()}
    out = []
    for g0 in range(0, len(pt), per):
        grp = pt[g0:g0 + per]
        stream = [cube[ch][t] for t in range(3) for ch in grp]
        out += [inv[tuple(stream[3 * j:3 * j + 3])] for j in range(len(grp))]
    return "".join(out)


def selftest():
    rnd = random.Random(8)
    cells = [(a, b, c) for a in range(3) for b in range(3) for c in range(3)]
    rnd.shuffle(cells)
    cube = dict(zip(AZ + "+", cells))
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    ct = encrypt("".join(pt), 7, cube)
    sat, n = solve(equalities(ct, 7, 0))
    print(f"selftest: planted Trifid period 7 -> {sat} with {n} equalities")


def main():
    selftest()
    rnd = random.Random(1)
    randoms = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(20)]
    print(f"{'per':>3} {'off':>3} {'eqs':>4}  K4    random-ciphertext SAT rate")
    for per in range(2, 25):
        for off in range(per):
            sat, n = solve(equalities(K4, per, off))
            rs = [solve(equalities(r, per, off))[0] for r in randoms]
            rate = f"{sum(1 for s in rs if s)}/{sum(1 for s in rs if s is not None)}"
            k4 = {True: "SAT", False: "UNSAT", None: "?"}[sat]
            if sat is not False or per <= 3:
                print(f"{per:3} {off:3} {n:4}  {k4:5} {rate}")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
