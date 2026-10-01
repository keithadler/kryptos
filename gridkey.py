"""Key letters taken from the sculpture by POSITION.

K4 sits in the last four rows of the left (ciphertext) panel. The key letter for each K4 letter is
taken as the letter at the same row and column of the tableau panel or of the ciphertext panel, at
every row and column offset, mirrored or not (the letters are cut through, so the back shows them
mirrored). Every reading order of both grids as a single stream is tried too: rows, mirrored rows,
boustrophedon, columns in each direction.

The key letter becomes a shift in two ways:
  exact  its index in A-Z or KRYPTOS is the shift (a running key);
  table  ANY lookup table from key letter to shift: equal key letters must force equal shifts.
The tableau repeats few letters across the clue positions, so the table test holds at most 2-3
constraints. It is reported with what random ciphertexts do, and proves little on its own.
"""
import pathlib
import random
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ, KA

DATA = pathlib.Path(__file__).with_name("data")
ALPH = {"AZ": AZ, "KA": KA}
FAMS = [(k, xn, yn) for k in ("vig", "beau") for xn in ALPH for yn in ALPH]
LEFT = [l.strip() for l in open(DATA / "sculpture_left.txt") if l.strip()]
TAB = [l.strip() for l in open(DATA / "tableau.txt") if l.strip()]
# K4's cells on the left panel: the last 4 letters of row 25, then rows 26-28
CELLS = [(24, c) for c in range(27, 31)] + [(r, c) for r in (25, 26, 27) for c in range(31)]
assert len(LEFT) == len(TAB) == 28 and "".join(LEFT[r][c] for r, c in CELLS) == kryptos.K4


def ix(a):
    return {c: i for i, c in enumerate(a)}


def forced(ct, kind, xn, yn):
    x, y = ix(ALPH[xn]), ix(ALPH[yn])
    return [(y[ct[p]] - x[CRIBS[p]]) % 26 if kind == "vig" else (y[ct[p]] + x[CRIBS[p]]) % 26 for p in CRIB_POS]


def streams(grid, name):
    width = max(map(len, grid))
    cols = ["".join(r[c] for r in grid if c < len(r)) for c in range(width)]
    rcols = ["".join(r[len(r) - 1 - c] for r in grid if c < len(r)) for c in range(width)]
    out = {
        f"{name} rows": "".join(grid),
        f"{name} rows mirrored": "".join(r[::-1] for r in grid),
        f"{name} boustrophedon": "".join(r if i % 2 == 0 else r[::-1] for i, r in enumerate(grid)),
        f"{name} columns down, left to right": "".join(cols),
        f"{name} columns down, right to left": "".join(cols[::-1]),
        f"{name} columns up, left to right": "".join(c[::-1] for c in cols),
        f"{name} right-justified columns down": "".join(rcols),
    }
    out.update({k + " (reversed)": v[::-1] for k, v in list(out.items())})
    return {k: "".join(ch for ch in v if ch.isalpha()) for k, v in out.items()}


def alignments():
    """(label, key letter or None for each clue position)"""
    for name, grid in (("tableau", TAB), ("left panel", LEFT)):
        for mirror in (0, 1):
            for dr in range(28):
                for dc in range(-31, 32):
                    ks = []
                    for p in CRIB_POS:
                        r, c = CELLS[p]
                        row = grid[(r + dr) % 28]
                        cc = (len(row) - 1 - c if mirror else c) + dc
                        ks.append(row[cc] if 0 <= cc < len(row) and row[cc].isalpha() else None)
                    if sum(k is not None for k in ks) >= 20:
                        yield f"{name} cell, row {dr:+d} col {dc:+d}{' mirrored' if mirror else ''}", ks
        for sname, s in streams(grid, name).items():
            for off in range(-CRIB_POS[0], len(s) - CRIB_POS[-1]):
                yield f"{sname}, offset {off}", [s[off + p] for p in CRIB_POS]


ALIGN = list(alignments())


def run(ct, align=None):
    """(tests, best exact match (count, where), {constraints held: [survivors]} for the table test)"""
    F = {f: forced(ct, *f) for f in FAMS}
    exact, table, tests = (0, None), {}, 0
    for label, ks in align or ALIGN:
        for f, need in F.items():
            tests += 1
            for kn, ka in ALPH.items():
                m = sum(1 for k, v in zip(ks, need) if ka[v] == k)
                if m > exact[0]:
                    exact = (m, (label, f, kn))
            seen, ok, checks = {}, True, 0
            for k, v in zip(ks, need):
                if k is None:
                    continue
                if k in seen:
                    checks += 1
                    if seen[k] != v:
                        ok = False
                        break
                else:
                    seen[k] = v
            if ok and checks:
                table.setdefault(checks, []).append((label, f))
    return tests, exact, table


def main():
    rnd = random.Random(2026)
    tests, exact, table = run(kryptos.K4)
    print(f"{len(ALIGN)} alignments x 8 families = {tests} tests")
    opp = [TAB[CELLS[p][0]][CELLS[p][1]] for p in CRIB_POS]
    print(f"tableau letters directly opposite the clue letters: {''.join(opp[:13])} | {''.join(opp[13:])}")
    print("== K4")
    print(f"  exact: best {exact[0]}/24 key letters at {exact[1]}")
    print(f"  any lookup table: survivors by constraints held: { {c: len(v) for c, v in sorted(table.items())} }")
    here = [f for c in table for label, f in table[c] if label == "tableau cell, row +0 col +0"]
    print(f"  the directly opposite tableau letter through any lookup table: "
          f"{here if here else 'contradiction in all 8 families (2 constraints)'}")
    print("== Random ciphertexts with the same clue letters")
    for _ in range(6):
        _, e, t = run("".join(rnd.choice(AZ) for _ in range(97)))
        print(f"  exact best {e[0]}/24; lookup-table survivors { {c: len(v) for c, v in sorted(t.items())} }")
    lookup, a = {c: rnd.randrange(26) for c in AZ}, ix(KA)
    ct = [rnd.choice(AZ) for _ in range(97)]
    for p in CRIB_POS:
        r, c = CELLS[p]
        ct[p] = KA[(lookup[TAB[r][c]] - a[CRIBS[p]]) % 26]
    _, _, t = run("".join(ct))
    found = [c for c in t for label, f in t[c] if label == "tableau cell, row +0 col +0" and f == ("beau", "KA", "KA")]
    print(f"== Planted: opposite tableau letter through a random lookup table, KRYPTOS Beaufort -> "
          f"{'found, ' + str(found[0]) + ' constraints' if found else 'NOT FOUND'}")


if __name__ == "__main__":
    main()
