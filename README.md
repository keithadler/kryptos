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
./trans rot 8                             # K3-style single/double rotation x periodic
python3 drag.py [WORDS...]                # guessed words at every open position, vs chance
python3 typo.py                           # reruns allowing one wrong clue letter or an added/dropped letter
python3 keywords.py | ./trans ord 8       # keyword-ordered columnar, widths 12-30
python3 dictalpha.py                      # every dictionary word as the keyed alphabet
python3 runkey.py [THRESH]                # running key over data/running_keys/*.txt, with tolerance
cc -O3 -o dfs dfs.c && ./dfs 12 14 26 8   # every column order at widths 12-14, pruned exactly
python3 digits.py                         # Gronsfeld / Gromark / digit keystreams
python3 trifid.py                         # Trifid, any cube, via coordinate equalities
python3 mixedalpha.py                     # Quagmire I/II with any of the 26! alphabets
python3 quag34.py                         # Quagmire III/IV with unknown alphabet(s) on both sides
cc -O3 -o quag3 quag3.c && ./quag3 vig 18 # same for QIII, in C, for the periods Python timed out on
python3 quadgrams.py && cc -O3 -o sa sa.c -lm && ./run_sa_k4.sh   # English-scored annealing + random baselines
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
| Columnar transposition, every column order, columns read down / up / alternating, forward and inverse, substitution before or after, periods 1–26 | **Eliminated for widths 2–11** (44M column orders, 110 billion combinations; strongest chance survivor holds 7 constraints) |
| K3-style rotation: one rotation, or two at any pair of widths (2–96), clockwise or counter, forward and inverse, before or after a repeating key with period 1–26 | **Eliminated** (30M combinations, none past 4 constraints) |
| Same 8 families with 20 theme-word keyed alphabets (PALIMPSEST, ABSCISSA, WELTZEITUHR, …), periodic / autokey / running key | **Eliminated**. The only multi-constraint survivors are 3-constraint progressive hits, which is chance level for ~600k tests. |
| **Typo tolerance** (`typo.py`): periodic, progressive and running key rerun with any one clue letter wrong, or a letter added/dropped (±1–3) anywhere before or inside a clue | **Eliminated.** No survivor holds more than 2 constraints; 580 survivors vs ~516 expected by chance. Planted typo and dropped letter are both recovered (12–13 constraints). |
| Keyword-ordered columnar, widths 12–30: 115k dictionary words, proper names and theme phrases, both ordering conventions, 3 read directions, forward and inverse, substitution before or after, periods 1–26 | **Eliminated** (287M combinations, none past 4 constraints). Planted PALIMPSESTABSCISSA order recovered with 17 constraints. |
| Periodic key 1–26 with any dictionary word as the keyed alphabet (209k distinct alphabets; Quagmire I/II/III, KA→word, word→KA; Vigenère and Beaufort) (`dictalpha.py`) | **Eliminated.** All 68k survivors sit at period 26 on the single available constraint, which is chance level. Planted Quagmire III recovered with 16 constraints. |
| **Running key from outside texts, with tolerance** (`runkey.py`): Carter's *The Tomb of Tut-ankh-Amen* vols 1–3 (archive.org OCR; vol 1 contains K3's source passage), the King James Bible, the Declaration, Constitution, Bill of Rights, Poe's *Works* vol 1 (*The Gold-Bug*), and the 1923 Gutenberg Tutankhamen account. Each forward and reversed, 8 families, key read via either alphabet | **No signal.** 149M offsets tested; the best anywhere is 9/24 matching key letters, while chance reaches 9 about 36 times at this scale and 12 is the threshold. A planted Carter key with 2 typos scores 22/24. (Planting also showed English can reach 12/24 against English by shared phrasing, so any 12+ hit needs inspection.) |
| **Columnar at widths 12–14 with *every* column order** (`dfs.c`): depth-first column placement with crib pruning, both directions, 8 families, substitution before or after, periods 1–26 | **Widths 12–14 eliminated** (2.9B, 21B and 276B search nodes). Width 14 left one cluster of 3 near-identical orders at exactly 8 constraints (KA Vigenère after transposition, period 25); decrypting them gives gibberish between the clue words, so they are chance. Matches brute force exactly at width 7; planted cipher recovered with 17 constraints. |
| **Digit-shift ciphers** (Gronsfeld, Gromark, any digit keystream) (`digits.py`): every forced shift must be 0–9, over AZ, KA and 209k dictionary alphabets in 5 arrangements, both directions | **Eliminated.** No alphabet gives all 24 shifts ≤ 9 (best 21/24; a real digit cipher gives 24/24). |
| **Trifid**, any 3×3×3 cube, periods 2–24, every group offset (`trifid.py`): the clues force 72 coordinate equalities, then a solver checks whether any cube satisfies them | **Eliminated:** all 299 cases have no solution. 1,794 planted Trifids across all periods and offsets were all solved correctly. |
| Anything built on a 5×5 square (Bifid, Playfair, two-square, four-square, ADFGX) | **Eliminated outright:** K4 uses all 26 letters, and a 5×5 square outputs only 25 |
| **Any masking alphabet, then a repeating key** (general Quagmire I), and **a repeating key, then any substitution of the output** (general Quagmire II): all 26! alphabets at once via difference equations mod 26 (`mixedalpha.py`) | **Eliminated for periods 1–12, 14, 15, 17, 18, 21, 22, 25.** The rest (13, 16, 19, 20, 23, 24, 26) have ≤1 constraint, so the clues can't test them with a free alphabet. Planted ciphers are recovered. |
| **General Quagmire III** (one unknown alphabet on both sides, the K1/K2 cipher type with any alphabet) and **general Quagmire IV** (two independent unknown alphabets), periods 1–26 (`quag34.py`, calibrated by `calib_quag.py`) | **QIII Vigenère: eliminated at every period 1–26** (18–20 settled by `quag3.c`). **QIII Beaufort: eliminated at 1–12, 14–17, 19–22, 24, 25**; 13 and 18 still open after 30 min of C search; 23 and 26 are satisfiable, but 10–27 of 30 random ciphertexts are too. `quag3.c` recovered 48/48 planted QIII ciphers. **QIV: eliminated at 1–7, 9, 10, 15, 17, 22, 25**. Satisfiable at 8, 13, 16, 19, 20, 23, 24, 26, but random ciphertexts pass those at similar or higher rates (9–30 of 30 SAT outright, most of the rest timeouts), so none of that is evidence. The K→K at 74 kills most QIII periods outright: one alphabet on both sides forces a zero shift on that key residue. |
| **English-scored attack on the periods the clues can't test** (`sa.c`, simulated annealing over the free alphabet and key, English quadgram score + clue weight; quadgrams built by `quadgrams.py`) | **Negative wherever the method is proven.** Planted ciphers are recovered 88–97/97: QI (free plaintext alphabet, KA ciphertext) at periods 13, 16, 20, 24; QII (AZ plaintext, free ciphertext) at 13, 16. Recovered plaintexts score −4.2 to −4.4 per quadgram with 24/24 clues. K4's best at every mode/period is −4.6 to −5.7 with 16–24 clues, which is the same range random ciphertexts reach (−4.8 to −5.5, 16–22 clues). **Not informative:** QIV at period 8 (planted recovery only 38–61/97; the method makes English-looking junk), QII at 20+, QI at 26. |
| Playfair, Porta, and any cipher that never maps a letter to itself | **Eliminated outright:** position 74 is K→K |
| Periodic key with period 27–48 plus one guessed word (52 theme words: WELTZEITUHR, BERLINWALL, EGYPT, COMPASSROSE, DELIVER, …) at every open position (`drag.py`) | **No signal.** 23 survivors against ~109 expected by chance, and none holding 4+ constraints. |

Statistics: K4's index of coincidence is 0.0361 (random text ≈ 0.0385, English ≈ 0.066), so it is
not a transposition of English alone. Something polyalphabetic or fractionating is involved.
One pair repeats: plaintext R becomes ciphertext P at both 28 and 66, 38 apart.
That fits any key that happens to repeat there.

## Guessed plaintext (conditional results)

`KRYPTOS_GUESS="61:THE" python3 guess_run.py` adds guessed letters for one run only; the confirmed
clues in `kryptos.py` never change. A guess only adds constraints, so families already eliminated
stay eliminated, and only the families the confirmed clues left open are rerun. Every satisfiable
result is compared with random ciphertexts under the same crib set.

**THE at 61–63 (…THEBERLINCLOCK), if right:**
- Quagmire I/II with any alphabet: open periods shrink from {13, 16, 19, 20, 23, 24, 26} to {23, 24, 26} (plus 19 for QII, on one constraint).
- General Quagmire III Beaufort: 13 and 18 become UNSAT; 23 and 26 stay SAT, as random text also does (7/12, 11/12).
- General Quagmire IV: 8, 16, 20 become UNSAT. 13, 23, 24, 26 stay SAT at rates random text matches. 19 stays SAT (with or without THE), while plain random text is 0/30 SAT. The cause is K4's one repeat (plaintext R becomes P at both 28 and 66, 38 = 2×19 apart). Random ciphertexts given that same repeat are 21/30 SAT (`REPEAT=1 python3 calib_c.py vig4 19 30 180`), so period 19 is explained and is not a signal.
- Hill 4×4: alignment 0 becomes testable and is eliminated; alignment 3 is still untestable.
- Periodic 27–48: no survivors.

## The World Clock

Sanborn confirmed in November 2025 that BERLINCLOCK means the Weltzeituhr at Alexanderplatz. Its
drum has 24 sides, one per time zone, and it stands on a stone compass-rose mosaic
(de.wikipedia, `data/weltzeituhr_de.txt`). Any key built from the clock that repeats every
24 or 12 letters is a periodic key, and those are eliminated in all 8 families, even
with an advancing offset each cycle. The Kurfürstendamm set-theory clock (24 lamps) falls
the same way. If the clock drives the key, it isn't through a simple 24- or 12-cycle.

## Not yet tested
- More running-key texts: drop them into `data/running_keys/*.txt` and run `python3 runkey.py`.
- Transposition searches with typo tolerance; keyed *double* columnar; routes other than columns and rotations.
- Fractionating ciphers on a 6×6 square (with digits) or with a transposition layer.
- Non-repeating keys from the Weltzeituhr's city names. Parked: no reliable per-face list exists, and the 1997 renovation renamed cities, added 20 and moved some between faces, so today's list isn't the one Sanborn saw in 1990.
