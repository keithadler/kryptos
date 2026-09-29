# Kryptos K4: crib-elimination harness

K4 is the fourth, 97-letter passage on Jim Sanborn's *Kryptos* sculpture at CIA headquarters. Its
plaintext is known privately: Kobek and Byrne found it in Sanborn's Smithsonian papers in September
2025, and Sanborn confirmed it. It has never been published. Paradigm bought the archive at auction
for $962,500 in November 2025. It now verifies submitted answers against it for $1 each, without
learning the answer. The *method* is also unpublished. Publicly, K4 is unsolved.

This repo attacks it the only honest way: the 24 plaintext letters Sanborn released are hard
constraints. A cipher family is **eliminated** when no key reproduces all of them, and it
**survives** only when one does. Every result reports how many constraints the clues actually
imposed, because a family the clues can't reach survives trivially and proves nothing.

| Clue (1-based) | Ciphertext | Plaintext | Released |
|---|---|---|---|
| 22–25 | FLRV | EAST | 2020 |
| 26–34 | QQPRNGKSS | NORTHEAST | 2020 |
| 64–69 | NYPVTT | BERLIN | 2010 |
| 70–74 | MZFPK | CLOCK | 2014 |

## Run

```
python3 attacks.py            # periodic, progressive, autokey, running key, Hill
python3 selftest.py           # plants known encryptions, confirms each test finds them
cc -O3 -o trans trans.c && ./trans 10 8   # columnar transposition x periodic substitution
```

Harness check: `kryptos.py` decrypts K1 with the KRYPTOS tableau and PALIMPSEST exactly.
The sculpture text in `data/` is from Wikipedia's source. It has 869 characters on the left
side and 867 in the tableau, matching the published counts.

## Results (2026-09-28)

Substitution model: `y(C) = x(P) + k` (Vigenère) or `y(C) = k − x(P)` (Beaufort), with each of the
plaintext and ciphertext alphabets `x`, `y` either A–Z or KRYPTOSABCDEFGHIJLMNQUVWXZ. That covers
Vigenère, Beaufort, variant Beaufort and Quagmire I–IV keyed with KRYPTOS: 8 families.

| Family | Result |
|---|---|
| Periodic key, periods 1–26, all 8 families | **Eliminated.** At period 27 and above the clues no longer constrain anything. |
| Progressive key `K[i mod p] + s·⌊i/p⌋`, p ≤ 26 | Eliminated, except period 26 with a single constraint (chance level, not evidence) |
| Autokey, ciphertext- or plaintext-keyed, every lag | **Eliminated** |
| Running key: K1/K2/K3 plaintext, the whole left side, the tableau, each forward and reversed, every offset | **Eliminated** |
| Hill 2×2, 3×3, 4×4 (A–Z and KA indexing, every block alignment) | **Eliminated**, except 4×4 at two alignments, where the clues give too few blocks to test |
| Columnar transposition, widths 2–11, every column order, columns read down / up / alternating, forward and inverse, substitution before or after, periods 1–26 | See `log_trans11.txt` |

Statistics: K4's index of coincidence is 0.0361 (random text ≈ 0.0385, English ≈ 0.066), so it is
not a transposition of English alone. Something polyalphabetic or fractionating is involved.
One pair repeats: plaintext R becomes ciphertext P at both 28 and 66, 38 apart.
That fits any key that happens to repeat there.

## Not yet tested
- Running key from Howard Carter's *The Tomb of Tut-ankh-Amen* (K3's source). Drop texts into
  `data/running_keys/*.txt`; `attacks.py running` picks them up.
- Transpositions wider than 11, route ciphers other than columns, and double transposition
  (K3 used two rotations).
- Keyed alphabets other than KRYPTOS (e.g. PALIMPSEST, ABSCISSA, BERLIN, CLOCK) in the 8 families.
- Keys driven by the Weltzeituhr itself: its 24 time-zone faces and the city names on them.
