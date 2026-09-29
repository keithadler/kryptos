"""Emit keyword-derived column orders for trans.c ord mode: 'label w o0,o1,...'.
Two conventions: ord = columns in alphabetical rank order, and its inverse permutation."""
import sys, re
THEME = """KRYPTOS PALIMPSEST ABSCISSA BERLINCLOCK EASTNORTHEAST WELTZEITUHR ALEXANDERPLATZ
URANIAWELTZEITUHR BERLINWALL CHECKPOINTCHARLIE TUTANKHAMUN HOWARDCARTER LORDCARNARVON
JAMESSANBORN EDWARDSCHEIDT CENTRALINTELLIGENCEAGENCY LANGLEYVIRGINIA IQLUSION UNDERGRUUND
LAYERTWO DESPARATLY KRYPTOSPALIMPSEST PALIMPSESTABSCISSA KRYPTOSABSCISSA SHADOWFORCES
BETWEENSUBTLESHADING THEABSENCEOFLIGHT DELIVERINGAMESSAGE COMPASSROSE WINDROSE
VIRTUALLYINVISIBLE TOTALLYINVISIBLE MAGNETICFIELD WONDERFULTHINGS CANYOUSEEANYTHING
YESWONDERFULTHINGS NORTHEASTOFHERE ITSBURIEDOUTTHERESOMEWHERE""".split()
seen = set()
def emit(label, word):
    w = len(word)
    if not (12 <= w <= 30): return
    ranks = sorted(range(w), key=lambda i: (word[i], i))   # ranks[k] = column read k-th
    inv = [0] * w
    for k, col in enumerate(ranks): inv[col] = k
    for tag, o in (("", ranks), ("~inv", inv)):
        key = tuple(o)
        if key in seen: continue
        seen.add(key)
        print(f"{label}{tag} {w} {','.join(map(str, o))}")
for t in THEME: emit(t, t)
for f in ("/usr/share/dict/words", "/usr/share/dict/propernames"):
    for line in open(f):
        wd = line.strip().upper()
        if re.fullmatch(r"[A-Z]+", wd): emit(wd, wd)
