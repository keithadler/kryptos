"""Run the families the confirmed cribs left OPEN under a guessed-plaintext hypothesis.

usage: KRYPTOS_GUESS="61:THE" python3 guess_run.py
A guess only adds constraints, so families already eliminated stay eliminated; only the open ones
are rerun. Every SAT/survivor is compared with random ciphertexts under the SAME crib set, so a
grammar-shaped guess can't manufacture a false positive.
"""
import io
import contextlib
import random
import kryptos
from kryptos import CRIBS, GUESS
import mixedalpha
import quag34
import attacks

assert GUESS, "set KRYPTOS_GUESS"
AZ = kryptos.AZ
REAL = kryptos.K4
rnd = random.Random(2026)
RANDOMS = ["".join(rnd.choice(AZ) for _ in range(97)) for _ in range(12)]


def with_ct(ct, fn):
    mixedalpha.K4 = quag34.K4 = attacks.K4 = ct
    try:
        return fn()
    finally:
        mixedalpha.K4 = quag34.K4 = attacks.K4 = REAL


def rate(fn):
    res = [with_ct(r, fn) for r in RANDOMS]
    sat = sum(1 for x in res if x is True)
    return f"random {sat}/{len(res)} SAT" + (f", {sum(1 for x in res if x is None)} timeout" if None in res else "")


print(f"cribs: 24 confirmed + {len(GUESS)} guessed")
print("\n== Quagmire I/II, any alphabet on one side (periods open under confirmed cribs)")
for side in ("plain", "cipher"):
    for kind in ("vig", "beau"):
        for ka in ("AZ", "KA"):
            surv = []
            for per in (13, 16, 19, 20, 23, 24, 26):
                ok, cyc = mixedalpha.run(side, kind, ka, per)
                if ok:
                    surv.append((per, cyc))
            print(f"  {'QI ' if side == 'plain' else 'QII'} {kind:4} {ka}: still open at {surv or 'none -> all eliminated'}")

print("\n== general Quagmire III Beaufort / IV (periods open under confirmed cribs)")
for mode, kind, pers in (("III", "beau", (13, 18, 23, 26)), ("IV", "vig", (8, 13, 16, 19, 20, 23, 24, 26))):
    for per in pers:
        r = quag34.solve(mode, per, kind, limit=300_000)[0]
        tag = {True: "SAT", False: "UNSAT", None: "timeout"}[r]
        extra = ""
        if r is not False:
            extra = "   (" + rate(lambda: quag34.solve(mode, per, kind, limit=100_000)[0]) + ")"
        print(f"  Q{mode} {kind} period {per:2}: {tag}{extra}")

print("\n== Hill 4x4 and periodic 27-48")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    attacks.test_hill()
print("\n".join("  " + l.strip() for l in buf.getvalue().splitlines() if "n=4" in l))
fams = list(attacks.families())
for kind, xn, yn, x, y in fams:
    forced = [(p, attacks.kval(kind, x, y, CRIBS[p], REAL[p])) for p in kryptos.CRIB_POS]
    s = [(per, c) for per in range(27, 49) for ok, c in [attacks.periodic(forced, per)] if ok and c > 0]
    print(f"  periodic 27-48 {kind:4} P:{xn} C:{yn}: survivors (period, constraints) {s or 'none'}")
