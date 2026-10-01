# Kryptos K4: a documented search

*Status as of 2026-10-01. No solution found. This document records what the 24 publicly released
plaintext letters rule out, how each claim was tested, and what they cannot decide.*

## 1. What is known

K4 is the 97-letter fourth passage of Jim Sanborn's *Kryptos* (CIA headquarters, 1990):

```
OBKRUOXOGHULBSOLIFBBWFLRVQQPRNGKSSOTWTQSJQSSEKZZWATJKLUDIAWINFBNYPVTTMZFPKWGDKZXTJCDIGKUHUAUEKCAR
```

Sanborn has released 24 plaintext letters at fixed positions:

| Positions (1-based) | Ciphertext | Plaintext | Released |
|---|---|---|---|
| 22–25 | FLRV | EAST | 2020 |
| 26–34 | QQPRNGKSS | NORTHEAST | 2020 |
| 64–69 | NYPVTT | BERLIN | 2010 |
| 70–74 | MZFPK | CLOCK | 2014 |

In November 2025 he confirmed that BERLINCLOCK means the World Clock (Weltzeituhr) at
Alexanderplatz. He also said a 1986 trip to Egypt and the 1989 fall of the Berlin Wall bear on the
solution, and that the theme is "delivering a message". In 2006 he said the answers to K1–K3
contain clues to K4.

**Public status.** Jarett Kobek and Richard Byrne found the full plaintext in Sanborn's papers at
the Smithsonian in September 2025, and Sanborn confirmed it. It has not been published, and the
files are sealed until 2075. The archive sold at auction for $962,500. Its buyer, Paradigm, checks
submitted answers against the solution for $1 each without learning it. The *method* is also
unpublished. Publicly, K4 is unsolved.

**Ground truth used here.** The sculpture text comes from Wikipedia's source (`data/SOURCES.md`).
It has 869 characters on the left side and 867 in the tableau, matching the published counts.
`verify.py` checks that K1 decrypts exactly with the KRYPTOS tableau and the key PALIMPSEST.

Two properties of the ciphertext matter throughout:
- **Index of coincidence 0.0361.** Random text is about 0.0385 and English about 0.066, so K4 is not
  English merely rearranged; some substitution flattens the letter frequencies.
- **One repeated pair.** Plaintext R becomes ciphertext P at both 28 and 66, 38 letters apart.
  **Position 74 is K→K**, a letter encrypting to itself, and so is **position 33, S→S**.

## 2. How the search works

**Exact elimination.** The 24 clue letters are hard constraints. For a cipher family, the search
asks whether *any* key reproduces all 24. If none does, the family is **eliminated**, and that's a
proof, not a statistical judgment.

**Constraint counting.** A family is only tested if the clues actually constrain it. For example,
with a repeating key of length 30 no two clue letters share a key letter, so every such key "fits"
and nothing is learned. Every survivor is reported with the number of independent constraints it
satisfied. A random survivor holds c constraints with probability about 26⁻ᶜ, so survivors are
compared with the count chance alone would produce.

**Planted-cipher verification.** A search that can't find a known answer proves nothing about
K4. For every search, `verify.py` encrypts a fake plaintext (random letters, with the four clue
words in place) using a method from that family, runs the same search code on it, and requires a
find. `make verify` runs all 28 checks in about 30 seconds, and all pass (two need optional data
and are skipped without it).

**Calibration of satisfiable results.** Where the question is "does *any* alphabet or key fit"
(a constraint-satisfaction result), K4 passing can just mean the family is too flexible. Every
such result is repeated on random ciphertexts carrying the same clue letters. K4 counts as a lead
only if it passes where random text almost never does.

**English scoring only where proven.** Where the clues cannot decide a family, a
simulated-annealing attack scored by English four-letter-group statistics is used. It counts only
at settings where it first recovered planted ciphers of the same shape.

**Guesses kept separate.** Guessed plaintext (e.g. THE before BERLIN) is added only in an explicit
hypothesis mode (`KRYPTOS_GUESS=...`). It never changes the confirmed clues, and its results are
reported in their own section as conditional.

## 3. Assumptions: what "eliminated" means

Every elimination holds under these assumptions. If one is wrong, the affected results reopen.
1. **The ciphertext is the 97 letters as carved**, with no nulls and no missing letters. The
   exception is the typo pass (§4.A), which allows one wrong clue letter, or 1–3 letters added or
   dropped, for the repeating-key and running-key families.
2. **The clue positions are plaintext positions, aligned with the carved ciphertext positions.**
   Substitution-only families use them as given. Transposition searches treat them as positions in
   the plaintext before transposition.
3. **The `?` before OBKR belongs to K3**, whose plaintext ends "…CAN YOU SEE ANYTHING Q?".
4. **Letters are A–Z.** Alphabets are either A–Z, the sculpture's KRYPTOSABCDEFGHIJLMNQUVWXZ, or
   (where stated) arbitrary.
5. **"Tableau cipher" means** y(C) = x(P) + k (Vigenère) or y(C) = k − x(P) (Beaufort), with
   plaintext alphabet x and ciphertext alphabet y each A–Z or KRYPTOS-keyed. That gives 8 families,
   covering Vigenère, Beaufort, variant Beaufort and Quagmire I–IV with KRYPTOS. Variant Beaufort
   has the same survivors as Vigenère.

## 4. Results

Evidence files are in `results/`. "Verify" names the planted check in `verify.py` that shows
the search can find an example of that family.

### A. Tableau ciphers with repeating keys

| Family | Result | Evidence |
|---|---|---|
| Repeating key, length 1–26 and 30–52, all 8 tableau families | **Eliminated.** Lengths 27–29 and 53+ are unconstrained by the clues: no two clue letters share a key letter. | `01` |
| Progressive key K[i mod p] + s·⌊i/p⌋ (key advances each cycle), p ≤ 26 | **Eliminated.** Only 1-constraint survivors at p = 26, which is chance. | `01` |
| Autokey, ciphertext- or plaintext-keyed, every lag | **Eliminated** | `01` |
| The 8 families with 20 theme-word alphabets (PALIMPSEST, ABSCISSA, WELTZEITUHR, …) | **Eliminated.** Best survivors hold 3 constraints, about 30 expected by chance. | `03` |
| The same with any of 209k dictionary-word alphabets (5 arrangements, Vigenère and Beaufort) | **Eliminated.** All 68k survivors sit at p = 26 on its single constraint. | `09` |
| Typo tolerance: repeating, progressive and running keys, allowing one wrong clue letter, or 1–3 letters added or dropped | **Eliminated.** 580 survivors against 516 expected by chance, none above 2 constraints. | `04` |
| Digit keys (Gronsfeld, Gromark, any keystream of 0–9 shifts), over A–Z, KRYPTOS and all dictionary alphabets | **Eliminated.** No alphabet makes all 24 shifts digits (best 21/24). | `11` |
| Keys from the World Clock that repeat every 24 or 12 letters (24 faces; the 24-lamp set-theory clock) | **Eliminated** as special cases of the repeating-key result | `01` |
| Key computed from the position: every cubic a + b·i + c·C(i,2) + d·C(i,3), which includes steps that grow by a fixed amount | **Eliminated.** 26⁴ keys per family, none fit. | `24` |
| Key from a two-term recurrence over 26 letters, k[i] = α·k[i−a] + β·k[i−b] + γ, lags a < b ≤ 9 (the Gromark/Fibonacci shape) | **Eliminated.** 5.1M tests, none fit, where chance is at most 26⁻⁶ each. | `24` |
| Interrupted key: a repeating key (length 1–40) that restarts after each ciphertext letter X | **Eliminated.** No survivor holds even 1 constraint. | `24` |
| Interrupted key: restarts at or after each plaintext letter X (length 2–26, any starting points) | **Eliminated.** 260 survivors, all on 1 constraint; random ciphertexts give 60–1,000, some on 2–3. | `24` |
| Key restarting at each word, with *any* alphabet per key letter | **Eliminated outright:** T is the 4th letter of both EAST and NORTHEAST and encrypts to V in one and R in the other. Shorter keys fail the same way on other letters. | `24` |

### B. Keys taken from texts (running keys)

| Family | Result | Evidence |
|---|---|---|
| K1, K2, K3 plaintexts, the whole carved left side, the tableau; forward and reversed; every offset; 8 families | **Eliminated** | `02` |
| K1–K3 solutions with an *unknown* alphabet on one side (any of 26!); carved spellings, corrected spellings, K2's pre-2006 ending "IDBYROWS", and the carved K1–K3 ciphertext | **Eliminated.** 141k tests, 0 survivors, where chance survival is about 26⁻¹¹ each. | `18` |
| Carter's *The Tomb of Tut-ankh-Amen* vols 1–3 (source of K3), King James Bible, Declaration, Constitution, Bill of Rights, Poe vol 1, a 1923 Tutankhamen account; 8 families; tolerant of OCR errors and typos | **No signal.** 149M offsets; best 9/24 key letters, which chance reaches about 36 times at this scale. A planted Carter key with 2 typos scores 22/24. | `10` |
| **Any English text** as running key, 8 families and variant Beaufort. The key letters the clues force must themselves read as English, whatever the book. | **Eliminated.** K4's best key fragments score −7.3 per four-letter group (e.g. XYHANZEFHYHMK, BNENTXBQRMA). The worst of 218 real English fragments scores −5.1, and planted keys −3.8 to −4.4. | `23` |
| **Any German text** as running key (umlauts written AE, OE, UE, SS), same families | **Eliminated.** K4's best −7.6; the worst of 2,035 real German fragments −6.5, median −4.3, planted keys −3.7 to −5.1. | `23b` |
| English or German running key under any dictionary-word alphabet (208k English, 236k with German; 5 arrangements) | **No signal.** K4's best (−5.2 English, −5.4 German) sits inside the range of random ciphertexts. 94% of English and 82% of German fragments would have stood out, so this is a result at about that power, not a proof. | `23`, `23b` |
| The Morse phrases on the entrance slabs as running or repeating key: 7,200 orders and spellings (with and without the stray E's, INTERPRETATIT/U/ON, SOS and RQ), every offset | **Eliminated.** 10.6M tests, best 8/24 key letters; chance predicts about 20 tests at 8 or more. | `24` |
| Sculpture letters taken *by position*: the letter at K4's own row and column on the tableau or ciphertext panel, every row/column offset, mirrored or not; both grids read by rows, mirrored rows, boustrophedon and columns | **Eliminated as an exact key** (best 8/24, as random text). Through *any* lookup table from key letter to shift, the directly opposite tableau letters (HIJLMNQUVWXZK, KRYABCDEFGH) contradict themselves in all 8 families. Other alignments hold at most 2 constraints, at random-text rates, so the table form is barely testable. | `26` |

### C. Transposition combined with a repeating tableau key

| Family | Result | Evidence |
|---|---|---|
| Columnar, **every column order, widths 2–11**, columns read down/up/alternating, forward and inverse, key before or after, key length 1–26 | **Eliminated.** 44M column orders, 110 billion combinations. | `05`, `05b` |
| Columnar, **every column order, widths 12–14**, via pruned search (identical results to brute force at width 7) | **Eliminated.** 2.9B / 21B / 276B search nodes. Width 14 left 3 near-identical orders at exactly 8 constraints, which decrypt to gibberish: chance. | `08`, `08b` |
| Keyword-ordered columnar, widths 12–30, 115k dictionary words, names and theme phrases | **Eliminated.** 287M combinations. | `07` |
| K3's method: one grid rotation, or two at any pair of widths | **Eliminated.** 30M combinations. | `06` |

### D. Other classical families

| Family | Result | Evidence |
|---|---|---|
| Hill cipher 2×2, 3×3, 4×4 (A–Z and KRYPTOS indexing) | **Eliminated**, except 4×4 at two block alignments the clues can't test | `01` |
| Trifid, any 3×3×3 cube, periods 2–24, every group offset | **Eliminated.** 299 of 299 cases have no solution. | `12` |
| Anything built on a 5×5 square (Bifid, Playfair, two-square, four-square, ADFGX) | **Eliminated outright:** K4 uses all 26 letters, and a 5×5 square outputs 25 | — |
| Playfair, Porta, and any cipher that never maps a letter to itself | **Eliminated outright:** position 74 is K→K | — |

### E. Unknown alphabets (any of 26!)

| Family | Result | Evidence |
|---|---|---|
| Any masking alphabet then a repeating key (general Quagmire I), or a repeating key then any substitution (general Quagmire II) | **Eliminated at lengths 1–12, 14, 15, 17, 18, 21, 22, 25** (some variants also 13, 20, 23). The rest hold at most 1 constraint, so the clues can't test them. | `13` |
| **One unknown alphabet on both sides**: K1/K2's own cipher type with any alphabet (general Quagmire III), Vigenère form | **Eliminated at every length 1–26** | `14`, `14b` |
| The same, Beaufort form | **Eliminated at 1–12, 14–17, 19–22, 24, 25.** 13 and 18 unresolved after 30 min of search. 23 and 26 satisfiable, but so are 10–27 of 30 random ciphertexts. | `14`, `14b`, `15` |
| Two independent unknown alphabets (general Quagmire IV) | **Eliminated at 1–7, 9, 10, 15, 17, 22, 25.** Satisfiable at 8, 13, 16, 19, 20, 23, 24, 26, but random ciphertexts pass at similar rates (§5 settles 19). | `14`, `15` |
| Ciphertext autokey with one unknown alphabet on all three sides, Vigenère, Beaufort and variant forms | **Eliminated at every lag 1–21** (24 equations each; no alphabet fits). Longer lags leave too few equations. | `25` |
| Plaintext autokey with one unknown alphabet | **Eliminated at lags 1–5**, and at 6–10 for the Vigenère and variant forms. Beaufort form satisfiable at 6, 7, 8, 10, but so are 16–30 of 30 random ciphertexts. | `25` |

The K→K at 74 does much of the work for Quagmire III: with one alphabet on both sides it forces a
zero shift on that key letter, so every other clue letter on the same key letter would have to
encrypt to itself.

### F. Two layers ("LAYER TWO", the last words of K2)

| Family | Result | Evidence |
|---|---|---|
| The K1/K2 tableau cipher applied twice, two repeating keys of lengths a ≤ b ≤ 26, same alphabet both layers, any Vigenère/Beaufort mix. The combined key u[i mod a] + v[i mod b] is solved exactly as linear equations mod 26. | **Eliminated at all 932 testable length pairs.** 2 consistent, each on 1 constraint, against about 4 expected by chance. 472 pairs have too many unknowns for 24 letters. | `17` |
| Columnar or rotation transposition before or after a repeating key | **Eliminated**, see §C | |

### G. English-scored attack on what the clues can't decide

Simulated annealing over the free alphabet and key, scored by English four-letter-group statistics
plus clue agreement (`c/sa.c`). It recovers planted ciphers **88–97 of 97 letters** for Quagmire I
at lengths 13, 16, 20, 24 and Quagmire II at 13, 16. Recovered plaintexts score −4.2 to −4.4 per
letter group with all 24 clues.

**K4 at those settings:** best −4.6 to −5.7, with 16–24 clues. That's the same range random
ciphertexts reach (−4.8 to −5.5, 16–22 clues). **No hidden Quagmire I/II at the proven settings.**
(Evidence `16`.)

**Not informative:** two free alphabets at length 8 (planted recovery only 38–61/97; the method
produces English-looking nonsense), Quagmire II at 20+, Quagmire I at 26.

## 5. Guessed plaintext (conditional: holds only if the guess is right)

The best guesses sit where grammar forces them next to the known words: **THE** at 61–63
(…THEBERLINCLOCK), **OF** at 35–36 (…NORTHEASTOF…), **IS** at 75–76 (…CLOCKIS…). A guess only
adds constraints, so it can never reopen an eliminated family; each was rerun only on what the
confirmed clues left open (`guess_run.py`; evidence `20_*`).

- **Hill 4×4:** with OF or IS, all four alignments become testable and all are eliminated.
- **Quagmire I/II, any alphabet:** with all three guesses, only lengths 23 and 24 stay open (plus 19
  for Quagmire II on one constraint).
- **Quagmire III Beaufort:** with all three guesses, 13, 18 and 26 are eliminated. 23 stays
  satisfiable at random-text rates.
- **Quagmire IV:** with all three guesses, 8, 13, 16, 20 are eliminated, and 23 and 24 stay
  satisfiable at random-text rates. **Length 19** stays satisfiable with or without guesses, while
  plain random text almost never is (0/30). The cause is K4's repeated pair (R→P at 28 and 66, 38 =
  2×19 apart). Random ciphertexts given that same repeat are satisfiable 21/30, so length 19 is
  explained, not a signal (evidence `21`, `21b`).
- IS alone makes Quagmire IV length 8 satisfiable, but random text is too, 9/30 (evidence `22`).
- **Nothing under any guess beats the random-text rate.**

**A published full reconstruction.** solvekryptos.com proposes a complete 97-letter plaintext
(THECOMPASSROSEISHERE…), which its author has not checked against Paradigm's verifier. Taken as a
hypothesis it fits nothing here: no repeating key of any length up to 95 in any of the 8 families,
no Quagmire I–IV at any open length, no Hill 4×4, no autokey. The method offered with it gives
each of K4's four rows its own lookup table from the opposite tableau letter to a shift, plus a
free bit per position, which is more free values than there are letters, so any plaintext would
fit (evidence `27`). With a single lookup table the same idea is testable, and fails (§4.B, `26`).

Earlier, 52 theme words (WELTZEITUHR, BERLINWALL, EGYPT, COMPASSROSE, DELIVER, …) were slid across
every open position against repeating keys of length 27–48. That gave 23 survivors against 109
expected by chance, and none held 4+ constraints (evidence `19`).

## 6. What remains open, and why

Every classical single-layer cipher that 24 letters can test is eliminated, along with every
transposition-plus-repeating-key combination searched. What remains falls into cases the clues
**cannot decide**. The obstacle there is information, not computing power:

- **Too many unknowns.** Two free alphabets, keys longer than 26, or stacked layers with long keys
  have more unknowns than 24 letters can pin down. Many keys fit equally well, so neither exact
  search nor English scoring can single one out from 97 letters.
- **Methods without a clean form.** Ed Scheidt, who taught Sanborn, has described "masking"
  techniques. A hand method invented for the sculpture may not belong to any family that can be
  written down and searched.
- **Keys from sources not tried.** With the A–Z and KRYPTOS alphabets no English or German text
  can be the key (§4.B), so what is left is a key text in another language, a key that isn't
  prose, or a key under an alphabet that isn't in the dictionary. The World Clock's city names are
  one such list. The forced key letters share no more than 4 letters in a row with any of 502
  city names in the time-zone database, the same as random text (evidence `24`), but those are
  English spellings.
  There's no reliable per-face list of the German names, and the 1997 renovation changed them
  (Leningrad, Alma Ata, Bratislava; Jerusalem and Tel Aviv added), so today's clock isn't the one
  Sanborn saw in 1990.
- **Not yet searched:** transposition searches with typo tolerance, keyed double columnar, route
  ciphers other than columns and rotations, fractionation on a 6×6 square.

**What would change this:** more confirmed plaintext, or **K5**. Sanborn created a second
97-character passage, reportedly in the same system, and Paradigm plans to release it. Two
messages under one method double the constraints, and much of what is undecidable today would
become decidable. Sanborn has said the two messages share some of the same coded words in the same
positions. If that means equal ciphertext for equal plaintext at the same place, the cipher depends
only on position, and K4 and K5 are two messages under one key: subtracting one from the other
removes the key in every additive family. Every search here can be rerun against K5 as soon as it
is public.

## 7. Reproduce

```
make verify                   # build, then 28 planted-cipher checks (~30 s)
checks/fetch_texts.sh         # download the public-domain running-key texts (~6 MB)
checks/quadgrams_local.py     # or: English and (with 'german') German letter statistics, no download
checks/reproduce.sh           # regenerate the quick evidence logs in results/ (~1 min)
checks/reproduce.sh --long    # also rerun the multi-hour searches
KRYPTOS_GUESS="61:THE" python3 guess_run.py    # rerun the open families under a guess
```

Requires Python 3 with numpy, and a C compiler. The dictionary searches use macOS's
`/usr/share/dict/words` and `propernames`.

## 8. Sources

- Wikipedia, *Kryptos*: https://en.wikipedia.org/wiki/Kryptos (ciphertext, clue history, auction, archive discovery)
- Paradigm, *Project Kryptos*: https://www.paradigm.xyz/writing/kryptos (verification service)
- Scientific American, *A Solution to the CIA's Kryptos Code Is Found after 35 Years*: https://www.scientificamerican.com/article/a-solution-to-the-cias-kryptos-code-is-found-after-35-years/
- Scientific American, *Artist Releases Final Clues to Solve CIA Kryptos Puzzle*: https://www.scientificamerican.com/article/cia-kryptos-puzzle-creator-releases-final-clues/
- German Wikipedia, *Weltzeituhr (Alexanderplatz)*: https://de.wikipedia.org/wiki/Weltzeituhr_(Alexanderplatz)
- Running-key texts: Internet Archive and Project Gutenberg (`data/SOURCES.md`)
