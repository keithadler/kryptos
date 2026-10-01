"""Planted-cipher verification for every search in this repo.

Each check encrypts a fake 97-letter plaintext (random letters, with the four released clue words
at their real positions) using a method from a searched family, hands that ciphertext to the same
search code that was run on K4, and requires the search to find it. A search that cannot find a
planted example has proved nothing about K4, so every "eliminated" claim in SEARCH.md rests on one
of these passing.

usage: make verify          (builds bin/, then runs this)
       python3 verify.py --slow   (adds the simulated-annealing recovery checks, ~2 min)
"""
import contextlib
import io
import pathlib
import random
import subprocess
import sys

import numpy

import kryptos
from kryptos import AZ, KA, CRIBS, K1_CT, K1_PT, K2_PT

ROOT = pathlib.Path(__file__).resolve().parent
KAI = {c: i for i, c in enumerate(KA)}
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def fake_pt(seed):
    rnd = random.Random(seed)
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    return "".join(pt), rnd


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def patched(mods, ct, fn):
    old = [m.K4 for m in mods]
    for m in mods:
        m.K4 = ct
    try:
        return fn()
    finally:
        for m, o in zip(mods, old):
            m.K4 = o


def run_bin(args, ct=None):
    return subprocess.run([str(ROOT / "bin" / args[0])] + args[1:] + ([ct] if ct else []),
                          capture_output=True, text=True, cwd=ROOT).stdout


def columnar_sigma(w, order, n=97):
    rows, s, t = -(-n // w), [0] * n, 0
    for col in order:
        for r in range(rows if (n % w == 0 or col < n % w) else rows - 1):
            s[r * w + col] = t
            t += 1
    return s


def rotation(w, ccw, n=97):
    rows, sig, t = -(-n // w), [0] * n, 0
    for k in range(w):
        col = w - 1 - k if ccw else k
        nrow = rows if (col < n % w or n % w == 0) else rows - 1
        for rr in range(nrow):
            sig[(rr if ccw else nrow - 1 - rr) * w + col] = t
            t += 1
    return sig


# ------------------------------------------------------------------ ground truth
k = kryptos.keyword_vals(KA, "PALIMPSEST")
check("K1 decrypts with the KRYPTOS tableau and PALIMPSEST",
      kryptos.decrypt("vig", KA, K1_CT, (k * 10)[:len(K1_CT)]) == K1_PT)
check("ciphertext is 97 letters and the clues sit at 22-34, 64-74",
      len(kryptos.K4) == 97 and kryptos.K4[21:34] == "FLRVQQPRNGKSS" and kryptos.K4[63:74] == "NYPVTTMZFPK")

# ------------------------------------------------------------------ attacks.py
import attacks
pt, _ = fake_pt(7)
key = [KAI[c] for c in "KRYPTOSCLOCK"]
ct = "".join(KA[(KAI[p] + key[i % 12]) % 26] for i, p in enumerate(pt))
_, out = quiet(patched, [attacks], ct, attacks.test_periodic)
check("periodic key (KA Vigenere, period 12)", "vig  P:KA C:KA  falsifiable survivors: [(12," in out)
ct = "".join(KA[(KAI[p] + KAI[K2_PT[100 + i]]) % 26] for i, p in enumerate(pt))
_, out = quiet(patched, [attacks], ct, attacks.test_running_key)
check("running key (K2 plaintext, offset 100)", "('vig', 'KA', 'KA', 'x', 100)" in out)
c = []
for i, p in enumerate(pt):
    c.append(KA[(KAI[p] + (KAI["Q"] if i < 5 else KAI[c[i - 5]])) % 26])
_, out = quiet(patched, [attacks], "".join(c), attacks.test_autokey)
check("ciphertext autokey (lag 5)", "vig  P:KA C:KA key=ct via x-alphabet  survivors: [(5," in out)

# ------------------------------------------------------------------ typo.py
import typo
pt, _ = fake_pt(11)
key = [KAI[c] for c in "BERLINCLOCK"]
c = [KA[(KAI[p] + key[i % 11]) % 26] for i, p in enumerate(pt)]
c[29] = "A" if c[29] != "A" else "B"
_, out = quiet(patched, [typo, attacks], "".join(c), typo.main)
check("typo tolerance: one wrong clue letter", "'drop 30', 'vig-PKA-CKA', 'periodic p=11'" in out)
pt98 = pt[:45] + "Q" + pt[45:]
c98 = [KA[(KAI[p] + key[i % 11]) % 26] for i, p in enumerate(pt98)]
_, out = quiet(patched, [typo, attacks], "".join(c98[:45] + c98[46:]), typo.main)
check("typo tolerance: one dropped letter", "'shift@35+1', 'vig-PKA-CKA', 'periodic p=11'" in out)

# ------------------------------------------------------------------ bin/trans (columnar, rotation, keyword)
pt, rnd = fake_pt(3)
sig = columnar_sigma(7, [3, 0, 6, 1, 5, 2, 4])
inter = [KA[(KAI[p] + KAI["PALIMPS"[i % 7]]) % 26] for i, p in enumerate(pt)]
ct = [None] * 97
for i in range(97):
    ct[sig[i]] = inter[i]
out = run_bin(["trans", "7", "8"], "".join(ct))
check("columnar transposition, every order (w=7) + KA Vigenere", "w=7 ord=3,0,6,1,5,2,4 updown=0 inv=0 fam=vig-PKA-CKA order=A per=7" in out)
out = run_bin(["dfs", "7", "7", "12", "8"], "".join(ct))
check("pruned column search (dfs) finds the same plant", "dir=0 fam=vig-PKA-CKA order=A per=7 checks=17 ord=3,0,6,1,5,2,4" in out)

pt, _ = fake_pt(5)
s1, s2 = rotation(24, 0), rotation(8, 0)
sig = [s2[s1[i]] for i in range(97)]
inter = [None] * 97
for i in range(97):
    inter[sig[i]] = pt[i]
key = [KAI[ch] for ch in "ABSCISSAXY"]
ct = "".join(KA[(key[j % 10] - KAI[inter[j]]) % 26] for j in range(97))
out = run_bin(["trans", "rot", "8"], ct)
check("K3-style double rotation (24 then 8) + KA Beaufort", "w=2 ord=24,8 updown=0 inv=0 fam=beau-PKA-CKA order=B per=10" in out)

pt, _ = fake_pt(9)
word = "PALIMPSESTABSCISSA"
order = sorted(range(len(word)), key=lambda i: (word[i], i))
sig = columnar_sigma(len(word), order)
inter = [None] * 97
for i in range(97):
    inter[sig[i]] = pt[i]
ct = "".join(AZ[(AZ.index(inter[j]) + AZ.index("SHADOWS"[j % 7])) % 26] for j in range(97))
line = f"{word} {len(word)} {','.join(map(str, order))}\n"
out = subprocess.run([str(ROOT / "bin/trans"), "ord", "8", ct], input=line, capture_output=True, text=True).stdout
check("keyword-ordered columnar (PALIMPSESTABSCISSA, w=18)", "keyword PALIMPSESTABSCISSA" in out)

# ------------------------------------------------------------------ alphabets
import dictalpha
import numpy as np
from attacks import keyed
W = keyed("TELESCOPE")
wi = {ch: i for i, ch in enumerate(W)}
pt, rnd = fake_pt(2)
key = [3, 17, 8, 22, 5, 11, 0, 19]
ct = "".join(W[(key[i % 8] - wi[p]) % 26] for i, p in enumerate(pt))
old = dictalpha.CL
dictalpha.CL = np.array([ord(ct[p]) - 65 for p in kryptos.CRIB_POS])
_, out = quiet(dictalpha.main, ["TELESCOPE", "GARDEN", "PIANO"])
dictalpha.CL = old
check("dictionary keyed alphabet (Quagmire III Beaufort, TELESCOPE)", "Q3 beau period 8 checks 16" in out)

import mixedalpha
pt, rnd = fake_pt(21)
xs = list(AZ); rnd.shuffle(xs); X = "".join(xs)
key = [rnd.randrange(26) for _ in range(9)]
ct = "".join(KA[(X.index(p) + key[i % 9]) % 26] for i, p in enumerate(pt))
check("any masking alphabet + periodic key (general Quagmire I)",
      patched([mixedalpha], ct, lambda: mixedalpha.run("plain", "vig", "KA", 9))[0])

import quag34
for mode, kind, per, seed in (("III", "vig", 7, 31), ("III", "beau", 7, 32), ("IV", "vig", 5, 33)):
    pt, rnd = fake_pt(seed)
    A = "".join(rnd.sample(AZ, 26)); B = "".join(rnd.sample(AZ, 26))
    key = [rnd.randrange(26) for _ in range(per)]
    if mode == "III":
        ct = "".join(A[((A.index(p) + key[i % per]) if kind == "vig" else (key[i % per] - A.index(p))) % 26] for i, p in enumerate(pt))
    else:
        ct = "".join(B[(A.index(p) + key[i % per]) % 26] for i, p in enumerate(pt))
    r = patched([quag34], ct, lambda: quag34.solve(mode, per, kind)[0])
    out = run_bin(["quag3", {"III": kind, "IV": "vig4"}[mode], str(per)], ct)
    check(f"general Quagmire {mode} {kind} period {per} (Python and C solvers)", r is True and " SAT" in out)

import layer2
pt, _ = fake_pt(4)
u = [KAI[ch] for ch in "PALIMPSEST"]; v = [KAI[ch] for ch in "ABSCISSA"]
mid = [KA[(KAI[p] + u[i % 10]) % 26] for i, p in enumerate(pt)]
ct = "".join(KA[(KAI[m] + v[i % 8]) % 26] for i, m in enumerate(mid))
check("K1/K2 cipher applied twice (PALIMPSEST then ABSCISSA)",
      layer2.test("vig", KA, 8, 10, ct=ct)[0] and not layer2.test("vig", KA, 7, 10, ct=ct)[0])

import runkey_mixed
pt, rnd = fake_pt(12)
X = "".join(rnd.sample(AZ, 26))
ct = "".join(KA[(X.index(p) + KAI[K2_PT[57 + i]]) % 26] for i, p in enumerate(pt))
r = patched([runkey_mixed], ct, lambda: (runkey_mixed.check("plain", "vig", "KA", "KA", K2_PT, 57),
                                         runkey_mixed.check("plain", "vig", "KA", "KA", K2_PT, 58)))
check("K2 as running key under a masking alphabet", r[0][0] and not r[1][0])
table = rnd.sample(range(26), 26)
ct = "".join(KA[(KAI[p] + table[AZ.index(K2_PT[57 + i])]) % 26] for i, p in enumerate(pt))
r = patched([runkey_mixed], ct, lambda: (runkey_mixed.check_table("vig", "KA", "KA", K2_PT, 57),
                                         runkey_mixed.check_table("vig", "KA", "KA", K2_PT, 58)))
check("K2 as running key through an arbitrary lookup table", r[0][0] and r[0][1] >= 8 and not r[1][0])

import digits
pt, rnd = fake_pt(6)
key = [rnd.randrange(10) for _ in range(97)]
ct = "".join(AZ[(AZ.index(p) + key[i]) % 26] for i, p in enumerate(pt))
hits, _ = quiet(digits.main, ct)
check("digit keystream (Gronsfeld/Gromark shape) passes the digit filter",
      any(h[0] == "x=AZ y=W" and h[1] == "C=P+d" and h[2] == AZ for h in hits))

# ------------------------------------------------------------------ Trifid
import trifid
bad = tot = 0
for seed in range(2):
    rnd = random.Random(100 + seed)
    cells = [(a, b, c_) for a in range(3) for b in range(3) for c_ in range(3)]
    rnd.shuffle(cells)
    cube = dict(zip(AZ + "+", cells))
    pt, _ = fake_pt(200 + seed)
    for per in (3, 7, 12, 20):
        for off in (0, 1):
            ct = (trifid.encrypt(pt[:off], per, cube) if off else "") + trifid.encrypt(pt[off:], per, cube)
            tot += 1
            bad += trifid.solve(trifid.equalities(ct, per, off))[0] is not True
check("Trifid, random cubes, several periods and offsets", bad == 0, f"{tot - bad}/{tot}")

# ------------------------------------------------------------------ generated keystreams, autokey, sculpture grid
import keygen
rnd = random.Random(31)
check("polynomial keystream (5 + 3i + 7C(i,2), KA Vigenere)",
      keygen.poly(keygen.plant(rnd, [5 + 3 * i + 7 * (i * (i - 1) // 2) for i in range(97)])) == [("vig", "KA", "KA", 5, 3, 7, 0)])
ks = [3, 17, 8, 22, 5]
for i in range(5, 97):
    ks.append((ks[i - 2] + ks[i - 5]) % 26)
check("recurrence keystream (k_i = k_(i-2) + k_(i-5))",
      ("vig", "KA", "KA", 2, 5, 1, 1, 0, 14) in keygen.recur(keygen.plant(rnd, ks))[0])
pt, _ = fake_pt(32)
key, ct, j = [KAI[ch] for ch in "PALIMPSEST"], [], 0
for p in pt:
    ct.append(KA[(KAI[p] + key[j % 10]) % 26])
    j = 0 if ct[-1] == "S" else j + 1
check("interrupted key (PALIMPSEST, restart after ciphertext S)",
      any(h[:5] == ("S", 10, "vig", "KA", "KA") and h[5] >= 10 for h in keygen.ct_interrupt("".join(ct))[0]))
texts = keygen.morse_texts()[1200:1300]
best, where, _, _ = keygen.morse(keygen.plant(rnd, [KAI[texts[34][(17 + i) % len(texts[34])]] for i in range(97)]), texts)
check("Morse phrases as the key (KA Vigenere, offset 17)", best == 24 and where[0] == ("vig", "KA", "KA", "KA"))

import autokey_mixed
pt, rnd = fake_pt(33)
X = rnd.sample(AZ, 26)
ct = list("QWERT")
for i in range(5, 97):
    ct.append(X[(X.index(pt[i]) + X.index(ct[i - 5])) % 26])
check("ciphertext autokey under an unknown alphabet (lag 5)",
      [L for L in range(1, 10) if autokey_mixed.solve(autokey_mixed.equations("".join(ct), "ct", L, "vig"))] == [5])

import gridkey
pt, rnd = fake_pt(34)
lookup = {ch: rnd.randrange(26) for ch in AZ}
ct = "".join(KA[(lookup[gridkey.TAB[r][c] if c < len(gridkey.TAB[r]) else "A"] - KAI[p]) % 26]
             for p, (r, c) in zip(pt, gridkey.CELLS))
here = [a for a in gridkey.ALIGN if a[0] in ("tableau cell, row +0 col +0", "tableau cell, row +3 col +0")]
_, _, t = gridkey.run(ct, here)
check("opposite tableau letter through a lookup table (KA Beaufort)",
      [(c, lab, f) for c in t for lab, f in t[c]] == [(2, "tableau cell, row +0 col +0", ("beau", "KA", "KA"))])

import keylanguage
quad = next((f for f in (ROOT / "data/quadgrams.bin", ROOT / "data/quadgrams_local.bin") if f.exists()), None)
if quad:
    keylanguage.LOGP = numpy.fromfile(quad, dtype=numpy.float32)
    _, rnd = fake_pt(35)
    _, best = keylanguage.search(keylanguage.plant(rnd, KA, KA, "vig", kryptos.K3_PT, 100), [KA])
    check("English running key shows as English key fragments (K3 as key)",
          best[0][1] == "vig P:KA C:KA key:KA" and best[0][3][:13] == kryptos.K3_PT[121:134] and best[0][0] > -4.6)
else:
    print("SKIP  English running key scoring (run checks/quadgrams_local.py or quadgrams.py first)")

# ------------------------------------------------------------------ Hill with a constant, keyword pairs, SAT, K5
import hillaffine
pt, rnd = fake_pt(36)
M = numpy.array([[6, 24, 1], [13, 16, 10], [20, 17, 15]])
ct = "".join(AZ[(v - 1) % 26] for b in range(0, 96, 3)
             for v in (M @ numpy.array([AZ.index(ch) + 1 for ch in pt[b:b + 3]])) % 26) + "A"
check("3x3 Hill numbered A=1..Z=26 (a Hill with a constant)",
      (3, 0, "AZ", "AZ", "C=MP+b") in [r[:5] for r in hillaffine.test(ct) if 0 not in r[6]])

import quag4dict
from attacks import keyed
pt, rnd = fake_pt(37)
alphas = sorted({keyed("".join(rnd.sample(AZ, 6))) for _ in range(3000)} | {keyed("BERLIN"), keyed("CLOCK")})
W = numpy.stack([keylanguage.index_of(a) for a in alphas])
X, Y, key = keyed("BERLIN"), keyed("CLOCK"), [AZ.index(ch) for ch in "PALIMPSEST"]
ct = "".join(Y[(X.index(p) + key[i % 10]) % 26] for i, p in enumerate(pt))
check("Quagmire IV with two keyword alphabets (BERLIN / CLOCK, key PALIMPSEST)",
      ("vig", alphas.index(X), alphas.index(Y)) in quag4dict.survivors(ct, W, 10) and not quag4dict.survivors(ct, W, 9))

import shutil
import quagsat
if shutil.which("kissat"):
    pt, rnd = fake_pt(38)
    X, Y, key = rnd.sample(AZ, 26), rnd.sample(AZ, 26), [rnd.randrange(26) for _ in range(13)]
    ct = "".join(Y[(X.index(p) + key[i % 13]) % 26] for i, p in enumerate(pt))
    check("SAT solver: Quagmire IV with random alphabets fits at its key length 13, not at 9 or 11",
          quagsat.solve(ct, "IV", "vig", 13) is True and quagsat.solve(ct, "IV", "vig", 11) is False
          and quagsat.solve(ct, "IV", "vig", 9) is False)
else:
    print("SKIP  SAT solver checks (kissat not installed)")

if quad:
    import k5
    (case, exact, _, _), _ = quiet(k5.selftest, keylanguage.LOGP)
    check("K5 tool: second message read off at the known positions under a random 97-letter key",
          case == ("vig", "KA", "KA") and exact)
    o = subprocess.run([sys.executable, "checks/plant_sakw.py", "4", "16", "1"], capture_output=True, text=True, cwd=ROOT).stdout.split()
    best = subprocess.run([str(ROOT / "bin/sakw"), "4", "16", "8", "2000000", o[0], "1"], capture_output=True, text=True, cwd=ROOT).stdout
    got = [l.split()[6] for l in best.splitlines() if l.startswith("BEST")][0]
    check("keyword-alphabet annealing recovers a planted Quagmire IV (random keywords, length 16)",
          sum(a == b for a, b in zip(got, o[1])) >= 90)
else:
    print("SKIP  K5 tool and keyword annealing (need a quadgram model)")

# ------------------------------------------------------------------ running key over downloaded texts
carter = ROOT / "data/running_keys/carter_vol1.txt"
if carter.exists():
    import runkey
    t = runkey.load(carter)
    pt, _ = fake_pt(4)
    c = [KA[(KAI[p] + KAI[AZ[t[123456 + i]]]) % 26] for i, p in enumerate(pt)]
    c[25] = "Z" if c[25] != "Z" else "Y"
    c[70] = "Q" if c[70] != "Q" else "R"
    _, out = quiet(patched, [runkey], "".join(c), runkey.main)
    check("running key from Carter vol 1 with two typos", "22/24 vig-PKA-CKA key via x offset 123456" in out)
else:
    print("SKIP  running key over downloaded texts (run checks/fetch_texts.sh first)")

# ------------------------------------------------------------------ slow: English-scored annealing
if "--slow" in sys.argv:
    for mode, per in ((1, 13), (2, 13)):
        o = subprocess.run([sys.executable, "checks/plant_sa.py", str(mode), str(per), "1"], capture_output=True, text=True, cwd=ROOT).stdout.split()
        best = subprocess.run([str(ROOT / "bin/sa"), str(mode), str(per), "12", "4000000", o[0], "1"],
                              capture_output=True, text=True, cwd=ROOT, env={"CRIBW": "10"}).stdout
        got = [l.split()[1] for l in best.splitlines() if l.startswith("BEST")][0]
        n = sum(a == b for a, b in zip(o[1], got))
        check(f"annealing recovers a planted Quagmire {'I' if mode == 1 else 'II'} period {per}", n >= 85, f"{n}/97 letters")

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
