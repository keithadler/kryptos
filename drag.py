"""Crib dragging: slide guessed words across K4's unknown positions.

The released cribs already kill every periodic key of period 1..26, so extra words can only matter
for periods 27..48, where the released cribs impose no constraints at all. For each guessed word,
each placement, each of the 8 substitution families and each period, we count how many constraints
the combined cribs impose and whether they hold.

A random placement survives c constraints with probability 26^-c, so we compare observed survivors
against the expected number sum(26^-c). Only an excess over that is evidence.

Guesses are hypotheses: they are never merged into the confirmed cribs.
"""
import sys
from kryptos import K4, CRIBS, AZ, KA

N = len(K4)
ALPH = {"AZ": AZ, "KA": KA}
FAM = [(k, xn, yn) for k in ("vig", "beau") for xn in ALPH for yn in ALPH]
IX = {n: {c: i for i, c in enumerate(a)} for n, a in ALPH.items()}

WORDS = sys.argv[1:] or """
WELTZEITUHR ALEXANDERPLATZ BERLINWALL THEWALL WALL EGYPT CAIRO GIZA PYRAMID PYRAMIDS SPHINX
NILE TOMB LANGLEY VIRGINIA MESSAGE DELIVER DELIVERING DELIVERED COMPASS COMPASSROSE BEARING
DEGREES MINUTES SECONDS NORTHWEST SOUTHEAST SOUTHWEST NORTH SOUTH WEST SHADOW LIGHT BURIED
LAYERTHREE LAYERFOUR TIME HOURS WORLDCLOCK CHECKPOINTCHARLIE EASTBERLIN WESTBERLIN
SANBORN SCHEIDT TUTANKHAMUN CARTER THEREFORE UNDERGROUND LOCATION HERE THERE FROMHERE
""".split()


def forced(fam, pos, pch):
    kind, xn, yn = fam
    c, p = IX[yn][K4[pos]], IX[xn][pch]
    return (c - p) % 26 if kind == "vig" else (c + p) % 26


def test(cribs, fam, per):
    """Counts every constraint (no early exit) so the chance baseline sum(26^-c) is honest."""
    seen, checks, ok = {}, 0, True
    for pos, ch in cribs.items():
        v, r = forced(fam, pos, ch), pos % per
        if r in seen:
            checks += 1
            ok &= seen[r] == v
        else:
            seen[r] = v
    return ok, checks


def main():
    base = {per: {f: test(CRIBS, f, per)[1] for f in FAM} for per in range(27, 49)}
    print(f"{'word':18} {'place':>5} {'tests':>7} {'surv':>5} {'expect':>7}  strongest survivors (start 1-based, family, period, constraints)")
    total_obs = total_exp = 0.0
    for w in WORDS:
        tests = obs = 0
        exp = 0.0
        strong = []
        places = 0
        for s in range(N - len(w) + 1):
            if any(s + i in CRIBS and CRIBS[s + i] != ch for i, ch in enumerate(w)):
                continue
            if all(s + i in CRIBS for i in range(len(w))):
                continue
            places += 1
            cr = dict(CRIBS)
            cr.update({s + i: ch for i, ch in enumerate(w)})
            for per in range(27, 49):
                for f in FAM:
                    ok, c = test(cr, f, per)
                    if c == 0:
                        continue
                    tests += 1
                    exp += 26.0 ** -c
                    if ok:
                        obs += 1
                        if c >= 4:
                            strong.append((c, s + 1, "-".join(f), per))
        total_obs += obs
        total_exp += exp
        strong.sort(reverse=True)
        print(f"{w:18} {places:5} {tests:7} {obs:5} {exp:7.2f}  "
              + (", ".join(f"({s},{f},{p},{c})" for c, s, f, p in strong[:3]) or "-"))
    print(f"\nTOTAL observed {total_obs:.0f} vs expected by chance {total_exp:.1f}")


if __name__ == "__main__":
    main()
