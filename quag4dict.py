"""Quagmire IV with ANY TWO dictionary keywords: every pair of keyed alphabets, every key length.

K1 and K2 use one keyword alphabet (KRYPTOS) on both sides and a keyword key. The natural next step
is a different keyword alphabet on each side: plaintext alphabet X = keyed(word1), ciphertext
alphabet Y = keyed(word2), and a repeating key of length p:

    vig   Y[C_i] - X[P_i] = k_(i mod p)        beau   Y[C_i] + X[P_i] = k_(i mod p)

dictalpha.py pairs each dictionary alphabet only with A-Z, KRYPTOS or itself. All pairs is ~5e10
combinations per key length, too many to try one by one, but the key cancels: for two clue letters
i, j on the same key letter,

    Y[C_i] - Y[C_j] = +/-(X[P_i] - X[P_j]).

The left side depends only on word2 and the right only on word1. So each alphabet gets a
"signature" (those differences, over every such pair), and a pair of words fits exactly when the
signatures are equal: a join, not a double loop. Key lengths 1-52 that give at least MINC
constraints are tested. Every fitting pair is then used to decrypt all of K4 (key letters the clues
don't reach are left blank) and the newly revealed letters are scored as English.

usage: python3 quag4dict.py            K4, then planted and random controls
Needs a quadgram model (data/quadgrams.bin or data/quadgrams_local.bin) for the scoring step.
"""
import pathlib
import random
import sys
import numpy as np
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ, KA
from attacks import keyed
from keylanguage import dictionary, index_of

DATA = pathlib.Path(__file__).with_name("data")
MINC = 5           # fewer constraints than this and chance pairs run to hundreds of thousands or more
MAXPER = 52
M1, M2 = (1 << 61) - 1, (1 << 31) - 1


def alphabets():
    extra = DATA / "words_de_local.txt"
    al = set(dictionary(extra if extra.exists() else None)) | {AZ, KA}
    cities = DATA / "weltzeituhr_cities.txt"
    if cities.exists():
        import keygen
        al |= {keyed(n) for n in keygen.clock_names() if len(n) >= 4}
    return sorted(al)


def pairs_for(per):
    """(first, other) indices into CRIB_POS for clue letters on the same key letter."""
    first, a, b = {}, [], []
    for j, p in enumerate(CRIB_POS):
        r = p % per
        if r in first:
            a.append(first[r]); b.append(j)
        else:
            first[r] = j
    return np.array(a, dtype=np.int64), np.array(b, dtype=np.int64)


def hashes(sig):
    """Two independent row hashes of an (n, c) array of values 0..25."""
    h1 = np.zeros(len(sig), dtype=np.int64)
    h2 = np.zeros(len(sig), dtype=np.int64)
    for col in sig.T:
        h1 = (h1 * 131 + col + 1) % M1
        h2 = (h2 * 31 + col + 7) % M2
    return h1 * 4 + (h2 & 3), h2


def survivors(ct, W, per):
    """[(kind, x index, y index)] for every alphabet pair that fits all clue letters at this key length."""
    a, b = pairs_for(per)
    if len(a) < MINC:
        return None
    PL = np.array([ord(CRIBS[p]) - 65 for p in CRIB_POS])
    CL = np.array([ord(ct[p]) - 65 for p in CRIB_POS])
    xv, yv = W[:, PL].astype(np.int64), W[:, CL].astype(np.int64)
    sy = (yv[:, a] - yv[:, b]) % 26
    out = []
    for kind, sx in (("vig", (xv[:, a] - xv[:, b]) % 26), ("beau", (xv[:, b] - xv[:, a]) % 26)):
        hx, _ = hashes(sx)
        hy, _ = hashes(sy)
        common = np.intersect1d(hx, hy)
        if len(common) == 0:
            continue
        xi = np.nonzero(np.isin(hx, common))[0]
        yi = np.nonzero(np.isin(hy, common))[0]
        by = {}
        for j in yi:
            by.setdefault(sy[j].tobytes(), []).append(int(j))
        for i in xi:
            for j in by.get(sx[i].tobytes(), ()):               # exact comparison, not just the hash
                out.append((kind, int(i), j))
    return out


def decrypt(ct, kind, x, y, per, logp):
    """Plaintext for one alphabet pair, key from the clues; letters whose key letter the clues
    don't reach are left as dots. Returns (mean quadgram score over fully known groups outside the
    clue words, plaintext, known letters outside the clue words)."""
    xi, yi = {c: i for i, c in enumerate(x)}, {c: i for i, c in enumerate(y)}
    key = {}
    for p in CRIB_POS:
        key[p % per] = (yi[ct[p]] - xi[CRIBS[p]]) % 26 if kind == "vig" else (yi[ct[p]] + xi[CRIBS[p]]) % 26
    out = []
    for i, c in enumerate(ct):
        if i % per not in key:
            out.append(".")
        else:
            out.append(x[(yi[c] - key[i % per]) % 26] if kind == "vig" else x[(key[i % per] - yi[c]) % 26])
    pt = "".join(out)
    tot = n = 0
    for i in range(len(pt) - 3):
        q = pt[i:i + 4]
        if "." not in q and not all(i + t in CRIBS for t in range(4)):       # new information only
            tot += logp[((ord(q[0]) - 65) * 26 + ord(q[1]) - 65) * 676 + (ord(q[2]) - 65) * 26 + ord(q[3]) - 65]
            n += 1
    new = sum(1 for i, c in enumerate(pt) if c != "." and i not in CRIBS)
    return (tot / n if n else -99.0), pt, new


def run(ct, alphas, W, logp, label, show=3, detail=False):
    """Every fitting pair, ranked by how English the newly revealed letters are. Pairs that reveal
    fewer than 20 letters beyond the clue words say nothing and are only counted."""
    total, best, counts, thin = 0, [], {}, 0
    for per in range(1, MAXPER + 1):
        s = survivors(ct, W, per)
        if s is None:
            continue
        counts[per] = len(s)
        total += len(s)
        for kind, i, j in s:
            sc, pt, new = decrypt(ct, kind, alphas[i], alphas[j], per, logp)
            if new >= 20:
                best.append((sc, per, kind, alphas[i], alphas[j], new, pt))
            else:
                thin += 1
    best.sort(reverse=True)
    print(f"  {label}: {total} fitting pairs; by key length {dict((p, c) for p, c in counts.items() if c)}; "
          f"{len(best)} reveal 20+ new letters")
    for sc, per, kind, x, y, new, pt in best[:show]:
        print(f"    {sc:6.2f}  length {per:2} {kind:4} X={x} Y={y}  ({new} new letters)\n            {pt}")
    if detail:
        for per in sorted({b[1] for b in best}):
            sc, _, kind, x, y, new, pt = next(b for b in best if b[1] == per)
            print(f"    best at length {per:2}: {sc:6.2f} ({new} new letters)  {pt}")
    return total, best


def plant(rnd, x, y, keyword, kind="vig"):
    pt = list((kryptos.K2_PT + kryptos.K3_PT)[rnd.randrange(500):][:97])
    for p, ch in CRIBS.items():
        pt[p] = ch
    xi = {c: i for i, c in enumerate(x)}
    k = [AZ.index(c) for c in keyword]
    return "".join(y[(xi[p] + k[i % len(k)]) % 26] if kind == "vig" else y[(k[i % len(k)] - xi[p]) % 26]
                   for i, p in enumerate(pt)), "".join(pt)


def main():
    quad = next((f for f in (DATA / "quadgrams.bin", DATA / "quadgrams_local.bin") if f.exists()), None)
    if quad is None:
        raise SystemExit("no quadgram model: run checks/quadgrams_local.py")
    logp = np.fromfile(quad, dtype=np.float32)
    alphas = alphabets()
    W = np.stack([index_of(a) for a in alphas])
    tested = [p for p in range(1, MAXPER + 1) if len(pairs_for(p)[0]) >= MINC]
    print(f"{len(alphas)} keyed alphabets -> {len(alphas) ** 2:.2e} ordered pairs, Vigenere and Beaufort")
    print(f"key lengths with at least {MINC} constraints: {tested}")
    print("== K4")
    run(kryptos.K4, alphas, W, logp, "K4", detail=True)
    rnd = random.Random(2026)
    print("== Planted: two dictionary keywords and a keyword key, English plaintext with the clue words in place")
    for wx, wy, kw, kind in (("BERLIN", "CLOCK", "PALIMPSEST", "vig"), ("SHADOW", "FORCES", "LUCIDMEMORY", "beau"),
                             ("PHARAOH", "DESERT", "INVISIBLE", "vig"), ("COMPASS", "LODESTONE", "MAGNETICFIELDEASTWARD", "vig")):
        assert keyed(wx) in alphas and keyed(wy) in alphas
        ct, pt = plant(rnd, keyed(wx), keyed(wy), kw, kind)
        tot, best = run(ct, alphas, W, logp, f"{wx}/{wy}, key {kw}, {kind}", show=1)
        ok = bool(best) and all(a == b for a, b in zip(best[0][6], pt) if a != ".")
        print(f"      top-ranked pair gives the planted plaintext at every letter it reveals: {ok}")
    print("== Random ciphertexts with the same clue letters")
    for i in range(5):
        run("".join(rnd.choice(AZ) for _ in range(97)), alphas, W, logp, f"random {i + 1}", show=1)
    print("Scores are over the letters the pair newly reveals: English is about -4.2 to -4.6, noise about -6.5 or worse.")


if __name__ == "__main__":
    main()
