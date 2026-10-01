"""K1-K3 solutions as a running key, with an UNKNOWN alphabet on one side (any of 26!).

  y(C_i) = x(P_i) + t(K_{o+i})    (vig; beau: y(C_i) = t(K) - x(P_i))
Known side alphabet in {AZ, KA}; key letters valued via t in {AZ, KA}; offset o anywhere.
Unknown plaintext alphabet x: every crib pins x(P_i); repeated plaintext letters in the cribs must
agree, and different letters must get different values. Unknown ciphertext alphabet y: the same
with the cribs' ciphertext letters. With 11+ repeats in the cribs, chance survival is ~26^-11 per test.

A third pass leaves both alphabets fixed (A-Z or KRYPTOS) and frees t instead: ANY lookup table
from key letter to shift, so equal key letters must force equal shifts. English text repeats
letters often enough that 24 key letters carry about 10 such constraints.

Texts: K1/K2/K3 plaintexts as carved, with corrected spellings, with K2's pre-2006 ending
("IDBYROWS"), joined in order, and the carved K1-K3 ciphertext; each forward and reversed.
"""
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA, K1_PT, K2_PT, K3_PT
import attacks

IX = {"AZ": {c: i for i, c in enumerate(AZ)}, "KA": {c: i for i, c in enumerate(KA)}}


def texts():
    k1c = K1_PT.replace("IQLUSION", "ILLUSION")
    k2c = K2_PT.replace("UNDERGRUUND", "UNDERGROUND")
    k3c = K3_PT.replace("DESPARATLY", "DESPERATELY")
    k2old = K2_PT[: K2_PT.rindex("XLAYERTWO")] + "IDBYROWS"
    left = "".join(ch for ch in open("data/sculpture_left.txt").read() if "A" <= ch <= "Z")
    t = {
        "K1": K1_PT, "K2": K2_PT, "K3": K3_PT, "K1K2K3": K1_PT + K2_PT + K3_PT,
        "K1 corrected": k1c, "K2 corrected": k2c, "K3 corrected": k3c, "K1K2K3 corrected": k1c + k2c + k3c,
        "K2 pre-2006 ending": k2old, "K1K2K3 pre-2006": K1_PT + k2old + K3_PT,
        "carved K1-K3 ciphertext": left[: left.index("OBKRUOXOG")],
    }
    t.update({k + " (reversed)": v[::-1] for k, v in list(t.items())})
    return t


def check(unknown, kind, known, tkey, text, off):
    kn, tk = IX[known], IX[tkey]
    val, used = {}, {}
    checks = 0
    for p in CRIB_POS:
        j = off + p
        if not 0 <= j < len(text):
            return False, checks
        t = tk[text[j]]
        if unknown == "plain":           # x(P) from known y(C)
            letter = CRIBS[p]
            v = (kn[K4[p]] - t) % 26 if kind == "vig" else (t - kn[K4[p]]) % 26
        else:                            # y(C) from known x(P)
            letter = K4[p]
            v = (kn[CRIBS[p]] + t) % 26 if kind == "vig" else (t - kn[CRIBS[p]]) % 26
        if letter in val:
            checks += 1
            if val[letter] != v:
                return False, checks
        else:
            if v in used:
                return False, checks
            val[letter] = v
            used[v] = letter
    return True, checks


def check_table(kind, xn, yn, text, off):
    """Both alphabets known, key letter -> shift by any table. Returns (consistent, constraints)."""
    x, y = IX[xn], IX[yn]
    seen, checks = {}, 0
    for p in CRIB_POS:
        j = off + p
        if not 0 <= j < len(text):
            return False, checks
        v = (y[K4[p]] - x[CRIBS[p]]) % 26 if kind == "vig" else (y[K4[p]] + x[CRIBS[p]]) % 26
        if text[j] in seen:
            checks += 1
            if seen[text[j]] != v:
                return False, checks
        else:
            seen[text[j]] = v
    return True, checks


def main():
    tests = hits = 0
    for name, text in texts().items():
        found = []
        for unknown in ("plain", "cipher"):
            for kind in ("vig", "beau"):
                for known in ("AZ", "KA"):
                    for tkey in ("AZ", "KA"):
                        for off in range(-CRIB_POS[0], len(text) - CRIB_POS[-1]):
                            tests += 1
                            ok, c = check(unknown, kind, known, tkey, text, off)
                            if ok:
                                found.append((unknown, kind, known, tkey, off, c))
        hits += len(found)
        print(f"  {name:28} {len(text):4} letters: {found or 'none'}")
    print(f"{tests} tests, {hits} survivors")
    tests = 0
    found = []
    for name, text in texts().items():
        for kind in ("vig", "beau"):
            for xn in ("AZ", "KA"):
                for yn in ("AZ", "KA"):
                    for off in range(-CRIB_POS[0], len(text) - CRIB_POS[-1]):
                        tests += 1
                        ok, c = check_table(kind, xn, yn, text, off)
                        if ok and c:
                            found.append((name, kind, xn, yn, off, c))
    print(f"any lookup table from key letter to shift: {tests} tests, survivors: {found or 'none'}")


if __name__ == "__main__":
    main()
