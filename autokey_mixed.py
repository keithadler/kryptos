"""Autokey with ONE unknown alphabet on all three sides (any of 26!).

attacks.py eliminates autokey with the A-Z and KRYPTOS alphabets. Here the alphabet A is free:
  vig      A[C_i] = A[P_i] + A[K_i]
  beau     A[C_i] = A[K_i] - A[P_i]
  varbeau  A[C_i] = A[P_i] - A[K_i]
where K_i is the ciphertext letter (or the plaintext letter) L places back. Each clue letter gives
one linear equation mod 26 over the positions of letters in A, and A must be a permutation.
Ciphertext autokey gives 24 equations at every lag up to 21; plaintext autokey gives 24 - 2L inside
the clue runs. Backtracking with propagation decides each case: SAT, UNSAT, or unresolved.

Satisfiable cases are repeated on random ciphertexts carrying the same clue letters.
"""
import math
import random
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ

INV = {u: pow(u, -1, 26) for u in range(26) if math.gcd(u, 26) == 1}
FORMS = ("vig", "beau", "varbeau")


def solve(eqs, limit=300_000):
    """eqs: dicts letter -> coefficient with sum(coef * A[letter]) = 0 mod 26, A injective.
    True (satisfiable), False (no alphabet fits) or None (node limit reached)."""
    eqs = [{k: v % 26 for k, v in e.items() if v % 26} for e in eqs]
    letters = sorted({l for e in eqs for l in e}, key=lambda l: -sum(l in e for e in eqs))
    by_letter = {l: [e for e in eqs if l in e] for l in letters}
    A, used, nodes = {}, set(), [0]

    def assign(l, v, trail):
        A[l] = v
        used.add(v)
        trail.append(l)
        stack = [l]
        while stack:
            for e in by_letter[stack.pop()]:
                free = [k for k in e if k not in A]
                if not free:
                    if sum(c * A[k] for k, c in e.items()) % 26:
                        return False
                elif len(free) == 1 and e[free[0]] in INV:          # two known: the third is forced
                    w = (-sum(c * A[k] for k, c in e.items() if k in A) * INV[e[free[0]]]) % 26
                    if w in used:
                        return False
                    A[free[0]] = w
                    used.add(w)
                    trail.append(free[0])
                    stack.append(free[0])
        return True

    def rec():
        nodes[0] += 1
        if nodes[0] > limit:
            return None
        free = [l for l in letters if l not in A]
        if not free:
            return True
        for v in range(26):
            if v in used:
                continue
            trail = []
            r = rec() if assign(free[0], v, trail) else False
            if r:
                return True
            for t in trail:
                used.discard(A.pop(t))
            if r is None:
                return None
        return False
    return rec()


def equations(ct, src, lag, form):
    eqs = []
    for p in CRIB_POS:
        j = p - lag
        if j < 0 or (src == "pt" and j not in CRIBS):
            continue
        k = ct[j] if src == "ct" else CRIBS[j]
        e = {}
        for letter, coef in ((ct[p], 1), (CRIBS[p], 1 if form == "beau" else -1), (k, 1 if form == "varbeau" else -1)):
            e[letter] = e.get(letter, 0) + coef
        eqs.append(e)
    return eqs


def tag(r):
    return {True: "SAT", False: "UNSAT", None: "unresolved"}[r]


def main():
    rnd = random.Random(2026)
    K4 = kryptos.K4
    randoms = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(30)]

    print("== Ciphertext autokey, lags 1-21 (24 equations each)")
    for form in FORMS:
        res = {L: solve(equations(K4, "ct", L, form), limit=5_000_000) for L in range(1, 22)}
        rs = sum(1 for c in randoms[:5] for L in range(1, 22) if solve(equations(c, "ct", L, form)) is not False)
        print(f"  {form:7}: SAT {[L for L, r in res.items() if r] or 'none'}, "
              f"unresolved {[L for L, r in res.items() if r is None] or 'none'}   (random x5: {rs} of 105 not UNSAT)")

    print("== Plaintext autokey, lags inside the clue runs (K4 against 30 random ciphertexts)")
    for form in FORMS:
        for L in range(1, 11):
            eqs = equations(K4, "pt", L, form)
            r = solve(eqs, limit=5_000_000)
            rr = [solve(equations(c, "pt", L, form)) for c in randoms]
            print(f"  {form:7} lag {L:2} ({len(eqs):2} equations): K4 {tag(r):10} random SAT {sum(x is True for x in rr):2}/30"
                  + (f", {sum(x is None for x in rr)} unresolved" if None in rr else ""))

    alpha = list(AZ)
    rnd.shuffle(alpha)
    a = {c: i for i, c in enumerate(alpha)}
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    ct = list("QWERT")
    for i in range(5, 97):
        ct.append(alpha[(a[pt[i]] + a[ct[i - 5]]) % 26])
    sat = [L for L in range(1, 22) if solve(equations("".join(ct), "ct", L, "vig"))]
    print(f"== Planted: ciphertext autokey, lag 5, random alphabet -> SAT at lags {sat}")


if __name__ == "__main__":
    main()
