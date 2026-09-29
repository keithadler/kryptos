"""'LAYER TWO': the K1/K2 tableau cipher applied twice, with two repeating keys of lengths a and b.

With the same alphabet on both layers (A-Z/A-Z or KA/KA), two Vigenere layers add their shifts,
and mixing Vigenere and Beaufort layers gives a Beaufort or Vigenere with the sum/difference key.
So the combined key is k_i = u[i mod a] + v[i mod b] (signs absorbed into u, v).
Every crib gives one linear equation mod 26 in the unknowns u, v. A system over Z/26 is solvable iff
it is solvable mod 2 and mod 13 (CRT), which Gaussian elimination decides exactly.

Constraints = equations - rank (mod 13). A consistent system with c constraints happens by chance
about 26^-c of the time, so survivors are compared with that.
"""
import sys
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA


def solvable(rows, rhs, p):
    """Gaussian elimination mod prime p. Returns (consistent, rank)."""
    m = [r[:] + [b] for r, b in zip(rows, rhs)]
    n = len(rows[0])
    rank = 0
    for col in range(n):
        piv = next((i for i in range(rank, len(m)) if m[i][col] % p), None)
        if piv is None:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        inv = pow(m[rank][col], p - 2, p)
        m[rank] = [(x * inv) % p for x in m[rank]]
        for i in range(len(m)):
            if i != rank and m[i][col] % p:
                f = m[i][col]
                m[i] = [(x - f * y) % p for x, y in zip(m[i], m[rank])]
        rank += 1
    consistent = all(any(x % p for x in r[:-1]) or r[-1] % p == 0 for r in m)
    return consistent, rank


def test(kind, alpha, a, b, cribs=None, ct=K4):
    cribs = cribs or CRIBS
    ix = {c: i for i, c in enumerate(alpha)}
    rows, rhs = [], []
    for p in sorted(cribs):
        k = (ix[ct[p]] - ix[cribs[p]]) % 26 if kind == "vig" else (ix[ct[p]] + ix[cribs[p]]) % 26
        r = [0] * (a + b)
        r[p % a] += 1
        r[a + p % b] += 1
        rows.append(r)
        rhs.append(k)
    ok2, _ = solvable(rows, rhs, 2)
    ok13, rank = solvable(rows, rhs, 13)
    return ok2 and ok13, len(rows) - rank


def main():
    maxp = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    surv, tests, expect = [], 0, 0.0
    for kind in ("vig", "beau"):
        for an, alpha in (("AZ", AZ), ("KA", KA)):
            for a in range(1, maxp + 1):
                for b in range(a, maxp + 1):
                    ok, c = test(kind, alpha, a, b)
                    if c == 0:
                        continue
                    tests += 1
                    expect += 26.0 ** -c
                    if ok:
                        surv.append((c, kind, an, a, b))
    surv.sort(reverse=True)
    print(f"two-layer periodic, key lengths a <= b <= {maxp}: {tests} testable combos, "
          f"{len(surv)} consistent (chance expects ~{expect:.1f})")
    for s in surv[:15]:
        print(f"  constraints {s[0]:2}  {s[1]:4} {s[2]}  lengths {s[3]} + {s[4]}")


if __name__ == "__main__":
    main()
