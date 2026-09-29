"""General Quagmire III / IV against the cribs: unknown alphabet(s) on BOTH sides, periodic key.

QIII: one unknown alphabet A on both sides  vig: A(C) - A(P) = k_r    beau: A(C) + A(P) = k_r
QIV : two independent unknown alphabets     vig: Y(C) - X(P) = k_r    (beau reduces to vig: X -> -X)
(K1 and K2 are QIII-vig with A = KRYPTOSABC..., which the tableau tests already cover; here A is free.)

Constraint search: variables are the alphabet positions of the letters that occur in the cribs and
the key residues; each crib gives one 3-variable linear equation mod 26; alphabets are injective.
Backtracking with propagation (two known -> third forced). Symmetry: shifting an alphabet (and the
key with it) changes nothing, so one letter per alphabet is pinned to 0.

UNSAT = no alphabet(s) and key of that period reproduce the cribs. Periods where the cribs give few
equations beyond the unknowns are reported but trivially SAT.
"""
import sys
from kryptos import K4, CRIBS, CRIB_POS

sys.setrecursionlimit(10000)


def build(mode, per, kind):
    cons = []   # (yvar, xvar, kvar, sign): Y(C) + sign*X(P) = k
    for p in CRIB_POS:
        P, C = CRIBS[p], K4[p]
        if mode == "III":
            yv, xv = ("A", C), ("A", P)
        else:
            yv, xv = ("Y", C), ("X", P)
        sign = -1 if kind == "vig" else 1
        cons.append((yv, xv, ("k", p % per), sign))
    return cons


def solve(mode, per, kind, limit=2_000_000):
    cons = build(mode, per, kind)
    vars_ = sorted({v for c in cons for v in c[:3]})
    val = {}
    used = {}   # alphabet name -> set of used values
    nodes = [0]
    by_var = {v: [c for c in cons if v in c[:3]] for v in vars_}

    def ok_assign(v, x):
        if v[0] != "k" and x in used.setdefault(v[0], set()):
            return False
        return True

    def assign(v, x, trail):
        val[v] = x
        if v[0] != "k":
            used.setdefault(v[0], set()).add(x)
        trail.append(v)

    def undo(trail, n):
        while len(trail) > n:
            v = trail.pop()
            if v[0] != "k":
                used[v[0]].discard(val[v])
            del val[v]

    def propagate(trail, queue):
        while queue:
            v = queue.pop()
            for (yv, xv, kv, s) in by_var[v]:
                known = [w for w in (yv, xv, kv) if w in val]
                if len(known) == 3:
                    if (val[yv] + s * val[xv] - val[kv]) % 26:
                        return False
                elif len(known) == 2:
                    if yv not in val:
                        w, x = yv, (val[kv] - s * val[xv]) % 26
                    elif xv not in val:
                        w, x = xv, ((val[kv] - val[yv]) * s) % 26   # s = +-1 so s^-1 = s
                    else:
                        w, x = kv, (val[yv] + s * val[xv]) % 26
                    if not ok_assign(w, x):
                        return False
                    assign(w, x, trail)
                    queue.append(w)
        return True

    def pick():
        best, bs = None, -1
        for v in vars_:
            if v in val:
                continue
            score = sum(1 for c in by_var[v] for w in c[:3] if w in val)
            if score > bs:
                best, bs = v, score
        return best

    def bt(trail):
        nodes[0] += 1
        if nodes[0] > limit:
            raise TimeoutError
        v = pick()
        if v is None:
            return True
        for x in range(26):
            if not ok_assign(v, x):
                continue
            n = len(trail)
            assign(v, x, trail)
            if propagate(trail, [v]) and bt(trail):
                return True
            undo(trail, n)
        return False

    trail = []
    # symmetry: pin the first letter of each alphabet to 0
    for alpha in ("A", "X", "Y"):
        first = next((v for v in vars_ if v[0] == alpha), None)
        if first:
            assign(first, 0, trail)
            if not propagate(trail, [first]):
                return False, len(cons), nodes[0]
    try:
        return bt(trail), len(cons), nodes[0]
    except TimeoutError:
        return None, len(cons), nodes[0]


def slack(mode, per):
    """equations minus free unknowns (after symmetry); <= 0 means the cribs can't really test it."""
    cons = build(mode, per, "vig")
    nv = len({v for c in cons for v in c[:3]})
    return len(cons) - (nv - (1 if mode == "III" else 2))


def main():
    for mode, kinds in (("III", ("vig", "beau")), ("IV", ("vig",))):
        for kind in kinds:
            print(f"== general Quagmire {mode} {kind}")
            for per in range(1, 27):
                r, ncons, nodes = solve(mode, per, kind)
                print(f"  period {per:2}: {({True: 'SAT', False: 'UNSAT', None: 'timeout'})[r]:7} "
                      f"slack {slack(mode, per):3}  nodes {nodes}")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
