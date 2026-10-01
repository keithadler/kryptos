"""General Quagmire III / IV by SAT solver: settles the cases backtracking left unresolved.

Same model as quag34.py (unknown alphabet(s) on both sides, repeating key of a given length), but
written out as clauses and handed to kissat, which proves UNSAT or finds an alphabet outright
instead of timing out.

  QIII  one alphabet A on both sides   vig: A[C] - A[P] = k_r    beau: A[C] + A[P] = k_r
  QIV   alphabets X (plain), Y (cipher)                           vig: Y[C] - X[P] = k_r

Encoding: every letter position and key value is one of 26 (exactly one true), letters of one
alphabet take different positions, and each clue letter gives 676 clauses "if A[C]=a and A[P]=b
then k_r=a+b". Shifting an alphabet changes nothing, so one letter per alphabet is pinned to 0.

usage: python3 quagsat.py                 every key length 1-60, with random calibration where satisfiable
       python3 quagsat.py III beau 13     one case
Needs kissat on the PATH (brew install kissat).
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ


FIXED = {"AZ": AZ, "KA": kryptos.KA}


def cnf(ct, mode, kind, per, cribs=None, m=None, fixed="AZ"):
    """m=None: any alphabet. m=0..26: keyword alphabets only, the keyword having at most m different
    letters (the first m places are free, the rest of the alphabet follows in A-Z order).
    Modes I and II have one unknown alphabet (plain / cipher side) and the fixed one on the other."""
    if m is not None or mode in ("I", "II"):
        return cnf_keyword(ct, mode, kind, per, cribs or CRIBS, m, fixed)
    cribs = cribs or CRIBS
    var, clauses = {}, []

    def v(name, d):
        return var.setdefault((name, d), len(var) + 1)

    def one_of_26(name):
        clauses.append([v(name, d) for d in range(26)])
        for a in range(26):
            for b in range(a + 1, 26):
                clauses.append([-v(name, a), -v(name, b)])

    names = set()
    for p in sorted(cribs):
        P, C = cribs[p], ct[p]
        xa, ya = (("A", P), ("A", C)) if mode == "III" else (("X", P), ("Y", C))
        k = ("k", p % per)
        for n in (xa, ya, k):
            if n not in names:
                names.add(n)
                one_of_26(n)
        sign = -1 if kind == "vig" else 1
        for a in range(26):
            if xa == ya:                                    # a letter enciphered to itself
                clauses.append([-v(ya, a), v(k, (a + sign * a) % 26)])
                continue
            for b in range(26):
                clauses.append([-v(ya, a), -v(xa, b), v(k, (a + sign * b) % 26)])
    for alpha in ("A", "X", "Y"):
        ls = sorted(n for n in names if n[0] == alpha)
        for i, m in enumerate(ls):
            for n in ls[i + 1:]:
                for d in range(26):
                    clauses.append([-v(m, d), -v(n, d)])
        if ls:
            clauses.append([v(ls[0], 0)])                   # pin: shifting the alphabet is a symmetry
    return var, clauses


def cnf_keyword(ct, mode, kind, per, cribs, m, fixed):
    var, clauses = {}, []
    sign = -1 if kind == "vig" else 1
    fx = {c: i for i, c in enumerate(FIXED[fixed])}

    def v(name, d):
        return var.setdefault((name, d), len(var) + 1)

    def one_of_26(name):
        clauses.append([v(name, d) for d in range(26)])
        for a in range(26):
            for b in range(a + 1, 26):
                clauses.append([-v(name, a), -v(name, b)])

    unknown = {"III": "A", "IV": "XY", "I": "X", "II": "Y"}[mode]
    for alpha in unknown:
        for i, u in enumerate(AZ):
            one_of_26((alpha, u))
            for w in AZ[i + 1:]:
                for d in range(26):
                    clauses.append([-v((alpha, u), d), -v((alpha, w), d)])
                if m is not None:                           # past the keyword, u comes before w
                    for a in range(m, 26):
                        for b in range(m, a):
                            clauses.append([-v((alpha, u), a), -v((alpha, w), b)])
    for r in sorted({p % per for p in cribs}):
        one_of_26(("k", r))
    for p in sorted(cribs):
        P, C = cribs[p], ct[p]
        xa = ("A", P) if mode == "III" else ("X", P) if "X" in unknown else None
        ya = ("A", C) if mode == "III" else ("Y", C) if "Y" in unknown else None
        k = ("k", p % per)
        if xa is None:                                      # plaintext side fixed
            for a in range(26):
                clauses.append([-v(ya, a), v(k, (a + sign * fx[P]) % 26)])
        elif ya is None:                                    # ciphertext side fixed
            for b in range(26):
                clauses.append([-v(xa, b), v(k, (fx[C] + sign * b) % 26)])
        elif xa == ya:
            for a in range(26):
                clauses.append([-v(ya, a), v(k, (a + sign * a) % 26)])
        else:
            for a in range(26):
                for b in range(26):
                    clauses.append([-v(ya, a), -v(xa, b), v(k, (a + sign * b) % 26)])
    return var, clauses


def solve(ct, mode, kind, per, cribs=None, timeout=3600, m=None, fixed="AZ", model=False):
    """True (an alphabet and key exist), False (none does), None (kissat gave up).
    model=True returns the alphabets found instead of True."""
    var, clauses = cnf(ct, mode, kind, per, cribs, m, fixed)
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False) as f:
        f.write(f"p cnf {len(var)} {len(clauses)}\n")
        f.writelines(" ".join(map(str, c)) + " 0\n" for c in clauses)
    r = subprocess.run(["kissat", "-q", f"--time={timeout}", f.name], capture_output=True, text=True)
    os.unlink(f.name)
    if r.returncode == 10 and model:
        true = {int(t) for line in r.stdout.splitlines() if line.startswith("v") for t in line.split()[1:] if int(t) > 0}
        got = {name: d for (name, d), i in var.items() if i in true}
        out = {}
        for alpha in "AXY":
            pos = {n[1]: d for n, d in got.items() if n[0] == alpha}
            if pos:
                out[alpha] = "".join(sorted(pos, key=pos.get)) if len(pos) == 26 else pos
        out["key"] = [got.get(("k", r)) for r in range(per)]
        return out
    return {10: True, 20: False}.get(r.returncode)


def shortest_keyword(ct, mode, kind, per, fixed="AZ", cribs=None, timeout=600):
    """Smallest m (most different letters a keyword needs) at which the case is satisfiable.
    SAT at m implies SAT at m+1, so bisect. 27 means not even a free alphabet works."""
    lo, hi = 0, 27
    while lo < hi:
        mid = (lo + hi) // 2
        r = solve(ct, mode, kind, per, cribs, timeout, m=min(mid, 26), fixed=fixed) if mid < 27 else False
        if r is None:
            return None
        if r:
            hi = mid
        else:
            lo = mid + 1
    return lo


def tag(r):
    return {True: "SAT", False: "UNSAT", None: "unresolved"}[r]


def main():
    if not shutil.which("kissat"):
        raise SystemExit("kissat not found (brew install kissat)")
    if len(sys.argv) == 4:
        mode, kind, per = sys.argv[1], sys.argv[2], int(sys.argv[3])
        print(f"Q{mode} {kind} period {per}: {tag(solve(kryptos.K4, mode, kind, per))}")
        return
    rnd = random.Random(2026)
    randoms = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(30)]
    print("== Agreement with the backtracking solvers on settled cases")
    for mode, kind, per, want in (("III", "vig", 18, False), ("III", "beau", 11, False), ("III", "beau", 19, False),
                                  ("III", "beau", 20, False), ("IV", "vig", 7, False), ("IV", "vig", 8, True)):
        got = solve(kryptos.K4, mode, kind, per)
        print(f"  Q{mode} {kind} period {per}: {tag(got)}  ({'agrees' if got == want else 'DISAGREES'})")
    for mode, kind, label in (("III", "vig", "Quagmire III, Vigenere form"), ("III", "beau", "Quagmire III, Beaufort form"),
                              ("IV", "vig", "Quagmire IV")):
        print(f"== {label}: key lengths 1-60, any alphabet(s)")
        res = {per: solve(kryptos.K4, mode, kind, per) for per in range(1, 61)}
        print(f"  no alphabet fits (eliminated): {[p for p, r in res.items() if r is False]}")
        if None in res.values():
            print(f"  unresolved: {[p for p, r in res.items() if r is None]}")
        print("  satisfiable, with how many of 30 random ciphertexts are too:")
        for per in [p for p, r in res.items() if r]:
            rr = [solve(c, mode, kind, per, timeout=600) for c in randoms]
            print(f"    length {per:2}: random {sum(x is True for x in rr):2}/30"
                  + (f", {sum(x is None for x in rr)} unresolved" if None in rr else ""), flush=True)
    rnd = random.Random(7)
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    X, Y = rnd.sample(AZ, 26), rnd.sample(AZ, 26)
    key = [rnd.randrange(26) for _ in range(13)]
    ct = "".join(Y[(X.index(p) + key[i % 13]) % 26] for i, p in enumerate(pt))
    print(f"== Planted Quagmire IV, random alphabets, key length 13: {tag(solve(ct, 'IV', 'vig', 13))} at 13, "
          f"{tag(solve(ct, 'IV', 'vig', 12))} at 12")


if __name__ == "__main__":
    main()
