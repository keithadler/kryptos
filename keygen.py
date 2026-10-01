"""Keystreams that are generated rather than repeated: is the key the clues force a formula's output?

For each of the 8 tableau families the clues force 24 key letters. A periodic key is already
eliminated (attacks.py). These are the other ways to make a key by hand without a long text:

  poly       k_i = a + b*i + c*C(i,2) + d*C(i,3)   every integer-valued cubic in the position,
             which includes steps that grow by a fixed amount (triangular numbers)
  recur      k_i = al*k_{i-a} + be*k_{i-b} + ga     two-term recurrence over 26 letters
             (the Gromark / Fibonacci shape; digits.py covers the digit version)
  interrupt  a repeating key that restarts after a chosen ciphertext letter, at or after a chosen
             plaintext letter, or at each word
  morse      the Morse phrases on the entrance slabs, in every order and spelling, as the key
  cities     a key strung together from city names: does any forced key fragment contain a long
             piece of a name? Names: the time-zone database (English) and the 147 entries on the
             Berlin World Clock (German, data/weltzeituhr_cities.txt). The clock's list is also
             tried as a running key in face order, and by initials.

usage: python3 keygen.py [poly] [recur] [interrupt] [morse] [cities]     (default: all)
"""
import itertools
import math
import os
import pathlib
import unicodedata
import random
import sys
import numpy as np
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ, KA

K4 = kryptos.K4
ALPH = {"AZ": AZ, "KA": KA}
FAMS = [(k, xn, yn) for k in ("vig", "beau") for xn in ALPH for yn in ALPH]
NP = np.array(CRIB_POS)


def ix(a):
    return {c: i for i, c in enumerate(a)}


def forced(ct, kind, xn, yn):
    """The 24 key values the clues force for one family."""
    x, y = ix(ALPH[xn]), ix(ALPH[yn])
    return np.array([(y[ct[p]] - x[CRIBS[p]]) % 26 if kind == "vig" else (y[ct[p]] + x[CRIBS[p]]) % 26
                     for p in CRIB_POS])


def random_ct(rnd):
    return "".join(rnd.choice(AZ) for _ in range(97))


def plant(rnd, keystream, kind="vig"):
    """Random ciphertext whose clue positions are the clue words under KA/KA with this keystream."""
    a, ct = ix(KA), list(random_ct(rnd))
    for p in CRIB_POS:
        ct[p] = KA[(a[CRIBS[p]] + keystream[p]) % 26 if kind == "vig" else (keystream[p] - a[CRIBS[p]]) % 26]
    return "".join(ct)


# ---------------------------------------------------------------- polynomial in the position
_CO = np.array(list(itertools.product(range(26), repeat=3)))                       # b, c, d
_BASE = (_CO @ np.stack([NP, NP * (NP - 1) // 2, NP * (NP - 1) * (NP - 2) // 6]) % 26)   # (26^3, 24)


def poly(ct):
    hits = []
    for kind, xn, yn in FAMS:
        d = (forced(ct, kind, xn, yn)[None, :] - _BASE) % 26        # must be the constant a
        for i in np.nonzero(np.all(d == d[:, :1], axis=1))[0]:
            hits.append((kind, xn, yn, int(d[i, 0]), *map(int, _CO[i])))
    return hits


def test_poly(rnd):
    print("== Polynomial keystream a + b*i + c*C(i,2) + d*C(i,3), 26^4 keys per family")
    print(f"  K4 survivors: {poly(K4) or 'none'}")
    print(f"  random ciphertexts x20: {sum(len(poly(random_ct(rnd))) for _ in range(20))} survivors")
    ct = plant(rnd, [5 + 3 * i + 7 * (i * (i - 1) // 2) for i in range(97)])
    print(f"  planted 5 + 3i + 7C(i,2): {poly(ct)}")


# ---------------------------------------------------------------- linear recurrence
_ABG = np.array(list(itertools.product(range(26), repeat=3)))                      # al, be, ga


def recur(ct, maxlag=9):
    hits, tests = [], 0
    for kind, xn, yn in FAMS:
        f = dict(zip(CRIB_POS, forced(ct, kind, xn, yn)))
        for a, b in itertools.combinations(range(1, maxlag + 1), 2):
            tri = np.array([(f[p], f[p - a], f[p - b]) for p in CRIB_POS if p - a in f and p - b in f])
            pred = (_ABG[:, 0:1] * tri[:, 1] + _ABG[:, 1:2] * tri[:, 2] + _ABG[:, 2:3]) % 26
            tests += len(_ABG)
            for i in np.nonzero(np.all(pred == tri[:, 0], axis=1))[0]:
                hits.append((kind, xn, yn, a, b, *map(int, _ABG[i]), len(tri)))
    return hits, tests


def test_recur(rnd):
    print("== Two-term linear recurrence k_i = al*k_(i-a) + be*k_(i-b) + ga, lags a < b <= 9")
    h, n = recur(K4)
    print(f"  K4: {n} tests, survivors: {h or 'none'}")
    print(f"  random ciphertexts x10: {[len(recur(random_ct(rnd))[0]) for _ in range(10)]} survivors")
    ks = [3, 17, 8, 22, 5]
    for i in range(5, 97):
        ks.append((ks[i - 2] + ks[i - 5]) % 26)
    print(f"  planted k_i = k_(i-2) + k_(i-5): {recur(plant(rnd, ks))[0]}")


# ---------------------------------------------------------------- interrupted keys
def consistent(idx, vals):
    """Equal key indices must force equal key values. Returns (ok, constraints checked)."""
    seen, checks = {}, 0
    for j, v in zip(idx, vals):
        if j in seen:
            checks += 1
            if seen[j] != v:
                return False, checks
        else:
            seen[j] = v
    return True, checks


def ct_interrupt(ct, maxper=40):
    """Key restarts after every ciphertext letter X. The whole index sequence is known from the ciphertext."""
    hits, tests = [], 0
    F = {f: forced(ct, *f) for f in FAMS}
    for X in AZ:
        raw, j = [], 0
        for c in ct:
            raw.append(j)
            j = 0 if c == X else j + 1
        for per in range(1, maxper + 1):
            idx = [raw[p] % per for p in CRIB_POS]
            if len(set(idx)) == len(idx):
                continue                                   # no two clue letters share a key letter
            for f, vals in F.items():
                tests += 1
                ok, checks = consistent(idx, vals)
                if ok:
                    hits.append((X, per, *f, checks))
    return hits, tests


def pt_interrupt(ct, maxper=26):
    """Key restarts at (mode 0) or after (mode 1) every plaintext letter X. The plaintext between
    the clue runs is unknown, so each run starts at an unknown point in the key."""
    hits, tests = [], 0
    F = {f: forced(ct, *f) for f in FAMS}
    runs = [[p for p in CRIB_POS if p < 50], [p for p in CRIB_POS if p > 50]]
    for X in sorted(set(CRIBS[p] for p in CRIB_POS)):
        for mode in (0, 1):
            for per in range(2, maxper + 1):
                for starts in itertools.product(range(per), repeat=2):
                    idx = []
                    for run, j in zip(runs, starts):
                        for p in run:
                            if mode == 0 and CRIBS[p] == X:
                                j = 0
                            idx.append(j % per)
                            j = 0 if mode == 1 and CRIBS[p] == X else j + 1
                    if len(set(idx)) == len(idx):
                        continue
                    for f, vals in F.items():
                        tests += 1
                        ok, checks = consistent(idx, vals)
                        if ok:
                            hits.append((X, mode, per, starts, *f, checks))
    return hits, tests


def word_restart():
    """Key restarts at each word, with ANY alphabet per key letter (not just the 8 families):
    the same plaintext letter at the same place in two words must give the same ciphertext letter."""
    words = [(21, "EAST"), (25, "NORTHEAST"), (63, "BERLIN"), (69, "CLOCK")]
    out = {}
    for per in range(1, 10):                               # 9 = longest word; longer keys behave the same
        seen, bad = {}, None
        for s, w in words:
            for i, ch in enumerate(w):
                c = seen.setdefault((i % per, ch), K4[s + i])
                if c != K4[s + i]:
                    bad = f"{ch} at key letter {i % per + 1} gives both {c} and {K4[s + i]}"
        out[per] = bad
    return out


def by_checks(hits):
    n = {}
    for h in hits:
        n[h[-1]] = n.get(h[-1], 0) + 1
    return dict(sorted(n.items())) or "none"


def test_interrupt(rnd):
    print("== Interrupted key: restart after ciphertext letter X, key length 1-40")
    h, n = ct_interrupt(K4)
    print(f"  K4: {n} constrained tests; survivors by constraints held: {by_checks(h)}")
    print(f"  random ciphertexts x10: {[by_checks(ct_interrupt(random_ct(rnd))[0]) for _ in range(10)]}")
    a, key, ks, j = ix(KA), [ix(KA)[c] for c in "PALIMPSEST"], [], 0
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p in CRIB_POS:
        pt[p] = CRIBS[p]
    ct = []
    for i in range(97):
        ct.append(KA[(a[pt[i]] + key[j % 10]) % 26])
        j = 0 if ct[-1] == "S" else j + 1
    best = max(ct_interrupt("".join(ct))[0], key=lambda h: h[-1])
    print(f"  planted (PALIMPSEST, restart after ciphertext S): best survivor {best}")

    print("== Interrupted key: restart at/after plaintext letter X (X in the clue words), key length 2-26")
    h, n = pt_interrupt(K4)
    print(f"  K4: {n} constrained tests; survivors by constraints held: {by_checks(h)}")
    print(f"  random ciphertexts x5: {[by_checks(pt_interrupt(random_ct(rnd))[0]) for _ in range(5)]}")
    ks, j = [], 3
    for i in range(97):
        ks.append(key[j % 10])
        j = 0 if pt[i] == "T" else j + 1
    ct = "".join(KA[(a[pt[i]] + ks[i]) % 26] for i in range(97))
    best = max(pt_interrupt(ct)[0], key=lambda h: h[-1])
    print(f"  planted (PALIMPSEST, restart after plaintext T): best survivor {best}")

    print("== Key restarting at each word (EAST / NORTHEAST / BERLIN / CLOCK), any alphabet per key letter")
    for per, bad in word_restart().items():
        print(f"  key length {per}{'+' if per == 9 else ' '}: {'contradiction: ' + bad if bad else 'consistent'}")


# ---------------------------------------------------------------- Morse phrases as the key
def morse_texts():
    """The slab phrases with and without the stray E's, three readings of INTERPRETATI?, every order
    of the five phrases, SOS and RQ appended or not; forward and reversed."""
    full = ["EEVIRTUALLYEEEEEEEINVISIBLE", "DIGETALEEEINTERPRETATI?", "EESHADOWEEFORCESEEEEE",
            "LUCIDEEEMEMORYE", "TISYOURPOSITIONE"]
    bare = ["VIRTUALLYINVISIBLE", "DIGETALINTERPRETATI?", "SHADOWFORCES", "LUCIDMEMORY", "TISYOURPOSITION"]
    out = {}
    for base in (full, bare):
        for end in ("T", "U", "ON"):
            ph = [p.replace("?", end) for p in base]
            for perm in itertools.permutations(range(5)):
                for tail in ("", "SOS", "RQ", "SOSRQ", "RQSOS"):
                    t = "".join(ph[i] for i in perm) + tail
                    out[t] = out[t[::-1]] = None
    return list(out)


def morse(ct, texts):
    """key_i = T[(o + i) mod len(T)] for every offset o: how many of the 24 forced key letters match?"""
    need = {(*f, kn): np.array([ord(ALPH[kn][v]) - 65 for v in forced(ct, *f)]) for f in FAMS for kn in ALPH}
    best, where, tests, hist = 0, None, 0, np.zeros(25, dtype=np.int64)
    for t in texts:
        a = np.frombuffer(t.encode(), dtype=np.uint8) - 65
        K = a[(np.arange(len(t))[:, None] + NP[None, :]) % len(t)]          # (offsets, 24)
        for fam, nd in need.items():
            m = (K == nd).sum(axis=1)
            tests += len(t)
            hist += np.bincount(m, minlength=25)
            if m.max() > best:
                best, where = int(m.max()), (fam, int(m.argmax()), t)
    return best, where, tests, hist


def test_morse(rnd):
    texts = morse_texts()
    print(f"== Morse phrases as a running or repeating key: {len(texts)} orderings and spellings, every offset")
    best, where, tests, hist = morse(K4, texts)
    print(f"  K4: {tests} tests, best {best}/24 key letters ({where[0]}, offset {where[1]})")
    print(f"  tests reaching m matches: { {m: int(hist[m:].sum()) for m in (6, 7, 8, 9) } }")
    tail = {m: tests * sum(math.comb(24, j) * 25 ** (24 - j) for j in range(m, 25)) / 26 ** 24 for m in (6, 7, 8, 9)}
    print(f"  expected by chance:        { {m: round(v, 1) for m, v in tail.items()} }")
    t, a = texts[1234], ix(KA)
    ct = plant(rnd, [a[t[(17 + i) % len(t)]] for i in range(97)])
    best, where, _, _ = morse(ct, texts)
    print(f"  planted (KA Vigenere, offset 17): best {best}/24 ({where[0]}, offset {where[1]})")


# ---------------------------------------------------------------- city names as the key
def city_names():
    """City names of the time-zone database (English spellings), letters only."""
    names = set()
    for root, _, files in os.walk("/usr/share/zoneinfo"):
        if root != "/usr/share/zoneinfo":
            names.update(n for n in ("".join(c for c in f.upper() if "A" <= c <= "Z") for f in files) if len(n) >= 4)
    return names


PRE_1997 = {"St. Petersburg": "Leningrad", "Almaty": "Alma Ata", "Pressburg": "Bratislava",
            "Nischnij Nowgorod": "Gorki", "Jekaterinburg": "Swerdlowsk", "Bischkek": "Frunse",
            "Aschgabat": "Aschchabad", "Santafé de Bogotá": "Bogotá", "Wilna": "Vilnius"}


def letters_de(name, expand):
    """A-Z only. expand: AE/OE/UE for umlauts (the hand-cipher way); otherwise plain A/O/U."""
    if expand:
        name = name.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "AE", "Ö": "OE", "Ü": "UE", "ß": "ss"}))
    name = unicodedata.normalize("NFD", name)
    return "".join(c for c in name.upper() if "A" <= c <= "Z")


def clock_faces():
    """The World Clock's entries, one list per face, UTC+1 first."""
    f = pathlib.Path(__file__).with_name("data") / "weltzeituhr_cities.txt"
    return [[n.strip() for n in l.split(",")] for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]


def clock_names():
    """Every spelling tried: as listed and with the names the clock carried before 1997."""
    names = set()
    for n in [n for face in clock_faces() for n in face] + list(PRE_1997.values()):
        for expand in (True, False):
            names.add(letters_de(n, expand))
            names.update(w for w in (letters_de(part, expand) for part in n.replace("-", " ").split()) if len(w) >= 4)
    return {n for n in names if len(n) >= 3}


def clock_streams():
    """The list as one key text: face order from each starting face, east or west, cities in listed
    order or reversed, post- or pre-1997 names, umlauts both ways; whole names and initials."""
    out = {}
    faces = clock_faces()
    for era in ("1997", "1969"):
        fs = [[PRE_1997.get(n, n) if era == "1969" else n for n in face] for face in faces]
        for start in range(24):
            for step in (1, -1):
                for rev in (0, 1):
                    order = [fs[(start + step * i) % 24][::-1] if rev else fs[(start + step * i) % 24] for i in range(24)]
                    flat = [n for face in order for n in face]
                    for expand in (True, False):
                        out["".join(letters_de(n, expand) for n in flat)] = None
                        out["".join(letters_de(n, expand)[0] for n in flat)] = None
    return list(out)


def longest_piece(ct, blob):
    """Longest stretch of any forced key fragment (either run, any family, key read in A-Z or KRYPTOS)
    that occurs inside a name."""
    best = (0, "")
    for f in FAMS:
        vals = forced(ct, *f)
        for ka in ALPH.values():
            for neg in (1, -1):                              # -1: variant Beaufort
                s = "".join(ka[(neg * v) % 26] for v in vals)
                for frag in (s[:13], s[13:]):
                    for L in range(len(frag), best[0], -1):
                        hit = next((frag[i:i + L] for i in range(len(frag) - L + 1) if frag[i:i + L] in blob), None)
                        if hit:
                            best = (L, hit)
                            break
    return best


def test_cities(rnd):
    names = city_names()
    print(f"== Key strung together from city names: {len(names)} time-zone database names (English spellings)")
    if not names:
        print("  no /usr/share/zoneinfo here: skipped")
        return
    blob = "|".join(sorted(names))
    print(f"  K4: longest piece of a key fragment inside a city name: {longest_piece(K4, blob)}")
    print(f"  random ciphertexts x20: {sorted(longest_piece(random_ct(rnd), blob)[0] for _ in range(20))}")
    key = "CAIROMOSCOWHAVANATOKYOBERLINWARSAWLISBONDELHIBAGHDADATHENSPRAGUEHONOLULUANCHORAGEDENVERCHICAGOLIMACARACAS"
    a = ix(KA)
    print(f"  planted (KA Vigenere, key CAIROMOSCOWHAVANA...): {longest_piece(plant(rnd, [a[c] for c in key]), blob)}")

    names = clock_names()
    print(f"== Key strung together from the Berlin World Clock's place names, any order: {len(names)} spellings")
    blob = "|".join(sorted(names))
    print(f"  K4: longest piece of a key fragment inside a name: {longest_piece(K4, blob)}")
    print(f"  random ciphertexts x20: {sorted(longest_piece(random_ct(rnd), blob)[0] for _ in range(20))}")
    key = "KAIROMOSKAUHAVANNATOKYOBERLINWARSCHAULISSABONNEWDELHIBAGDADATHENPRAGHONOLULUANCHORAGEDENVERLIMACARACASPEKING"
    print(f"  planted (KA Vigenere, key KAIROMOSKAUHAVANNA...): {longest_piece(plant(rnd, [a[c] for c in key]), blob)}")

    texts = clock_streams()
    print(f"== The clock's list as a running key in face order: {len(texts)} readings (start face, direction, era, "
          f"umlauts; names or initials), every offset, wrapping")
    best, where, tests, hist = morse(K4, texts)
    print(f"  K4: {tests} tests, best {best}/24 key letters ({where[0]}, offset {where[1]})")
    print(f"  tests reaching m matches: { {m: int(hist[m:].sum()) for m in (6, 7, 8, 9) } }")
    tail = {m: tests * sum(math.comb(24, j) * 25 ** (24 - j) for j in range(m, 25)) / 26 ** 24 for m in (6, 7, 8, 9)}
    print(f"  expected by chance:        { {m: round(v, 1) for m, v in tail.items()} }")
    t = texts[40]
    best, where, _, _ = morse(plant(rnd, [a[t[(200 + i) % len(t)]] for i in range(97)]), texts)
    print(f"  planted (KA Vigenere, offset 200): best {best}/24 ({where[0]}, offset {where[1]})")


if __name__ == "__main__":
    which = sys.argv[1:] or ["poly", "recur", "interrupt", "morse", "cities"]
    rnd = random.Random(2026)
    for name in which:
        {"poly": test_poly, "recur": test_recur, "interrupt": test_interrupt, "morse": test_morse,
         "cities": test_cities}[name](rnd)
