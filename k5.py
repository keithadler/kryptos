"""K5 against K4: two messages under one key.

Sanborn has said K5 is 97 letters, uses a similar system, and shares "some of the same coded words
in the same position" as K4. If the cipher depends only on the position (y(C_i) = x(P_i) + k_i or
k_i - x(P_i), any key at all), then for the two ciphertexts

    y(C4_i) - y(C5_i) = +/- (x(P4_i) - x(P5_i))

and the key is gone. This script, given K5's ciphertext:
  1. lists where K5 equals K4 letter for letter (same key + same plaintext, if the model holds);
  2. reads off K5's plaintext at K4's 24 known positions, for each numbering of the two sides, and
     scores it as English. This is the decisive step: under the right model the 13 and 11 letters
     are English outright; under a wrong one they are noise. No key, period or alphabet beyond
     A-Z/KRYPTOS is assumed;
  3. drafts both plaintexts together with a beam search scored by English quadgrams, K4's known
     letters held fixed. Quadgrams are too weak to finish this alone (about half the letters on a
     planted pair), so treat it as a draft to extend by hand with --drag;
  4. --drag WORD slides a guessed word along each message and lists where the other message's
     implied letters read as English.

usage: python3 k5.py CIPHERTEXT [--drag WORD]     (97 letters)
       python3 k5.py --selftest                   (two planted messages under a random 97-letter key)
Needs data/quadgrams.bin or data/quadgrams_local.bin.
"""
import pathlib
import random
import sys
import numpy as np
import kryptos
from kryptos import CRIBS, CRIB_POS, AZ, KA, K2_PT, K3_PT

DATA = pathlib.Path(__file__).with_name("data")
ALPH = {"AZ": AZ, "KA": KA}
# vig: y(C) = x(P) + k.  beau: y(C) = k - x(P).  Variant Beaufort differs from vig only in the key.
CASES = [(kind, xn, yn) for kind in ("vig", "beau") for xn in ALPH for yn in ALPH]


def load_model():
    quad = next((f for f in (DATA / "quadgrams.bin", DATA / "quadgrams_local.bin") if f.exists()), None)
    if quad is None:
        raise SystemExit("no quadgram model: run checks/quadgrams_local.py (or fetch_texts.sh then quadgrams.py)")
    return np.fromfile(quad, dtype=np.float32)


def other_plain(kind, xn, yn, c4, c5, p4_letters):
    """x-index of the K5 plaintext letter for each candidate K4 plaintext letter (array of 26, in A-Z order)."""
    x, y = ALPH[xn], ALPH[yn]
    d = (y.index(c4) - y.index(c5)) % 26
    xi = np.array([x.index(ch) for ch in p4_letters])
    return (xi - d) % 26 if kind == "vig" else (xi + d) % 26


def at_cribs(kind, xn, yn, c4, c5):
    """K5 plaintext at K4's known positions."""
    x = ALPH[xn]
    return "".join(x[int(other_plain(kind, xn, yn, c4[p], c5[p], CRIBS[p])[0])] for p in CRIB_POS)


def solve(kind, xn, yn, c4, c5, logp, beam=3000):
    """Both plaintexts by beam search. Returns (mean quadgram score over both, P4, P5)."""
    x = ALPH[xn]
    xl = np.array([ord(ch) - 65 for ch in x])                 # x-index -> letter 0..25
    n = len(c4)
    score = np.zeros(1)
    h4 = np.zeros((1, 0), dtype=np.int8)
    h5 = np.zeros((1, 0), dtype=np.int8)
    for i in range(n):
        cand = [CRIBS[i]] if i in CRIBS else list(AZ)
        a = np.array([ord(ch) - 65 for ch in cand])                                   # K4 plaintext letters
        b = xl[other_plain(kind, xn, yn, c4[i], c5[i], cand)]                         # matching K5 letters
        B, m = len(score), len(cand)
        s = np.repeat(score, m)
        n4 = np.concatenate([np.repeat(h4, m, axis=0), np.tile(a, B)[:, None].astype(np.int8)], axis=1)
        n5 = np.concatenate([np.repeat(h5, m, axis=0), np.tile(b, B)[:, None].astype(np.int8)], axis=1)
        if i >= 3:
            for h in (n4, n5):
                t = h[:, -4:].astype(np.int64)
                s = s + logp[((t[:, 0] * 26 + t[:, 1]) * 26 + t[:, 2]) * 26 + t[:, 3]]
        if len(s) > beam:
            # merge hypotheses that agree on the last three letters of both messages, keep the best
            order = np.argsort(-s)
            st = np.zeros(len(s), dtype=np.int64)
            for h in (n4, n5):
                for col in h[:, -3:].T:
                    st = st * 26 + col
            _, first = np.unique(st[order], return_index=True)
            keep = order[np.sort(first)][:beam]
            s, n4, n5 = s[keep], n4[keep], n5[keep]
        score, h4, h5 = s, n4, n5
    j = int(np.argmax(score))
    txt = lambda h: "".join(AZ[v] for v in h[j])
    return float(score[j]) / (2 * (n - 3)), txt(h4), txt(h5)


def qmean(s, logp):
    a = np.frombuffer(s.encode(), dtype=np.uint8).astype(np.int64) - 65
    return float(logp[((a[:-3] * 26 + a[1:-2]) * 26 + a[2:-1]) * 26 + a[3:]].mean())


def drag(kind, xn, yn, c4, c5, word, logp, top=12):
    """Guess WORD in one message at every position; show what it forces in the other."""
    x = ALPH[xn]
    out = []
    for i in range(97 - len(word) + 1):
        if any(i + t in CRIBS and CRIBS[i + t] != ch for t, ch in enumerate(word)):
            in4 = None                                             # contradicts K4's known letters
        else:
            in4 = "".join(x[int(other_plain(kind, xn, yn, c4[i + t], c5[i + t], ch)[0])] for t, ch in enumerate(word))
        # WORD in K5 forces K4: invert by swapping the roles of the two ciphertexts
        in5 = "".join(x[int(other_plain(kind, xn, yn, c5[i + t], c4[i + t], ch)[0])] for t, ch in enumerate(word))
        if all(i + t not in CRIBS or CRIBS[i + t] == ch for t, ch in enumerate(in5)):
            out.append((qmean(in5, logp), i + 1, "K5", in5))
        if in4:
            out.append((qmean(in4, logp), i + 1, "K4", in4))
    print(f"\n{word} placed in one message -> letters forced in the other ({kind} P:{xn} C:{yn}), best {top}:")
    for sc, pos, where, txt in sorted(out, reverse=True)[:top]:
        other = "K5" if where == "K4" else "K4"
        print(f"  {sc:6.2f}  {word} in {where} at {pos:2}  ->  {other} reads {txt}")


def report(c5, logp, word=None):
    c4 = kryptos.K4
    same = [i for i in range(97) if c4[i] == c5[i]]
    runs, s = [], None
    for i in range(98):
        if i in same and s is None:
            s = i
        elif i not in same and s is not None:
            runs.append((s + 1, i, c4[s:i]))
            s = None
    print(f"K5 equals K4 at {len(same)} of 97 positions (chance: about 3.7)")
    for a, b, w in runs:
        if b - a + 1 >= 2:
            pt = "".join(CRIBS.get(i, ".") for i in range(a - 1, b))
            print(f"   positions {a}-{b}: {w}   K4 plaintext there: {pt}")
    print("\nK5 plaintext at K4's 24 known positions (English is about -5.1 or better; noise about -6.5 to -7.5):")
    res = []
    for kind, xn, yn in CASES:
        frag = at_cribs(kind, xn, yn, c4, c5)
        res.append(((qmean(frag[:13], logp) * 10 + qmean(frag[13:], logp) * 8) / 18, kind, xn, yn, frag))
    res.sort(reverse=True)
    for sc, kind, xn, yn, frag in res:
        print(f"  {sc:6.2f}  {kind:4} P:{xn} C:{yn}   22-34: {frag[:13]}   64-74: {frag[13:]}")
    sc, kind, xn, yn, frag = res[0]
    if sc < -5.3:
        print("\nNo numbering gives English: K5 is not K4's key reused position for position in these 8 families.")
        return res[0], None, None
    _, p4, p5 = solve(kind, xn, yn, c4, c5, logp)
    print(f"\nDraft of both messages ({kind} P:{xn} C:{yn}); only the stretches that read as English are likely right:")
    print(f"  K4: {p4}\n  K5: {p5}")
    if word:
        drag(kind, xn, yn, c4, c5, word, logp)
    return res[0], p4, p5


def selftest(logp, seed=5):
    """Two English messages under one random 97-letter key, KRYPTOS alphabet both sides."""
    rnd = random.Random(seed)
    key = [rnd.randrange(26) for _ in range(97)]
    p5 = K3_PT[130:227]
    p4 = list(K2_PT[69:166])
    for p, ch in CRIBS.items():
        p4[p] = ch
    p4 = "".join(p4)
    enc = lambda pt: "".join(KA[(KA.index(c) + k) % 26] for c, k in zip(pt, key))
    real, kryptos.K4 = kryptos.K4, enc(p4)
    try:
        best, d4, d5 = report(enc(p5), logp, word="CHAMBER")
    finally:
        kryptos.K4 = real
    exact = best[4] == "".join(p5[p] for p in CRIB_POS)
    ok4, ok5 = sum(a == b for a, b in zip(d4, p4)), sum(a == b for a, b in zip(d5, p5))
    print(f"\nselftest: best case {best[1]} P:{best[2]} C:{best[3]}; message 2 at the known positions "
          f"{'exact' if exact else 'WRONG'}; draft has {ok4}/97 of message 1 and {ok5}/97 of message 2")
    return best[1:4], exact, ok4, ok5


if __name__ == "__main__":
    args = sys.argv[1:]
    word = args.pop(args.index("--drag") + 1).upper() if "--drag" in args else None
    args = [a for a in args if a != "--drag"]
    if len(args) != 1:
        raise SystemExit(__doc__)
    logp = load_model()
    if args[0] == "--selftest":
        selftest(logp)
    else:
        c5 = "".join(ch for ch in args[0].upper() if "A" <= ch <= "Z")
        if len(c5) != 97:
            raise SystemExit(f"expected 97 letters, got {len(c5)}")
        report(c5, logp, word)
