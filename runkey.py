"""Running-key search over large texts, with mismatch tolerance.

For each substitution family, the cribs force 24 key letters at fixed positions (two runs of 13 and
11, 42 apart). A running key from text T at offset o supplies key letter T[o + i] at position i.
We count, at every offset, how many of the 24 forced key letters the text supplies.

Chance: one position matches with p = 1/26, so ~1 match of 24 is typical. 12+ matches has
probability ~2.8e-11 per test; across ~1e9 tests that is ~0.03 expected. Anything >= 12 is signal,
and tolerance covers OCR errors and a Sanborn slip.

Texts: data/running_keys/*.txt (letters only, forward and reversed).
"""
import pathlib
import sys
import numpy as np
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA
import attacks

THRESH = 12
POS = np.array(CRIB_POS)


def ai(alpha):
    out = np.empty(26, dtype=np.int8)
    for i, c in enumerate(alpha):
        out[ord(c) - 65] = i
    return out


def load(path):
    raw = path.read_text(errors="ignore").upper()
    # drop Project Gutenberg boilerplate if present
    s, e = raw.find("*** START OF"), raw.find("*** END OF")
    if s != -1:
        raw = raw[raw.find("\n", s) + 1: e if e != -1 else None]
    b = np.frombuffer(raw.encode("ascii", "ignore"), dtype=np.uint8)
    b = b[(b >= 65) & (b <= 90)] - 65
    return b.astype(np.int8)


def main():
    texts = {}
    for f in sorted(pathlib.Path(__file__).with_name("data").joinpath("running_keys").glob("*.txt")):
        t = load(f)
        texts[f.stem] = t
        texts[f.stem + " (reversed)"] = t[::-1].copy()
    fams = [(k, xn, yn) for k in ("vig", "beau") for xn in ("AZ", "KA") for yn in ("AZ", "KA")]
    A = {"AZ": ai(AZ), "KA": ai(KA)}
    tests = 0
    best_overall = []
    for name, t in texts.items():
        L = len(t) - POS[-1]
        best = (0, None)
        for kind, xn, yn in fams:
            x, y = A[xn], A[yn]
            p = np.array([x[ord(CRIBS[q]) - 65] for q in CRIB_POS])
            c = np.array([y[ord(K4[q]) - 65] for q in CRIB_POS])
            need = (c - p) % 26 if kind == "vig" else (c + p) % 26
            for kan in ("x", "y"):
                keyidx = (x if kan == "x" else y)[t]           # text letters as key shifts
                score = np.zeros(L, dtype=np.int16)
                for j, pos in enumerate(POS):
                    score += keyidx[pos: pos + L] == need[j]
                tests += L
                m = int(score.max())
                if m > best[0]:
                    o = int(score.argmax())
                    best = (m, f"{kind}-P{xn}-C{yn} key via {kan} offset {o}")
                for o in np.nonzero(score >= THRESH)[0]:
                    print(f"HIT {name}: {int(score[o])}/24 {kind}-P{xn}-C{yn} key via {kan} offset {o}")
        best_overall.append((best[0], name, best[1]))
        print(f"{name:34} {len(t):9} letters  best {best[0]:2}/24  ({best[1]})")
    print(f"\n{tests:.3g} offset tests; threshold {THRESH}/24")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        THRESH = int(sys.argv[1])
    main()
