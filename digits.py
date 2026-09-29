"""Digit-shift ciphers (Gronsfeld, Gromark and any digit keystream): every forced shift must be 0..9.

For each arrangement x (plaintext alphabet) / y (ciphertext alphabet) over AZ, KA and every
dictionary keyed alphabet, and each direction (C = P + d, or C = P - d), check whether all 24
crib shifts are digits. A random alphabet passes with odds (10/26)^24 ~ 1e-10.
Any survivor would then need its digit keystream checked (e.g. Gromark's lagged-Fibonacci primer).
"""
import os
import re
import numpy as np
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA
from attacks import keyed
from dictalpha import alphabet_index, PL

def main(ct=K4, extra_words=()):
    """Returns the list of alphabet arrangements whose 24 forced shifts are all digits."""
    words = set()
    for f in [p for p in ("/usr/share/dict/words", "/usr/share/dict/propernames") if os.path.exists(p)]:
        for line in open(f):
            w = line.strip().upper()
            if re.fullmatch(r"[A-Z]+", w): words.add(w)
    words.update(extra_words)
    alphas = sorted({keyed(w) for w in words} | {AZ, KA})
    Wd = np.stack([alphabet_index(a) for a in alphas])
    fixed = {"AZ": np.broadcast_to(alphabet_index(AZ), Wd.shape), "KA": np.broadcast_to(alphabet_index(KA), Wd.shape)}
    arr = {"x=AZ y=W": (fixed["AZ"], Wd), "x=KA y=W": (fixed["KA"], Wd), "x=W y=AZ": (Wd, fixed["AZ"]),
           "x=W y=KA": (Wd, fixed["KA"]), "x=W y=W": (Wd, Wd)}
    hits = []
    for name, (X, Y) in arr.items():
        cl = np.array([ord(ct[p]) - 65 for p in CRIB_POS])
        d = (Y[:, cl].astype(int) - X[:, PL].astype(int)) % 26
        for sense, v in (("C=P+d", d), ("C=P-d", (-d) % 26)):
            ok = np.all(v <= 9, axis=1)
            best = int(np.max(np.sum(v <= 9, axis=1)))
            print(f"{name:10} {sense}: {int(ok.sum())} alphabets pass all 24 (best any alphabet: {best}/24)")
            for i in np.nonzero(ok)[0]:
                hits.append((name, sense, alphas[i], v[i]))
    for name, sense, a, v in hits:
        print("SURVIVOR", name, sense, a, list(v))   # would then need a Gromark primer / keystream test
    print("digit-filter survivors:", len(hits))
    return hits


if __name__ == "__main__":
    main()
