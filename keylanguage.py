"""Running key from ANY English or German text: is the key the clues force natural language?

runkey.py tries particular books. This asks the general question. If K4 were enciphered with a
running key taken from prose, the key letters forced at the clue positions (a run of 13 and a run
of 11) would themselves be prose, whatever the book. They are scored with quadgram statistics under:
  - the 8 fixed tableau families (alphabets A-Z and KRYPTOS), and
  - every dictionary-word keyed alphabet W in five arrangements (as dictalpha.py),
with Vigenere, Beaufort and variant Beaufort, and the key letter read in each alphabet in play.

Controls: real prose as planted running keys; random ciphertexts carrying the same clue letters;
and the score range of real prose fragments of the same shape.

usage: python3 keylanguage.py [english|german]
English needs data/quadgrams.bin (quadgrams.py, after checks/fetch_texts.sh) or
data/quadgrams_local.bin; German needs data/quadgrams_de_local.bin (checks/quadgrams_local.py).
German is written the hand-cipher way: AE, OE, UE, SS.
"""
import pathlib
import random
import sys
import numpy as np
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ, KA, K2_PT, K3_PT
from attacks import keyed

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
LOGP = None
PL = np.array([ord(CRIBS[p]) - 65 for p in CRIB_POS])
# contiguous runs of clue positions, as slices into the 24 (or more, under a guess) forced key letters
RUNS, _s = [], 0
for _i in range(1, len(CRIB_POS) + 1):
    if _i == len(CRIB_POS) or CRIB_POS[_i] != CRIB_POS[_i - 1] + 1:
        if _i - _s >= 4:
            RUNS.append(slice(_s, _i))
        _s = _i


def qscore(K):
    """K: (n, clue letters) key letters as 0..25. Mean log10 quadgram probability over the runs."""
    K = K.astype(np.int64)
    parts = []
    for r in RUNS:
        a = K[:, r]
        parts.append(LOGP[((a[:, :-3] * 26 + a[:, 1:-2]) * 26 + a[:, 2:-1]) * 26 + a[:, 3:]])
    return np.concatenate(parts, axis=1).mean(axis=1)


def index_of(alpha):
    out = np.empty(26, dtype=np.int16)
    for i, c in enumerate(alpha):
        out[ord(c) - 65] = i
    return out


def letters_of(alpha):
    return np.array([ord(c) - 65 for c in alpha], dtype=np.int16)


def search(ct, alphas):
    """Best-scoring key fragments. alphas = [KA] runs the 8 fixed families; a dictionary list runs
    the five keyed arrangements. Returns (tests, [(score, family, alphabet, key letters)])."""
    CL = np.array([ord(ct[p]) - 65 for p in CRIB_POS])
    W, WL = np.stack([index_of(a) for a in alphas]), np.stack([letters_of(a) for a in alphas])
    side = {"AZ": (np.broadcast_to(index_of(AZ), W.shape), np.broadcast_to(letters_of(AZ), W.shape)),
            "KA": (np.broadcast_to(index_of(KA), W.shape), np.broadcast_to(letters_of(KA), W.shape)),
            "W": (W, WL)}
    fixed = len(alphas) == 1
    arrangements = [("AZ", "AZ"), ("AZ", "KA"), ("KA", "AZ"), ("KA", "KA")] if fixed else \
                   [("W", "AZ"), ("AZ", "W"), ("W", "W"), ("KA", "W"), ("W", "KA")]
    best, tests = [], 0
    for xn, yn in arrangements:
        xv, yv = side[xn][0][:, PL], side[yn][0][:, CL]
        for kind, ki in (("vig", (yv - xv) % 26), ("beau", (yv + xv) % 26), ("varbeau", (xv - yv) % 26)):
            for kn in sorted({xn, yn, "AZ"}):                # which alphabet turns the shift into a key letter
                KL = np.take_along_axis(side[kn][1], ki, axis=1)
                sc = qscore(KL)
                tests += len(alphas)
                i = int(np.argmax(sc))
                best.append((float(sc[i]), f"{kind} P:{xn} C:{yn} key:{kn}",
                             "" if fixed else alphas[i], "".join(AZ[v] for v in KL[i])))
    return tests, sorted(best, reverse=True)


def show(label, tests, best, n=1):
    print(f"  {label}: {tests} tests")
    for sc, fam, alpha, key in best[:n]:
        frags = " | ".join(key[r] for r in RUNS)
        print(f"    {sc:6.2f}  {fam:28} {alpha:26}  {frags}")


def plant(rnd, x, y, kind, keytext, off):
    """Random plaintext with the clue words in place, enciphered with keytext[off:] as running key."""
    pt = [rnd.choice(AZ) for _ in range(97)]
    for p, ch in CRIBS.items():
        pt[p] = ch
    xi = {c: i for i, c in enumerate(x)}
    out = []
    for i, p in enumerate(pt):
        k = xi[keytext[off + i]]
        out.append(y[(xi[p] + k) % 26] if kind == "vig" else y[(k - xi[p]) % 26])
    return "".join(out)


def dictionary(extra=None):
    words = set()
    for f in ("/usr/share/dict/words", "/usr/share/dict/propernames", extra):
        if f and pathlib.Path(f).exists():
            for w in open(f):
                w = w.strip().upper()
                if w.isascii() and w.isalpha() and 4 <= len(w) <= 20:
                    words.add(w)
    return sorted({keyed(w) for w in words})


def main(lang):
    global LOGP
    if lang == "german":
        sys.path.insert(0, str(ROOT / "checks"))
        from quadgrams_local import german_letters, wikitext_prose
        models, extra = [DATA / "quadgrams_de_local.bin"], DATA / "words_de_local.txt"
        prose = german_letters(wikitext_prose(DATA / "weltzeituhr_de.txt"))    # held out of the model
        source, words = "the German Weltzeituhr article", ("WELTZEITUHR", "ALEXANDERPLATZ", "MAUER")
    else:
        models, extra = [DATA / "quadgrams.bin", DATA / "quadgrams_local.bin"], None
        prose = K2_PT + K3_PT
        source, words = "K2/K3 plaintext", ("TELESCOPE", "PALIMPSEST", "SHADOW")
    quad = next((f for f in models if f.exists()), None)
    if quad is None:
        raise SystemExit("no quadgram model: run checks/quadgrams_local.py" + (" german" if lang == "german" else ""))
    LOGP = np.fromfile(quad, dtype=np.float32)
    print(f"language: {lang}; quadgram model: {quad.name}")
    rnd = random.Random(2026)
    span = CRIB_POS[-1] - CRIB_POS[0] + 1
    ref = np.sort(qscore(np.array([[ord(prose[o + p - CRIB_POS[0]]) - 65 for p in CRIB_POS]
                                   for o in range(0, len(prose) - span, 3)])))
    print(f"== {lang.capitalize()} key fragments of the same shape ({source}, {len(ref)} samples): "
          f"worst {ref[0]:.2f}, median {ref[len(ref) // 2]:.2f}, best {ref[-1]:.2f}")

    print("== Fixed alphabets (A-Z and KRYPTOS), 8 families and variant Beaufort")
    t, best = search(kryptos.K4, [KA])
    show("K4", t, best, n=3)
    fixed_best = best[0][0]
    offs = [rnd.randrange(len(prose) - 97) for _ in range(3)]
    for (x, y, kind, label), off in zip(((AZ, AZ, "vig", "A-Z Vigenere"), (KA, KA, "vig", "KRYPTOS Vigenere"),
                                         (KA, KA, "beau", "KRYPTOS Beaufort")), offs):
        show(f"planted {label}, {source} as key", *search(plant(rnd, x, y, kind, prose, off), [KA]))
    print(f"  -> K4's best ({fixed_best:.2f}) is {'below' if fixed_best < ref[0] else 'NOT below'} the worst "
          f"{lang.capitalize()} fragment ({ref[0]:.2f}): "
          f"{'ELIMINATED' if fixed_best < ref[0] else 'NOT eliminated'} for any {lang.capitalize()} key text")

    alphas = dictionary(extra)
    print(f"== Dictionary-keyed alphabets: {len(alphas)} alphabets, 5 arrangements")
    t, best = search(kryptos.K4, alphas)
    show("K4", t, best, n=3)
    k4best = best[0][0]
    for word, kind in zip(words, ("beau", "vig", "vig")):
        w = keyed(word)
        t, best = search(plant(rnd, w, w, kind, prose, rnd.randrange(len(prose) - 97)), alphas)
        show(f"planted {word} {kind} (Quagmire III), {source} as key", t, best)
        print(f"      right alphabet found: {best[0][2] == w}")
    rb = []
    for i in range(8):
        t, best = search("".join(rnd.choice(AZ) for _ in range(97)), alphas)
        rb.append(best[0][0])
    print(f"  random ciphertexts x8, best score each: {sorted(round(r, 2) for r in rb)}")
    power = float((ref > max(rb)).mean())
    print(f"  -> K4's best ({k4best:.2f}) is {'inside' if k4best <= max(rb) else 'ABOVE'} the random range. "
          f"{power:.0%} of {lang.capitalize()} fragments would have beaten every random best, so this is a "
          f"no-signal result at about that power, not a proof.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "english")
