"""Kryptos K4: ciphertext, confirmed cribs, alphabets and the basic cipher operations.

Positions are 0-based everywhere in code. Sanborn's public clues are 1-based:
EAST 22-25, NORTHEAST 26-34, BERLIN 64-69, CLOCK 70-74.
"""

K4 = ("OBKR"
      "UOXOGHULBSOLIFBBWFLRVQQPRNGKSSO"
      "TWTQSJQSSEKZZWATJKLUDIAWINFBNYP"
      "VTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR")
assert len(K4) == 97

# 1-based start -> plaintext, as released by Sanborn (2010, 2014, 2020).
CRIBS_1 = {22: "EASTNORTHEAST", 64: "BERLINCLOCK"}
CRIBS = {s - 1 + i: ch for s, w in CRIBS_1.items() for i, ch in enumerate(w)}  # pos -> plain letter
CONFIRMED = dict(CRIBS)

# Hypothesis mode: KRYPTOS_GUESS="61:THE,35:OF" (1-based starts) adds GUESSED plaintext for one run.
# Never edit CRIBS_1 for a guess; results under a guess are conditional on it being right.
import os as _os
import sys as _sys
GUESS = {}
for _item in filter(None, _os.environ.get("KRYPTOS_GUESS", "").split(",")):
    _s, _w = _item.split(":")
    for _i, _ch in enumerate(_w.upper()):
        _p = int(_s) - 1 + _i
        if _p in CRIBS and CRIBS[_p] != _ch:
            raise SystemExit(f"guess {_item} contradicts confirmed crib at {_p + 1}")
        GUESS[_p] = _ch
if GUESS:
    CRIBS.update(GUESS)
    print(f"[HYPOTHESIS MODE] guessed plaintext {_os.environ['KRYPTOS_GUESS']} "
          f"({len(GUESS)} letters) added to the 24 confirmed", file=_sys.stderr)
CRIB_POS = sorted(CRIBS)

AZ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
KA = "KRYPTOSABCDEFGHIJLMNQUVWXZ"  # the sculpture's keyed alphabet (K1, K2)

# The sculpture's left-side text, K1..K4 in order, '?' kept (data/sculpture_left.txt).
K1_CT = "EMUFPHZLRFAXYUSDJKZLDKRNSHGNFIVJYQTQUXQBQVYUVLLTREVJYQTMKYRDMFD"
K1_PT = "BETWEENSUBTLESHADINGANDTHEABSENCEOFLIGHTLIESTHENUANCEOFIQLUSION"
K2_PT = ("ITWASTOTALLYINVISIBLEHOWSTHATPOSSIBLETHEYUSEDTHEEARTHSMAGNETICFIELDX"
         "THEINFORMATIONWASGATHEREDANDTRANSMITTEDUNDERGRUUNDTOANUNKNOWNLOCATIONX"
         "DOESLANGLEYKNOWABOUTTHISTHEYSHOULDITSBURIEDOUTTHERESOMEWHEREX"
         "WHOKNOWSTHEEXACTLOCATIONONLYWWTHISWASHISLASTMESSAGEX"
         "THIRTYEIGHTDEGREESFIFTYSEVENMINUTESSIXPOINTFIVESECONDSNORTH"
         "SEVENTYSEVENDEGREESEIGHTMINUTESFORTYFOURSECONDSWESTXLAYERTWO")
K3_PT = ("SLOWLYDESPARATLYSLOWLYTHEREMAINSOFPASSAGEDEBRISTHATENCUMBEREDTHELOWER"
         "PARTOFTHEDOORWAYWASREMOVEDWITHTREMBLINGHANDSIMADEATINYBREACHINTHEUPPER"
         "LEFTHANDCORNERANDTHENWIDENINGTHEHOLEALITTLEIINSERTEDTHECANDLEANDPEERED"
         "INTHEHOTAIRESCAPINGFROMTHECHAMBERCAUSEDTHEFLAMETOFLICKERBUTPRESENTLY"
         "DETAILSOFTHEROOMWITHINEMERGEDFROMTHEMISTXCANYOUSEEANYTHINGQ")


def idx(alpha):
    return {c: i for i, c in enumerate(alpha)}


# Tableau ciphers over a mixed alphabet A (used for both rows and columns, as on the sculpture).
# vig:      C = A[(a(P) + a(K)) % 26]
# beaufort: C = A[(a(K) - a(P)) % 26]
# varbeau:  C = A[(a(P) - a(K)) % 26]
def key_value(kind, alpha, p, c):
    """Key shift (as an index into alpha) that maps plain p to cipher c."""
    a = idx(alpha)
    if kind == "vig":
        return (a[c] - a[p]) % 26
    if kind == "beaufort":
        return (a[c] + a[p]) % 26
    if kind == "varbeau":
        return (a[p] - a[c]) % 26
    raise ValueError(kind)


def decrypt(kind, alpha, ct, keyvals):
    a = idx(alpha)
    out = []
    for c, k in zip(ct, keyvals):
        if kind == "vig":
            out.append(alpha[(a[c] - k) % 26])
        elif kind == "beaufort":
            out.append(alpha[(k - a[c]) % 26])
        else:
            out.append(alpha[(a[c] + k) % 26])
    return "".join(out)


def keyword_vals(alpha, word):
    a = idx(alpha)
    return [a[ch] for ch in word]


def crib_keys(kind, alpha, ct=K4):
    """pos -> key value forced by the cribs, for a position-aligned substitution."""
    return {p: key_value(kind, alpha, CRIBS[p], ct[p]) for p in CRIB_POS}


KINDS = ("vig", "beaufort", "varbeau")
ALPHAS = {"AZ": AZ, "KA": KA}
