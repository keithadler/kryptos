"""Re-run the exact eliminations allowing for a Sanborn slip.

K1 and K2 both carry transcription errors on the sculpture, so an exact crib test could wrongly
kill the true family. Variants tried:
  drop j      one crib letter is wrong (its ciphertext or plaintext): ignore crib j
  shift j,d   a letter was dropped (d>0) or added (d<0) in the ciphertext before position j:
              key index = pos + d for every crib at or after j
Families: periodic (1..26), progressive, running key, over the 8 base families (THEMES=1 adds the
theme-word alphabets from attacks.py). Survivors are compared with the chance count sum(26^-c).
"""
import os
from kryptos import K4, CRIBS, CRIB_POS
import attacks

N = len(K4)


def variants():
    base = [(p, CRIBS[p], p) for p in CRIB_POS]
    yield "exact", base
    for j in range(len(base)):
        yield f"drop {base[j][0] + 1}", base[:j] + base[j + 1:]
    # split points that actually change relative alignment: inside the first crib, between the
    # cribs (one case covers 35..64), inside the second crib
    splits = list(range(23, 35)) + [35] + list(range(65, 75))
    for j1 in splits:
        for d in (-3, -2, -1, 1, 2, 3):
            yield f"shift@{j1}{d:+d}", [(p, ch, p + (d if p + 1 >= j1 else 0)) for p, ch, _ in base]


def consistent(pairs, period):
    seen, checks, ok = {}, 0, True
    for i, v in pairs:
        r = i % period
        if r in seen:
            checks += 1
            ok &= seen[r] == v
        else:
            seen[r] = v
    return ok, checks


def main():
    fams = list(attacks.families())
    texts = attacks.running_key_texts()
    obs = exp = 0.0
    hits = []
    for label, cribs in variants():
        for kind, xn, yn, x, y in fams:
            forced = [(ki, attacks.kval(kind, x, y, ch, K4[p])) for p, ch, ki in cribs]
            fam = f"{kind}-P{xn}-C{yn}"
            for per in range(1, 27):
                ok, c = consistent(forced, per)
                if c:
                    exp += 26.0 ** -c
                    if ok:
                        obs += 1
                        hits.append((c, label, fam, f"periodic p={per}"))
                for s in range(1, 26):
                    ok, c = consistent([(ki, (v - s * (ki // per)) % 26) for ki, v in forced], per)
                    if c:
                        exp += 26.0 ** -c
                        if ok:
                            obs += 1
                            hits.append((c, label, fam, f"progressive p={per} s={s}"))
            # running key: every constraint is a check (c = number of cribs)
            for keyalpha, ka in (("x", x), ("y", y)):
                for tname, t in texts.items():
                    for off in range(-N, len(t)):
                        if all(0 <= off + ki < len(t) and ka[t[off + ki]] == v for ki, v in forced):
                            hits.append((len(forced), label, fam, f"running {tname} off={off} via {keyalpha}"))
    hits.sort(reverse=True)
    strong = [h for h in hits if h[0] >= 5]
    print(f"periodic/progressive survivors: {obs:.0f} observed vs {exp:.1f} expected by chance")
    print(f"survivors holding 5+ constraints: {len(strong)}")
    for h in strong[:30]:
        print("  ", h)
    print("top by constraint count:")
    for h in hits[:10]:
        print("  ", h)


if __name__ == "__main__":
    main()
