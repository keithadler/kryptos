"""Crib-elimination battery for K4.

Every test here is exact: a family "survives" only if some key reproduces all 24 released
plaintext letters. Each result also reports how many independent constraints the cribs imposed,
because a family with zero constraints survives trivially and proves nothing.

Substitution model (covers Vigenere, Beaufort, variant Beaufort and Quagmire I-IV with KRYPTOS):
    vig:  y(C) = x(P) + k      beau:  y(C) = k - x(P)
x = plaintext-side alphabet, y = ciphertext-side alphabet, each AZ or KA.
(variant Beaufort is vig with k negated, so it has the same survivors as vig.)
"""
import itertools
import sys
from kryptos import K4, CRIBS, CRIB_POS, AZ, KA, K1_PT, K2_PT, K3_PT

N = len(K4)
ALPH = {"AZ": AZ, "KA": KA}


def keyed(word):
    """Keyword alphabet the KRYPTOS way: keyword letters once each, then the rest in order."""
    seen = []
    for c in word + AZ:
        if c not in seen:
            seen.append(c)
    return "".join(seen)


assert keyed("KRYPTOS") == KA
THEME_WORDS = ["PALIMPSEST", "ABSCISSA", "BERLIN", "CLOCK", "BERLINCLOCK", "WELTZEITUHR",
               "ALEXANDERPLATZ", "NORTHEAST", "EASTNORTHEAST", "SANBORN", "SCHEIDT", "LANGLEY",
               "SHADOW", "IQLUSION", "UNDERGRUUND", "LAYERTWO", "COMPASS", "LODESTONE", "EGYPT", "CARTER"]
if __import__("os").environ.get("THEMES"):
    for w in THEME_WORDS:
        ALPH[w] = keyed(w)
PAIRS = [(xn, yn) for xn in ALPH for yn in ALPH]


def ix(a):
    return {c: i for i, c in enumerate(a)}


def kval(kind, x, y, p, c):
    return (y[c] - x[p]) % 26 if kind == "vig" else (y[c] + x[p]) % 26


def families():
    for kind in ("vig", "beau"):
        for xn, yn in PAIRS:
            yield kind, xn, yn, ix(ALPH[xn]), ix(ALPH[yn])


# ---------------------------------------------------------------- 1. periodic key
def periodic(pairs, period):
    """pairs: list of (key_index, forced_value). Returns (consistent, constraints_checked)."""
    seen, checks = {}, 0
    for i, v in pairs:
        r = i % period
        if r in seen:
            checks += 1
            if seen[r] != v:
                return False, checks
        else:
            seen[r] = v
    return True, checks


def test_periodic():
    print("== 1. Periodic key, position-aligned (Vigenere/Beaufort/Quagmire I-IV)")
    for kind, xn, yn, x, y in families():
        forced = [(p, kval(kind, x, y, CRIBS[p], K4[p])) for p in CRIB_POS]
        survivors = []
        for per in range(1, N):
            ok, checks = periodic(forced, per)
            if ok:
                survivors.append((per, checks))
        real = [s for s in survivors if s[1] > 0]
        first_trivial = min((s[0] for s in survivors if s[1] == 0), default=None)
        print(f"  {kind:4} P:{xn} C:{yn}  falsifiable survivors: {real or 'none'}"
              f"   (cribs stop constraining at period {first_trivial})")


# ---------------------------------------------------------------- 2. progressive keys
def test_progressive():
    """k_i = K[i mod p] + s * (i // p)  (progressive / 'clock-advancing' key), p <= 26, s in 1..25."""
    print("== 2. Progressive periodic key  k_i = K[i mod p] + s*floor(i/p)")
    for kind, xn, yn, x, y in families():
        hits = []
        for per in range(1, 27):
            for s in range(1, 26):
                forced = [(p, (kval(kind, x, y, CRIBS[p], K4[p]) - s * (p // per)) % 26) for p in CRIB_POS]
                ok, checks = periodic(forced, per)
                if ok and checks:
                    hits.append((per, s, checks))
        print(f"  {kind:4} P:{xn} C:{yn}  survivors: {hits or 'none'}")


# ---------------------------------------------------------------- 3. autokey
def test_autokey():
    print("== 3. Autokey (key = earlier ciphertext or plaintext letter at lag L)")
    for kind, xn, yn, x, y in families():
        for src in ("ct", "pt"):
            for keyalpha in ("x", "y"):
                ka = x if keyalpha == "x" else y
                hits = []
                for L in range(1, N):
                    checks, ok = 0, True
                    for p in CRIB_POS:
                        j = p - L
                        if j < 0:
                            continue
                        if src == "ct":
                            kch = K4[j]
                        elif j in CRIBS:
                            kch = CRIBS[j]
                        else:
                            continue
                        checks += 1
                        if kval(kind, x, y, CRIBS[p], K4[p]) != ka[kch]:
                            ok = False
                            break
                    if ok and checks:
                        hits.append((L, checks))
                print(f"  {kind:4} P:{xn} C:{yn} key={src} via {keyalpha}-alphabet  survivors: {hits or 'none'}")


# ---------------------------------------------------------------- 4. running key
def letters(s):
    return "".join(c for c in s.upper() if "A" <= c <= "Z")   # ASCII only: OCR texts carry accents


def running_key_texts():
    import pathlib
    sculpt = pathlib.Path(__file__).with_name("data").joinpath("sculpture_left.txt").read_text()
    left = letters(sculpt)
    tableau = letters(pathlib.Path(__file__).with_name("data").joinpath("tableau.txt").read_text())
    texts = {
        "K1 plaintext": K1_PT, "K2 plaintext": K2_PT, "K3 plaintext": K3_PT,
        "K1-K3 plaintext": K1_PT + K2_PT + K3_PT,
        "sculpture left side (all letters)": left,
        "sculpture left side before K4": left[: left.index("OBKRUOXOG")],
        "tableau (right side) row-major": tableau,
    }
    for name, t in list(texts.items()):
        texts[name + " (reversed)"] = t[::-1]
    extra = pathlib.Path(__file__).with_name("data").joinpath("running_keys")
    if extra.is_dir():
        for f in sorted(extra.glob("*.txt")):
            t = letters(f.read_text(errors="ignore"))
            texts[f.stem] = t
    return texts


def test_running_key():
    print("== 4. Running key from sculpture and source texts (every offset)")
    for name, text in running_key_texts().items():
        found = []
        for kind, xn, yn, x, y in families():
            for keyalpha in ("x", "y"):
                ka = x if keyalpha == "x" else y
                need = [(p, kval(kind, x, y, CRIBS[p], K4[p])) for p in CRIB_POS]
                for off in range(-N, len(text)):
                    ok = True
                    for p, v in need:
                        j = off + p
                        if not (0 <= j < len(text)) or ka[text[j]] != v:
                            ok = False
                            break
                    if ok:
                        found.append((kind, xn, yn, keyalpha, off))
        print(f"  {name} ({len(text)} letters): {found or 'none'}")


# ---------------------------------------------------------------- 5. Hill cipher
def test_hill():
    """C_block = M * P_block (mod 26), rows solved independently. Letters indexed in AZ or KA."""
    print("== 5. Hill cipher n=2..4, every block alignment, AZ and KA indexing")
    for an, a in ALPH.items():
        ai = ix(a)
        for n in (2, 3, 4):
            for align in range(n):
                blocks = []
                for b in range(align, N - n + 1, n):
                    if all(b + t in CRIBS for t in range(n)):
                        blocks.append(([ai[CRIBS[b + t]] for t in range(n)], [ai[K4[b + t]] for t in range(n)]))
                if len(blocks) <= n:  # not enough blocks to over-determine a row
                    print(f"  {an} n={n} align={align}: only {len(blocks)} crib blocks, cannot falsify")
                    continue
                rows_ok = []
                for r in range(n):
                    cnt = 0
                    for row in itertools.product(range(26), repeat=n):
                        if all(sum(m * p for m, p in zip(row, P)) % 26 == C[r] for P, C in blocks):
                            cnt += 1
                    rows_ok.append(cnt)
                verdict = "ELIMINATED" if 0 in rows_ok else f"rows survive {rows_ok}"
                print(f"  {an} n={n} align={align}: {len(blocks)} blocks -> {verdict}")


if __name__ == "__main__":
    which = sys.argv[1:] or ["periodic", "progressive", "autokey", "running", "hill"]
    for w in which:
        {"periodic": test_periodic, "progressive": test_progressive, "autokey": test_autokey,
         "running": test_running_key, "hill": test_hill}[w]()
